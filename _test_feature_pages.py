"""Test all feature pages (crop-recommend, soil-analysis, farm-calendar) + chat
for Tamil, Telugu, Kannada, Hindi to verify:
- Feature pages: fast response, NO audio
- Chat page: response with audio (if within time budget)
"""
import json, time, urllib.request

API = "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod"

tests = [
    # (label, session_prefix, message, language)
    ("CropRecommend-Tamil",  "crop-recommend-test1", "What is the best crop for red soil in summer season in Tamil Nadu?", "ta"),
    ("CropRecommend-Telugu", "crop-recommend-test2", "What crop should I plant in black soil during kharif?", "te"),
    ("CropRecommend-Kannada","crop-recommend-test3", "Suggest crops for sandy loam soil in Karnataka rabi season", "kn"),
    ("CropRecommend-Hindi",  "crop-recommend-test4", "Which crop is best for clay soil in UP?", "hi"),
    ("SoilAnalysis-Tamil",   "soil-analysis-test1",  "How to improve soil fertility for paddy?", "ta"),
    ("FarmCalendar-Tamil",   "farm-calendar-test1",  "What should I plant in June in Tamil Nadu?", "ta"),
    ("Chat-Tamil",           "chat-test-tamil1",     "What government schemes are available for farmers?", "ta"),
    ("Chat-Hindi",           "chat-test-hindi1",     "Tell me about PM Kisan scheme", "hi"),
]

results = []
for label, session, msg, lang in tests:
    payload = json.dumps({"message": msg, "session_id": session, "language": lang}).encode()
    req = urllib.request.Request(f"{API}/chat", data=payload, headers={"Content-Type": "application/json"})
    
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            elapsed = time.time() - t0
            data = json.loads(resp.read())
            body = data if 'reply' in data else json.loads(data.get('body', '{}'))
            has_audio = bool(body.get('audio_url'))
            reply_len = len(body.get('reply', ''))
            status = "OK"
    except Exception as e:
        elapsed = time.time() - t0
        has_audio = False
        reply_len = 0
        status = f"FAIL: {e}"
    
    is_feature = any(session.startswith(p) for p in ['crop-recommend-', 'soil-analysis-', 'farm-calendar-'])
    expected_no_audio = is_feature  # Feature pages should have NO audio
    audio_check = "CORRECT" if (not has_audio) == expected_no_audio else "UNEXPECTED"
    
    results.append((label, elapsed, status, has_audio, reply_len, audio_check))
    print(f"{label:25s} | {elapsed:5.1f}s | {status:6s} | audio={str(has_audio):5s} ({audio_check:10s}) | reply={reply_len} chars")

print("\n=== SUMMARY ===")
ok = sum(1 for r in results if r[2] == 'OK')
print(f"Passed: {ok}/{len(results)}")
feature_fast = [r for r in results if any(r[0].startswith(p) for p in ['CropRecommend', 'SoilAnalysis', 'FarmCalendar'])]
if feature_fast:
    avg = sum(r[1] for r in feature_fast if r[2] == 'OK') / max(1, sum(1 for r in feature_fast if r[2] == 'OK'))
    print(f"Feature page avg time: {avg:.1f}s")
chat_tests = [r for r in results if r[0].startswith('Chat')]
if chat_tests:
    avg = sum(r[1] for r in chat_tests if r[2] == 'OK') / max(1, sum(1 for r in chat_tests if r[2] == 'OK'))
    print(f"Chat page avg time: {avg:.1f}s")
