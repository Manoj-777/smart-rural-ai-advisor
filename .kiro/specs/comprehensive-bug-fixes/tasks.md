# Implementation Plan: Active Bug Fixes Only

## Overview

This task list contains only currently reproducible bugs:
- Critical: none
- High: none
- Medium: none
- Low: none

Recently completed:
- 1.8 Profile cache thread safety (all 1.8.x tasks complete)
- 1.9 Batch write truncation (all 1.9.x tasks complete)
- 1.12 Injection checks coverage expansion (all 1.12.x tasks complete)
- 1.13 CORS unauthorized-origin rejection (all 1.13.x tasks complete)
- 1.15 Transcribe job ID entropy increase (all 1.15.x tasks complete)
- 1.16 Rate limiter fail-closed behavior (all 1.16.x tasks complete)
- 1.22 Indirect toxicity pattern coverage (all 1.22.x tasks complete)
- 1.23 HTML artifact stripping broadening (all 1.23.x tasks complete)
- 1.25 Audit timestamp precision (all 1.25.x tasks complete)
- 1.27 State schemes filtering by farmer_state (all 1.27.x tasks complete)
- 1.28 Corrupt-media validation hardening (all 1.28.x tasks complete)
- 1.29 Odia transcribe language mapping (all 1.29.x tasks complete)
- 1.31 CORS helper standardization in agent orchestrator timeout response (all 1.31.x tasks complete)
- 1.32 Logging severity policy alignment in agent orchestrator (all 1.32.x tasks complete)
- 1.33 Canonical error envelope alignment in farmer_profile handler (all 1.33.x tasks complete)
- 1.34 Timeout policy alignment between globals and orchestrator config (all 1.34.x tasks complete)
- 1.35 Startup required-env validation in agent orchestrator (all 1.35.x tasks complete)
- Post-close hardening: local-language list indentation/numbering formatting (completed with regression tests)

Method for each bug:
1) Reproduce fault on current code
2) Add preservation test(s)
3) Implement fix
4) Re-run same tests

---

## CRITICAL

### Bug 1.8: Profile cache not thread-safe (Completed)
- [x] 1.8.1 Add concurrent access race reproduction test
- [x] 1.8.2 Add preservation test for cache TTL behavior
- [x] 1.8.3 Add lock-protected cache access
- [x] 1.8.4 Re-run 1.8.1 and 1.8.2

### Bug 1.9: Batch write drops messages >25 (Completed)
- [x] 1.9.1 Add reproduction test with 30+ messages
- [x] 1.9.2 Add preservation test for <=25 messages
- [x] 1.9.3 Implement chunked batch writes (all items)
- [x] 1.9.4 Re-run 1.9.1 and 1.9.2

- [x] 1.10 Checkpoint: Critical complete

---

## HIGH

### Bug 1.12: Injection checks too narrow (Completed)
- [x] 1.12.1 Add reproduction test for SQL/command injection pass-through
- [x] 1.12.2 Add preservation tests for safe agri queries
- [x] 1.12.3 Expand injection detection patterns
- [x] 1.12.4 Re-run 1.12.1 and 1.12.2

### Bug 1.13: CORS unauthorized origin fallback (Completed)
- [x] 1.13.1 Add reproduction test for unauthorized origin accepted path
- [x] 1.13.2 Add preservation tests for allowed origins
- [x] 1.13.3 Enforce strict origin validation/rejection
- [x] 1.13.4 Re-run 1.13.1 and 1.13.2

### Bug 1.15: Transcribe job ID too short (Completed)
- [x] 1.15.1 Add collision-risk/entropy test for generated IDs
- [x] 1.15.2 Add preservation tests for transcription flow
- [x] 1.15.3 Increase ID entropy (full UUID or equivalent)
- [x] 1.15.4 Re-run 1.15.1 and 1.15.2

### Bug 1.16: Rate limiter fail-open (Completed)
- [x] 1.16.1 Add reproduction test for DynamoDB failure path returning allowed=True
- [x] 1.16.2 Add preservation tests for normal rate windows
- [x] 1.16.3 Implement fail-closed (or bounded retry then fail-closed)
- [x] 1.16.4 Re-run 1.16.1 and 1.16.2

- [x] 1.20 Checkpoint: High complete

---

## MEDIUM

### Bug 1.22: Indirect toxicity not covered (Completed)
- [x] 1.22.1 Add reproduction test for indirect harmful phrasing
- [x] 1.22.2 Add preservation tests for benign agricultural phrasing
- [x] 1.22.3 Expand toxicity pattern coverage
- [x] 1.22.4 Re-run 1.22.1 and 1.22.2

### Bug 1.23: HTML stripping too narrow (Completed)
- [x] 1.23.1 Add reproduction test for non-span HTML artifact leakage
- [x] 1.23.2 Add preservation tests for markdown/plain text output
- [x] 1.23.3 Implement broader artifact stripping
- [x] 1.23.4 Re-run 1.23.1 and 1.23.2

### Bug 1.25: Audit timestamp microseconds (Completed)
- [x] 1.25.1 Add reproduction test expecting microseconds in timestamp
- [x] 1.25.2 Add preservation tests for UTC and field schema
- [x] 1.25.3 Emit no-microsecond ISO-8601 UTC timestamp
- [x] 1.25.4 Re-run 1.25.1 and 1.25.2

### Bug 1.27: Schemes not filtered by state (Completed)
- [x] 1.27.1 Add reproduction test for `farmer_state` returning all states
- [x] 1.27.2 Add preservation tests for national schemes inclusion
- [x] 1.27.3 Implement state-based filtering
- [x] 1.27.4 Re-run 1.27.1 and 1.27.2

### Bug 1.28: Corrupt media defaults to JPEG (Completed)
- [x] 1.28.1 Add reproduction test for corrupt input returning JPEG type
- [x] 1.28.2 Add preservation tests for valid JPEG/PNG/GIF/WebP detection
- [x] 1.28.3 Return explicit validation error for unknown signatures
- [x] 1.28.4 Re-run 1.28.1 and 1.28.2

### Bug 1.29: Odia mapping missing (Completed)
- [x] 1.29.1 Add reproduction test for `or-IN` mapping behavior
- [x] 1.29.2 Add preservation tests for existing language mappings
- [x] 1.29.3 Add explicit Odia mapping/fallback policy
- [x] 1.29.4 Re-run 1.29.1 and 1.29.2

- [x] 1.30 Checkpoint: Medium complete

---

## LOW (STANDARDIZATION)

### Bug 1.31: CORS implementation inconsistent (Completed)
- [x] 1.31.1 Inventory all handler CORS patterns
- [x] 1.31.2 Standardize through shared helper usage
- [x] 1.31.3 Verify preflight and normal responses across handlers

### Bug 1.32: Log severity inconsistent (Completed)
- [x] 1.32.1 Define severity policy
- [x] 1.32.2 Align handler log calls to policy
- [x] 1.32.3 Verify with representative error/recovery paths

### Bug 1.33: Error response format inconsistent (Completed)
- [x] 1.33.1 Define canonical error envelope
- [x] 1.33.2 Align handlers to canonical envelope
- [x] 1.33.3 Verify status code and body consistency

### Bug 1.34: Timeout config inconsistency (Completed)
- [x] 1.34.1 Document intended timeout strategy and exceptions
- [x] 1.34.2 Align template comments/configuration to strategy
- [x] 1.34.3 Verify API Gateway boundary assumptions remain valid

### Bug 1.35: Missing env validation at startup (Completed)
- [x] 1.35.1 Define required env vars per handler
- [x] 1.35.2 Add startup validation with clear error logs
- [x] 1.35.3 Verify optional vars still permit safe defaults

- [x] 1.36 Checkpoint: Low complete

---

## FINAL VALIDATION

- [x] 1.37 Run active-bug test suite end-to-end
- [x] 1.38 Verify no regressions on preserved behaviors
- [x] 1.39 Run integration checks for chat/voice/weather/schemes/image flows
- [x] 1.40 Verify consistency standards (CORS, logs, errors, env validation)
- [x] 1.41 Final readiness review

## Notes

- This file intentionally excludes fixed/non-reproducible items from the earlier 35-bug plan.
- Bug IDs are preserved for traceability with existing references.
