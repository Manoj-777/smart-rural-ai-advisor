"""
Apply all handler.py optimizations directly to disk:
1. import time as _time
2. Constants: API_GW_TIMEOUT_SEC, TTS_TIME_BUDGET_SEC, FAST_PATH_PREFIXES
3. Timer + _is_feature_page detection
4. Fast-path routing for feature pages
5. TTS skip for feature pages, time-budget for chat
6. Timing log before return
"""
import re

path = r'c:\Users\MSanjay1\OneDrive - Unisys\Documents\AI Workshop AWS\Rural AI workshop\smart-rural-ai-advisor\backend\lambdas\agent_orchestrator\handler.py'

with open(path, encoding='utf-8') as f:
    content = f.read()

original = content  # keep backup

# ── 1. Add 'import time as _time' after 'import re' ──
content = content.replace(
    'import re\nfrom concurrent.futures',
    'import re\nimport time as _time\nfrom concurrent.futures'
)
assert 'import time as _time' in content, "FAIL: time import"
print("1. time import added")

# ── 2. Add constants after 'logger.setLevel(logging.INFO)' ──
content = content.replace(
    'logger.setLevel(logging.INFO)\n',
    (
        'logger.setLevel(logging.INFO)\n'
        '\n'
        '# API Gateway hard timeout is 29s. We must return before that.\n'
        'API_GW_TIMEOUT_SEC = 29\n'
        'TTS_TIME_BUDGET_SEC = 18  # skip TTS if elapsed > this\n'
        '\n'
        '# Feature-page session prefixes: pre-structured prompts that\n'
        '# don\'t need the 4-agent cognitive pipeline.\n'
        'FAST_PATH_PREFIXES = (\'crop-recommend-\', \'soil-analysis-\', \'farm-calendar-\')\n'
    )
)
assert 'FAST_PATH_PREFIXES' in content, "FAIL: constants"
print("2. Constants added")

# ── 3. Add timer + _is_feature_page detection ──
content = content.replace(
    "        if not user_message:\n            return error_response('Message is required', 400)",
    (
        "        _t_start = _time.time()\n"
        "        _is_feature_page = any(session_id.startswith(p) or body.get('session_id', '').startswith(p) for p in FAST_PATH_PREFIXES)\n"
        "        logger.info(f'Session {session_id} | feature_page={_is_feature_page}')\n"
        "\n"
        "        if not user_message:\n"
        "            return error_response('Message is required', 400)"
    )
)
assert '_is_feature_page' in content, "FAIL: feature page detection"
print("3. Timer + feature page detection added")

# ── 4. Fast-path routing for feature pages ──
content = content.replace(
    "        # --- Step 3: Invoke AI Agent ---\n"
    "        pipeline_meta_extra = {}\n"
    "\n"
    "        if USE_AGENTCORE and PIPELINE_MODE == 'cognitive':",
    (
        "        # --- Step 3: Invoke AI Agent ---\n"
        "        pipeline_meta_extra = {}\n"
        "\n"
        "        if _is_feature_page:\n"
        "            # FAST PATH: feature pages skip 4-agent pipeline, use single Bedrock call\n"
        "            logger.info(f'FAST PATH for feature page (elapsed {_time.time()-_t_start:.1f}s)')\n"
        "            routed_prompt = _build_tool_first_prompt(english_message, intents, farmer_context)\n"
        "            result_text, tools_used, _ = _invoke_bedrock_direct(routed_prompt, farmer_context)\n"
        "\n"
        "        elif USE_AGENTCORE and PIPELINE_MODE == 'cognitive':"
    )
)
assert 'FAST PATH for feature page' in content, "FAIL: fast-path routing"
print("4. Fast-path routing added")

# ── 5. Replace TTS section: skip for feature pages, time-budget for chat ──
old_tts = (
    "        # --- Step 5: Generate Polly audio ---\n"
    "        audio_url = None\n"
    "        polly_text_truncated = False\n"
    "        try:\n"
    "            polly_result = text_to_speech(\n"
    "                translated_reply,\n"
    "                detected_lang or 'en',\n"
    "                return_metadata=True,\n"
    "            )\n"
    "            if isinstance(polly_result, dict):\n"
    "                audio_url = polly_result.get('audio_url')\n"
    "                polly_text_truncated = bool(polly_result.get('truncated', False))\n"
    "            else:\n"
    "                audio_url = polly_result\n"
    "        except Exception as polly_err:\n"
    '            logger.warning(f"Polly audio failed (non-fatal): {polly_err}")'
)

new_tts = (
    "        # --- Step 5: Generate TTS audio ---\n"
    "        _elapsed = _time.time() - _t_start\n"
    "        audio_url = None\n"
    "        polly_text_truncated = False\n"
    "        if _is_feature_page:\n"
    "            logger.info(f'Feature page - skipping TTS for speed (elapsed {_elapsed:.1f}s)')\n"
    "        elif _elapsed > TTS_TIME_BUDGET_SEC:\n"
    "            logger.warning(f'Skipping TTS - elapsed {_elapsed:.1f}s > {TTS_TIME_BUDGET_SEC}s budget')\n"
    "        else:\n"
    "            try:\n"
    "                polly_result = text_to_speech(\n"
    "                    translated_reply,\n"
    "                    detected_lang or 'en',\n"
    "                    return_metadata=True,\n"
    "                )\n"
    "                if isinstance(polly_result, dict):\n"
    "                    audio_url = polly_result.get('audio_url')\n"
    "                    polly_text_truncated = bool(polly_result.get('truncated', False))\n"
    "                else:\n"
    "                    audio_url = polly_result\n"
    "                logger.info(f'TTS completed in {_time.time()-_t_start-_elapsed:.1f}s, audio={bool(audio_url)}')\n"
    "            except Exception as polly_err:\n"
    '                logger.warning(f"Polly audio failed (non-fatal): {polly_err}")'
)

assert old_tts in content, f"FAIL: old TTS not found"
content = content.replace(old_tts, new_tts)
assert 'Feature page - skipping TTS' in content, "FAIL: TTS skip"
print("5. TTS skip for feature pages added")

# ── 6. Add timing log before return ──
content = content.replace(
    "        # --- Step 7: Return response (matches API contract) ---\n"
    "        return success_response({",
    (
        "        # --- Step 7: Return response (matches API contract) ---\n"
        "        logger.info(f'Total handler time: {_time.time()-_t_start:.1f}s | feature_page={_is_feature_page} | audio={bool(audio_url)}')\n"
        "        return success_response({"
    )
)
assert 'Total handler time' in content, "FAIL: timing log"
print("6. Timing log added")

# ── Write to disk ──
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("\nALL CHANGES WRITTEN TO DISK")

# ── Verify ──
with open(path, encoding='utf-8') as f:
    verify = f.read()

checks = [
    ('import time as _time', 'time import'),
    ('FAST_PATH_PREFIXES', 'constants'),
    ('_is_feature_page', 'feature page detection'),
    ('FAST PATH for feature page', 'fast-path routing'),
    ('Feature page - skipping TTS', 'TTS skip'),
    ('Total handler time', 'timing log'),
]
all_ok = True
for text, label in checks:
    ok = text in verify
    if not ok:
        all_ok = False
    print(f"  {label}: {'OK' if ok else 'MISSING'}")

lines = verify.split('\n')
print(f"\nTotal lines: {len(lines)}")

# Syntax check
import ast
ast.parse(verify)
print("Syntax: OK")

if all_ok:
    print("\n=== ALL OPTIMIZATIONS APPLIED SUCCESSFULLY ===")
else:
    print("\n=== SOME CHANGES MISSING - CHECK ABOVE ===")
