# Post-Deploy Multilingual Smoke Dashboard

- Generated UTC: 2026-03-04T16:52:40.608622+00:00
- Source report: artifacts/post_deploy_multilang_smoke_report.json
- Total languages: 11
- Successful: 11
- Failed: 0
- Flagged: 11
- Localization modes: translate_only: 11

Thresholds: latin_ratio <= 0.2, expected_script_ratio >= 0.8, no errors

| Status | Lang | HTTP | Localization | Pipeline | Latin Ratio | Script Ratio | Flags |
|---|---:|---:|---|---|---:|---:|---|
| 🟢 | hi | 200 | translate_only | cache_hit | 0.1869 | 0.8131 | control_char_found |
| 🟢 | te | 200 | translate_only | cache_hit | 0.0365 | 0.9635 | control_char_found |
| 🟢 | kn | 200 | translate_only | cache_hit | 0.0093 | 0.9907 | control_char_found |
| 🟢 | ml | 200 | translate_only | cache_hit | 0.0944 | 0.9056 | control_char_found |
| 🟢 | mr | 200 | translate_only | cache_hit | 0.0056 | 0.9944 | control_char_found |
| 🟢 | bn | 200 | translate_only | cache_hit | 0.0062 | 0.9938 | control_char_found |
| 🟢 | gu | 200 | translate_only | cache_hit | 0.084 | 0.916 | control_char_found |
| 🟢 | pa | 200 | translate_only | cache_hit | 0.0493 | 0.9507 | control_char_found |
| 🟢 | or | 200 | translate_only | cache_hit | 0.18 | 0.8175 | control_char_found |
| 🟢 | as | 200 | translate_only | cache_hit | 0.0056 | 0.9944 | control_char_found |
| 🟢 | ur | 200 | translate_only | cache_hit | 0.022 | 0.978 | control_char_found |

Top 3 attention items: hi (latin=0.1869, script=0.8131), or (latin=0.18, script=0.8175), ml (latin=0.0944, script=0.9056)

## QA Priority (High Latin Ratio First)

| Rank | Status | Lang | Latin Ratio | Script Ratio | HTTP | Localization | Flags |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | 🟢 | hi | 0.1869 | 0.8131 | 200 | translate_only | control_char_found |
| 2 | 🟢 | or | 0.18 | 0.8175 | 200 | translate_only | control_char_found |
| 3 | 🟢 | ml | 0.0944 | 0.9056 | 200 | translate_only | control_char_found |
| 4 | 🟢 | gu | 0.084 | 0.916 | 200 | translate_only | control_char_found |
| 5 | 🟢 | pa | 0.0493 | 0.9507 | 200 | translate_only | control_char_found |
| 6 | 🟢 | te | 0.0365 | 0.9635 | 200 | translate_only | control_char_found |
| 7 | 🟢 | ur | 0.022 | 0.978 | 200 | translate_only | control_char_found |
| 8 | 🟢 | kn | 0.0093 | 0.9907 | 200 | translate_only | control_char_found |
| 9 | 🟢 | bn | 0.0062 | 0.9938 | 200 | translate_only | control_char_found |
| 10 | 🟢 | mr | 0.0056 | 0.9944 | 200 | translate_only | control_char_found |
| 11 | 🟢 | as | 0.0056 | 0.9944 | 200 | translate_only | control_char_found |

## Notes
- `control_char_found` is currently expected in many responses due to newline formatting in model output.
- `prompt_source` values are available in JSON report for diagnostics (`translate`, `override`, `english_fallback`).