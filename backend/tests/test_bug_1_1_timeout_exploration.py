"""
Bug 1.1 Exploration Test: API Gateway Timeout Protection

**Validates: Requirements 1.1, 2.1**

This test encodes the EXPECTED BEHAVIOR for Bug 1.1:
- When requests approach 29s API Gateway timeout, system should return graceful timeout response
- This test MUST FAIL on unfixed code (proves bug exists)
- This test WILL PASS after fix is implemented (validates fix works)

Bug Condition (from design.md):
  FUNCTION isBugCondition(request, context)
    elapsed_ms = initial_timeout_ms - context.get_remaining_time_in_millis()
    RETURN elapsed_ms > 24000 AND response_not_yet_sent
  END FUNCTION

Expected Behavior (from bugfix.md Requirement 2.1):
  When the orchestrator detects it's approaching the 29-second API Gateway timeout,
  it SHALL return a partial response or graceful error message before the hard timeout.
"""

import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock missing modules before importing handler
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

# Import the handler
from lambdas.agent_orchestrator.handler import lambda_handler


class TestBug11TimeoutExploration:
    """
    Bug Condition Exploration Test for Bug 1.1: API Gateway Timeout
    
    CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    The test simulates a request that takes longer than 29 seconds by:
    1. Mocking Lambda context to report low remaining time (< 5s buffer)
    2. Verifying that WITHOUT the fix, the system does NOT return early
    3. Verifying that WITH the fix, the system returns graceful timeout response
    """
    
    def test_long_running_request_without_timeout_protection(self):
        """
        Property 1: Fault Condition - API Gateway Timeout Detection
        
        Test that requests approaching 29s timeout do NOT get graceful handling
        when ENABLE_TIMEOUT_PROTECTION is OFF (unfixed code).
        
        EXPECTED OUTCOME: This test FAILS on unfixed code because:
        - The system does NOT check remaining time
        - The system does NOT return early with graceful timeout
        - The request continues processing until API Gateway times out
        
        Counterexample: A complex query taking 30+ seconds results in Gateway Timeout
        instead of graceful timeout response.
        """
        # Arrange: Mock a request that has been running for 25+ seconds
        # (only 4 seconds remaining before 29s API Gateway timeout)
        mock_context = Mock()
        mock_context.get_remaining_time_in_millis.return_value = 4000  # 4 seconds left
        mock_context.function_name = "test-agent-orchestrator"
        mock_context.invoked_function_arn = "arn:aws:lambda:ap-south-1:123456789012:function:test"
        
        # Create a test event
        event = {
            'body': json.dumps({
                'message': 'What are the best crops for my farm?',
                'session_id': 'test-session-123',
                'farmer_id': 'test-farmer-456',
                'language': 'en'
            }),
            'headers': {
                'Content-Type': 'application/json'
            },
            'requestContext': {
                'requestId': 'test-request-789'
            }
        }
        
        # Mock environment variables to disable timeout protection
        with patch.dict(os.environ, {
            'ENABLE_TIMEOUT_PROTECTION': 'false',  # Bug condition: flag OFF
            'TIMEOUT_BUFFER_MS': '5000',
            'FOUNDATION_MODEL': 'test-model',
            'AWS_REGION': 'ap-south-1'
        }):
            # Mock all external dependencies
            with patch('lambdas.agent_orchestrator.handler.bedrock_rt') as mock_bedrock, \
                 patch('lambdas.agent_orchestrator.handler.lambda_client') as mock_lambda, \
                 patch('lambdas.agent_orchestrator.handler.check_rate_limit') as mock_rate_limit, \
                 patch('lambdas.agent_orchestrator.handler.run_all_guardrails') as mock_guardrails, \
                 patch('lambdas.agent_orchestrator.handler.get_farmer_profile') as mock_profile, \
                 patch('lambdas.agent_orchestrator.handler.save_chat_message') as mock_save, \
                 patch('lambdas.agent_orchestrator.handler.audit_request_start') as mock_audit_start, \
                 patch('lambdas.agent_orchestrator.handler.audit_request_complete') as mock_audit_complete, \
                 patch('lambdas.agent_orchestrator.handler.get_cached_response', return_value=None), \
                 patch('lambdas.agent_orchestrator.handler.cache_response'), \
                 patch('lambdas.agent_orchestrator.handler.get_chat_history', return_value=[]), \
                 patch('lambdas.agent_orchestrator.handler.text_to_speech', return_value=None):
                
                # Configure mocks
                mock_rate_limit.return_value = {'allowed': True, 'reason': None}  # Rate limit passed
                mock_guardrails.return_value = {
                    'passed': True,
                    'pii_masked_message': 'What are the best crops for my farm?',
                    'threat_details': None,
                    'pii_detected': False,
                    'sanitized_message': 'What are the best crops for my farm?',
                    'blocked_reason': None,
                    'blocked_response': None
                }
                mock_profile.return_value = {
                    'farmer_id': 'test-farmer-456',
                    'name': 'Test Farmer',
                    'language': 'en'
                }
                
                # Mock Bedrock to simulate a slow response
                mock_bedrock.converse.return_value = {
                    'output': {
                        'message': {
                            'role': 'assistant',
                            'content': [
                                {'text': 'Based on your location, I recommend rice and wheat.'}
                            ]
                        }
                    },
                    'stopReason': 'end_turn',
                    'usage': {
                        'inputTokens': 100,
                        'outputTokens': 50
                    }
                }
                
                # Act: Call the handler
                response = lambda_handler(event, mock_context)
                
                # Assert: Verify the bug exists (no early timeout handling)
                # On UNFIXED code, the handler should NOT return early
                # It should process the request normally and NOT include timeout_fallback flag
                
                assert response is not None, "Handler should return a response"
                assert response['statusCode'] == 200, "Should return 200 status"
                
                body = json.loads(response['body'])
                
                # BUG VERIFICATION: The unfixed code does NOT have timeout protection
                # So it will NOT return a timeout_fallback response
                # This assertion FAILS on unfixed code (which is correct - proves bug exists)
                # This assertion PASSES after fix is implemented (validates fix works)
                
                # Check if timeout_fallback flag exists in response
                has_timeout_fallback = body.get('timeout_fallback', False)
                
                # CRITICAL ASSERTION: This MUST FAIL on unfixed code
                # On unfixed code: has_timeout_fallback = False (no timeout protection)
                # After fix: has_timeout_fallback = True (graceful timeout response)
                assert has_timeout_fallback is True, (
                    "EXPECTED BEHAVIOR: System should detect approaching timeout "
                    "(4s remaining < 5s buffer) and return graceful timeout response. "
                    "ACTUAL BEHAVIOR (UNFIXED): System does NOT check remaining time, "
                    "continues processing, and eventually hits API Gateway 29s timeout. "
                    "COUNTEREXAMPLE: Complex query taking 30+ seconds results in "
                    "Gateway Timeout error instead of graceful timeout message."
                )
                
                # Additional assertions for the expected behavior
                if has_timeout_fallback:
                    # After fix is implemented, verify the timeout response structure
                    assert 'reply' in body, "Timeout response should include reply"
                    assert body['audio_url'] is None, "Timeout response should not include audio"
                    
                    # Verify the message is user-friendly
                    reply = body['reply']
                    assert len(reply) > 0, "Timeout message should not be empty"
                    assert any(word in reply.lower() for word in ['processing', 'longer', 'expected']), \
                        "Timeout message should explain the delay"


    def test_timeout_detection_with_various_remaining_times(self):
        """
        Property 1 (Extended): Test timeout detection across multiple time thresholds
        
        This test verifies the bug condition across different remaining time values:
        - 10000ms (10s): Should NOT trigger timeout (plenty of time)
        - 6000ms (6s): Should NOT trigger timeout (above 5s buffer)
        - 4000ms (4s): SHOULD trigger timeout (below 5s buffer)
        - 2000ms (2s): SHOULD trigger timeout (well below buffer)
        - 500ms (0.5s): SHOULD trigger timeout (critical)
        
        EXPECTED OUTCOME: On unfixed code, NONE of these trigger early return.
        After fix, times < 5000ms should trigger graceful timeout.
        """
        test_cases = [
            (10000, False, "10s remaining - should NOT timeout"),
            (6000, False, "6s remaining - should NOT timeout"),
            (4000, True, "4s remaining - SHOULD timeout (< 5s buffer)"),
            (2000, True, "2s remaining - SHOULD timeout"),
            (500, True, "0.5s remaining - SHOULD timeout"),
        ]
        
        for remaining_ms, should_timeout, description in test_cases:
            with self.subTest(remaining_ms=remaining_ms, description=description):
                # Arrange
                mock_context = Mock()
                mock_context.get_remaining_time_in_millis.return_value = remaining_ms
                mock_context.function_name = "test-agent-orchestrator"
                mock_context.invoked_function_arn = "arn:aws:lambda:ap-south-1:123456789012:function:test"
                
                event = {
                    'body': json.dumps({
                        'message': 'Test query',
                        'session_id': 'test-session',
                        'farmer_id': 'test-farmer',
                        'language': 'en'
                    }),
                    'headers': {'Content-Type': 'application/json'},
                    'requestContext': {'requestId': 'test-request'}
                }
                
                # Test with flag OFF (unfixed code)
                with patch.dict(os.environ, {
                    'ENABLE_TIMEOUT_PROTECTION': 'false',
                    'TIMEOUT_BUFFER_MS': '5000',
                    'FOUNDATION_MODEL': 'test-model',
                    'AWS_REGION': 'ap-south-1'
                }):
                    with patch('lambdas.agent_orchestrator.handler.bedrock_rt') as mock_bedrock, \
                         patch('lambdas.agent_orchestrator.handler.lambda_client'), \
                         patch('lambdas.agent_orchestrator.handler.check_rate_limit', return_value={'allowed': True, 'reason': None}), \
                         patch('lambdas.agent_orchestrator.handler.run_all_guardrails', return_value={
                             'passed': True,
                             'pii_masked_message': 'Test query',
                             'threat_details': None,
                             'pii_detected': False,
                             'sanitized_message': 'Test query',
                             'blocked_reason': None,
                             'blocked_response': None
                         }), \
                         patch('lambdas.agent_orchestrator.handler.get_farmer_profile', return_value={'farmer_id': 'test'}), \
                         patch('lambdas.agent_orchestrator.handler.save_chat_message'), \
                         patch('lambdas.agent_orchestrator.handler.audit_request_start'), \
                         patch('lambdas.agent_orchestrator.handler.audit_request_complete'), \
                         patch('lambdas.agent_orchestrator.handler.get_cached_response', return_value=None), \
                         patch('lambdas.agent_orchestrator.handler.cache_response'), \
                         patch('lambdas.agent_orchestrator.handler.get_chat_history', return_value=[]), \
                         patch('lambdas.agent_orchestrator.handler.text_to_speech', return_value=None):
                        
                        mock_bedrock.converse.return_value = {
                            'output': {
                                'message': {
                                    'role': 'assistant',
                                    'content': [{'text': 'Test response'}]
                                }
                            },
                            'stopReason': 'end_turn',
                            'usage': {'inputTokens': 10, 'outputTokens': 10}
                        }
                        
                        # Act
                        response = lambda_handler(event, mock_context)
                        body = json.loads(response['body'])
                        has_timeout_fallback = body.get('timeout_fallback', False)
                        
                        # Assert
                        if should_timeout:
                            # CRITICAL: This FAILS on unfixed code (proves bug exists)
                            assert has_timeout_fallback is True, (
                                f"{description}: EXPECTED graceful timeout with {remaining_ms}ms remaining "
                                f"(< 5000ms buffer), but got normal response. "
                                f"BUG: System does NOT detect approaching timeout."
                            )
                        else:
                            # Should NOT timeout - normal processing
                            assert has_timeout_fallback is False, (
                                f"{description}: Should NOT timeout with {remaining_ms}ms remaining "
                                f"(>= 5000ms buffer)"
                            )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
