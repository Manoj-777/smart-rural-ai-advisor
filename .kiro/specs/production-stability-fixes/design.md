# Production Stability Fixes - Technical Design Document

## Overview

This design document provides detailed technical implementation specifications for fixing 28 production bugs in the Smart Rural AI Advisor system. All fixes follow a conservative feature flag approach where new code is added alongside existing code, with flags defaulting to OFF to ensure zero breaking changes.

The bugs span 4 severity levels:
- **CRITICAL (5)**: System hangs, timeouts, data loss, race conditions
- **HIGH (8)**: Degraded performance, incorrect behavior, missing retries
- **MEDIUM (10)**: Resource inefficiencies, validation gaps, missing optimizations
- **LOW (5)**: Minor UX issues, inconsistencies, missing observability

## Glossary

- **Bug_Condition (C)**: The condition that triggers each bug - specific inputs, states, or timing conditions
- **Property (P)**: The desired correct behavior when the bug condition is met
- **Preservation**: Existing behavior that must remain unchanged (all fixes default to OFF)
- **Feature Flag**: Environment variable controlling each fix (default: 'false')
- **Fail-Open**: Design pattern where errors in non-critical paths allow requests to proceed
- **Thread-Safe**: Code that correctly handles concurrent access from multiple threads
- **Idempotency**: Property where repeated operations produce the same result
- **TTL (Time To Live)**: DynamoDB attribute for automatic record expiration
- **ReDoS**: Regular Expression Denial of Service attack via catastrophic backoff

## Architecture Context

### System Components

- **Agent Orchestrator Lambda**: Main request handler (`backend/lambdas/agent_orchestrator/handler.py`)
  - Processes farmer queries through Bedrock converse API
  - Executes tools in parallel using ThreadPoolExecutor
  - Manages conversation history and context
  - Current timeout: 120s (Lambda), 29s (API Gateway)

- **Tool Lambdas**: Specialized functions invoked by orchestrator
  - `crop_advisory`: Queries Bedrock Knowledge Base for farming advice
  - `weather_lookup`: Fetches weather data from OpenWeather API
  - `schemes_lookup`: Retrieves government scheme information
  - `profile_manager`: Manages farmer profile CRUD operations

- **Utility Modules**: Shared helper functions
  - `rate_limiter.py`: DynamoDB-based rate limiting (15 RPM, 120 RPH, 500 daily)
  - `translate_helper.py`: AWS Translate integration for 13 languages
  - `polly_helper.py`: Text-to-speech using Polly (en, hi) and gTTS (ta, te, kn, ml, etc.)
  - `dynamodb_helper.py`: Profile and chat session persistence
  - `guardrails.py`: PII masking, prompt injection defense, toxicity filtering

- **Infrastructure**: AWS CloudFormation (`infrastructure/template.yaml`)
  - DynamoDB tables: `farmer_profiles`, `chat_sessions`, `rate_limits`
  - S3 bucket: Audio file storage for TTS
  - Bedrock: Foundation models and Knowledge Base
  - API Gateway: REST API with 29-second timeout

### Current Behavior Summary

The system currently processes requests through this flow:
1. API Gateway receives farmer query (29s timeout)
2. Agent Orchestrator Lambda invokes Bedrock converse API (120s timeout)
3. Bedrock may request tool execution (weather, crop advisory, etc.)
4. Tools execute in parallel via ThreadPoolExecutor (no timeout)
5. Response translated to farmer's language
6. Text-to-speech audio generated
7. Response returned with text + audio URL

**Known Issues**:
- No proactive timeout detection before API Gateway 29s limit
- Tool execution can hang indefinitely
- DynamoDB rate_limits table grows unbounded (no TTL)
- No fallback to FOUNDATION_MODEL_LITE on throttling
- Race conditions in parallel tool execution (shared list mutations)
- Missing retries on transient failures
- Input validation gaps
- Resource pooling not configured

## Bug Details and Implementation

---

## CRITICAL SEVERITY BUGS

### Bug 1.1: API Gateway Timeout (29s Hard Limit)

#### Fault Condition

The bug manifests when the agent orchestrator processes a request that takes longer than 29 seconds. API Gateway has a hard 29-second timeout, but Lambda continues processing for up to 120 seconds, wasting compute resources and providing no response to the farmer.

**Formal Specification:**
```
FUNCTION isBugCondition(request, context)
  INPUT: request (event dict), context (Lambda context object)
  OUTPUT: boolean
  
  elapsed_ms = context.get_remaining_time_in_millis()
  initial_timeout_ms = 120000  # Lambda timeout
  time_spent_ms = initial_timeout_ms - elapsed_ms
  
  RETURN time_spent_ms > 24000  # More than 24 seconds elapsed (5s buffer before 29s)
         AND response_not_yet_sent
END FUNCTION
```

#### Expected Behavior

When the orchestrator detects it's approaching the 29-second API Gateway timeout, it SHALL return a partial response or graceful error message before the hard timeout, controlled by feature flag ENABLE_TIMEOUT_PROTECTION (default: false).

#### Hypothesized Root Cause

The `lambda_handler()` function in `backend/lambdas/agent_orchestrator/handler.py` does not check `context.get_remaining_time_in_millis()` during processing. Complex queries involving multiple tool calls can exceed 29 seconds, causing API Gateway to return "Gateway Timeout" while Lambda continues processing.

#### Fix Implementation

**File**: `backend/lambdas/agent_orchestrator/handler.py`

**Changes Required**:

1. **Add feature flag at module level** (after imports, before functions):

```python
# Feature flag: Timeout protection (default: OFF)
ENABLE_TIMEOUT_PROTECTION = os.environ.get('ENABLE_TIMEOUT_PROTECTION', 'false').lower() == 'true'
TIMEOUT_BUFFER_MS = int(os.environ.get('TIMEOUT_BUFFER_MS', '5000'))  # 5 seconds before API Gateway timeout
```

2. **Add helper function** (before `lambda_handler`):
```python
def _check_timeout_approaching(context, buffer_ms=5000):
    """Check if Lambda is approaching API Gateway timeout (29s).
    Returns (is_approaching: bool, remaining_ms: int)"""
    if not context:
        return False, 0
    remaining_ms = context.get_remaining_time_in_millis()
    # API Gateway timeout is 29s, we want to respond before that
    is_approaching = remaining_ms < buffer_ms
    return is_approaching, remaining_ms

def _timeout_fallback_response(farmer_context=None):
    """Generate graceful timeout response."""
    return (
        "I'm still processing your detailed request. This is taking longer than expected. "
        "Please try asking a simpler question, or I can provide a quick answer now if you'd like."
    )
```

3. **Modify `lambda_handler()` function** - add timeout check at strategic points:

```python
def lambda_handler(event, context):
    # ... existing code ...
    
    # NEW: Check timeout before expensive operations
    if ENABLE_TIMEOUT_PROTECTION:
        is_approaching, remaining_ms = _check_timeout_approaching(context, TIMEOUT_BUFFER_MS)
        if is_approaching:
            logger.warning(f"Timeout approaching: {remaining_ms}ms remaining, returning early")
            fallback_text = _timeout_fallback_response(farmer_context)
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({
                    'reply': fallback_text,
                    'audio_url': None,
                    'timeout_fallback': True
                })
            }
    
    # EXISTING: Continue with normal processing
    # ... rest of function ...
```

4. **Add timeout check in `_invoke_bedrock_direct()` function** - check before each tool execution turn:
```python
def _invoke_bedrock_direct(prompt, farmer_context=None, skip_native_guardrail=False, 
                          chat_history=None, model_id=None, lambda_context=None):
    # ... existing code ...
    
    try:
        for turn in range(5):
            # NEW: Check timeout before each turn
            if ENABLE_TIMEOUT_PROTECTION and lambda_context:
                is_approaching, remaining_ms = _check_timeout_approaching(lambda_context, TIMEOUT_BUFFER_MS)
                if is_approaching:
                    logger.warning(f"Timeout approaching in turn {turn}: {remaining_ms}ms remaining")
                    return _timeout_fallback_response(), tools_used, tool_data_log, False
            
            # EXISTING: Continue with Bedrock call
            # ... rest of loop ...
```

**CloudFormation Changes** (`infrastructure/template.yaml`):

Add environment variable to AgentOrchestratorFunction:
```yaml
Environment:
  Variables:
    ENABLE_TIMEOUT_PROTECTION: 'false'  # Default: OFF
    TIMEOUT_BUFFER_MS: '5000'  # 5 seconds buffer
```

#### Testing Strategy

**Unit Tests**:
- Mock `context.get_remaining_time_in_millis()` to return values < 5000ms
- Verify `_check_timeout_approaching()` returns True
- Verify `_timeout_fallback_response()` is called
- Verify response includes `timeout_fallback: true` flag

**Integration Tests**:
- Simulate slow Bedrock responses (mock with delays)
- Verify early return before 29 seconds
- Verify flag OFF: no behavior change

**Load Tests**:
- Run 100 concurrent requests with complex queries
- Measure timeout rate before/after fix
- Verify no increase in Lambda errors

#### Rollback Plan

1. Set `ENABLE_TIMEOUT_PROTECTION: 'false'` in CloudFormation
2. Deploy stack update (< 2 minutes)
3. Verify requests process normally without early returns
4. Monitor CloudWatch logs for "Timeout approaching" messages (should be zero)

---

### Bug 1.2: Tool Execution Hangs (No Timeout)

#### Fault Condition

The bug manifests when Bedrock model invokes multiple tools in parallel and one tool Lambda hangs indefinitely. The `ThreadPoolExecutor` with `as_completed()` blocks indefinitely if a tool Lambda hangs, blocking the entire request.

**Formal Specification:**
```
FUNCTION isBugCondition(tool_execution)
  INPUT: tool_execution (Future object from ThreadPoolExecutor)
  OUTPUT: boolean
  
  RETURN tool_execution.running_time > TOOL_TIMEOUT_THRESHOLD
         AND tool_execution.not_completed
         AND parallel_execution_mode = true
END FUNCTION
```

#### Expected Behavior

When tools execute in parallel, the system SHALL enforce a per-tool timeout (configurable via TOOL_EXECUTION_TIMEOUT_SEC, default: 25 seconds) using `concurrent.futures.wait()` with timeout parameter, controlled by feature flag ENABLE_TOOL_TIMEOUT (default: false).

#### Hypothesized Root Cause

In `_invoke_bedrock_direct()` function (lines 1070-1095), the parallel tool execution uses:
```python
for future in as_completed(futures):
    result = future.result()  # Blocks indefinitely if tool hangs
```

The `as_completed()` iterator has no timeout, and `future.result()` blocks until the future completes. If a tool Lambda hangs (network issue, infinite loop, downstream service hang), the entire request hangs until Lambda's 120-second timeout.

#### Fix Implementation

**File**: `backend/lambdas/agent_orchestrator/handler.py`

**Changes Required**:

1. **Add feature flag at module level**:
```python
# Feature flag: Tool execution timeout (default: OFF)
ENABLE_TOOL_TIMEOUT = os.environ.get('ENABLE_TOOL_TIMEOUT', 'false').lower() == 'true'
TOOL_EXECUTION_TIMEOUT_SEC = int(os.environ.get('TOOL_EXECUTION_TIMEOUT_SEC', '25'))
```

2. **Add helper function for timeout handling**:
```python
def _execute_tool_with_timeout(tool_name, tool_input, timeout_sec):
    """Execute tool with timeout protection. Returns (result, timed_out, error)."""
    try:
        result = _execute_tool(tool_name, tool_input)
        return result, False, None
    except Exception as e:
        logger.error(f"Tool {tool_name} execution error: {str(e)}")
        return {"error": str(e)}, False, str(e)
```

3. **Modify parallel tool execution in `_invoke_bedrock_direct()`** (replace lines 1070-1095):

```python
# ── PARALLEL TOOL EXECUTION ──
tool_results = []
if len(pending_tools) >= 2:
    logger.info(f"Parallel tool execution: {[t['name'] for t in pending_tools]}")
    
    if ENABLE_TOOL_TIMEOUT:
        # NEW: Execute with timeout protection
        with ThreadPoolExecutor(max_workers=len(pending_tools)) as pool:
            futures = {
                pool.submit(_execute_tool, t["name"], t["input"]): t
                for t in pending_tools
            }
            
            # Wait with timeout
            done, not_done = wait(futures.keys(), timeout=TOOL_EXECUTION_TIMEOUT_SEC)
            
            # Process completed tools
            for future in done:
                t = futures[future]
                tool_name = t["name"]
                tool_input = t["input"]
                tool_id = t["id"]
                tools_used.append(tool_name)
                
                try:
                    result = future.result()  # Already completed, won't block
                    result = _enrich_tool_result(result, tool_name, tool_input, prompt)
                    tool_data_log.append({"tool": tool_name, "input": tool_input, "output": result})
                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tool_id,
                            "content": [{"json": result}],
                        }
                    })
                except Exception as e:
                    logger.error(f"Tool {tool_name} result error: {str(e)}")
                    error_result = {"error": f"Tool execution failed: {str(e)}"}
                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tool_id,
                            "content": [{"json": error_result}],
                        }
                    })
            
            # Handle timed-out tools
            for future in not_done:
                t = futures[future]
                tool_name = t["name"]
                tool_id = t["id"]
                logger.error(f"Tool {tool_name} TIMED OUT after {TOOL_EXECUTION_TIMEOUT_SEC}s")
                tools_used.append(f"{tool_name}_TIMEOUT")
                
                timeout_result = {
                    "error": f"Tool execution timed out after {TOOL_EXECUTION_TIMEOUT_SEC} seconds",
                    "tool": tool_name,
                    "timeout": True
                }
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_id,
                        "content": [{"json": timeout_result}],
                    }
                })
                
                # Cancel the future to free resources
                future.cancel()
    else:
        # EXISTING: No timeout protection (original code)
        with ThreadPoolExecutor(max_workers=len(pending_tools)) as pool:
            futures = {
                pool.submit(_execute_tool, t["name"], t["input"]): t
                for t in pending_tools
            }
            for future in as_completed(futures):
                t = futures[future]
                tool_name = t["name"]
                tool_input = t["input"]
                tool_id = t["id"]
                tools_used.append(tool_name)
                result = future.result()
                result = _enrich_tool_result(result, tool_name, tool_input, prompt)
                tool_data_log.append({"tool": tool_name, "input": tool_input, "output": result})
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_id,
                        "content": [{"json": result}],
                    }
                })
else:
    # EXISTING: Single tool — execute directly (no thread overhead)
    # ... keep existing code unchanged ...
```

**CloudFormation Changes**:
```yaml
Environment:
  Variables:
    ENABLE_TOOL_TIMEOUT: 'false'  # Default: OFF
    TOOL_EXECUTION_TIMEOUT_SEC: '25'  # 25 seconds per tool
```

#### Testing Strategy

**Unit Tests**:
- Mock `_execute_tool()` to sleep for 30 seconds
- Verify timeout triggers after 25 seconds
- Verify timeout result includes `"timeout": true`
- Verify other tools complete successfully

**Integration Tests**:
- Deploy test Lambda that sleeps for 60 seconds
- Invoke orchestrator with 2 tools (1 normal, 1 slow)
- Verify fast tool completes, slow tool times out
- Verify response includes both results

**Chaos Testing**:
- Randomly inject 30-second delays in tool Lambdas
- Verify system remains responsive
- Verify no cascading failures

#### Rollback Plan

1. Set `ENABLE_TOOL_TIMEOUT: 'false'`
2. Deploy stack update
3. Verify parallel tool execution works as before
4. Monitor for any tool execution errors

---

### Bug 1.3: DynamoDB Rate Limits Table Growth (No TTL)

#### Fault Condition

The bug manifests when rate limit records are written to the DynamoDB `rate_limits` table. Records persist indefinitely because no TTL attribute is configured in the CloudFormation template, causing unbounded table growth.

**Formal Specification:**
```
FUNCTION isBugCondition(rate_limit_record)
  INPUT: rate_limit_record (DynamoDB item)
  OUTPUT: boolean
  
  RETURN rate_limit_record.ttl_epoch EXISTS
         AND DynamoDB_TTL_enabled = false
         AND record_age > expected_lifetime
END FUNCTION
```

#### Expected Behavior

When rate limit records are written to DynamoDB, the CloudFormation template SHALL configure `TimeToLiveSpecification` with `AttributeName='ttl_epoch'` to automatically delete expired records, controlled by feature flag ENABLE_RATE_LIMIT_TTL (default: false).

#### Hypothesized Root Cause

The `infrastructure/template.yaml` CloudFormation template defines the `RateLimitsTable` resource but does not include a `TimeToLiveSpecification` property. The `rate_limiter.py` code already writes `ttl_epoch` attributes (lines 60, 78, 96), but DynamoDB doesn't automatically delete records unless TTL is enabled at the table level.

#### Fix Implementation

**File**: `infrastructure/template.yaml`

**Changes Required**:

1. **Locate the RateLimitsTable resource** (search for `RateLimitsTable:`):

```yaml
RateLimitsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: rate_limits
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: rate_key
        AttributeType: S
      - AttributeName: window
        AttributeType: S
    KeySchema:
      - AttributeName: rate_key
        KeyType: HASH
      - AttributeName: window
        KeyType: RANGE
    # NEW: Add TTL configuration (controlled by parameter)
    TimeToLiveSpecification:
      Enabled: !Ref EnableRateLimitTTL
      AttributeName: ttl_epoch
```

2. **Add CloudFormation parameter** (in Parameters section):
```yaml
Parameters:
  # ... existing parameters ...
  
  EnableRateLimitTTL:
    Type: String
    Default: 'false'
    AllowedValues:
      - 'true'
      - 'false'
    Description: Enable DynamoDB TTL for rate_limits table (default OFF for safety)
```

**Note**: DynamoDB TTL is a table-level setting, not controlled by Lambda environment variables. The feature flag is implemented as a CloudFormation parameter that controls whether TTL is enabled when the stack is deployed.

**Alternative Implementation** (if table already exists in production):

If the `rate_limits` table already exists and cannot be recreated, add a separate CloudFormation custom resource to enable TTL:

```yaml
EnableRateLimitTTLCustomResource:
  Type: Custom::EnableTTL
  Condition: ShouldEnableRateLimitTTL
  Properties:
    ServiceToken: !GetAtt EnableTTLLambda.Arn
    TableName: !Ref RateLimitsTable
    AttributeName: ttl_epoch

Conditions:
  ShouldEnableRateLimitTTL: !Equals [!Ref EnableRateLimitTTL, 'true']
```

#### Testing Strategy

**Pre-Deployment Tests**:
- Query existing `rate_limits` table for record count
- Document current table size and item count
- Verify `ttl_epoch` attribute exists in records

**Post-Deployment Tests** (with flag ON):
- Verify TTL is enabled: `aws dynamodb describe-time-to-live --table-name rate_limits`
- Write test record with `ttl_epoch` = current_time + 60 seconds
- Wait 90 seconds, verify record is deleted
- Monitor table size over 24 hours, verify it stabilizes

**Rollback Tests** (with flag OFF):
- Verify TTL remains disabled
- Verify records persist indefinitely
- Verify no change in table behavior

#### Rollback Plan

1. Set `EnableRateLimitTTL: 'false'` in CloudFormation parameters
2. Deploy stack update
3. Verify TTL is disabled: `aws dynamodb describe-time-to-live --table-name rate_limits`
4. Note: Existing records with TTL will still be deleted (DynamoDB behavior), but new records won't be affected

**Important**: Disabling TTL after enabling it does NOT restore deleted records. Plan rollback carefully.

---

### Bug 1.4: Bedrock Model Fallback Control (Feature Flag Missing)

#### Fault Condition

The system currently has bidirectional model fallback implemented (Nova Pro ↔ Nova 2 Lite) that is ALWAYS enabled with no way to disable it. The bug is the lack of a feature flag to control this behavior.

**Current Behavior**: The `_bedrock_converse_with_retry()` function automatically falls back between models:
- Nova Pro fails → automatically tries Nova 2 Lite
- Nova 2 Lite fails → automatically tries Nova Pro

**Formal Specification:**
```
FUNCTION isBugCondition(bedrock_response, retry_count)
  INPUT: bedrock_response (API response), retry_count (int)
  OUTPUT: boolean
  
  RETURN bedrock_response.error IN ['ThrottlingException', 'ServiceUnavailableException']
         AND retry_count >= MAX_RETRIES
         AND fallback_executed_without_flag_check
END FUNCTION
```

#### Expected Behavior

The existing bidirectional model fallback (Nova Pro ↔ Nova 2 Lite) SHALL be controlled by feature flag ENABLE_MODEL_FALLBACK (default: false). When disabled, the system should fail immediately without attempting fallback.

#### Hypothesized Root Cause

The `_bedrock_converse_with_retry()` function (lines 688-735) has bidirectional fallback logic using the `MODEL_FALLBACK` dictionary, but there is no feature flag to control whether this fallback should execute. The fallback always runs, which may not be desired for conservative deployments.

#### Fix Implementation

**File**: `backend/lambdas/agent_orchestrator/handler.py`

**Changes Required**:

1. **Add feature flag at module level** (after line 62):
```python
# Feature flag: Model fallback control (default: OFF)
ENABLE_MODEL_FALLBACK = os.environ.get('ENABLE_MODEL_FALLBACK', 'false').lower() == 'true'
```

2. **Modify `_bedrock_converse_with_retry()` function** - wrap existing fallback logic in feature flag check (around line 720):

**BEFORE (current code - fallback always runs)**:
```python
    # ── MODEL FALLBACK ──
    fallback_model = MODEL_FALLBACK.get(primary_model)
    if fallback_model and last_exc:
        error_code = ''
        if isinstance(last_exc, ClientError):
            error_code = last_exc.response.get('Error', {}).get('Code', '')
        logger.warning(
            f"Primary model {primary_model} failed ({error_code}) after {1+MAX_RETRIES} attempts — "
            f"falling back to {fallback_model}"
        )
        try:
            fallback_kwargs = {**kwargs, 'modelId': fallback_model}
            response = bedrock_client.converse(**fallback_kwargs)
            logger.info(f"Model fallback SUCCESS: {fallback_model}")
            return response
        except Exception as fb_err:
            logger.error(f"Model fallback FAILED: {fallback_model} — {fb_err}")
    
    # Raise the original exception
    if last_exc:
        raise last_exc
```

**AFTER (with feature flag control)**:
```python
    # ── MODEL FALLBACK (controlled by feature flag) ──
    if ENABLE_MODEL_FALLBACK:
        fallback_model = MODEL_FALLBACK.get(primary_model)
        if fallback_model and last_exc:
            error_code = ''
            if isinstance(last_exc, ClientError):
                error_code = last_exc.response.get('Error', {}).get('Code', '')
            logger.warning(
                f"Primary model {primary_model} failed ({error_code}) after {1+MAX_RETRIES} attempts — "
                f"falling back to {fallback_model}"
            )
            try:
                fallback_kwargs = {**kwargs, 'modelId': fallback_model}
                response = bedrock_client.converse(**fallback_kwargs)
                logger.info(f"Model fallback SUCCESS: {fallback_model}")
                return response
            except Exception as fb_err:
                logger.error(f"Model fallback FAILED: {fallback_model} — {fb_err}")
    else:
        logger.info("Model fallback DISABLED (ENABLE_MODEL_FALLBACK=false)")
    
    # Raise the original exception
    if last_exc:
        raise last_exc
```

**Key Changes**:
- Wrap the entire fallback block in `if ENABLE_MODEL_FALLBACK:`
- Add else clause to log when fallback is disabled
- When flag is OFF: fail immediately with original error (conservative)
- When flag is ON: use existing bidirectional fallback (Nova Pro ↔ Nova 2 Lite)

**CloudFormation Changes**:
```yaml
Environment:
  Variables:
    ENABLE_MODEL_FALLBACK: 'false'  # Default: OFF (conservative)
    FOUNDATION_MODEL: 'apac.amazon.nova-pro-v1:0'  # Primary model
    FOUNDATION_MODEL_LITE: 'global.amazon.nova-2-lite-v1:0'  # Fallback model
```

#### Testing Strategy

**Unit Tests (flag OFF)**:
- Mock Bedrock client to raise `ThrottlingException` for Nova Pro
- Verify NO fallback to Nova 2 Lite is attempted
- Verify original error is raised immediately
- Verify log message: "Model fallback DISABLED"

**Unit Tests (flag ON)**:
- Mock Nova Pro to throttle, Nova 2 Lite to succeed
- Verify fallback to Nova 2 Lite is attempted
- Verify response returned from Nova 2 Lite
- Mock Nova 2 Lite to throttle, Nova Pro to succeed
- Verify bidirectional fallback works (Lite → Pro)

**Integration Tests**:
- Test with flag OFF: verify failures are immediate
- Test with flag ON: verify fallback reduces error rate during throttling
- Verify response is returned from fallback model
- Mock fallback to also fail, verify original error is raised

**Integration Tests**:
- Temporarily set primary model to invalid ID
- Verify fallback to FOUNDATION_MODEL_LITE succeeds
- Verify response quality is acceptable (may be lower quality)
- Verify flag OFF: no fallback attempted

**Load Tests**:
- Generate high load to trigger throttling
- Verify fallback reduces error rate
- Measure latency impact of fallback

#### Rollback Plan

1. Set `ENABLE_MODEL_FALLBACK: 'false'`
2. Deploy stack update
3. Verify throttling errors are raised without fallback
4. Monitor error rate (may increase without fallback)

---

### Bug 1.5: Parallel Tool Race Conditions (Shared State Mutations)

#### Fault Condition

The bug manifests when multiple tools execute in parallel via ThreadPoolExecutor and one tool modifies shared state (`tools_used` list, `tool_data_log` list). Race conditions can occur causing incorrect tool attribution or missing tool results.

**Formal Specification:**
```
FUNCTION isBugCondition(parallel_execution)
  INPUT: parallel_execution (ThreadPoolExecutor context)
  OUTPUT: boolean
  
  RETURN parallel_execution.worker_count >= 2
         AND shared_state_accessed_without_lock
         AND (tools_used.append() OR tool_data_log.append())
END FUNCTION
```

#### Expected Behavior

When multiple tools execute in parallel, the system SHALL use thread-safe data structures (queue.Queue or threading.Lock) to protect shared state (tools_used, tool_data_log), controlled by feature flag ENABLE_THREAD_SAFE_TOOLS (default: false).

#### Hypothesized Root Cause

In `_invoke_bedrock_direct()` function (lines 1070-1095), multiple threads append to shared lists:
```python
tools_used.append(tool_name)  # NOT thread-safe
tool_data_log.append({"tool": tool_name, ...})  # NOT thread-safe
```

Python's `list.append()` is not atomic for complex objects. While CPython's GIL provides some protection, race conditions can still occur with:
- Concurrent appends causing lost updates
- List resizing during concurrent access
- Incorrect ordering of results

#### Fix Implementation

**File**: `backend/lambdas/agent_orchestrator/handler.py`

**Changes Required**:

1. **Add feature flag and imports at module level**:
```python
import threading
from queue import Queue

# Feature flag: Thread-safe tool execution (default: OFF)
ENABLE_THREAD_SAFE_TOOLS = os.environ.get('ENABLE_THREAD_SAFE_TOOLS', 'false').lower() == 'true'
```

2. **Modify `_invoke_bedrock_direct()` function** - replace shared lists with thread-safe structures:

```python
def _invoke_bedrock_direct(prompt, farmer_context=None, skip_native_guardrail=False, 
                          chat_history=None, model_id=None, lambda_context=None):
    """Call Bedrock model directly with tool use (converse API)."""
    
    if ENABLE_THREAD_SAFE_TOOLS:
        # NEW: Thread-safe data structures
        tools_used_queue = Queue()
        tool_data_log_queue = Queue()
        tools_used = []  # Will be populated from queue after parallel execution
        tool_data_log = []  # Will be populated from queue after parallel execution
    else:
        # EXISTING: Regular lists (not thread-safe)
        tools_used = []
        tool_data_log = []
    
    guardrail_intervened = False
    
    # ... existing code for building messages ...
    
    try:
        for turn in range(5):
            # ... existing code for Bedrock call ...
            
            if stop_reason == "tool_use":
                # ... existing code for collecting pending_tools ...
                
                # ── PARALLEL TOOL EXECUTION ──
                tool_results = []
                if len(pending_tools) >= 2:
                    logger.info(f"Parallel tool execution: {[t['name'] for t in pending_tools]}")
                    
                    if ENABLE_THREAD_SAFE_TOOLS:
                        # NEW: Thread-safe execution
                        def execute_tool_safe(tool_info):
                            """Execute tool and add results to thread-safe queues."""
                            tool_name = tool_info["name"]
                            tool_input = tool_info["input"]
                            tool_id = tool_info["id"]
                            
                            try:
                                result = _execute_tool(tool_name, tool_input)
                                result = _enrich_tool_result(result, tool_name, tool_input, prompt)
                                
                                # Add to thread-safe queues
                                tools_used_queue.put(tool_name)
                                tool_data_log_queue.put({
                                    "tool": tool_name, 
                                    "input": tool_input, 
                                    "output": result
                                })
                                
                                return {
                                    "toolResult": {
                                        "toolUseId": tool_id,
                                        "content": [{"json": result}],
                                    }
                                }
                            except Exception as e:
                                logger.error(f"Tool {tool_name} execution error: {str(e)}")
                                tools_used_queue.put(f"{tool_name}_ERROR")
                                error_result = {"error": str(e)}
                                return {
                                    "toolResult": {
                                        "toolUseId": tool_id,
                                        "content": [{"json": error_result}],
                                    }
                                }
                        
                        with ThreadPoolExecutor(max_workers=len(pending_tools)) as pool:
                            futures = [pool.submit(execute_tool_safe, t) for t in pending_tools]
                            
                            if ENABLE_TOOL_TIMEOUT:
                                done, not_done = wait(futures, timeout=TOOL_EXECUTION_TIMEOUT_SEC)
                                for future in done:
                                    tool_results.append(future.result())
                                for future in not_done:
                                    future.cancel()
                                    # Add timeout result
                                    tools_used_queue.put("TIMEOUT")
                            else:
                                for future in as_completed(futures):
                                    tool_results.append(future.result())
                        
                        # Collect results from queues into lists
                        while not tools_used_queue.empty():
                            tools_used.append(tools_used_queue.get())
                        while not tool_data_log_queue.empty():
                            tool_data_log.append(tool_data_log_queue.get())
                    
                    else:
                        # EXISTING: Original code (not thread-safe)
                        with ThreadPoolExecutor(max_workers=len(pending_tools)) as pool:
                            futures = {
                                pool.submit(_execute_tool, t["name"], t["input"]): t
                                for t in pending_tools
                            }
                            for future in as_completed(futures):
                                t = futures[future]
                                tool_name = t["name"]
                                tool_input = t["input"]
                                tool_id = t["id"]
                                tools_used.append(tool_name)  # Race condition possible
                                result = future.result()
                                result = _enrich_tool_result(result, tool_name, tool_input, prompt)
                                tool_data_log.append({
                                    "tool": tool_name, 
                                    "input": tool_input, 
                                    "output": result
                                })  # Race condition possible
                                tool_results.append({
                                    "toolResult": {
                                        "toolUseId": tool_id,
                                        "content": [{"json": result}],
                                    }
                                })
                else:
                    # EXISTING: Single tool — no race condition
                    # ... keep existing code unchanged ...
                
                # ... rest of function ...
```

**CloudFormation Changes**:
```yaml
Environment:
  Variables:
    ENABLE_THREAD_SAFE_TOOLS: 'false'  # Default: OFF
```

#### Testing Strategy

**Unit Tests**:
- Mock 10 tools executing in parallel
- Verify `tools_used` list has exactly 10 entries
- Verify `tool_data_log` list has exactly 10 entries
- Verify no duplicate or missing entries

**Concurrency Tests**:
- Run 100 requests with 5 parallel tools each
- Verify tool attribution is correct in all responses
- Compare results with flag ON vs OFF
- Verify no data corruption

**Race Condition Tests**:
- Inject random delays in tool execution
- Verify results are consistent across runs
- Use thread sanitizer tools if available

#### Rollback Plan

1. Set `ENABLE_THREAD_SAFE_TOOLS: 'false'`
2. Deploy stack update
3. Verify parallel tool execution works as before
4. Monitor for any tool result inconsistencies

---

## HIGH SEVERITY BUGS

### Bug 1.6: KB Retrieve No Retry (Crop Advisory)

#### Fault Condition

The bug manifests when the crop advisory Lambda calls `bedrock_kb.retrieve()` and receives a throttling error. The system fails immediately without retry, causing farmers to receive "service unavailable" errors during peak usage.

**Formal Specification:**
```
FUNCTION isBugCondition(kb_retrieve_call)
  INPUT: kb_retrieve_call (Bedrock KB API call)
  OUTPUT: boolean
  
  RETURN kb_retrieve_call.error = 'ThrottlingException'
         AND retry_count = 0
         AND no_retry_logic_present
END FUNCTION
```

#### Expected Behavior

When the crop advisory Lambda calls `bedrock_kb.retrieve()` and receives a throttling error, the system SHALL retry up to 3 times with exponential backoff (1s, 2s, 4s), controlled by feature flag ENABLE_KB_RETRY (default: false).

#### Hypothesized Root Cause

In `backend/lambdas/crop_advisory/handler.py` (line 120), the KB retrieve call has no try/except retry logic:
```python
response = bedrock_kb.retrieve(
    knowledgeBaseId=KB_ID,
    retrievalQuery={'text': search_query},
    ...
)
```

Bedrock Knowledge Base can throttle during peak usage, but the code doesn't handle `ThrottlingException`.

#### Fix Implementation

**File**: `backend/lambdas/crop_advisory/handler.py`

**Changes Required**:

1. **Add feature flag and imports at module level**:
```python
import time

# Feature flag: KB retrieve retry (default: OFF)
ENABLE_KB_RETRY = os.environ.get('ENABLE_KB_RETRY', 'false').lower() == 'true'
KB_RETRY_MAX_ATTEMPTS = int(os.environ.get('KB_RETRY_MAX_ATTEMPTS', '3'))
KB_RETRY_BASE_DELAY = float(os.environ.get('KB_RETRY_BASE_DELAY', '1.0'))
```

2. **Add helper function for KB retrieve with retry**:

```python
def _kb_retrieve_with_retry(bedrock_kb_client, **kwargs):
    """Call bedrock_kb.retrieve() with exponential backoff retry."""
    if not ENABLE_KB_RETRY:
        # EXISTING: No retry logic
        return bedrock_kb_client.retrieve(**kwargs)
    
    # NEW: Retry logic
    last_error = None
    for attempt in range(KB_RETRY_MAX_ATTEMPTS):
        try:
            response = bedrock_kb_client.retrieve(**kwargs)
            if attempt > 0:
                logger.info(f"KB retrieve succeeded on attempt {attempt + 1}")
            return response
        except bedrock_kb_client.exceptions.ThrottlingException as e:
            last_error = e
            if attempt < KB_RETRY_MAX_ATTEMPTS - 1:
                delay = KB_RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"KB throttled (attempt {attempt + 1}/{KB_RETRY_MAX_ATTEMPTS}), "
                             f"retrying in {delay}s")
                time.sleep(delay)
            else:
                logger.error(f"KB throttled after {KB_RETRY_MAX_ATTEMPTS} attempts")
                raise
        except Exception as e:
            # Non-retryable error
            logger.error(f"KB retrieve error: {str(e)}")
            raise
    
    raise last_error
```

3. **Replace direct KB call in `lambda_handler()`** (line 120):
```python
# OLD:
# response = bedrock_kb.retrieve(...)

# NEW:
response = _kb_retrieve_with_retry(
    bedrock_kb,
    knowledgeBaseId=KB_ID,
    retrievalQuery={'text': search_query},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 8
        }
    }
)
```

**CloudFormation Changes** (add to CropAdvisoryFunction):
```yaml
Environment:
  Variables:
    ENABLE_KB_RETRY: 'false'
    KB_RETRY_MAX_ATTEMPTS: '3'
    KB_RETRY_BASE_DELAY: '1.0'
```

---

### Bug 1.7: Coordinate Validation Missing (Weather Lookup)

#### Fix Implementation

**File**: `backend/lambdas/weather_lookup/handler.py`

**Changes**:

1. **Add feature flag**:
```python
ENABLE_COORDINATE_VALIDATION = os.environ.get('ENABLE_COORDINATE_VALIDATION', 'false').lower() == 'true'
```

2. **Add validation function**:
```python
def _validate_coordinates(lat, lon):
    """Validate latitude and longitude ranges. Returns (valid, error_msg)."""
    if not ENABLE_COORDINATE_VALIDATION:
        return True, None
    
    try:
        lat_f = float(lat) if lat else None
        lon_f = float(lon) if lon else None
        
        if lat_f is not None and not (-90 <= lat_f <= 90):
            return False, f"Invalid latitude: {lat}. Must be between -90 and 90."
        
        if lon_f is not None and not (-180 <= lon_f <= 180):
            return False, f"Invalid longitude: {lon}. Must be between -180 and 180."
        
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid coordinate format. Must be numeric."
```

3. **Add validation in `lambda_handler()`** (after extracting lat/lon):
```python
# NEW: Validate coordinates
if ENABLE_COORDINATE_VALIDATION and (lat or lon):
    is_valid, error_msg = _validate_coordinates(lat, lon)
    if not is_valid:
        logger.warning(f"Coordinate validation failed: {error_msg}")
        return error_response(error_msg, 400, origin=origin)
```

---

### Bugs 1.8-1.13: Implementation Summary

Due to space constraints, here's a condensed implementation approach for the remaining HIGH severity bugs:

**Bug 1.8 - Translation Length Limit**:
- Add `ENABLE_TRANSLATION_CHUNKING` flag
- Check text length before translation (AWS Translate limit: ~10,000 bytes)
- Split into chunks if needed, translate separately, rejoin
- File: `backend/utils/translate_helper.py`

**Bug 1.9 - gTTS Fixed Backoff**:
- Add `ENABLE_GTTS_EXPONENTIAL_BACKOFF` flag
- Replace fixed 0.6s delay with exponential: `base * (2 ** attempt)`
- Add jitter: `delay * (1 + random.uniform(-0.25, 0.25))`
- File: `backend/utils/polly_helper.py`, function `_gtts_tts()`

**Bug 1.10 - Chat History Pagination**:
- Add `ENABLE_CHAT_PAGINATION` flag
- Check for `LastEvaluatedKey` in DynamoDB response
- Loop until all messages retrieved or limit reached
- File: `backend/utils/dynamodb_helper.py`, function `get_chat_history()`

**Bug 1.11 - Audio URL Expiry**:
- Add `ENABLE_EXTENDED_AUDIO_EXPIRY` flag
- Change presigned URL expiry from 3600s to 7200s
- Return both URL and S3 key for refresh capability
- File: `backend/utils/polly_helper.py`, function `_upload_audio_bytes()`

**Bug 1.12 - Regex DoS Protection**:
- Add `ENABLE_REGEX_DOS_PROTECTION` flag
- Limit input length to 2000 chars before regex matching
- Use atomic groups in patterns: `(?>...)` instead of `(...)`
- File: `backend/utils/guardrails.py`, function `check_prompt_injection()`

**Bug 1.13 - Smart Truncation**:
- Add `ENABLE_SMART_TRUNCATION` flag
- Search last 500 chars (instead of 200) for sentence boundary
- File: `backend/utils/guardrails.py`, function `truncate_output()`

---

## MEDIUM SEVERITY BUGS (1.14-1.24)

### Implementation Pattern

All MEDIUM bugs follow this pattern:
1. Add feature flag (default: 'false')
2. Implement new logic in `if ENABLE_X:` branch
3. Keep existing logic in `else:` branch
4. Add comprehensive logging for both paths
5. Update CloudFormation with environment variable

### Bug 1.14: Connection Pooling

**File**: All Lambda handlers and utils

**Changes**:
```python
from botocore.config import Config

ENABLE_CONNECTION_POOLING = os.environ.get('ENABLE_CONNECTION_POOLING', 'false').lower() == 'true'

if ENABLE_CONNECTION_POOLING:
    boto_config = Config(max_pool_connections=25)
    bedrock_rt = boto3.client('bedrock-runtime', config=boto_config)
    lambda_client = boto3.client('lambda', config=boto_config)
    s3 = boto3.client('s3', config=boto_config)
    dynamodb = boto3.resource('dynamodb', config=boto_config)
else:
    # EXISTING: No config
    bedrock_rt = boto3.client('bedrock-runtime')
    lambda_client = boto3.client('lambda')
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
```

### Bug 1.15: Batch Chat Writes

**File**: `backend/utils/dynamodb_helper.py`

**Changes**:
```python
ENABLE_BATCH_CHAT_WRITES = os.environ.get('ENABLE_BATCH_CHAT_WRITES', 'false').lower() == 'true'

def save_chat_messages_batch(messages):
    """Save multiple chat messages in a single batch write."""
    if not ENABLE_BATCH_CHAT_WRITES or len(messages) <= 1:
        # EXISTING: Save one at a time
        for msg in messages:
            save_chat_message(**msg)
        return True
    
    # NEW: Batch write (up to 25 items)
    try:
        with sessions_table.batch_writer() as batch:
            for msg in messages[:25]:  # DynamoDB limit
                item = {
                    'session_id': msg['session_id'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'role': msg['role'],
                    'message': msg['message'],
                    'language': msg.get('language', 'en'),
                    'ttl': int(_time.time()) + (CHAT_TTL_DAYS * 86400),
                }
                if msg.get('farmer_id'):
                    item['farmer_id'] = msg['farmer_id']
                if msg.get('message_en'):
                    item['message_en'] = msg['message_en']
                batch.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Batch write error: {str(e)}")
        return False
```

### Bug 1.16: Backoff Jitter

**File**: `backend/lambdas/agent_orchestrator/handler.py`

**Changes** in `_bedrock_converse_with_retry()`:
```python
ENABLE_BACKOFF_JITTER = os.environ.get('ENABLE_BACKOFF_JITTER', 'false').lower() == 'true'

if ENABLE_BACKOFF_JITTER:
    import random
    delay = base_delay * (2 ** attempt)
    jitter = delay * random.uniform(-0.25, 0.25)
    delay = delay + jitter
else:
    delay = base_delay * (2 ** attempt)
```

### Bugs 1.17-1.24: Quick Reference

| Bug | File | Key Change |
|-----|------|------------|
| 1.17 Profile Cache | `dynamodb_helper.py` | Add module-level dict cache with TTL |
| 1.18 Farmer ID Validation | `handler.py` | Regex: `^[a-zA-Z0-9\-_]{1,64}$` |
| 1.19 Model Validation | `handler.py` | Check against allowed list |
| 1.20 Language Logging | `translate_helper.py` | Log invalid language codes |
| 1.21 Tool Timeout | `handler.py` | Set `Config(read_timeout=30)` |
| 1.22 Voice Validation | `polly_helper.py` | Check against VOICE_MAP |
| 1.23 S3 Validation | `polly_helper.py` | Call `s3.head_bucket()` at init |
| 1.24 Chat Idempotency | `dynamodb_helper.py` | Add idempotency_token + ConditionExpression |

---

## LOW SEVERITY BUGS (1.25-1.28)

### Bug 1.25: TTS List Formatting

**File**: `backend/utils/polly_helper.py`

**Changes** in `_strip_markdown_for_tts()`:
```python
ENABLE_TTS_LIST_FORMATTING = os.environ.get('ENABLE_TTS_LIST_FORMATTING', 'false').lower() == 'true'

if ENABLE_TTS_LIST_FORMATTING:
    # NEW: Replace numbered lists with words
    s = re.sub(r'^\s*1\.\s+', 'First, ', s, flags=re.MULTILINE)
    s = re.sub(r'^\s*2\.\s+', 'Second, ', s, flags=re.MULTILINE)
    s = re.sub(r'^\s*3\.\s+', 'Third, ', s, flags=re.MULTILINE)
    s = re.sub(r'^\s*4\.\s+', 'Fourth, ', s, flags=re.MULTILINE)
    s = re.sub(r'^\s*5\.\s+', 'Fifth, ', s, flags=re.MULTILINE)
else:
    # EXISTING: Just remove numbers
    s = re.sub(r'^\d+\.\s+', '', s, flags=re.MULTILINE)
```

### Bug 1.26: HTTPS Weather API

**File**: `backend/lambdas/weather_lookup/handler.py`

**Changes**:
```python
ENABLE_HTTPS_WEATHER_API = os.environ.get('ENABLE_HTTPS_WEATHER_API', 'false').lower() == 'true'

if ENABLE_HTTPS_WEATHER_API:
    OPENWEATHER_BASE = 'https://api.openweathermap.org/data/2.5'
else:
    OPENWEATHER_BASE = 'http://api.openweathermap.org/data/2.5'  # EXISTING
```

### Bug 1.27: Tool Metrics

**File**: `backend/lambdas/agent_orchestrator/handler.py`

**Changes**:
```python
ENABLE_TOOL_METRICS = os.environ.get('ENABLE_TOOL_METRICS', 'false').lower() == 'true'

if ENABLE_TOOL_METRICS:
    cloudwatch = boto3.client('cloudwatch')

def _emit_tool_metric(tool_name, duration_ms, success):
    """Emit CloudWatch custom metric for tool execution."""
    if not ENABLE_TOOL_METRICS:
        return
    
    try:
        cloudwatch.put_metric_data(
            Namespace='SmartRuralAI/Tools',
            MetricData=[
                {
                    'MetricName': 'ExecutionDuration',
                    'Value': duration_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'ToolName', 'Value': tool_name},
                        {'Name': 'Success', 'Value': str(success)}
                    ]
                }
            ]
        )
    except Exception as e:
        logger.warning(f"Failed to emit metric: {str(e)}")
```

### Bug 1.28: Unified CORS

**File**: Create new `backend/utils/cors_helper.py`

**Changes**:
```python
import os

ENABLE_UNIFIED_CORS = os.environ.get('ENABLE_UNIFIED_CORS', 'false').lower() == 'true'
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', '*')

def get_cors_headers(origin=None):
    """Get standardized CORS headers."""
    if not ENABLE_UNIFIED_CORS:
        # EXISTING: Each Lambda implements its own
        return {}
    
    # NEW: Unified CORS headers
    return {
        'Access-Control-Allow-Origin': origin or ALLOWED_ORIGIN,
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
        'Access-Control-Max-Age': '86400'
    }

def handle_cors_preflight(event):
    """Handle OPTIONS preflight requests."""
    if not ENABLE_UNIFIED_CORS:
        return None
    
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(event.get('headers', {}).get('origin')),
            'body': ''
        }
    return None
```

Then update all Lambda handlers to use:
```python
from utils.cors_helper import get_cors_headers, handle_cors_preflight

def lambda_handler(event, context):
    # Check for preflight
    preflight_response = handle_cors_preflight(event)
    if preflight_response:
        return preflight_response
    
    # ... existing logic ...
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(event.get('headers', {}).get('origin')),
        'body': json.dumps(result)
    }
```

---

## Correctness Properties

Property 1: Fault Condition - Timeout Protection

_For any_ request where processing time approaches the 29-second API Gateway timeout, the fixed system SHALL detect the approaching timeout and return a graceful response before the hard timeout, preventing "Gateway Timeout" errors.

**Validates: Requirements 2.1**

Property 2: Fault Condition - Tool Timeout Protection

_For any_ parallel tool execution where one or more tools exceed the configured timeout threshold, the fixed system SHALL cancel the timed-out tools and return results from completed tools, preventing indefinite hangs.

**Validates: Requirements 2.2**

Property 3: Fault Condition - DynamoDB TTL

_For any_ rate limit record written to DynamoDB with a ttl_epoch attribute, the fixed system SHALL automatically delete the record after expiration when TTL is enabled, preventing unbounded table growth.

**Validates: Requirements 2.3**

Property 4: Fault Condition - Model Fallback

_For any_ Bedrock API call that fails with throttling after exhausting retries, the fixed system SHALL attempt one final call using FOUNDATION_MODEL_LITE, providing graceful degradation.

**Validates: Requirements 2.4**

Property 5: Fault Condition - Thread Safety

_For any_ parallel tool execution involving 2 or more tools, the fixed system SHALL use thread-safe data structures to prevent race conditions in shared state mutations.

**Validates: Requirements 2.5**

Property 6: Preservation - Feature Flags Default OFF

_For any_ request when all feature flags are set to their default values (false), the fixed system SHALL execute exactly the same code paths as the original system, producing identical behavior.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.15, 3.16, 3.17, 3.18, 3.19, 3.20**

---

## Testing Strategy

### Validation Approach

The testing strategy follows a three-phase approach:
1. **Exploratory Testing**: Verify bugs exist on unfixed code
2. **Fix Validation**: Verify fixes work with flags ON
3. **Preservation Testing**: Verify no behavior change with flags OFF

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate each bug BEFORE implementing fixes.

**Test Plan**: Write tests that trigger each bug condition on UNFIXED code to confirm root cause analysis.

**Test Cases** (Critical Bugs):
1. **Timeout Test**: Send complex query requiring 35+ seconds, observe Gateway Timeout (will fail on unfixed code)
2. **Tool Hang Test**: Mock tool Lambda to sleep 60s, observe request hang (will fail on unfixed code)
3. **TTL Test**: Query rate_limits table after 24 hours, observe unbounded growth (will fail on unfixed code)
4. **Throttle Test**: Trigger Bedrock throttling, observe no fallback attempt (will fail on unfixed code)
5. **Race Condition Test**: Run 100 parallel tool executions, observe inconsistent results (may fail on unfixed code)

**Expected Counterexamples**:
- Gateway Timeout errors after 29 seconds
- Request hangs until 120-second Lambda timeout
- DynamoDB table size grows without bound
- Throttling errors with no fallback
- Missing or duplicate tool results

### Fix Checking

**Goal**: Verify that for all inputs where bug conditions hold, the fixed functions produce expected behavior.

**Pseudocode**:
```
FOR EACH bug IN [1.1, 1.2, ..., 1.28] DO
  SET feature_flag[bug] = true
  FOR ALL input WHERE isBugCondition[bug](input) DO
    result := fixedFunction[bug](input)
    ASSERT expectedBehavior[bug](result)
  END FOR
END FOR
```

**Test Cases**:
- Enable each flag individually
- Trigger bug condition
- Verify fix behavior
- Measure performance impact

### Preservation Checking

**Goal**: Verify that for all inputs where bug conditions do NOT hold, the fixed functions produce the same results as original functions.

**Pseudocode**:
```
FOR EACH bug IN [1.1, 1.2, ..., 1.28] DO
  SET feature_flag[bug] = false
  FOR ALL input WHERE NOT isBugCondition[bug](input) DO
    ASSERT originalFunction(input) = fixedFunction(input)
  END FOR
END FOR
```

**Testing Approach**: Property-based testing is recommended because:
- Generates many test cases automatically
- Catches edge cases manual tests miss
- Provides strong guarantees of unchanged behavior

**Test Plan**:
1. Run full regression suite with all flags OFF
2. Compare results with baseline (pre-fix)
3. Verify zero behavioral differences
4. Verify zero performance degradation

### Unit Tests

- Test each helper function in isolation
- Mock external dependencies (Bedrock, DynamoDB, S3)
- Test both flag ON and flag OFF paths
- Verify error handling and logging

### Property-Based Tests

- Generate random inputs across valid ranges
- Verify correctness properties hold
- Test edge cases (empty inputs, max lengths, special characters)
- Verify preservation properties with flags OFF

### Integration Tests

- Deploy to test environment
- Run end-to-end scenarios
- Test all 28 fixes together
- Verify no interactions between fixes

### Load Tests

- Generate 1000 requests/minute
- Enable fixes one at a time
- Measure latency, error rate, cost
- Verify no performance degradation

---

## Rollout Strategy

### Phase 1: Deploy with All Flags OFF (Week 1)

1. Deploy all code changes with flags defaulting to 'false'
2. Run full regression suite
3. Monitor production for 48 hours
4. Verify zero behavioral changes

### Phase 2: Enable Low-Risk Fixes (Week 2)

Enable flags for LOW severity bugs (1.25-1.28):
- ENABLE_TTS_LIST_FORMATTING
- ENABLE_HTTPS_WEATHER_API
- ENABLE_TOOL_METRICS
- ENABLE_UNIFIED_CORS

Monitor for 48 hours, rollback if issues detected.

### Phase 3: Enable Medium-Risk Fixes (Week 3-4)

Enable flags for MEDIUM severity bugs (1.14-1.24) one at a time:
- Day 1: ENABLE_CONNECTION_POOLING
- Day 2: ENABLE_BACKOFF_JITTER
- Day 3: ENABLE_PROFILE_CACHE
- ... (continue with remaining MEDIUM bugs)

Monitor each for 24 hours before enabling next.

### Phase 4: Enable High-Risk Fixes (Week 5-6)

Enable flags for HIGH severity bugs (1.6-1.13) one at a time:
- Day 1: ENABLE_KB_RETRY
- Day 2: ENABLE_COORDINATE_VALIDATION
- Day 3: ENABLE_TRANSLATION_CHUNKING
- ... (continue with remaining HIGH bugs)

Monitor each for 48 hours before enabling next.

### Phase 5: Enable Critical Fixes (Week 7-8)

Enable flags for CRITICAL severity bugs (1.1-1.5) one at a time:
- Day 1: ENABLE_RATE_LIMIT_TTL (infrastructure change)
- Day 3: ENABLE_TIMEOUT_PROTECTION
- Day 5: ENABLE_MODEL_FALLBACK
- Day 7: ENABLE_TOOL_TIMEOUT
- Day 9: ENABLE_THREAD_SAFE_TOOLS

Monitor each for 72 hours before enabling next.

### Phase 6: Full Production (Week 9)

All flags enabled, monitor for 1 week before declaring success.

---

## Monitoring and Observability

### CloudWatch Dashboards

Create dashboard with widgets for:
- Feature flag status (custom metrics)
- Error rates by bug fix
- Latency percentiles (p50, p95, p99)
- Tool execution metrics
- DynamoDB table sizes
- Lambda timeout rates

### Alarms

Set alarms for:
- Error rate increase > 5% (rollback trigger)
- Latency p99 increase > 20% (investigate)
- DynamoDB throttling (capacity issue)
- Lambda timeout rate > 1% (timeout protection not working)

### Logging

All fixes include structured logging:
```python
logger.info(f"Feature {FEATURE_NAME} {'ENABLED' if FLAG else 'DISABLED'}")
logger.info(f"Bug fix applied: {bug_id}, result: {result}")
```

Search CloudWatch Logs for:
- "Feature.*ENABLED" - which fixes are active
- "Bug fix applied" - fix execution traces
- "TIMEOUT" - timeout events
- "RETRY" - retry events

---

## Rollback Procedures

### Individual Fix Rollback

1. Identify problematic fix via monitoring
2. Set feature flag to 'false' in CloudFormation
3. Deploy stack update (< 2 minutes)
4. Verify old behavior restored
5. Monitor for 30 minutes
6. Document issue for offline investigation

### Emergency Rollback (All Fixes)

If multiple fixes cause issues:

1. Revert to previous CloudFormation template version
2. Deploy stack update
3. Verify all flags are OFF
4. Monitor for 1 hour
5. Conduct post-mortem

### Rollback Testing

Before production rollout, test rollback procedures:
- Enable fix, verify it works
- Disable fix, verify rollback
- Measure rollback time (should be < 5 minutes)

---

## Success Criteria

1. ✅ All 28 fixes implemented behind feature flags
2. ✅ All flags default to 'false' (no behavior change)
3. ✅ All regression tests pass with flags OFF
4. ✅ All fix tests pass with flags ON
5. ✅ Rollback procedure validated for each fix
6. ✅ CloudWatch dashboards created
7. ✅ Runbook created for gradual rollout
8. ✅ Zero production incidents during rollout
9. ✅ Performance metrics within acceptable ranges
10. ✅ Cost impact < 5% increase

---

## Appendix: Feature Flag Reference

| Flag | Bug | File | Default | Risk |
|------|-----|------|---------|------|
| ENABLE_TIMEOUT_PROTECTION | 1.1 | handler.py | false | Low |
| ENABLE_TOOL_TIMEOUT | 1.2 | handler.py | false | Medium |
| ENABLE_RATE_LIMIT_TTL | 1.3 | template.yaml | false | Low |
| ENABLE_MODEL_FALLBACK | 1.4 | handler.py | false | Low |
| ENABLE_THREAD_SAFE_TOOLS | 1.5 | handler.py | false | Medium |
| ENABLE_KB_RETRY | 1.6 | crop_advisory/handler.py | false | Low |
| ENABLE_COORDINATE_VALIDATION | 1.7 | weather_lookup/handler.py | false | Low |
| ENABLE_TRANSLATION_CHUNKING | 1.8 | translate_helper.py | false | Medium |
| ENABLE_GTTS_EXPONENTIAL_BACKOFF | 1.9 | polly_helper.py | false | Low |
| ENABLE_CHAT_PAGINATION | 1.10 | dynamodb_helper.py | false | Low |
| ENABLE_EXTENDED_AUDIO_EXPIRY | 1.11 | polly_helper.py | false | Low |
| ENABLE_REGEX_DOS_PROTECTION | 1.12 | guardrails.py | false | Low |
| ENABLE_SMART_TRUNCATION | 1.13 | guardrails.py | false | Low |
| ENABLE_CONNECTION_POOLING | 1.14 | All files | false | Low |
| ENABLE_BATCH_CHAT_WRITES | 1.15 | dynamodb_helper.py | false | Medium |
| ENABLE_BACKOFF_JITTER | 1.16 | handler.py | false | Low |
| ENABLE_PROFILE_CACHE | 1.17 | dynamodb_helper.py | false | Low |
| ENABLE_FARMER_ID_VALIDATION | 1.18 | handler.py | false | Low |
| ENABLE_MODEL_VALIDATION | 1.19 | handler.py | false | Low |
| ENABLE_LANGUAGE_VALIDATION_LOGGING | 1.20 | translate_helper.py | false | Low |
| ENABLE_TOOL_INVOCATION_TIMEOUT | 1.21 | handler.py | false | Low |
| ENABLE_VOICE_VALIDATION | 1.22 | polly_helper.py | false | Low |
| ENABLE_S3_VALIDATION | 1.23 | polly_helper.py | false | Low |
| ENABLE_CHAT_IDEMPOTENCY | 1.24 | dynamodb_helper.py | false | Medium |
| ENABLE_TTS_LIST_FORMATTING | 1.25 | polly_helper.py | false | Low |
| ENABLE_HTTPS_WEATHER_API | 1.26 | weather_lookup/handler.py | false | Low |
| ENABLE_TOOL_METRICS | 1.27 | handler.py | false | Low |
| ENABLE_UNIFIED_CORS | 1.28 | All handlers | false | Low |

---

## Appendix: Code Change Summary

### Files Modified

1. `backend/lambdas/agent_orchestrator/handler.py` - 15 bugs
2. `backend/utils/rate_limiter.py` - 1 bug (TTL)
3. `backend/utils/translate_helper.py` - 2 bugs
4. `backend/utils/polly_helper.py` - 4 bugs
5. `backend/utils/dynamodb_helper.py` - 4 bugs
6. `backend/utils/guardrails.py` - 2 bugs
7. `backend/lambdas/crop_advisory/handler.py` - 1 bug
8. `backend/lambdas/weather_lookup/handler.py` - 2 bugs
9. `infrastructure/template.yaml` - 28 environment variables + 1 TTL config
10. `backend/utils/cors_helper.py` - NEW FILE (bug 1.28)

### Lines of Code Added

- New code: ~1,500 lines
- Modified code: ~500 lines
- Total impact: ~2,000 lines across 10 files

### Deployment Impact

- CloudFormation stack update required
- No database migrations required (except TTL enable)
- No API contract changes
- No breaking changes
- Backward compatible

---

## Conclusion

This design document provides comprehensive technical specifications for fixing 28 production bugs using a conservative feature flag approach. All fixes are independently deployable, testable, and rollback-able. The gradual rollout strategy minimizes risk while maximizing system stability and reliability.

The bug condition methodology ensures each fix is precisely targeted to the fault condition while preserving all existing behavior when flags are OFF. This approach enables safe production deployment with zero downtime and zero breaking changes.
