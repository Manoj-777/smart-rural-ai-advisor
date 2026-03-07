# Active Bug Verification Report

Date: 2026-03-07
Scope: Retained active bug set in bugfix/design/tasks
Method: Scripted static verification + syntax parse check, then local fix validation updates

## Verdict Summary

No retained active bug IDs are currently reproducible under the verification criteria used.
Bugs 1.8, 1.9, 1.12, 1.13, 1.15, 1.16, 1.22, 1.23, 1.25, 1.27, 1.28, 1.29, 1.31, 1.32, 1.33, 1.34, and 1.35 have been fixed locally and moved out of the retained-active list.

## Per-bug Evidence

No remaining active defects in the retained scope.


## Confidence Notes

- High confidence (direct, objective defects): none currently retained.
- Medium confidence (policy/coverage standardization issues): none currently retained.

## Post-fix Note (Bug 1.8)

- Implemented: lock-protected profile cache access in `backend/utils/dynamodb_helper.py`.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_8_profile_cache_thread_safety.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_14_to_1_28_medium_low.py -k profile_cache -q` → `1 passed`

## Post-fix Note (Bug 1.9)

- Implemented: chunked batch writes across all messages in `backend/utils/dynamodb_helper.py`.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_9_batch_write_chunking.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_14_to_1_28_medium_low.py -k chat_batch_write -q` → `1 passed`

## Post-fix Note (Bug 1.12)

- Implemented: expanded crop advisory injection checks to include SQL and command-injection signatures in `backend/lambdas/crop_advisory/handler.py`.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_12_crop_injection_coverage.py -q` → `4 passed`
	- `python -m pytest backend/tests/test_bug_1_6_kb_retry.py -q` → `2 passed`

## Post-fix Note (Bug 1.13)

- Implemented: strict origin validation/rejection in `backend/utils/response_helper.py` (unauthorized origins return 403 and do not receive allow-origin header).
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_13_cors_origin_rejection.py -q` → `4 passed`
	- `python -m pytest backend/tests/test_bug_1_14_to_1_28_medium_low.py -k unified_cors_preflight -q` → `1 passed`

## Post-fix Note (Bug 1.15)

- Implemented: full-entropy transcribe job ID generation via `_generate_job_id()` in `backend/lambdas/transcribe_speech/handler.py`.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_15_transcribe_job_id_entropy.py -q` → `3 passed`

## Post-fix Note (Bug 1.16)

- Implemented: rate limiter exception path is fail-closed in `backend/utils/rate_limiter.py` (returns `allowed: False` with retry guidance when backend store is unavailable).
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_16_rate_limiter_fail_closed.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_3_rate_limit_ttl.py -q` → `2 passed`

## Post-fix Note (Bug 1.22)

- Implemented: indirect sabotage toxicity pattern coverage expanded in `backend/lambdas/agent_orchestrator/utils/guardrails.py` and synchronized in `backend/utils/guardrails.py`.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_22_indirect_toxicity.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_12_1_13_guardrails.py -q` → `2 passed`

## Post-fix Note (Bug 1.23)

- Implemented: broadened HTML artifact stripping in `backend/utils/translate_helper.py` to remove generic leaked tags while preserving markdown/plain-text behavior.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_23_html_artifact_stripping.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_14_to_1_28_medium_low.py -q` → `6 passed`

## Post-fix Note (Bug 1.25)

- Implemented: audit timestamp format in `backend/utils/audit_logger.py` now uses second precision (`YYYY-MM-DDTHH:MM:SSZ`) with UTC `Z` suffix and no microseconds.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_25_audit_timestamp_precision.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_14_to_1_28_medium_low.py -q` → `6 passed`

## Post-fix Note (Bug 1.27)

- Implemented: `backend/lambdas/govt_schemes/handler.py` now filters `state_schemes` by provided `farmer_state` (case-insensitive), while preserving full state list when no state is provided.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_27_state_scheme_filtering.py -q` → `3 passed`
	- `python -m pytest backend/tests/test_bug_1_14_to_1_28_medium_low.py -q` → `6 passed`

## Post-fix Note (Bug 1.28)

- Implemented: `backend/lambdas/image_analysis/handler.py` now rejects unknown signatures with explicit 400 responses, removes JPEG fallback for unknown media type detection, and returns 400 for invalid base64 payloads.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_28_media_type_validation.py -q` → `3 passed`
	- `python -m pytest backend/tests/test_bug_1_14_to_1_28_medium_low.py -q` → `6 passed`

## Post-fix Note (Bug 1.29)

- Implemented: `backend/lambdas/transcribe_speech/handler.py` now includes explicit `or-IN` mapping in `LANGUAGE_MAP`, with unsupported fallback preserved for `as-IN` and `ur-IN`.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_29_odia_language_mapping.py -q` → `3 passed`
	- `python -m pytest backend/tests/test_bug_1_15_transcribe_job_id_entropy.py -q` → `3 passed`

## Post-fix Note (Bug 1.31)

- Implemented: `backend/lambdas/agent_orchestrator/handler.py` timeout HTTP response now uses shared CORS headers from `utils.cors_helper.get_cors_headers()` instead of hardcoded header dict.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_31_cors_unification.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_13_cors_origin_rejection.py -q` → `4 passed`

## Post-fix Note (Bug 1.32)

- Implemented: in `backend/lambdas/agent_orchestrator/handler.py`, operational/non-failure log events (runtime pass-through and invalid model override rejection) now use `logger.info`, with warning/error retained for degraded/failure conditions.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_32_log_severity_policy.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_31_cors_unification.py -q` → `2 passed`

## Post-fix Note (Bug 1.33)

- Implemented: `backend/lambdas/farmer_profile/handler.py` now emits canonical error envelopes (`status`, `data`, `message`, `language`) with backward-compatible legacy `error` field across profile/OTP/PIN error paths.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_33_error_envelope_consistency.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_32_log_severity_policy.py -q` → `2 passed`

## Post-fix Note (Bug 1.34)

- Implemented: removed `AgentOrchestratorFunction` timeout override in `infrastructure/template.yaml`, so global timeout policy is consistently applied.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_34_timeout_policy.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_33_error_envelope_consistency.py -q` → `2 passed`

## Post-fix Note (Bug 1.35)

- Implemented: `backend/lambdas/agent_orchestrator/handler.py` now includes startup required-env validator pattern (`_validate_required_env_vars`) with actionable missing-variable error logging.
- Local validation:
	- `python -m pytest backend/tests/test_bug_1_35_startup_env_validation.py -q` → `2 passed`
	- `python -m pytest backend/tests/test_bug_1_32_log_severity_policy.py -q` → `2 passed`

## Post-close Hardening Note (Local-language list formatting)

- Implemented:
	- `backend/lambdas/agent_orchestrator/handler.py` preserves leading indentation in list lines and disables heading auto-numbering for Indic-language outputs.
	- `backend/utils/polly_helper.py` preserves numeric list markers for Indic-script text even when `ENABLE_TTS_LIST_FORMATTING=true`.
	- Added regression coverage in `backend/tests/test_bug_local_language_list_formatting.py`.
- Local validation:
	- `python -m pytest backend/tests/test_bug_local_language_list_formatting.py backend/tests/test_bug_1_14_to_1_28_medium_low.py -q` → `10 passed`

## Repro Script

A one-off verification script was run from workspace root as _bug_verify.py to produce machine output for the table above.

## Final Validation Gate (1.37–1.41)

- Executed workspace regression task: `phase3-full-regression`
- Command: `python -u scripts/regression_multilang.py --max-workers 2 --delay 0.2`
- Result summary:
	- Total: 224
	- Pass: 224
	- Fail: 0
	- Pass rate: 1.0
	- By language: en 56/56, ta 56/56, hi 56/56, te 56/56
	- Elapsed: 476.99s
- Artifacts:
	- `artifacts/phase3_regression_report_20260307_082630.json`
	- `artifacts/phase3_regression_report_20260307_082630.md`

Conclusion: Final validation checklist items 1.37, 1.38, 1.39, 1.40, and 1.41 are complete.
