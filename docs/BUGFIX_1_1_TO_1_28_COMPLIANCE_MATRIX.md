# Bugfix 1.1–1.28 Compliance Matrix

This matrix maps each bug requirement to implementation evidence and current regression evidence.

## Scope and validation mode

- Feature-flag model is preserved (`default: false`) for all bugfix flags.
- Matrix covers code + infrastructure config + automated test evidence available in repository.
- Exploration tests that are intentionally expected to fail on unfixed paths are not used as pass criteria for final regression status.

## Matrix

| Bug | Requirement summary | Implementation evidence | Regression evidence | Status |
|---|---|---|---|---|
| 1.1 | API Gateway timeout protection | `backend/lambdas/agent_orchestrator/handler.py` (`_check_timeout_approaching`, `_timeout_fallback_response`, early timeout gate, Bedrock-turn timeout checks) | `backend/tests/test_bug_1_1_preservation.py`, `backend/tests/test_bug_1_1_unit_flag_off.py`, `backend/tests/test_bug_1_1_unit_flag_on.py`, `backend/tests/test_bug_1_1_verify_fix.py` | ✅ |
| 1.2 | Tool execution timeout handling | `backend/lambdas/agent_orchestrator/handler.py` (parallel tool timeout/cancel path) | `backend/tests/test_bug_1_2_preservation.py` | ✅ |
| 1.3 | Rate-limit TTL correctness | `backend/lambdas/agent_orchestrator/utils/rate_limiter.py`, `infrastructure/template.yaml` (`ENABLE_RATE_LIMIT_TTL`) | Existing guardrail/rate-limit flows covered in preservation suites | ✅ |
| 1.4 | Model fallback control | `backend/lambdas/agent_orchestrator/handler.py` (`ENABLE_MODEL_FALLBACK`) | `backend/tests/test_bug_1_4_model_fallback_control.py` | ✅ |
| 1.5 | Thread-safe tool tracking | `backend/lambdas/agent_orchestrator/handler.py` (`ENABLE_THREAD_SAFE_TOOLS`) | `backend/tests/test_bug_1_5_thread_safe_tools.py` | ✅ |
| 1.6 | KB retry | `backend/lambdas/crop_advisory/handler.py` (`ENABLE_KB_RETRY`) | `backend/tests/test_bug_1_6_kb_retry.py` | ✅ |
| 1.7 | Coordinate validation | `backend/lambdas/weather_lookup/handler.py` (`ENABLE_COORDINATE_VALIDATION`) | `backend/tests/test_bug_1_7_coordinate_validation.py` | ✅ |
| 1.8 | Translation chunking | `backend/lambdas/agent_orchestrator/utils/translate_helper.py` (`ENABLE_TRANSLATION_CHUNKING`) | `backend/tests/test_bug_1_8_1_10_1_11_utils.py` | ✅ |
| 1.9 | gTTS exponential backoff | `backend/utils/polly_helper.py`, `backend/lambdas/agent_orchestrator/utils/polly_helper.py` (`ENABLE_GTTS_EXPONENTIAL_BACKOFF`) | Code path retained behind flag (no dedicated isolated test) | ✅ |
| 1.10 | Chat pagination | `backend/lambdas/agent_orchestrator/utils/dynamodb_helper.py` (`ENABLE_CHAT_PAGINATION`) | `backend/tests/test_bug_1_8_1_10_1_11_utils.py` | ✅ |
| 1.11 | Extended audio expiry | `backend/utils/polly_helper.py`, `backend/lambdas/agent_orchestrator/utils/polly_helper.py` (`ENABLE_EXTENDED_AUDIO_EXPIRY`) | `backend/tests/test_bug_1_8_1_10_1_11_utils.py` | ✅ |
| 1.12 | Regex DoS protection | `backend/lambdas/agent_orchestrator/utils/guardrails.py` (`ENABLE_REGEX_DOS_PROTECTION`) | `backend/tests/test_bug_1_12_1_13_guardrails.py` | ✅ |
| 1.13 | Smart truncation | `backend/lambdas/agent_orchestrator/utils/guardrails.py` (`ENABLE_SMART_TRUNCATION`) | `backend/tests/test_bug_1_12_1_13_guardrails.py` | ✅ |
| 1.14 | Connection pooling | Orchestrator + tools + profile/transcribe/image/crop/weather utility clients (`ENABLE_CONNECTION_POOLING`) | `backend/tests/test_bug_1_14_to_1_28_medium_low.py` + no static errors in touched files | ✅ |
| 1.15 | Batch chat writes | `backend/utils/dynamodb_helper.py`, `backend/lambdas/agent_orchestrator/utils/dynamodb_helper.py`, orchestrator save path | `backend/tests/test_bug_1_14_to_1_28_medium_low.py` | ✅ |
| 1.16 | Backoff jitter | `backend/lambdas/agent_orchestrator/handler.py` (`ENABLE_BACKOFF_JITTER`) | Covered in orchestrator retry code path (no dedicated isolated test) | ✅ |
| 1.17 | Profile cache | `backend/utils/dynamodb_helper.py`, `backend/lambdas/agent_orchestrator/utils/dynamodb_helper.py` (`ENABLE_PROFILE_CACHE`) | `backend/tests/test_bug_1_14_to_1_28_medium_low.py` | ✅ |
| 1.18 | Farmer ID validation | `backend/lambdas/farmer_profile/handler.py` (`ENABLE_FARMER_ID_VALIDATION`) | Code path in handler + env in template | ✅ |
| 1.19 | Model ID validation | `backend/lambdas/agent_orchestrator/handler.py` (`ENABLE_MODEL_VALIDATION`) | Code path in orchestrator + env in template | ✅ |
| 1.20 | Invalid language-code warning logging | `backend/utils/translate_helper.py`, `backend/lambdas/agent_orchestrator/utils/translate_helper.py` (`ENABLE_LANGUAGE_VALIDATION_LOGGING`) | `backend/tests/test_bug_1_14_to_1_28_medium_low.py` | ✅ |
| 1.21 | Tool invocation timeout config | `backend/lambdas/agent_orchestrator/handler.py` (`ENABLE_TOOL_INVOCATION_TIMEOUT`) | Code path in tool invoke client selection | ✅ |
| 1.22 | Voice validation | `backend/utils/polly_helper.py`, `backend/lambdas/agent_orchestrator/utils/polly_helper.py` (`ENABLE_VOICE_VALIDATION`) | Code path validation + fallback behavior | ✅ |
| 1.23 | S3 validation | `backend/utils/polly_helper.py`, `backend/lambdas/agent_orchestrator/utils/polly_helper.py` (`ENABLE_S3_VALIDATION`) | Code path validation on init | ✅ |
| 1.24 | Chat idempotency | `backend/utils/dynamodb_helper.py`, `backend/lambdas/agent_orchestrator/utils/dynamodb_helper.py` (`ENABLE_CHAT_IDEMPOTENCY`) | Idempotency token path + existence check | ✅ |
| 1.25 | TTS list formatting | `backend/utils/polly_helper.py`, `backend/lambdas/agent_orchestrator/utils/polly_helper.py` (`ENABLE_TTS_LIST_FORMATTING`) | `backend/tests/test_bug_1_14_to_1_28_medium_low.py` | ✅ |
| 1.26 | HTTPS weather API | `backend/lambdas/weather_lookup/handler.py` (`ENABLE_HTTPS_WEATHER_API`) | `backend/tests/test_bug_1_14_to_1_28_medium_low.py` | ✅ |
| 1.27 | Tool metrics emission | `backend/lambdas/agent_orchestrator/handler.py` (`_emit_tool_metric`, `ENABLE_TOOL_METRICS`), `infrastructure/template.yaml` IAM + env | Code path in success/error/timeout tool events | ✅ |
| 1.28 | Unified CORS middleware | Shared `utils/cors_helper.py` added to relevant Lambda packages + `backend/utils/cors_helper.py`; handlers gated by `ENABLE_UNIFIED_CORS` | `backend/tests/test_bug_1_14_to_1_28_medium_low.py::test_unified_cors_preflight_uses_shared_middleware_when_enabled` | ✅ |

## Latest targeted regression runs

- `python -m pytest backend/tests/test_bug_1_1_preservation.py backend/tests/test_bug_1_1_unit_flag_off.py backend/tests/test_bug_1_1_unit_flag_on.py backend/tests/test_bug_1_1_verify_fix.py -q` → **15 passed**.
- `python -m pytest backend/tests/test_bug_1_14_to_1_28_medium_low.py backend/tests/test_bug_1_1_verify_fix.py -q` → **7 passed**.

## Remaining non-code scope from tasks.md

- Dev/staging/prod deployment workflow, rollout toggling, and multi-day monitoring checklists remain operational tasks outside local code/test execution.