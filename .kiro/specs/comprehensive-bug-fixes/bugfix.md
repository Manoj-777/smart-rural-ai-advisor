# Bugfix Requirements Document: Active Bug Set (Current Reality)

## Introduction

This document is narrowed to bugs that are currently reproducible in the codebase. Fixed or non-reproducible items from the earlier 35-bug list were removed.

Active bug IDs retained:
- Critical: none
- High: none
- Medium: none
- Low: none

Recently fixed:
- 1.8 (profile cache thread safety) — lock-protected cache access implemented and validated.
- 1.9 (batch write truncation) — chunked writes implemented and validated for >25 and <=25 paths.
- 1.12 (crop advisory injection coverage) — SQL/command signatures added while preserving safe agri query behavior.
- 1.13 (CORS origin validation) — unauthorized origins now return explicit 403 instead of default-origin fallback.
- 1.15 (transcribe job ID entropy) — short UUID slice replaced with full UUID-hex job IDs.
- 1.16 (rate limiter fail-open) — persistence errors now fail closed with bounded retry hint response.
- 1.22 (indirect toxicity coverage) — indirect sabotage phrasing is now blocked while benign prevention phrasing remains allowed.
- 1.23 (HTML artifact stripping) — sanitizer now removes broader HTML tag artifacts while preserving markdown/plain text semantics.
- 1.25 (audit timestamp precision) — audit logger now emits second-precision UTC timestamps without microseconds.
- 1.27 (state schemes filtering) — schemes handler now filters `state_schemes` to the requested `farmer_state` with case-insensitive matching.
- 1.28 (media validation fallback) — unknown/corrupted media no longer defaults to JPEG and now returns explicit 400 validation errors.
- 1.29 (Odia transcribe mapping) — `or-IN` now maps explicitly in transcribe language mapping while unsupported-language fallback remains for unsupported codes.
- 1.31 (CORS standardization) — agent orchestrator timeout HTTP path now uses shared CORS helper headers instead of hardcoded header blocks.
- 1.32 (logging severity policy) — non-failure operational events in agent orchestrator now log at `info` level instead of `warning`, while failure paths remain `error`.
- 1.33 (error envelope consistency) — farmer profile handler now emits canonical error envelope (`status`, `data`, `message`, `language`) with backward-compatible `error` field.
- 1.34 (timeout policy alignment) — infrastructure template now removes per-function orchestrator timeout override and uses the global timeout policy consistently.
- 1.35 (startup env validation) — agent orchestrator now validates required runtime env vars at startup and logs actionable configuration errors when missing.
- Post-close hardening (local-language list formatting) — local-language response sanitization now preserves list indentation, avoids forced heading auto-numbering for Indic languages, and keeps numeric point markers in TTS for Indic-script text.

## Bug Analysis

### Current Behavior (Defect)

#### CRITICAL ISSUES

No currently retained critical defects.

#### HIGH PRIORITY ISSUES

No currently retained high-priority defects.

#### MEDIUM PRIORITY ISSUES

#### LOW PRIORITY ISSUES

### Expected Behavior (Correct)

#### CRITICAL ISSUES

No currently retained critical defect requirements.

#### HIGH PRIORITY ISSUES

No currently retained high-priority requirements.

#### MEDIUM PRIORITY ISSUES

#### LOW PRIORITY ISSUES

### Unchanged Behavior (Regression Prevention)

