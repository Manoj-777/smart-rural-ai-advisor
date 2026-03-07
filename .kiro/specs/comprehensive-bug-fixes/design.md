# Smart Rural AI Advisor - Active Bug Fixes Design

## Overview

This design document now covers only currently reproducible bugs.

Active bugs retained:
- Critical: none
- High: none
- Medium: none
- Low: none

Recently fixed:
- 1.8 Profile cache thread safety (lock-protected cache read/write in `backend/utils/dynamodb_helper.py`, with targeted tests).
- 1.9 Batch write truncation (chunked batch writes across all messages, with >25 and <=25 tests).
- 1.12 Injection coverage in crop advisory (`_check_injection` expanded for SQL/command signatures with safe-query preservation tests).
- 1.13 CORS origin validation (`utils.response_helper` now rejects unauthorized origins with 403 and no allow-origin header).
- 1.15 Transcribe job ID entropy (`voice-` + full UUID hex via `_generate_job_id()`).
- 1.16 Rate limiter fail-open (`backend/utils/rate_limiter.py` now fails closed on persistence exceptions).
- 1.22 Indirect toxicity coverage (`utils/guardrails.py` now detects indirect sabotage crop-failure phrasing while preserving benign prevention queries).
- 1.23 HTML artifact stripping (`utils/translate_helper.py` now removes broader HTML tag artifacts from translated output while preserving markdown/plain text semantics).
- 1.25 Audit timestamp precision (`utils/audit_logger.py` now emits second-precision UTC timestamps with no microseconds).
- 1.27 State schemes filtering (`lambdas/govt_schemes/handler.py` now filters `state_schemes` by provided `farmer_state` while preserving national schemes output).
- 1.28 Media validation fallback (`lambdas/image_analysis/handler.py` now rejects unknown/corrupt media with explicit 400 errors and no JPEG default fallback).
- 1.29 Odia mapping in transcribe (`lambdas/transcribe_speech/handler.py` now maps `or-IN` explicitly while preserving fallback behavior for unsupported language codes).
- 1.31 CORS standardization (`lambdas/agent_orchestrator/handler.py` timeout response headers now come from shared `utils.cors_helper.get_cors_headers`).
- 1.32 Logging severity policy (`lambdas/agent_orchestrator/handler.py` now logs non-failure operational events at `info` level and reserves warnings/errors for degraded/failure paths).
- 1.33 Error envelope consistency (`lambdas/farmer_profile/handler.py` now emits canonical error envelopes with backward-compatible `error` field).
- 1.34 Timeout policy alignment (`infrastructure/template.yaml` now uses global function timeout policy for agent orchestrator without conflicting override).
- 1.35 Startup env validation (`lambdas/agent_orchestrator/handler.py` now validates required runtime env vars at startup and logs actionable missing-var errors).
- Post-close hardening: local-language list formatting (`lambdas/agent_orchestrator/handler.py` now preserves indentation and avoids forced heading auto-numbering for Indic languages; `utils/polly_helper.py` keeps numeric points for Indic-script TTS text).

## Design Goals

1. Fix correctness and safety defects first (critical + high).
2. Keep behavior unchanged for non-buggy paths.
3. Standardize cross-cutting concerns (CORS, logging, error schema, env validation).

## Active Bug Design Details

### CRITICAL

No currently retained critical defects.

### HIGH

No currently retained high-priority defects.

### MEDIUM

No currently retained medium-priority defects.

### LOW (STANDARDIZATION)

#### Bugs 1.31, 1.32, 1.33, 1.34, 1.35

**Design**
No currently retained low-priority defects.

## Testing Strategy

### Phases
1. Reproduce each active bug with focused tests.
2. Implement fix with minimal scope.
3. Re-run bug tests and regression tests.
4. Run integration checks on key flows.

### Required checks per bug
- **Fault reproduction test**: confirms bug exists in current code.
- **Fix verification test**: same test passes after fix.
- **Preservation test**: non-buggy behavior remains unchanged.

### Integration checks
- Chat flow with rate limit + guardrails.
- Transcription flow with unique job IDs + language mapping.
- Schemes flow with state filtering.
- Image flow with strict media validation.
- Cross-handler CORS and error-format consistency.

## Acceptance Criteria

- All retained active bug IDs fixed: 1.8, 1.9, 1.12, 1.13, 1.15, 1.16, 1.22, 1.23, 1.25, 1.27, 1.28, 1.29, 1.31, 1.32, 1.33, 1.34, 1.35.
- No silent data loss paths remain.
- No fail-open rate-limit path remains.
- No inconsistent CORS/error schema behavior remains across handlers.
