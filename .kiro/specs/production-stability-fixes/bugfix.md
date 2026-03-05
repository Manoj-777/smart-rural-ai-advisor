# Bugfix Requirements Document: Production Stability Fixes

## Introduction

This document defines requirements for fixing 28 production bugs in the Smart Rural AI Advisor system, a critical agricultural advisory platform serving Indian farmers across 13 languages. The system uses AWS Lambda, Bedrock, DynamoDB, S3, Translate, and Polly to provide real-time farming guidance.

The bugs are categorized across 4 severity levels:
- **CRITICAL (5 bugs)**: System hangs, timeouts, data loss
- **HIGH (8 bugs)**: Degraded performance, incorrect behavior
- **MEDIUM (10 bugs)**: Resource inefficiencies, validation gaps
- **LOW (5 bugs)**: Minor UX issues, missing optimizations

**Critical Constraint**: All fixes MUST be behind feature flags (default: OFF) to ensure zero breaking changes to existing production behavior. Each fix must be independently rollback-able.

---

## Bug Analysis

### Current Behavior (Defect)

#### CRITICAL SEVERITY

1.1 WHEN the agent orchestrator processes a request that takes longer than 29 seconds THEN the system returns API Gateway timeout error to the farmer even though Lambda continues processing for up to 120 seconds, wasting compute resources and providing no response

1.2 WHEN Bedrock model invokes multiple tools in parallel and one tool Lambda hangs indefinitely THEN the entire request hangs with no timeout protection, blocking the farmer's session and consuming Lambda resources until the 120-second Lambda timeout

1.3 WHEN rate limit records are written to the DynamoDB rate_limits table THEN the records persist indefinitely because no TTL attribute is configured in the CloudFormation template, causing unbounded table growth and eventual performance degradation

1.4 WHEN the Bedrock converse API fails with a retryable error (throttling, transient failure) THEN the system automatically falls back between models (Nova Pro ↔ Nova 2 Lite) with no way to disable this behavior, which may not be desired for conservative deployments that want explicit control over model fallback

1.5 WHEN multiple tools execute in parallel via ThreadPoolExecutor and one tool modifies shared state (tools_used list, tool_data_log list) THEN race conditions can occur causing incorrect tool attribution or missing tool results in the response

#### HIGH SEVERITY

1.6 WHEN the crop advisory Lambda calls bedrock_kb.retrieve() and receives a throttling error THEN the system fails immediately without retry, causing farmers to receive "service unavailable" errors during peak usage

1.7 WHEN weather lookup receives coordinates with invalid ranges (lat > 90, lon > 180) THEN the system passes invalid coordinates to OpenWeather API causing cryptic errors instead of validating input first

1.8 WHEN translate_response() is called with text longer than AWS Translate's limit THEN the translation fails silently and returns untranslated English text without logging the failure reason

1.9 WHEN gTTS synthesis fails due to network issues THEN the retry logic uses fixed backoff (0.6 seconds) which is insufficient for transient network issues, causing unnecessary failures

1.10 WHEN get_chat_history() queries DynamoDB with Limit=40 and the session has more than 40 messages THEN the function does not handle pagination, potentially missing older messages if the query returns a LastEvaluatedKey

1.11 WHEN polly_helper generates a presigned S3 URL with 3600-second expiry and the farmer's network is slow THEN the audio URL expires before playback completes, causing "access denied" errors

1.12 WHEN guardrails.py checks for prompt injection using complex regex patterns on very long inputs THEN the regex engine can experience catastrophic backoff (ReDoS), causing Lambda timeouts

1.13 WHEN the model generates a response longer than 8000 characters and truncate_output() is called THEN the truncation logic searches the last 200 characters for sentence boundaries, which may cut off important information if the last 200 chars are mid-paragraph

#### MEDIUM SEVERITY

1.14 WHEN Lambda functions initialize boto3 clients at module level (bedrock_rt, lambda_client, s3, dynamodb) THEN connection pooling is not explicitly configured, potentially causing connection exhaustion under high load

1.15 WHEN save_chat_message() is called for each message individually THEN the system makes one DynamoDB PutItem call per message instead of batching, increasing latency and costs

1.16 WHEN _bedrock_converse_with_retry() implements exponential backoff THEN it uses a fixed multiplier without jitter, causing thundering herd problems when multiple Lambdas retry simultaneously

1.17 WHEN get_farmer_profile() is called multiple times in a single request THEN the system queries DynamoDB each time instead of caching the profile in memory for the request duration

1.18 WHEN farmer_id is passed as a path parameter in /profile/{farmerId} THEN the system does not validate the format (should be alphanumeric + hyphens only), allowing injection attempts

1.19 WHEN model_id parameter is passed to _invoke_bedrock_direct() THEN the system does not validate that the model_id is in the allowed list, potentially allowing unauthorized model access

1.20 WHEN language_code is normalized in translate_helper.py THEN the system accepts any string and falls back to 'en', but does not log invalid language codes for monitoring

1.21 WHEN _execute_tool() invokes a Lambda function THEN the Lambda client does not specify a timeout, using the default SDK timeout which may be longer than desired

1.22 WHEN text_to_speech() is called with an unsupported voice_id THEN the system does not validate the voice_id against VOICE_MAP, potentially causing Polly API errors

1.23 WHEN polly_helper uploads audio to S3 THEN the system does not validate that the S3_BUCKET exists or is accessible, causing cryptic errors if misconfigured

1.24 WHEN the same session_id is used across multiple concurrent requests THEN DynamoDB does not enforce idempotency, potentially causing duplicate chat messages to be saved

#### LOW SEVERITY

1.25 WHEN _strip_markdown_for_tts() processes text with numbered lists "1. item" THEN it removes the number but leaves awkward spacing, causing TTS to pause unnaturally

1.26 WHEN weather_lookup builds OpenWeather API URLs THEN it uses hardcoded "http://" scheme for some endpoints and "https://" for others, causing inconsistent security posture

1.27 WHEN tools execute successfully THEN the system does not emit CloudWatch metrics for tool execution duration, making performance monitoring difficult

1.28 WHEN CORS preflight OPTIONS requests are received THEN each Lambda handler implements CORS logic independently instead of using a shared middleware, causing inconsistent CORS headers

---

### Expected Behavior (Correct)

#### CRITICAL SEVERITY

2.1 WHEN the agent orchestrator processes a request that approaches the 29-second API Gateway timeout THEN the system SHALL detect the approaching timeout (via context.get_remaining_time_in_millis()) and return a partial response or graceful error message before the hard timeout, controlled by feature flag ENABLE_TIMEOUT_PROTECTION (default: false)

2.2 WHEN Bedrock model invokes tools in parallel THEN the system SHALL enforce a per-tool timeout (configurable via TOOL_EXECUTION_TIMEOUT_SEC, default: 25 seconds) using concurrent.futures.wait() with timeout parameter, controlled by feature flag ENABLE_TOOL_TIMEOUT (default: false)

2.3 WHEN rate limit records are written to the DynamoDB rate_limits table THEN the CloudFormation template SHALL configure TimeToLiveSpecification with AttributeName='ttl_epoch' to automatically delete expired records, controlled by feature flag ENABLE_RATE_LIMIT_TTL (default: false)

2.4 WHEN the Bedrock converse API fails with a retryable error after exhausting retries THEN the system SHALL check the ENABLE_MODEL_FALLBACK feature flag (default: false) and only attempt bidirectional model fallback (Nova Pro ↔ Nova 2 Lite) when the flag is enabled, controlled by feature flag ENABLE_MODEL_FALLBACK (default: false)

2.5 WHEN multiple tools execute in parallel THEN the system SHALL use thread-safe data structures (queue.Queue or threading.Lock) to protect shared state (tools_used, tool_data_log), controlled by feature flag ENABLE_THREAD_SAFE_TOOLS (default: false)

#### HIGH SEVERITY

2.6 WHEN the crop advisory Lambda calls bedrock_kb.retrieve() and receives a throttling error THEN the system SHALL retry up to 3 times with exponential backoff (1s, 2s, 4s), controlled by feature flag ENABLE_KB_RETRY (default: false)

2.7 WHEN weather lookup receives coordinate parameters THEN the system SHALL validate lat ∈ [-90, 90] and lon ∈ [-180, 180] before making API calls, controlled by feature flag ENABLE_COORDINATE_VALIDATION (default: false)

2.8 WHEN translate_response() is called with text longer than AWS Translate's limit THEN the system SHALL detect the length, log a warning, and chunk the text or truncate gracefully, controlled by feature flag ENABLE_TRANSLATION_CHUNKING (default: false)

2.9 WHEN gTTS synthesis fails due to network issues THEN the system SHALL use exponential backoff with jitter (base: 0.6s, multiplier: 2, jitter: ±25%), controlled by feature flag ENABLE_GTTS_EXPONENTIAL_BACKOFF (default: false)

2.10 WHEN get_chat_history() queries DynamoDB THEN the system SHALL check for LastEvaluatedKey and continue querying until all messages within the limit are retrieved, controlled by feature flag ENABLE_CHAT_PAGINATION (default: false)

2.11 WHEN polly_helper generates presigned S3 URLs THEN the system SHALL increase expiry to 7200 seconds (2 hours) and return both the URL and the S3 key for later refresh, controlled by feature flag ENABLE_EXTENDED_AUDIO_EXPIRY (default: false)

2.12 WHEN guardrails.py checks for prompt injection THEN the system SHALL limit input length to 2000 characters before regex matching and use atomic groups to prevent ReDoS, controlled by feature flag ENABLE_REGEX_DOS_PROTECTION (default: false)

2.13 WHEN truncate_output() truncates long responses THEN the system SHALL search the last 500 characters (instead of 200) for sentence boundaries to preserve more context, controlled by feature flag ENABLE_SMART_TRUNCATION (default: false)

#### MEDIUM SEVERITY

2.14 WHEN Lambda functions initialize boto3 clients THEN the system SHALL configure connection pooling via botocore.config.Config(max_pool_connections=25), controlled by feature flag ENABLE_CONNECTION_POOLING (default: false)

2.15 WHEN multiple chat messages need to be saved THEN the system SHALL use DynamoDB batch_write_item() to write up to 25 messages per batch, controlled by feature flag ENABLE_BATCH_CHAT_WRITES (default: false)

2.16 WHEN _bedrock_converse_with_retry() implements exponential backoff THEN the system SHALL add random jitter (±25% of backoff time) to prevent thundering herd, controlled by feature flag ENABLE_BACKOFF_JITTER (default: false)

2.17 WHEN get_farmer_profile() is called THEN the system SHALL cache the profile in a request-scoped dictionary (Lambda global variable cleared per cold start) with TTL, controlled by feature flag ENABLE_PROFILE_CACHE (default: false)

2.18 WHEN farmer_id is received as input THEN the system SHALL validate format using regex ^[a-zA-Z0-9\-_]{1,64}$ before processing, controlled by feature flag ENABLE_FARMER_ID_VALIDATION (default: false)

2.19 WHEN model_id parameter is passed THEN the system SHALL validate against an allowed list [FOUNDATION_MODEL, FOUNDATION_MODEL_LITE] before invoking Bedrock, controlled by feature flag ENABLE_MODEL_VALIDATION (default: false)

2.20 WHEN language_code is normalized THEN the system SHALL log a warning when an invalid language code is received (not in SUPPORTED_LANGUAGES), controlled by feature flag ENABLE_LANGUAGE_VALIDATION_LOGGING (default: false)

2.21 WHEN _execute_tool() invokes a Lambda function THEN the system SHALL set InvocationType='RequestResponse' with explicit SDK timeout via Config(read_timeout=30), controlled by feature flag ENABLE_TOOL_INVOCATION_TIMEOUT (default: false)

2.22 WHEN text_to_speech() is called with a voice_id THEN the system SHALL validate voice_id against VOICE_MAP keys before calling Polly, controlled by feature flag ENABLE_VOICE_VALIDATION (default: false)

2.23 WHEN polly_helper initializes THEN the system SHALL verify S3_BUCKET accessibility by calling s3.head_bucket() during cold start, controlled by feature flag ENABLE_S3_VALIDATION (default: false)

2.24 WHEN save_chat_message() is called THEN the system SHALL include a client-provided idempotency_token in the DynamoDB item and use ConditionExpression to prevent duplicates, controlled by feature flag ENABLE_CHAT_IDEMPOTENCY (default: false)

#### LOW SEVERITY

2.25 WHEN _strip_markdown_for_tts() processes numbered lists THEN the system SHALL replace "1. " with "First, " and "2. " with "Second, " for better TTS pronunciation, controlled by feature flag ENABLE_TTS_LIST_FORMATTING (default: false)

2.26 WHEN weather_lookup builds OpenWeather API URLs THEN the system SHALL use HTTPS scheme consistently for all endpoints, controlled by feature flag ENABLE_HTTPS_WEATHER_API (default: false)

2.27 WHEN tools execute THEN the system SHALL emit CloudWatch custom metrics (tool_name, duration_ms, success/failure) using boto3 cloudwatch.put_metric_data(), controlled by feature flag ENABLE_TOOL_METRICS (default: false)

2.28 WHEN CORS preflight OPTIONS requests are received THEN the system SHALL use a shared CORS middleware function that all handlers import, controlled by feature flag ENABLE_UNIFIED_CORS (default: false)

---

### Unchanged Behavior (Regression Prevention)

#### Core Functionality Preservation

3.1 WHEN feature flags are set to their default values (false) THEN the system SHALL CONTINUE TO execute all existing code paths exactly as before with no behavioral changes

3.2 WHEN farmers send queries in any of the 13 supported languages THEN the system SHALL CONTINUE TO translate, process, and respond correctly regardless of which fixes are enabled

3.3 WHEN the agent orchestrator invokes tools (weather, crop advisory, schemes, profile) THEN the system SHALL CONTINUE TO return the same response structure and field names

3.4 WHEN rate limiting is enabled THEN the system SHALL CONTINUE TO enforce the same limits (15 RPM, 120 RPH, 500 daily) with the same fail-open behavior on errors

3.5 WHEN chat history is retrieved THEN the system SHALL CONTINUE TO return messages in chronological order (oldest to newest) with the same field structure

3.6 WHEN PII is detected in user input THEN the system SHALL CONTINUE TO mask it in logs using the same patterns and mask formats

3.7 WHEN prompt injection or toxicity is detected THEN the system SHALL CONTINUE TO block the request with the same error messages

3.8 WHEN Bedrock guardrails are configured THEN the system SHALL CONTINUE TO apply them with the same guardrailConfig structure

3.9 WHEN TTS is requested for Polly-native languages (en, hi) THEN the system SHALL CONTINUE TO use Polly with the same voice mappings

3.10 WHEN TTS is requested for gTTS languages (ta, te, kn, ml, etc.) THEN the system SHALL CONTINUE TO use gTTS with the same audio format and S3 upload behavior

3.11 WHEN translation is performed THEN the system SHALL CONTINUE TO use the same markdown protection tokens and post-processing cleanup

3.12 WHEN weather data is fetched THEN the system SHALL CONTINUE TO return the same JSON structure with current weather and 5-day forecast

3.13 WHEN crop advisory queries the knowledge base THEN the system SHALL CONTINUE TO return the same advisory_data structure with content, score, and source fields

3.14 WHEN farmer profiles are created or updated THEN the system SHALL CONTINUE TO store the same fields with the same DynamoDB schema

3.15 WHEN session messages are saved THEN the system SHALL CONTINUE TO include the same TTL calculation (CHAT_TTL_DAYS * 86400) and field structure

3.16 WHEN output guardrails run THEN the system SHALL CONTINUE TO mask PII, detect prompt leakage, and truncate at 8000 characters with the same logic

3.17 WHEN parallel tool execution is triggered (2+ tools) THEN the system SHALL CONTINUE TO use ThreadPoolExecutor with the same worker count

3.18 WHEN Bedrock converse API is called THEN the system SHALL CONTINUE TO use the same system prompt, tool configuration, and inference parameters

3.19 WHEN errors occur in any Lambda function THEN the system SHALL CONTINUE TO log errors with the same format and return the same error response structure

3.20 WHEN CORS headers are returned THEN the system SHALL CONTINUE TO use the same ALLOWED_ORIGIN environment variable value

---

## Root Causes and Impact

### CRITICAL Bugs

**1.1 API Gateway Timeout (29s hard limit)**
- **Root Cause**: Lambda timeout (120s) exceeds API Gateway timeout (29s); no proactive timeout detection
- **Impact**: Farmers see "Gateway Timeout" errors; wasted Lambda compute; poor UX during complex queries
- **Affected Code**: `backend/lambdas/agent_orchestrator/handler.py:lambda_handler()`

**1.2 Tool Execution Hangs**
- **Root Cause**: ThreadPoolExecutor.submit() with no timeout; as_completed() blocks indefinitely if tool Lambda hangs
- **Impact**: Entire request hangs; farmer session blocked; Lambda runs until 120s timeout; cascading failures
- **Affected Code**: `backend/lambdas/agent_orchestrator/handler.py:_invoke_bedrock_direct()` lines 1070-1085

**1.3 DynamoDB Rate Limits Table Growth**
- **Root Cause**: CloudFormation template missing TimeToLiveSpecification for rate_limits table
- **Impact**: Unbounded table growth; increased costs; eventual performance degradation; manual cleanup required
- **Affected Code**: `infrastructure/template.yaml` (missing TTL config)

**1.4 Bedrock Fallback Missing**
- **Root Cause**: _bedrock_converse_with_retry() retries same model; no fallback to FOUNDATION_MODEL_LITE
- **Impact**: Complete request failure when primary model is throttled; missed graceful degradation opportunity
- **Affected Code**: `backend/lambdas/agent_orchestrator/handler.py:_bedrock_converse_with_retry()` lines 643-698

**1.5 Parallel Tool Race Conditions**
- **Root Cause**: Multiple threads append to shared lists (tools_used, tool_data_log) without synchronization
- **Impact**: Incorrect tool attribution; missing tool results; data corruption in responses
- **Affected Code**: `backend/lambdas/agent_orchestrator/handler.py:_invoke_bedrock_direct()` lines 1070-1095

### HIGH Bugs

**1.6 KB Retrieve No Retry**
- **Root Cause**: bedrock_kb.retrieve() called without try/except retry logic
- **Impact**: Farmers see "service unavailable" during peak hours; poor reliability
- **Affected Code**: `backend/lambdas/crop_advisory/handler.py:lambda_handler()` line 120

**1.7 Coordinate Validation Missing**
- **Root Cause**: lat/lon extracted from query params but not validated before API call
- **Impact**: Cryptic OpenWeather errors; poor error messages to farmers
- **Affected Code**: `backend/lambdas/weather_lookup/handler.py:lambda_handler()` lines 150-165

**1.8 Translation Length Limit**
- **Root Cause**: AWS Translate has undocumented length limits; no pre-check or chunking
- **Impact**: Silent translation failures; farmers receive English text unexpectedly
- **Affected Code**: `backend/utils/translate_helper.py:translate_response()` line 280

**1.9 gTTS Fixed Backoff**
- **Root Cause**: GTTS_RETRY_BACKOFF_SEC=0.6 is fixed; no exponential increase
- **Impact**: Unnecessary failures during transient network issues; poor reliability
- **Affected Code**: `backend/utils/polly_helper.py:_gtts_tts()` line 145

**1.10 Chat History Pagination**
- **Root Cause**: get_chat_history() uses Limit=40 but doesn't check LastEvaluatedKey
- **Impact**: Missing older messages in long conversations; incomplete context for model
- **Affected Code**: `backend/utils/dynamodb_helper.py:get_chat_history()` lines 70-85

**1.11 Audio URL Expiry**
- **Root Cause**: Presigned URLs expire in 3600s (1 hour); slow networks may not complete playback
- **Impact**: "Access Denied" errors mid-playback; poor UX for farmers on 2G/3G
- **Affected Code**: `backend/utils/polly_helper.py:_upload_audio_bytes()` line 95

**1.12 Regex DoS in Guardrails**
- **Root Cause**: Complex regex patterns with nested quantifiers on unbounded input
- **Impact**: Lambda timeouts on malicious inputs; potential DoS vector
- **Affected Code**: `backend/utils/guardrails.py:check_prompt_injection()` lines 150-180

**1.13 Truncation Context Loss**
- **Root Cause**: truncate_output() searches only last 200 chars for sentence boundary
- **Impact**: Important information cut off mid-paragraph; poor UX
- **Affected Code**: `backend/utils/guardrails.py:truncate_output()` line 520

### MEDIUM Bugs

**1.14-1.24**: Resource inefficiencies, validation gaps, missing optimizations
- **Impact**: Increased latency, costs, and operational complexity; no immediate user-facing failures
- **Affected Code**: Multiple files across utils/ and lambdas/

### LOW Bugs

**1.25-1.28**: Minor UX issues, inconsistencies, missing observability
- **Impact**: Slight UX degradation; operational blind spots; technical debt
- **Affected Code**: Multiple files

---

## Fix Approach

### Conservative Feature Flag Strategy

Every fix follows this pattern:

1. **Add environment variable** to CloudFormation template (default: 'false')
2. **Read flag in code** at module level: `ENABLE_X = os.environ.get('ENABLE_X', 'false').lower() == 'true'`
3. **Implement new logic** alongside old code using `if ENABLE_X:` branches
4. **Preserve old code path** as the default (flag=false)
5. **Add comprehensive logging** for both paths
6. **Document rollback procedure** (set flag to 'false', redeploy)

### Example Pattern

```python
# Feature flag (default: OFF)
ENABLE_TIMEOUT_PROTECTION = os.environ.get('ENABLE_TIMEOUT_PROTECTION', 'false').lower() == 'true'

def lambda_handler(event, context):
    if ENABLE_TIMEOUT_PROTECTION:
        # NEW: Check remaining time
        remaining_ms = context.get_remaining_time_in_millis()
        if remaining_ms < 5000:  # 5 seconds buffer
            logger.warning("Approaching timeout, returning early")
            return early_response()
    
    # EXISTING: Original code path (unchanged)
    return process_request(event)
```

### Testing Checklist (Per Fix)

Each fix MUST be tested with:

1. **Flag OFF (default)**: Verify no behavior change
2. **Flag ON**: Verify fix works as expected
3. **Regression tests**: Verify unchanged behavior clauses (3.1-3.20)
4. **Load testing**: Verify no performance degradation
5. **Rollback test**: Toggle flag OFF, verify immediate revert

### Rollback Procedure

For any fix causing issues:

1. Set environment variable to 'false' in CloudFormation
2. Deploy stack update (< 2 minutes)
3. Verify old behavior restored
4. Investigate issue offline
5. Re-enable after fix validated

---

## Feature Flags Summary

| Flag | Bug | Default | Risk |
|------|-----|---------|------|
| ENABLE_TIMEOUT_PROTECTION | 1.1 | false | Low |
| ENABLE_TOOL_TIMEOUT | 1.2 | false | Medium |
| ENABLE_RATE_LIMIT_TTL | 1.3 | false | Low |
| ENABLE_MODEL_FALLBACK | 1.4 | false | Low |
| ENABLE_THREAD_SAFE_TOOLS | 1.5 | false | Medium |
| ENABLE_KB_RETRY | 1.6 | false | Low |
| ENABLE_COORDINATE_VALIDATION | 1.7 | false | Low |
| ENABLE_TRANSLATION_CHUNKING | 1.8 | false | Medium |
| ENABLE_GTTS_EXPONENTIAL_BACKOFF | 1.9 | false | Low |
| ENABLE_CHAT_PAGINATION | 1.10 | false | Low |
| ENABLE_EXTENDED_AUDIO_EXPIRY | 1.11 | false | Low |
| ENABLE_REGEX_DOS_PROTECTION | 1.12 | false | Low |
| ENABLE_SMART_TRUNCATION | 1.13 | false | Low |
| ENABLE_CONNECTION_POOLING | 1.14 | false | Low |
| ENABLE_BATCH_CHAT_WRITES | 1.15 | false | Medium |
| ENABLE_BACKOFF_JITTER | 1.16 | false | Low |
| ENABLE_PROFILE_CACHE | 1.17 | false | Low |
| ENABLE_FARMER_ID_VALIDATION | 1.18 | false | Low |
| ENABLE_MODEL_VALIDATION | 1.19 | false | Low |
| ENABLE_LANGUAGE_VALIDATION_LOGGING | 1.20 | false | Low |
| ENABLE_TOOL_INVOCATION_TIMEOUT | 1.21 | false | Low |
| ENABLE_VOICE_VALIDATION | 1.22 | false | Low |
| ENABLE_S3_VALIDATION | 1.23 | false | Low |
| ENABLE_CHAT_IDEMPOTENCY | 1.24 | false | Medium |
| ENABLE_TTS_LIST_FORMATTING | 1.25 | false | Low |
| ENABLE_HTTPS_WEATHER_API | 1.26 | false | Low |
| ENABLE_TOOL_METRICS | 1.27 | false | Low |
| ENABLE_UNIFIED_CORS | 1.28 | false | Low |

---

## Success Criteria

1. All 28 fixes implemented behind feature flags
2. All flags default to 'false' (no behavior change)
3. All regression tests pass with flags OFF
4. All fix tests pass with flags ON
5. Rollback procedure validated for each fix
6. CloudWatch dashboards updated to monitor flag usage
7. Runbook created for gradual rollout (1 flag at a time)
8. Zero production incidents during rollout
