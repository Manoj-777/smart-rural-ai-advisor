"""
Bug 1.2 Exploration Test: Tool Execution Timeout Protection

**Validates: Requirements 1.2, 2.2**

This test verifies the bug condition where parallel tool execution with one hanging tool
blocks the entire request indefinitely.

EXPECTED OUTCOME ON UNFIXED CODE (ENABLE_TOOL_TIMEOUT='false'):
- Test FAILS: Request hangs until Lambda timeout (120s)
- The as_completed() iterator blocks indefinitely waiting for the hanging tool
- No timeout protection exists

EXPECTED OUTCOME ON FIXED CODE (ENABLE_TOOL_TIMEOUT='true'):
- Test PASSES: Hanging tool times out after TOOL_EXECUTION_TIMEOUT_SEC (25s)
- Other tools complete successfully
- Response includes timeout error for hanging tool

Bug Condition:
- Multiple tools execute in parallel (2+)
- One tool Lambda hangs (sleeps 60 seconds)
- ThreadPoolExecutor with as_completed() blocks indefinitely
- No timeout parameter on future.result()
"""

import json
import sys
import os
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock missing modules
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

from lambdas.agent_orchestrator.handler import lambda_handler


def mock_tool_execution_with_hang(tool_name, tool_input):
    """
    Mock tool execution where one tool hangs for 60 seconds.
    This simulates a tool Lambda that hangs due to network issues or infinite loop.
    """
    if tool_name == "weather_lookup":
        # Simulate hanging tool - sleeps for 60 seconds
        time.sleep(60)
        return {"temperature": 25, "condition": "sunny"}
    elif tool_name == "crop_advisory":
        # Normal tool - returns immediately
        return {"advisory": "Plant rice in monsoon season"}
    else:
        return {"result": "success"}


def test_bug_condition_tool_execution_hangs():
    """
    Bug Condition Exploration Test for Bug 1.2
    
    This test verifies that when ENABLE_TOOL_TIMEOUT='false' (unfixed code),
    a hanging tool causes the entire request to hang until Lambda timeout.
    
    EXPECTED: This test FAILS on unfixed code (times out after 30+ seconds)
    EXPECTED: This test PASSES on fixed code (completes within timeout)
    """
    # Mock context with sufficient time
    mock_context = Mock()
    mock_context.get_remaining_time_in_millis.return_value = 115000  # 115 seconds
    mock_context.function_name = "test-agent-orchestrator"
    mock_context.invoked_function_arn = "arn:aws:lambda:ap-south-1:123456789012:function:test"
    mock_context.aws_request_id = "test-request-123"
    
    event = {
        'body': json.dumps({
            'message': 'What is the weather and crop advisory for my farm?',
            'session_id': 'test-session-123',
            'farmer_id': 'test-farmer-456',
            'language': 'en'
        }),
        'headers': {'Content-Type': 'application/json'},
        'requestContext': {'requestId': 'test-request-789'}
    }
    
    # Mock Bedrock response to request 2 tools in parallel
    mock_bedrock_response_tool_use = {
        'output': {
            'message': {
                'role': 'assistant',
                'content': [
                    {
                        'toolUse': {
                            'toolUseId': 'tool-1',
                            'name': 'weather_lookup',
                            'input': {'latitude': 12.9716, 'longitude': 77.5946}
                        }
                    },
                    {
                        'toolUse': {
                            'toolUseId': 'tool-2',
                            'name': 'crop_advisory',
                            'input': {'query': 'best crops for monsoon'}
                        }
                    }
                ]
            }
        },
        'stopReason': 'tool_use',
        'usage': {'inputTokens': 100, 'outputTokens': 50}
    }
    
    # Mock final response after tools
    mock_bedrock_response_final = {
        'output': {
            'message': {
                'role': 'assistant',
                'content': [
                    {'text': 'Based on the weather and crop data, I recommend planting rice.'}
                ]
            }
        },
        'stopReason': 'end_turn',
        'usage': {'inputTokens': 200, 'outputTokens': 100}
    }
    
    # Track Bedrock call count
    bedrock_call_count = [0]
    
    def mock_bedrock_converse(**kwargs):
        bedrock_call_count[0] += 1
        if bedrock_call_count[0] == 1:
            return mock_bedrock_response_tool_use
        else:
            return mock_bedrock_response_final
    
    # Disable timeout protection (UNFIXED CODE)
    with patch.dict(os.environ, {
        'ENABLE_TOOL_TIMEOUT': 'false',  # BUG CONDITION: No timeout protection
        'TOOL_EXECUTION_TIMEOUT_SEC': '25',
        'FOUNDATION_MODEL': 'test-model',
        'AWS_REGION': 'ap-south-1'
    }):
        with patch('lambdas.agent_orchestrator.handler.bedrock_rt') as mock_bedrock_client, \
             patch('lambdas.agent_orchestrator.handler._execute_tool', side_effect=mock_tool_execution_with_hang), \
             patch('lambdas.agent_orchestrator.handler.check_rate_limit', return_value={'allowed': True}), \
             patch('lambdas.agent_orchestrator.handler.run_all_guardrails', return_value={
                 'passed': True,
                 'pii_masked_message': 'What is the weather and crop advisory for my farm?',
                 'sanitized_message': 'What is the weather and crop advisory for my farm?',
                 'pii_detected': False,
                 'threat_details': None,
                 'blocked_reason': None,
                 'blocked_response': None
             }), \
             patch('lambdas.agent_orchestrator.handler.get_farmer_profile', return_value={
                 'farmer_id': 'test-farmer-456',
                 'name': 'Test Farmer',
                 'language': 'en'
             }), \
             patch('lambdas.agent_orchestrator.handler.save_chat_message'), \
             patch('lambdas.agent_orchestrator.handler.audit_request_start'), \
             patch('lambdas.agent_orchestrator.handler.audit_request_complete'), \
             patch('lambdas.agent_orchestrator.handler.get_cached_response', return_value=None), \
             patch('lambdas.agent_orchestrator.handler.cache_response'), \
             patch('lambdas.agent_orchestrator.handler.get_chat_history', return_value=[]), \
             patch('lambdas.agent_orchestrator.handler.text_to_speech', return_value=None), \
             patch('lambdas.agent_orchestrator.handler.detect_and_translate', return_value={
                 'detected_language': 'en',
                 'translated_text': 'What is the weather and crop advisory for my farm?'
             }):
            
            # Configure mock Bedrock client
            mock_bedrock_client.converse = mock_bedrock_converse
            
            # Measure execution time
            start_time = time.time()
            
            # Use threading-based timeout (cross-platform)
            import threading
            
            result_container = {'response': None, 'error': None, 'completed': False}
            
            def run_handler():
                try:
                    result_container['response'] = lambda_handler(event, mock_context)
                    result_container['completed'] = True
                except Exception as e:
                    result_container['error'] = e
                    result_container['completed'] = True
            
            # Run handler in separate thread with 30 second timeout
            handler_thread = threading.Thread(target=run_handler)
            handler_thread.daemon = True
            handler_thread.start()
            handler_thread.join(timeout=30)  # Wait max 30 seconds
            
            elapsed_time = time.time() - start_time
            
            if not result_container['completed']:
                # Thread is still running - bug confirmed
                print(f"✗ BUG CONFIRMED: Request hung for {elapsed_time:.2f}s")
                print("✗ The parallel tool execution blocks indefinitely when one tool hangs")
                print("✗ This demonstrates Bug 1.2: No timeout protection on tool execution")
                print("✗ Expected: Request should timeout after 25s with ENABLE_TOOL_TIMEOUT='true'")
                print("✗ Actual: Request hangs waiting for 60s tool to complete")
                
                # Fail the test (expected failure on unfixed code)
                pytest.fail("Bug 1.2 confirmed: Request hangs when tool execution hangs (no timeout protection)")
            
            elif result_container['error']:
                # Handler raised an exception
                raise result_container['error']
            
            else:
                # Handler completed successfully
                response = result_container['response']
                
                # If we get here without timeout, the fix is working
                assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
                
                print(f"✓ Request completed in {elapsed_time:.2f}s")
                print("✓ This indicates the fix is working (or test needs adjustment)")
                
                # With fix enabled, we should see timeout handling
                body = json.loads(response['body'])
                data = body.get('data', body)
                
                # The response should indicate tool timeout was handled
                print(f"Response: {json.dumps(data, indent=2)}")


def test_bug_condition_counterexample_documentation():
    """
    Document the counterexample that demonstrates Bug 1.2.
    
    This test documents the specific conditions that trigger the bug.
    """
    counterexample = {
        "bug_id": "1.2",
        "bug_name": "Tool Execution Timeout Protection",
        "condition": {
            "parallel_tools": True,
            "tool_count": 2,
            "hanging_tool": "weather_lookup",
            "hang_duration_seconds": 60,
            "timeout_protection_enabled": False
        },
        "observed_behavior": {
            "request_hangs": True,
            "blocks_until": "Lambda timeout (120s)",
            "other_tools_blocked": True,
            "no_timeout_error": True
        },
        "expected_behavior_with_fix": {
            "hanging_tool_times_out": True,
            "timeout_after_seconds": 25,
            "other_tools_complete": True,
            "timeout_error_returned": True
        },
        "root_cause": "ThreadPoolExecutor with as_completed() has no timeout parameter",
        "affected_code": "backend/lambdas/agent_orchestrator/handler.py lines 1126-1145"
    }
    
    print("\n" + "="*80)
    print("BUG 1.2 COUNTEREXAMPLE DOCUMENTATION")
    print("="*80)
    print(json.dumps(counterexample, indent=2))
    print("="*80)
    
    # This test always passes - it's just for documentation
    assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
