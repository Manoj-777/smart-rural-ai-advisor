# Implementation Tasks: Production Stability Fixes

## Overview

This task list implements fixes for 28 production bugs across 4 severity levels using a conservative feature flag approach. All fixes default to OFF to ensure zero breaking changes.

**Workflow**: Exploration → Preservation → Implementation → Validation

**Key Principles**:
- Write exploration tests BEFORE implementing fixes (tests will FAIL on unfixed code)
- Write preservation tests to verify no behavior change with flags OFF
- Implement fixes behind feature flags (default: false)
- Validate fixes with flags ON
- Each fix is independently testable and rollback-able

---

## PHASE 1: CRITICAL SEVERITY BUGS (1.1-1.5)

### Bug 1.1: API Gateway Timeout Protection

- [x] 1.1.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - API Gateway Timeout Detection
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the timeout bug exists
  - **Scoped PBT Approach**: Test requests that take 30+ seconds to process
  - Test that requests exceeding 29 seconds return Gateway Timeout (from Fault Condition in design)
  - The test assertions should match the Expected Behavior: graceful timeout response before 29s
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found (e.g., "Complex query with 3 tools takes 35s, returns Gateway Timeout")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 2.1_

- [x] 1.1.2 Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Normal Request Processing
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for requests completing within 24 seconds
  - Write property-based tests: for all requests completing within 24s, response is returned normally
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.18_


- [x] 1.1.3 Implement timeout protection fix
  - [x] 1.1.3.1 Add ENABLE_TIMEOUT_PROTECTION flag to handler.py
    - Add at module level after imports: `ENABLE_TIMEOUT_PROTECTION = os.environ.get('ENABLE_TIMEOUT_PROTECTION', 'false').lower() == 'true'`
    - Add TIMEOUT_BUFFER_MS configuration (default: 5000ms)
    - _Bug_Condition: isBugCondition(request) where time_spent_ms > 24000_
    - _Expected_Behavior: Return graceful timeout response before 29s API Gateway limit_
    - _Preservation: All requests completing within 24s process normally (Requirements 3.1, 3.2, 3.3)_
    - _Requirements: 2.1_
  
  - [x] 1.1.3.2 Implement _check_timeout_approaching() helper function
    - Check context.get_remaining_time_in_millis()
    - Return (is_approaching: bool, remaining_ms: int)
    - Compare remaining time against buffer threshold
    - _Requirements: 2.1_
  
  - [x] 1.1.3.3 Implement _timeout_fallback_response() helper function
    - Generate graceful timeout message for farmers
    - Return user-friendly message explaining the delay
    - _Requirements: 2.1_
  
  - [x] 1.1.3.4 Add timeout check in lambda_handler()
    - Check timeout before expensive operations
    - Return fallback response if approaching timeout
    - Include timeout_fallback: true flag in response
    - _Requirements: 2.1_
  
  - [x] 1.1.3.5 Add timeout check in _invoke_bedrock_direct()
    - Check timeout before each Bedrock turn (max 5 turns)
    - Return fallback response if approaching timeout
    - Pass lambda_context parameter through call chain
    - _Requirements: 2.1_
  
  - [x] 1.1.3.6 Write unit tests (flag OFF - verify no change)
    - Mock context.get_remaining_time_in_millis() to return 30000ms (safe)
    - Verify no early returns
    - Verify response structure unchanged
    - _Requirements: 3.1_
  
  - [x] 1.1.3.7 Write unit tests (flag ON - verify timeout protection)
    - Mock context.get_remaining_time_in_millis() to return 4000ms (approaching)
    - Verify _check_timeout_approaching() returns True
    - Verify _timeout_fallback_response() is called
    - Verify response includes timeout_fallback: true
    - _Requirements: 2.1_
  
  - [x] 1.1.3.8 Update CloudFormation template
    - Add ENABLE_TIMEOUT_PROTECTION: 'false' to AgentOrchestratorFunction environment
    - Add TIMEOUT_BUFFER_MS: '5000' to AgentOrchestratorFunction environment
    - _Requirements: 2.1_


  - [x] 1.1.3.9 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Graceful Timeout Response
    - **IMPORTANT**: Re-run the SAME test from task 1.1.1 - do NOT write a new test
    - The test from task 1.1.1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1.1.1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1_
  
  - [x] 1.1.3.10 Verify preservation tests still pass
    - **Property 2: Preservation** - Normal Request Processing
    - **IMPORTANT**: Re-run the SAME tests from task 1.1.2 - do NOT write new tests
    - Run preservation property tests from step 1.1.2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3_

- [ ] 1.1.4 Deploy and validate Bug 1.1 fix
  - [ ] 1.1.4.1 Deploy to dev with flag OFF
    - Deploy CloudFormation stack update
    - Verify ENABLE_TIMEOUT_PROTECTION='false' in environment
    - _Requirements: 3.1_
  
  - [ ] 1.1.4.2 Run regression tests in dev (flag OFF)
    - Run full test suite with flag OFF
    - Verify no behavior changes
    - Verify no performance degradation
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 1.1.4.3 Enable flag in dev, test timeout scenarios
    - Set ENABLE_TIMEOUT_PROTECTION='true'
    - Deploy stack update
    - Send complex queries requiring 30+ seconds
    - Verify graceful timeout response before 29s
    - Verify response includes timeout_fallback: true
    - _Requirements: 2.1_
  
  - [ ] 1.1.4.4 Deploy to staging with flag OFF
    - Deploy CloudFormation stack to staging
    - Verify flag OFF in environment
    - _Requirements: 3.1_
  
  - [ ] 1.1.4.5 Enable flag in staging, run load tests
    - Set ENABLE_TIMEOUT_PROTECTION='true'
    - Run load tests with 100 concurrent requests
    - Measure timeout rate before/after
    - Verify no increase in Lambda errors
    - _Requirements: 2.1_
  
  - [ ] 1.1.4.6 Deploy to production with flag OFF
    - Deploy CloudFormation stack to production
    - Verify flag OFF in environment
    - Monitor for 48 hours
    - _Requirements: 3.1_
  
  - [ ] 1.1.4.7 Enable flag in production
    - Set ENABLE_TIMEOUT_PROTECTION='true'
    - Deploy stack update
    - Monitor CloudWatch logs for "Timeout approaching" messages
    - Monitor error rates and latency
    - _Requirements: 2.1_
  
  - [ ] 1.1.4.8 Monitor for 72 hours
    - Track Gateway Timeout error rate (should decrease)
    - Track timeout_fallback responses
    - Verify no increase in other errors
    - Document results
    - _Requirements: 2.1_


### Bug 1.2: Tool Execution Timeout Protection

- [x] 1.2.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Tool Execution Hang Detection
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **GOAL**: Surface counterexamples that demonstrate tool hang bug exists
  - **Scoped PBT Approach**: Mock tool Lambda to sleep 60 seconds
  - Test that parallel tool execution with one hanging tool blocks entire request
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (request hangs until 120s Lambda timeout)
  - Document counterexamples found
  - _Requirements: 1.2, 2.2_

- [ ] 1.2.2 Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Normal Tool Execution
  - Observe behavior on UNFIXED code for tools completing within 25 seconds
  - Write property-based tests: for all tool executions completing within 25s, results are returned
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior)
  - _Requirements: 3.1, 3.3, 3.17_

- [ ] 1.2.3 Implement tool timeout protection fix
  - [ ] 1.2.3.1 Add ENABLE_TOOL_TIMEOUT flag to handler.py
    - Add at module level: `ENABLE_TOOL_TIMEOUT = os.environ.get('ENABLE_TOOL_TIMEOUT', 'false').lower() == 'true'`
    - Add TOOL_EXECUTION_TIMEOUT_SEC configuration (default: 25)
    - _Bug_Condition: isBugCondition(tool) where tool.running_time > 25s_
    - _Expected_Behavior: Cancel timed-out tools, return results from completed tools_
    - _Preservation: All tools completing within 25s return same results (Requirements 3.1, 3.3, 3.17)_
    - _Requirements: 2.2_
  
  - [ ] 1.2.3.2 Modify parallel tool execution in _invoke_bedrock_direct()
    - Replace as_completed() with wait() using timeout parameter
    - Process completed tools (done set)
    - Handle timed-out tools (not_done set)
    - Return timeout error for timed-out tools
    - Cancel futures for timed-out tools
    - Keep existing code path when flag OFF
    - _Requirements: 2.2_
  
  - [ ] 1.2.3.3 Write unit tests (flag OFF - verify no change)
    - Mock tools with various execution times
    - Verify all tools complete (no timeout)
    - Verify response structure unchanged
    - _Requirements: 3.1_
  
  - [ ] 1.2.3.4 Write unit tests (flag ON - verify timeout protection)
    - Mock tool to sleep 30 seconds
    - Verify timeout triggers after 25 seconds
    - Verify timeout result includes "timeout": true
    - Verify other tools complete successfully
    - _Requirements: 2.2_
  
  - [ ] 1.2.3.5 Update CloudFormation template
    - Add ENABLE_TOOL_TIMEOUT: 'false' to AgentOrchestratorFunction
    - Add TOOL_EXECUTION_TIMEOUT_SEC: '25' to AgentOrchestratorFunction
    - _Requirements: 2.2_


  - [ ] 1.2.3.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Tool Timeout Handling
    - Re-run the SAME test from task 1.2.1
    - **EXPECTED OUTCOME**: Test PASSES (confirms timeout protection works)
    - _Requirements: 2.2_
  
  - [ ] 1.2.3.7 Verify preservation tests still pass
    - **Property 2: Preservation** - Normal Tool Execution
    - Re-run the SAME tests from task 1.2.2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - _Requirements: 3.1, 3.3, 3.17_

- [ ] 1.2.4 Deploy and validate Bug 1.2 fix
  - [ ] 1.2.4.1 Deploy to dev with flag OFF
  - [ ] 1.2.4.2 Run regression tests in dev (flag OFF)
  - [ ] 1.2.4.3 Enable flag in dev, test timeout scenarios
    - Deploy test Lambda that sleeps 60 seconds
    - Invoke orchestrator with 2 tools (1 normal, 1 slow)
    - Verify fast tool completes, slow tool times out
    - Verify response includes both results
  - [ ] 1.2.4.4 Deploy to staging with flag OFF
  - [ ] 1.2.4.5 Enable flag in staging, run chaos tests
    - Randomly inject 30-second delays in tool Lambdas
    - Verify system remains responsive
    - Verify no cascading failures
  - [ ] 1.2.4.6 Deploy to production with flag OFF, monitor 48 hours
  - [ ] 1.2.4.7 Enable flag in production, monitor 72 hours

### Bug 1.3: DynamoDB Rate Limits Table TTL

- [ ] 1.3.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Rate Limit Record Persistence
  - **CRITICAL**: This test MUST FAIL on unfixed code
  - **GOAL**: Demonstrate that rate limit records persist indefinitely
  - Query rate_limits table for records older than expected lifetime
  - Verify records exist that should have been deleted
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (old records still exist)
  - Document table size growth over 24 hours
  - _Requirements: 1.3, 2.3_

- [ ] 1.3.2 Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Rate Limiting Functionality
  - Observe rate limiting behavior on UNFIXED code
  - Write property-based tests: rate limits enforced correctly (15 RPM, 120 RPH, 500 daily)
  - Verify fail-open behavior on errors
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior)
  - _Requirements: 3.1, 3.4_

- [ ] 1.3.3 Implement DynamoDB TTL configuration
  - [ ] 1.3.3.1 Add EnableRateLimitTTL parameter to CloudFormation
    - Add parameter with Type: String, Default: 'false'
    - AllowedValues: ['true', 'false']
    - Description: Enable DynamoDB TTL for rate_limits table
    - _Bug_Condition: isBugCondition(record) where record.ttl_epoch exists AND TTL_enabled = false_
    - _Expected_Behavior: Records automatically deleted after ttl_epoch expiration_
    - _Preservation: Rate limiting logic unchanged (Requirements 3.1, 3.4)_
    - _Requirements: 2.3_
  
  - [ ] 1.3.3.2 Add TimeToLiveSpecification to RateLimitsTable
    - Add to RateLimitsTable resource in template.yaml
    - Set Enabled: !Ref EnableRateLimitTTL
    - Set AttributeName: ttl_epoch
    - _Requirements: 2.3_
  
  - [ ] 1.3.3.3 Write integration tests (flag OFF)
    - Verify TTL is disabled
    - Verify records persist indefinitely
    - _Requirements: 3.1_
  
  - [ ] 1.3.3.4 Write integration tests (flag ON)
    - Verify TTL is enabled: aws dynamodb describe-time-to-live
    - Write test record with ttl_epoch = current_time + 60 seconds
    - Wait 90 seconds, verify record is deleted
    - _Requirements: 2.3_


  - [ ] 1.3.3.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Automatic Record Deletion
    - Re-run the SAME test from task 1.3.1
    - **EXPECTED OUTCOME**: Test PASSES (old records are deleted)
    - _Requirements: 2.3_
  
  - [ ] 1.3.3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Rate Limiting Functionality
    - Re-run the SAME tests from task 1.3.2
    - **EXPECTED OUTCOME**: Tests PASS (rate limiting unchanged)
    - _Requirements: 3.1, 3.4_

- [ ] 1.3.4 Deploy and validate Bug 1.3 fix
  - [ ] 1.3.4.1 Document current table state
    - Query rate_limits table for record count
    - Document current table size and item count
    - Verify ttl_epoch attribute exists in records
  - [ ] 1.3.4.2 Deploy to dev with EnableRateLimitTTL='false'
  - [ ] 1.3.4.3 Run regression tests in dev (flag OFF)
  - [ ] 1.3.4.4 Enable TTL in dev (EnableRateLimitTTL='true')
    - Deploy stack update
    - Verify TTL enabled: aws dynamodb describe-time-to-live --table-name rate_limits
    - Monitor table size over 24 hours
  - [ ] 1.3.4.5 Deploy to staging with flag OFF
  - [ ] 1.3.4.6 Enable TTL in staging, monitor table size
  - [ ] 1.3.4.7 Deploy to production with flag OFF, monitor 48 hours
  - [ ] 1.3.4.8 Enable TTL in production, monitor table size for 7 days

### Bug 1.4: Bedrock Model Fallback

- [ ] 1.4.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Fallback Without Flag Control
  - **CRITICAL**: This test MUST FAIL on unfixed code
  - **GOAL**: Demonstrate that model fallback always executes with no flag control
  - Mock Bedrock client to raise ThrottlingException for Nova Pro
  - Verify fallback to Nova 2 Lite is attempted (current behavior)
  - Verify no flag check is performed before fallback
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (fallback executes without flag check)
  - _Requirements: 1.4, 2.4_

- [ ] 1.4.2 Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Normal Bedrock Calls
  - Observe behavior on UNFIXED code for successful Bedrock calls
  - Write property-based tests: successful calls return expected response structure
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior)
  - _Requirements: 3.1, 3.18_

- [ ] 1.4.3 Implement model fallback control fix
  - [ ] 1.4.3.1 Add ENABLE_MODEL_FALLBACK flag to handler.py
    - Add at module level: `ENABLE_MODEL_FALLBACK = os.environ.get('ENABLE_MODEL_FALLBACK', 'false').lower() == 'true'`
    - _Bug_Condition: isBugCondition(response) where error = ThrottlingException AND fallback_executed_without_flag_check_
    - _Expected_Behavior: Only attempt bidirectional fallback (Nova Pro ↔ Nova 2 Lite) when flag is enabled_
    - _Preservation: Successful calls use same model (Requirements 3.1, 3.18)_
    - _Requirements: 2.4_
  
  - [ ] 1.4.3.2 Modify _bedrock_converse_with_retry() function
    - Wrap existing MODEL_FALLBACK logic in `if ENABLE_MODEL_FALLBACK:` check
    - Add else clause to log when fallback is disabled
    - When flag OFF: raise original error immediately (no fallback)
    - When flag ON: use existing bidirectional fallback logic
    - _Requirements: 2.4_
  
  - [ ] 1.4.3.3 Write unit tests (flag OFF - verify no fallback)
    - Mock throttling errors for Nova Pro
    - Verify NO fallback attempted
    - Verify original error raised
    - Verify log: "Model fallback DISABLED"
    - _Requirements: 3.1_
  
  - [ ] 1.4.3.4 Write unit tests (flag ON - verify bidirectional fallback)
    - Mock Nova Pro to throttle, Nova 2 Lite to succeed
    - Verify fallback to Nova 2 Lite is attempted
    - Verify response returned from Nova 2 Lite
    - Mock Nova 2 Lite to throttle, Nova Pro to succeed
    - Verify reverse fallback works (Lite → Pro)
    - _Requirements: 2.4_
  
  - [ ] 1.4.3.5 Update CloudFormation template
    - Add ENABLE_MODEL_FALLBACK: 'false' to AgentOrchestratorFunction
    - Verify FOUNDATION_MODEL: 'apac.amazon.nova-pro-v1:0' exists
    - Verify FOUNDATION_MODEL_LITE: 'global.amazon.nova-2-lite-v1:0' exists
    - _Requirements: 2.4_


  - [ ] 1.4.3.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Controlled Model Fallback
    - Re-run the SAME test from task 1.4.1
    - **EXPECTED OUTCOME**: Test PASSES (fallback only executes when flag is ON)
    - _Requirements: 2.4_
  
  - [ ] 1.4.3.7 Verify preservation tests still pass
    - **Property 2: Preservation** - Normal Bedrock Calls
    - Re-run the SAME tests from task 1.4.2
    - **EXPECTED OUTCOME**: Tests PASS (no regressions)
    - _Requirements: 3.1, 3.18_

- [ ] 1.4.4 Deploy and validate Bug 1.4 fix
  - [ ] 1.4.4.1 Deploy to dev with flag OFF
  - [ ] 1.4.4.2 Run regression tests in dev (flag OFF)
  - [ ] 1.4.4.3 Enable flag in dev, test bidirectional fallback
    - Mock Nova Pro throttling, verify fallback to Nova 2 Lite
    - Mock Nova 2 Lite throttling, verify fallback to Nova Pro
    - Verify response quality is acceptable from both models
  - [ ] 1.4.4.4 Deploy to staging with flag OFF
  - [ ] 1.4.4.5 Enable flag in staging, run load tests
    - Generate high load to trigger throttling
    - Verify fallback reduces error rate
    - Measure latency impact of fallback
  - [ ] 1.4.4.6 Deploy to production with flag OFF, monitor 48 hours
  - [ ] 1.4.4.7 Enable flag in production, monitor 72 hours

### Bug 1.5: Thread-Safe Tool Execution

- [ ] 1.5.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Race Condition Detection
  - **CRITICAL**: This test MUST FAIL on unfixed code
  - **GOAL**: Demonstrate race conditions in parallel tool execution
  - Run 100 requests with 5 parallel tools each
  - Verify tools_used list has exactly 5 entries per request
  - Verify tool_data_log list has exactly 5 entries per request
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (missing or duplicate entries)
  - Document race condition occurrences
  - _Requirements: 1.5, 2.5_

- [ ] 1.5.2 Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Single Tool Execution
  - Observe behavior on UNFIXED code for single tool execution
  - Write property-based tests: single tool execution returns correct results
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (single tool has no race condition)
  - _Requirements: 3.1, 3.3, 3.17_

- [ ] 1.5.3 Implement thread-safe tool execution fix
  - [ ] 1.5.3.1 Add ENABLE_THREAD_SAFE_TOOLS flag to handler.py
    - Add imports: threading, Queue
    - Add at module level: `ENABLE_THREAD_SAFE_TOOLS = os.environ.get('ENABLE_THREAD_SAFE_TOOLS', 'false').lower() == 'true'`
    - _Bug_Condition: isBugCondition(execution) where worker_count >= 2 AND shared_state_accessed_
    - _Expected_Behavior: Use thread-safe Queue for tools_used and tool_data_log_
    - _Preservation: Single tool execution unchanged (Requirements 3.1, 3.3, 3.17)_
    - _Requirements: 2.5_
  
  - [ ] 1.5.3.2 Modify _invoke_bedrock_direct() function
    - Replace shared lists with Queue when flag ON
    - Create execute_tool_safe() wrapper function
    - Use Queue.put() instead of list.append()
    - Collect results from queues after parallel execution
    - Keep existing code path when flag OFF
    - _Requirements: 2.5_
  
  - [ ] 1.5.3.3 Write unit tests (flag OFF - verify no change)
    - Mock 10 tools executing in parallel
    - Verify existing behavior unchanged
    - _Requirements: 3.1_
  
  - [ ] 1.5.3.4 Write unit tests (flag ON - verify thread safety)
    - Mock 10 tools executing in parallel
    - Verify tools_used has exactly 10 entries
    - Verify tool_data_log has exactly 10 entries
    - Verify no duplicate or missing entries
    - _Requirements: 2.5_
  
  - [ ] 1.5.3.5 Update CloudFormation template
    - Add ENABLE_THREAD_SAFE_TOOLS: 'false' to AgentOrchestratorFunction
    - _Requirements: 2.5_


  - [ ] 1.5.3.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Thread-Safe Execution
    - Re-run the SAME test from task 1.5.1
    - **EXPECTED OUTCOME**: Test PASSES (no race conditions)
    - _Requirements: 2.5_
  
  - [ ] 1.5.3.7 Verify preservation tests still pass
    - **Property 2: Preservation** - Single Tool Execution
    - Re-run the SAME tests from task 1.5.2
    - **EXPECTED OUTCOME**: Tests PASS (no regressions)
    - _Requirements: 3.1, 3.3, 3.17_

- [ ] 1.5.4 Deploy and validate Bug 1.5 fix
  - [ ] 1.5.4.1 Deploy to dev with flag OFF
  - [ ] 1.5.4.2 Run regression tests in dev (flag OFF)
  - [ ] 1.5.4.3 Enable flag in dev, test thread safety
    - Run 100 requests with 5 parallel tools each
    - Verify tool attribution is correct in all responses
    - Compare results with flag ON vs OFF
  - [ ] 1.5.4.4 Deploy to staging with flag OFF
  - [ ] 1.5.4.5 Enable flag in staging, run concurrency tests
    - Inject random delays in tool execution
    - Verify results are consistent across runs
  - [ ] 1.5.4.6 Deploy to production with flag OFF, monitor 48 hours
  - [ ] 1.5.4.7 Enable flag in production, monitor 72 hours

- [ ] 1.6 Phase 1 Checkpoint - Ensure all CRITICAL bug tests pass
  - Verify all exploration tests pass with flags ON
  - Verify all preservation tests pass with flags OFF
  - Verify all 5 critical fixes deployed to production
  - Document any issues or rollbacks
  - Ask user if questions arise

---

## PHASE 2: HIGH SEVERITY BUGS (1.6-1.13)

### Bug 1.6: Knowledge Base Retrieve Retry

- [ ] 1.6.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - KB Throttling Without Retry
  - **CRITICAL**: This test MUST FAIL on unfixed code
  - **GOAL**: Demonstrate KB throttling causes immediate failure
  - Mock bedrock_kb.retrieve() to raise ThrottlingException
  - Verify no retry is attempted
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (exception raised immediately)
  - _Requirements: 1.6, 2.6_

- [ ] 1.6.2 Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Successful KB Retrieval
  - Observe behavior on UNFIXED code for successful KB calls
  - Write property-based tests: successful KB calls return expected structure
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior)
  - _Requirements: 3.1, 3.13_

- [ ] 1.6.3 Implement KB retry fix
  - [ ] 1.6.3.1 Add ENABLE_KB_RETRY flag to crop_advisory/handler.py
    - Add import: time
    - Add flags: ENABLE_KB_RETRY, KB_RETRY_MAX_ATTEMPTS (default: 3), KB_RETRY_BASE_DELAY (default: 1.0)
    - _Bug_Condition: isBugCondition(call) where error = ThrottlingException AND retry_count = 0_
    - _Expected_Behavior: Retry up to 3 times with exponential backoff_
    - _Preservation: Successful calls unchanged (Requirements 3.1, 3.13)_
    - _Requirements: 2.6_
  
  - [ ] 1.6.3.2 Implement _kb_retrieve_with_retry() helper function
    - Implement exponential backoff (1s, 2s, 4s)
    - Handle ThrottlingException specifically
    - Log retry attempts
    - Return existing behavior when flag OFF
    - _Requirements: 2.6_
  
  - [ ] 1.6.3.3 Replace direct KB call in lambda_handler()
    - Replace bedrock_kb.retrieve() with _kb_retrieve_with_retry()
    - Pass all parameters through
    - _Requirements: 2.6_
  
  - [ ] 1.6.3.4 Write unit tests (flag OFF - verify no change)
  - [ ] 1.6.3.5 Write unit tests (flag ON - verify retry)
  - [ ] 1.6.3.6 Update CloudFormation template
    - Add ENABLE_KB_RETRY: 'false' to CropAdvisoryFunction
    - Add KB_RETRY_MAX_ATTEMPTS: '3'
    - Add KB_RETRY_BASE_DELAY: '1.0'
  - [ ] 1.6.3.7 Verify bug condition exploration test now passes
  - [ ] 1.6.3.8 Verify preservation tests still pass

- [ ] 1.6.4 Deploy and validate Bug 1.6 fix
  - [ ] 1.6.4.1 Deploy to dev with flag OFF
  - [ ] 1.6.4.2 Enable flag in dev, test retry behavior
  - [ ] 1.6.4.3 Deploy to staging, run load tests
  - [ ] 1.6.4.4 Deploy to production with flag OFF, monitor 48 hours
  - [ ] 1.6.4.5 Enable flag in production, monitor 72 hours


### Bug 1.7: Coordinate Validation

- [ ] 1.7.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Invalid Coordinates
  - Test with lat=100, lon=200 (invalid ranges)
  - **EXPECTED OUTCOME**: Test FAILS (cryptic OpenWeather error)
  - _Requirements: 1.7, 2.7_

- [ ] 1.7.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Valid Coordinates
  - Test with valid coordinates (-90 to 90, -180 to 180)
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.12_

- [ ] 1.7.3 Implement coordinate validation fix
  - [ ] 1.7.3.1 Add ENABLE_COORDINATE_VALIDATION flag to weather_lookup/handler.py
  - [ ] 1.7.3.2 Implement _validate_coordinates() function
  - [ ] 1.7.3.3 Add validation in lambda_handler() after extracting lat/lon
  - [ ] 1.7.3.4 Write unit tests (flag OFF and ON)
  - [ ] 1.7.3.5 Update CloudFormation template
  - [ ] 1.7.3.6 Verify exploration test passes
  - [ ] 1.7.3.7 Verify preservation tests pass

- [ ] 1.7.4 Deploy and validate Bug 1.7 fix

### Bug 1.8: Translation Length Limit

- [ ] 1.8.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Text Exceeds Translate Limit
  - Test with text > 10,000 bytes
  - **EXPECTED OUTCOME**: Test FAILS (silent failure, untranslated text)
  - _Requirements: 1.8, 2.8_

- [ ] 1.8.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Normal Length Text
  - Test with text < 10,000 bytes
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.11_

- [ ] 1.8.3 Implement translation chunking fix
  - [ ] 1.8.3.1 Add ENABLE_TRANSLATION_CHUNKING flag to translate_helper.py
  - [ ] 1.8.3.2 Implement length check and chunking logic
  - [ ] 1.8.3.3 Write unit tests (flag OFF and ON)
  - [ ] 1.8.3.4 Update CloudFormation template
  - [ ] 1.8.3.5 Verify exploration test passes
  - [ ] 1.8.3.6 Verify preservation tests pass

- [ ] 1.8.4 Deploy and validate Bug 1.8 fix

### Bug 1.9: gTTS Exponential Backoff

- [ ] 1.9.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - gTTS Network Failure
  - Mock network errors, verify fixed backoff insufficient
  - **EXPECTED OUTCOME**: Test FAILS (unnecessary failures)
  - _Requirements: 1.9, 2.9_

- [ ] 1.9.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Successful gTTS Calls
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.10_

- [ ] 1.9.3 Implement exponential backoff fix
  - [ ] 1.9.3.1 Add ENABLE_GTTS_EXPONENTIAL_BACKOFF flag to polly_helper.py
  - [ ] 1.9.3.2 Replace fixed 0.6s delay with exponential: base * (2 ** attempt)
  - [ ] 1.9.3.3 Add jitter: delay * (1 + random.uniform(-0.25, 0.25))
  - [ ] 1.9.3.4 Write unit tests (flag OFF and ON)
  - [ ] 1.9.3.5 Update CloudFormation template
  - [ ] 1.9.3.6 Verify exploration test passes
  - [ ] 1.9.3.7 Verify preservation tests pass

- [ ] 1.9.4 Deploy and validate Bug 1.9 fix

### Bug 1.10: Chat History Pagination

- [ ] 1.10.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Session With >40 Messages
  - Create session with 50 messages, query with Limit=40
  - Verify LastEvaluatedKey is ignored
  - **EXPECTED OUTCOME**: Test FAILS (only 40 messages returned)
  - _Requirements: 1.10, 2.10_

- [ ] 1.10.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Session With <40 Messages
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.5_

- [ ] 1.10.3 Implement pagination fix
  - [ ] 1.10.3.1 Add ENABLE_CHAT_PAGINATION flag to dynamodb_helper.py
  - [ ] 1.10.3.2 Check for LastEvaluatedKey in response
  - [ ] 1.10.3.3 Loop until all messages retrieved or limit reached
  - [ ] 1.10.3.4 Write unit tests (flag OFF and ON)
  - [ ] 1.10.3.5 Update CloudFormation template
  - [ ] 1.10.3.6 Verify exploration test passes
  - [ ] 1.10.3.7 Verify preservation tests pass

- [ ] 1.10.4 Deploy and validate Bug 1.10 fix


### Bug 1.11: Audio URL Expiry Extension

- [ ] 1.11.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Slow Network Playback
  - Simulate slow network, verify 3600s expiry insufficient
  - **EXPECTED OUTCOME**: Test FAILS (access denied mid-playback)
  - _Requirements: 1.11, 2.11_

- [ ] 1.11.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Normal Network Playback
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.10_

- [ ] 1.11.3 Implement extended expiry fix
  - [ ] 1.11.3.1 Add ENABLE_EXTENDED_AUDIO_EXPIRY flag to polly_helper.py
  - [ ] 1.11.3.2 Change presigned URL expiry from 3600s to 7200s
  - [ ] 1.11.3.3 Return both URL and S3 key for refresh capability
  - [ ] 1.11.3.4 Write unit tests (flag OFF and ON)
  - [ ] 1.11.3.5 Update CloudFormation template
  - [ ] 1.11.3.6 Verify exploration test passes
  - [ ] 1.11.3.7 Verify preservation tests pass

- [ ] 1.11.4 Deploy and validate Bug 1.11 fix

### Bug 1.12: Regex DoS Protection

- [ ] 1.12.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Long Input With Complex Patterns
  - Test with 5000 character input with nested patterns
  - **EXPECTED OUTCOME**: Test FAILS (Lambda timeout)
  - _Requirements: 1.12, 2.12_

- [ ] 1.12.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Normal Length Input
  - Test with input < 2000 characters
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.7_

- [ ] 1.12.3 Implement ReDoS protection fix
  - [ ] 1.12.3.1 Add ENABLE_REGEX_DOS_PROTECTION flag to guardrails.py
  - [ ] 1.12.3.2 Limit input length to 2000 chars before regex matching
  - [ ] 1.12.3.3 Use atomic groups in patterns: (?>...) instead of (...)
  - [ ] 1.12.3.4 Write unit tests (flag OFF and ON)
  - [ ] 1.12.3.5 Update CloudFormation template
  - [ ] 1.12.3.6 Verify exploration test passes
  - [ ] 1.12.3.7 Verify preservation tests pass

- [ ] 1.12.4 Deploy and validate Bug 1.12 fix

### Bug 1.13: Smart Truncation

- [ ] 1.13.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Long Response With Mid-Paragraph Cut
  - Test with 8500 char response, last 200 chars mid-paragraph
  - **EXPECTED OUTCOME**: Test FAILS (important info cut off)
  - _Requirements: 1.13, 2.13_

- [ ] 1.13.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Responses <8000 Characters
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.16_

- [ ] 1.13.3 Implement smart truncation fix
  - [ ] 1.13.3.1 Add ENABLE_SMART_TRUNCATION flag to guardrails.py
  - [ ] 1.13.3.2 Search last 500 chars (instead of 200) for sentence boundary
  - [ ] 1.13.3.3 Write unit tests (flag OFF and ON)
  - [ ] 1.13.3.4 Update CloudFormation template
  - [ ] 1.13.3.5 Verify exploration test passes
  - [ ] 1.13.3.6 Verify preservation tests pass

- [ ] 1.13.4 Deploy and validate Bug 1.13 fix

- [ ] 1.14 Phase 2 Checkpoint - Ensure all HIGH bug tests pass
  - Verify all exploration tests pass with flags ON
  - Verify all preservation tests pass with flags OFF
  - Verify all 8 high severity fixes deployed to production
  - Document any issues or rollbacks
  - Ask user if questions arise

---

## PHASE 3: MEDIUM SEVERITY BUGS (1.14-1.24)

### Bug 1.14: Connection Pooling

- [ ] 1.14.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - High Load Connection Exhaustion
  - Generate 100 concurrent requests
  - **EXPECTED OUTCOME**: Test FAILS (connection exhaustion)
  - _Requirements: 1.14, 2.14_

- [ ] 1.14.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Normal Load
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1_

- [ ] 1.14.3 Implement connection pooling fix
  - [ ] 1.14.3.1 Add ENABLE_CONNECTION_POOLING flag to all Lambda handlers
  - [ ] 1.14.3.2 Configure boto3 clients with Config(max_pool_connections=25)
  - [ ] 1.14.3.3 Write unit tests (flag OFF and ON)
  - [ ] 1.14.3.4 Update CloudFormation template for all functions
  - [ ] 1.14.3.5 Verify exploration test passes
  - [ ] 1.14.3.6 Verify preservation tests pass

- [ ] 1.14.4 Deploy and validate Bug 1.14 fix


### Bug 1.15: Batch Chat Writes

- [ ] 1.15.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Multiple Messages Saved Individually
  - Save 10 messages, measure DynamoDB PutItem calls
  - **EXPECTED OUTCOME**: Test FAILS (10 individual calls)
  - _Requirements: 1.15, 2.15_

- [ ] 1.15.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Single Message Save
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.15_

- [ ] 1.15.3 Implement batch writes fix
  - [ ] 1.15.3.1 Add ENABLE_BATCH_CHAT_WRITES flag to dynamodb_helper.py
  - [ ] 1.15.3.2 Implement save_chat_messages_batch() function
  - [ ] 1.15.3.3 Use batch_writer() for up to 25 messages
  - [ ] 1.15.3.4 Write unit tests (flag OFF and ON)
  - [ ] 1.15.3.5 Update CloudFormation template
  - [ ] 1.15.3.6 Verify exploration test passes
  - [ ] 1.15.3.7 Verify preservation tests pass

- [ ] 1.15.4 Deploy and validate Bug 1.15 fix

### Bug 1.16: Backoff Jitter

- [ ] 1.16.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Simultaneous Retries (Thundering Herd)
  - Trigger 10 Lambdas to retry simultaneously
  - **EXPECTED OUTCOME**: Test FAILS (all retry at same time)
  - _Requirements: 1.16, 2.16_

- [ ] 1.16.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Successful Calls
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.18_

- [ ] 1.16.3 Implement jitter fix
  - [ ] 1.16.3.1 Add ENABLE_BACKOFF_JITTER flag to handler.py
  - [ ] 1.16.3.2 Add random jitter (±25%) to backoff delay
  - [ ] 1.16.3.3 Write unit tests (flag OFF and ON)
  - [ ] 1.16.3.4 Update CloudFormation template
  - [ ] 1.16.3.5 Verify exploration test passes
  - [ ] 1.16.3.6 Verify preservation tests pass

- [ ] 1.16.4 Deploy and validate Bug 1.16 fix

### Bugs 1.17-1.24: Condensed Implementation

- [ ] 1.17 Profile Cache
  - [ ] 1.17.1 Exploration test (cache misses on repeated calls)
  - [ ] 1.17.2 Preservation test (single call behavior)
  - [ ] 1.17.3 Implement: Add module-level dict cache with TTL
  - [ ] 1.17.4 Deploy and validate

- [ ] 1.18 Farmer ID Validation
  - [ ] 1.18.1 Exploration test (invalid farmer_id accepted)
  - [ ] 1.18.2 Preservation test (valid farmer_id)
  - [ ] 1.18.3 Implement: Regex ^[a-zA-Z0-9\-_]{1,64}$
  - [ ] 1.18.4 Deploy and validate

- [ ] 1.19 Model Validation
  - [ ] 1.19.1 Exploration test (invalid model_id accepted)
  - [ ] 1.19.2 Preservation test (valid model_id)
  - [ ] 1.19.3 Implement: Check against allowed list
  - [ ] 1.19.4 Deploy and validate

- [ ] 1.20 Language Validation Logging
  - [ ] 1.20.1 Exploration test (invalid language code silent)
  - [ ] 1.20.2 Preservation test (valid language codes)
  - [ ] 1.20.3 Implement: Log warning for invalid codes
  - [ ] 1.20.4 Deploy and validate

- [ ] 1.21 Tool Invocation Timeout
  - [ ] 1.21.1 Exploration test (no SDK timeout set)
  - [ ] 1.21.2 Preservation test (normal tool calls)
  - [ ] 1.21.3 Implement: Config(read_timeout=30)
  - [ ] 1.21.4 Deploy and validate

- [ ] 1.22 Voice Validation
  - [ ] 1.22.1 Exploration test (invalid voice_id accepted)
  - [ ] 1.22.2 Preservation test (valid voice_id)
  - [ ] 1.22.3 Implement: Check against VOICE_MAP
  - [ ] 1.22.4 Deploy and validate

- [ ] 1.23 S3 Bucket Validation
  - [ ] 1.23.1 Exploration test (misconfigured bucket cryptic error)
  - [ ] 1.23.2 Preservation test (valid bucket)
  - [ ] 1.23.3 Implement: s3.head_bucket() at init
  - [ ] 1.23.4 Deploy and validate

- [ ] 1.24 Chat Idempotency
  - [ ] 1.24.1 Exploration test (duplicate messages saved)
  - [ ] 1.24.2 Preservation test (unique messages)
  - [ ] 1.24.3 Implement: idempotency_token + ConditionExpression
  - [ ] 1.24.4 Deploy and validate

- [ ] 1.25 Phase 3 Checkpoint - Ensure all MEDIUM bug tests pass
  - Verify all exploration tests pass with flags ON
  - Verify all preservation tests pass with flags OFF
  - Verify all 11 medium severity fixes deployed to production
  - Ask user if questions arise

---

## PHASE 4: LOW SEVERITY BUGS (1.25-1.28)

### Bug 1.25: TTS List Formatting

- [ ] 1.25.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Numbered Lists In TTS
  - Test with "1. First item\n2. Second item"
  - **EXPECTED OUTCOME**: Test FAILS (awkward TTS pauses)
  - _Requirements: 1.25, 2.25_

- [ ] 1.25.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Text Without Lists
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.10_

- [ ] 1.25.3 Implement TTS list formatting fix
  - [ ] 1.25.3.1 Add ENABLE_TTS_LIST_FORMATTING flag to polly_helper.py
  - [ ] 1.25.3.2 Replace "1. " with "First, ", "2. " with "Second, ", etc.
  - [ ] 1.25.3.3 Write unit tests (flag OFF and ON)
  - [ ] 1.25.3.4 Update CloudFormation template
  - [ ] 1.25.3.5 Verify exploration test passes
  - [ ] 1.25.3.6 Verify preservation tests pass

- [ ] 1.25.4 Deploy and validate Bug 1.25 fix


### Bug 1.26: HTTPS Weather API

- [ ] 1.26.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Inconsistent HTTP/HTTPS Usage
  - Verify some endpoints use http:// scheme
  - **EXPECTED OUTCOME**: Test FAILS (inconsistent security)
  - _Requirements: 1.26, 2.26_

- [ ] 1.26.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Weather Data Structure
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.12_

- [ ] 1.26.3 Implement HTTPS fix
  - [ ] 1.26.3.1 Add ENABLE_HTTPS_WEATHER_API flag to weather_lookup/handler.py
  - [ ] 1.26.3.2 Use https:// scheme consistently for all endpoints
  - [ ] 1.26.3.3 Write unit tests (flag OFF and ON)
  - [ ] 1.26.3.4 Update CloudFormation template
  - [ ] 1.26.3.5 Verify exploration test passes
  - [ ] 1.26.3.6 Verify preservation tests pass

- [ ] 1.26.4 Deploy and validate Bug 1.26 fix

### Bug 1.27: Tool Execution Metrics

- [ ] 1.27.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - No Tool Metrics Emitted
  - Execute tools, verify no CloudWatch metrics
  - **EXPECTED OUTCOME**: Test FAILS (no metrics found)
  - _Requirements: 1.27, 2.27_

- [ ] 1.27.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - Tool Execution Results
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.3_

- [ ] 1.27.3 Implement tool metrics fix
  - [ ] 1.27.3.1 Add ENABLE_TOOL_METRICS flag to handler.py
  - [ ] 1.27.3.2 Initialize CloudWatch client when flag ON
  - [ ] 1.27.3.3 Implement _emit_tool_metric() function
  - [ ] 1.27.3.4 Emit metrics after each tool execution (duration, success)
  - [ ] 1.27.3.5 Write unit tests (flag OFF and ON)
  - [ ] 1.27.3.6 Update CloudFormation template
  - [ ] 1.27.3.7 Verify exploration test passes
  - [ ] 1.27.3.8 Verify preservation tests pass

- [ ] 1.27.4 Deploy and validate Bug 1.27 fix

### Bug 1.28: Unified CORS Middleware

- [ ] 1.28.1 Write bug condition exploration test (BEFORE fix)
  - **Property 1: Fault Condition** - Inconsistent CORS Headers
  - Query all Lambda endpoints, compare CORS headers
  - **EXPECTED OUTCOME**: Test FAILS (inconsistent headers)
  - _Requirements: 1.28, 2.28_

- [ ] 1.28.2 Write preservation property tests (BEFORE fix)
  - **Property 2: Preservation** - CORS Functionality
  - **EXPECTED OUTCOME**: Tests PASS
  - _Requirements: 3.1, 3.20_

- [ ] 1.28.3 Implement unified CORS fix
  - [ ] 1.28.3.1 Create new backend/utils/cors_helper.py
  - [ ] 1.28.3.2 Add ENABLE_UNIFIED_CORS flag
  - [ ] 1.28.3.3 Implement get_cors_headers() function
  - [ ] 1.28.3.4 Implement handle_cors_preflight() function
  - [ ] 1.28.3.5 Update all Lambda handlers to import and use cors_helper
  - [ ] 1.28.3.6 Write unit tests (flag OFF and ON)
  - [ ] 1.28.3.7 Update CloudFormation template for all functions
  - [ ] 1.28.3.8 Verify exploration test passes
  - [ ] 1.28.3.9 Verify preservation tests pass

- [ ] 1.28.4 Deploy and validate Bug 1.28 fix

- [ ] 1.29 Phase 4 Checkpoint - Ensure all LOW bug tests pass
  - Verify all exploration tests pass with flags ON
  - Verify all preservation tests pass with flags OFF
  - Verify all 4 low severity fixes deployed to production
  - Ask user if questions arise

---

## PHASE 5: INTEGRATION AND FINAL VALIDATION

- [ ] 2.1 Integration Testing
  - [ ] 2.1.1 Deploy all fixes to test environment with all flags OFF
    - Verify zero behavioral changes
    - Run full regression test suite
    - Measure baseline performance metrics
  
  - [ ] 2.1.2 Enable all flags in test environment
    - Enable all 28 feature flags
    - Run full test suite
    - Verify all fixes work together
    - Check for interactions between fixes
  
  - [ ] 2.1.3 Load testing with all flags ON
    - Generate 1000 requests/minute
    - Measure latency (p50, p95, p99)
    - Measure error rates
    - Verify no performance degradation >5%
  
  - [ ] 2.1.4 Chaos testing
    - Inject random failures (network, throttling, timeouts)
    - Verify system remains stable
    - Verify graceful degradation
    - Verify no cascading failures

- [ ] 2.2 Documentation
  - [ ] 2.2.1 Create CloudWatch dashboard
    - Feature flag status widgets
    - Error rates by bug fix
    - Latency percentiles
    - Tool execution metrics
    - DynamoDB table sizes
  
  - [ ] 2.2.2 Create monitoring alarms
    - Error rate increase >5% (rollback trigger)
    - Latency p99 increase >20%
    - DynamoDB throttling
    - Lambda timeout rate >1%
  
  - [ ] 2.2.3 Document rollback procedures
    - Individual fix rollback steps
    - Emergency rollback (all fixes)
    - Rollback time estimates
    - Rollback testing results
  
  - [ ] 2.2.4 Create gradual rollout runbook
    - Week-by-week rollout schedule
    - Monitoring checklist per phase
    - Go/no-go criteria
    - Escalation procedures

- [ ] 2.3 Production Rollout
  - [ ] 2.3.1 Week 1: Deploy with all flags OFF
    - Deploy to production
    - Monitor for 48 hours
    - Verify zero behavioral changes
  
  - [ ] 2.3.2 Week 2: Enable LOW severity fixes (1.25-1.28)
    - Enable 4 LOW severity flags
    - Monitor for 48 hours
    - Rollback if issues detected
  
  - [ ] 2.3.3 Weeks 3-4: Enable MEDIUM severity fixes (1.14-1.24)
    - Enable 1 flag per day
    - Monitor each for 24 hours
    - Document any issues
  
  - [ ] 2.3.4 Weeks 5-6: Enable HIGH severity fixes (1.6-1.13)
    - Enable 1 flag per day
    - Monitor each for 48 hours
    - Document any issues
  
  - [ ] 2.3.5 Weeks 7-8: Enable CRITICAL severity fixes (1.1-1.5)
    - Enable 1 flag every 2 days
    - Monitor each for 72 hours
    - Document any issues
  
  - [ ] 2.3.6 Week 9: Full production validation
    - All 28 flags enabled
    - Monitor for 1 week
    - Verify all success criteria met
    - Declare rollout complete

- [ ] 2.4 Final Checkpoint
  - [ ] 2.4.1 Verify all 28 fixes deployed and enabled
  - [ ] 2.4.2 Verify all tests passing (exploration and preservation)
  - [ ] 2.4.3 Verify performance metrics within acceptable ranges
  - [ ] 2.4.4 Verify cost impact <5%
  - [ ] 2.4.5 Verify zero production incidents during rollout
  - [ ] 2.4.6 Document lessons learned
  - [ ] 2.4.7 Celebrate success! 🎉

---

## Success Criteria

✅ All 28 fixes implemented behind feature flags
✅ All flags default to 'false' (no behavior change)
✅ All regression tests pass with flags OFF
✅ All fix tests pass with flags ON
✅ Rollback procedure validated for each fix
✅ CloudWatch dashboards created
✅ Runbook created for gradual rollout
✅ Zero production incidents during rollout
✅ Performance metrics within acceptable ranges
✅ Cost impact <5% increase

