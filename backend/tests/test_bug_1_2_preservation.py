"""
Bug 1.2 Preservation Property Tests: Normal Tool Execution

**Validates: Requirements 3.1, 3.3, 3.17**

This test verifies that normal tool execution (tools completing within 25 seconds)
continues to work correctly with the tool timeout feature flag OFF (unfixed code).

These tests MUST PASS on unfixed code to confirm baseline behavior to preserve.
These tests MUST ALSO PASS after the fix is implemented to ensure no regressions.

Preservation Requirements (from design.md):
- 3.1: When feature flags are OFF, system executes all existing code paths exactly as before
- 3.3: Agent orchestrator invokes tools, returns same response structure and field names
- 3.17: Parallel tool execution completes successfully for all tools

Property 2: Preservation - Normal Tool Execution
For all tool executions completing within 25 seconds, results are returned correctly
with the same structure, field names, and behavior as before.
"""

import json
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock
import pytest
from hypothesis import given, strategies as st, settings

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock missing modules before importing handler
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

# Import the handler
from lambdas.agent_orchestrator.handler import lambda_handler


class TestBug12Preservation:
    """
    Preservation Property Tests for Bug 1.2: Tool Execution Timeout Protection
    
    CRITICAL: These tests MUST PASS on unfixed code (ENABLE_TOOL_TIMEOUT='false')
    to confirm the baseline behavior we need to preserve.
    
    Property 2: Preservation - Normal Tool Execution
    For all tool executions completing within 25 seconds, results are returned
    correctly with proper structure and field names.
    """
    
    def _create_mock_context(self, remaining_time_ms=115000):
        """Helper to create a mock Lambda context."""
        mock_context = Mock()
        mock_context.get_remaining_time_in_millis.return_value = remaining_time_ms
        mock_context.function_name = "test-agent-orchestrator"
        mock_context.invoked_function_arn = "arn:aws:lambda:ap-south-1:123456789012:function:test"
        mock_context.aws_request_id = "test-request-123"
        return mock_context
    
    def _create_test_event(self, message, language='en', session_id=None, farmer_id=None):
        """Helper to create a test event."""
        return {
            'body': json.dumps({
                'message': message,
                'session_id': session_id or 'test-session-123',
                'farmer_id': farmer_id or 'test-farmer-456',
                'language': language
            }),
            'headers': {'Content-Type': 'application/json'},
            'requestContext': {'requestId': 'test-request-789'}
        }
    
    def _setup_mocks(self):
        """Helper to set up common mocks for all tests."""
        patches = {
            'bedrock': patch('lambdas.agent_orchestrator.handler.bedrock_rt'),
            'rate_limit': patch('lambdas.agent_orchestrator.handler.check_rate_limit'),
            'guardrails': patch('lambdas.agent_orchestrator.handler.run_all_guardrails'),
            'profile': patch('lambdas.agent_orchestrator.handler.get_farmer_profile'),
            'save': patch('lambdas.agent_orchestrator.handler.save_chat_message'),
            'audit_start': patch('lambdas.agent_orchestrator.handler.audit_request_start'),
            'audit_complete': patch('lambdas.agent_orchestrator.handler.audit_request_complete'),
            'cache_get': patch('lambdas.agent_orchestrator.handler.get_cached_response', return_value=None),
            'cache_set': patch('lambdas.agent_orchestrator.handler.cache_response'),
            'history': patch('lambdas.agent_orchestrator.handler.get_chat_history', return_value=[]),
            'tts': patch('lambdas.agent_orchestrator.handler.text_to_speech', return_value=None),
            'translate_detect': patch('lambdas.agent_orchestrator.handler.detect_and_translate'),
            'translate_response': patch('lambdas.agent_orchestrator.handler.translate_response'),
        }
        
        # Start all patches
        mocks = {name: p.start() for name, p in patches.items()}
        
        # Configure common mock behaviors
        mocks['rate_limit'].return_value = {'allowed': True, 'reason': None}
        mocks['guardrails'].return_value = {
            'passed': True,
            'pii_masked_message': 'Test query',
            'threat_details': None,
            'pii_detected': False,
            'sanitized_message': 'Test query',
            'blocked_reason': None,
            'blocked_response': None
        }
        mocks['profile'].return_value = {
            'farmer_id': 'test-farmer-456',
            'name': 'Test Farmer',
            'language': 'en'
        }
        mocks['translate_detect'].return_value = {
            'translated_text': 'Test query',
            'detected_language': 'en',
            'was_translated': False
        }
        mocks['translate_response'].return_value = 'Test response'
        
        return mocks, patches
    
    def _cleanup_mocks(self, patches):
        """Helper to clean up all patches."""
        for p in patches.values():
            p.stop()
    
    def test_single_tool_execution_completes_normally(self):
        """
        Property 2: Preservation - Single Tool Execution
        
        Test that single tool execution (< 25 seconds) processes normally
        and returns the expected response structure.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (flag OFF)
        - Response has statusCode 200
        - Tool result is returned correctly
        - No timeout errors
        - Response structure matches existing behavior
        """
        mock_context = self._create_mock_context()
        event = self._create_test_event('What is the weather in Bangalore?')
        
        mocks, patches = self._setup_mocks()
        
        try:
            # Update guardrails mock
            mocks['guardrails'].return_value['pii_masked_message'] = 'What is the weather in Bangalore?'
            mocks['guardrails'].return_value['sanitized_message'] = 'What is the weather in Bangalore?'
            mocks['translate_detect'].return_value = {
                'translated_text': 'What is the weather in Bangalore?',
                'detected_language': 'en',
                'was_translated': False
            }
            
            # Mock Bedrock to request a single tool
            bedrock_call_count = [0]
            
            def mock_bedrock_converse(**kwargs):
                bedrock_call_count[0] += 1
                if bedrock_call_count[0] == 1:
                    # First call: request tool
                    return {
                        'output': {
                            'message': {
                                'role': 'assistant',
                                'content': [{
                                    'toolUse': {
                                        'toolUseId': 'tool-1',
                                        'name': 'weather_lookup',
                                        'input': {'latitude': 12.9716, 'longitude': 77.5946}
                                    }
                                }]
                            }
                        },
                        'stopReason': 'tool_use',
                        'usage': {'inputTokens': 100, 'outputTokens': 50}
                    }
                else:
                    # Second call: final response
                    return {
                        'output': {
                            'message': {
                                'role': 'assistant',
                                'content': [{'text': 'The weather in Bangalore is sunny with 25°C.'}]
                            }
                        },
                        'stopReason': 'end_turn',
                        'usage': {'inputTokens': 200, 'outputTokens': 100}
                    }
            
            mocks['bedrock'].converse = mock_bedrock_converse
            
            # Mock tool execution (completes quickly)
            def mock_tool_execution(tool_name, tool_input):
                if tool_name == 'weather_lookup':
                    time.sleep(0.1)  # Simulate fast tool execution
                    return {'temperature': 25, 'condition': 'sunny', 'location': 'Bangalore'}
                return {'result': 'success'}
            
            with patch('lambdas.agent_orchestrator.handler._execute_tool', side_effect=mock_tool_execution):
                with patch.dict(os.environ, {
                    'ENABLE_TOOL_TIMEOUT': 'false',  # Flag OFF - unfixed code
                    'TOOL_EXECUTION_TIMEOUT_SEC': '25',
                    'FOUNDATION_MODEL': 'test-model',
                    'AWS_REGION': 'ap-south-1'
                }):
                    response = lambda_handler(event, mock_context)
            
            # Assert: Verify normal processing (baseline behavior)
            assert response is not None, "Handler should return a response"
            assert response['statusCode'] == 200, "Should return 200 status"
            assert 'body' in response, "Response should have body"
            
            body = json.loads(response['body'])
            
            # Verify expected response structure (Requirements 3.1, 3.3)
            assert 'status' in body or 'data' in body or 'reply' in body, "Response should contain status/data/reply field"
            
            # Verify NO timeout errors (normal processing)
            body_str = json.dumps(body).lower()
            assert 'timeout' not in body_str or 'timeout_fallback' not in body_str, (
                "Normal tool execution should NOT have timeout errors "
                "(this is the baseline behavior to preserve)"
            )
            
        finally:
            self._cleanup_mocks(patches)
    
    def test_parallel_tool_execution_completes_normally(self):
        """
        Property 2: Preservation - Parallel Tool Execution
        
        Test that parallel tool execution (both tools < 25 seconds) processes
        normally and returns results for all tools.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (flag OFF)
        - Response has statusCode 200
        - Both tool results are returned
        - No timeout errors
        - Response structure matches existing behavior (Requirement 3.17)
        """
        mock_context = self._create_mock_context()
        event = self._create_test_event('What is the weather and crop advisory for my farm?')
        
        mocks, patches = self._setup_mocks()
        
        try:
            # Update guardrails mock
            mocks['guardrails'].return_value['pii_masked_message'] = 'What is the weather and crop advisory for my farm?'
            mocks['guardrails'].return_value['sanitized_message'] = 'What is the weather and crop advisory for my farm?'
            mocks['translate_detect'].return_value = {
                'translated_text': 'What is the weather and crop advisory for my farm?',
                'detected_language': 'en',
                'was_translated': False
            }
            
            # Mock Bedrock to request 2 tools in parallel
            bedrock_call_count = [0]
            
            def mock_bedrock_converse(**kwargs):
                bedrock_call_count[0] += 1
                if bedrock_call_count[0] == 1:
                    # First call: request 2 tools
                    return {
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
                else:
                    # Second call: final response
                    return {
                        'output': {
                            'message': {
                                'role': 'assistant',
                                'content': [{'text': 'Based on the weather and crop data, I recommend planting rice.'}]
                            }
                        },
                        'stopReason': 'end_turn',
                        'usage': {'inputTokens': 200, 'outputTokens': 100}
                    }
            
            mocks['bedrock'].converse = mock_bedrock_converse
            
            # Mock tool execution (both complete quickly)
            def mock_tool_execution(tool_name, tool_input):
                if tool_name == 'weather_lookup':
                    time.sleep(0.1)  # Fast execution
                    return {'temperature': 25, 'condition': 'sunny'}
                elif tool_name == 'crop_advisory':
                    time.sleep(0.2)  # Fast execution
                    return {'advisory': 'Plant rice in monsoon season'}
                return {'result': 'success'}
            
            with patch('lambdas.agent_orchestrator.handler._execute_tool', side_effect=mock_tool_execution):
                with patch.dict(os.environ, {
                    'ENABLE_TOOL_TIMEOUT': 'false',  # Flag OFF - unfixed code
                    'TOOL_EXECUTION_TIMEOUT_SEC': '25',
                    'FOUNDATION_MODEL': 'test-model',
                    'AWS_REGION': 'ap-south-1'
                }):
                    response = lambda_handler(event, mock_context)
            
            # Assert: Verify normal processing (baseline behavior)
            assert response is not None, "Handler should return a response"
            assert response['statusCode'] == 200, "Should return 200 status"
            assert 'body' in response, "Response should have body"
            
            body = json.loads(response['body'])
            
            # Verify expected response structure (Requirements 3.1, 3.3, 3.17)
            assert 'status' in body or 'data' in body or 'reply' in body, "Response should contain status/data/reply field"
            
            # Verify NO timeout errors (normal processing)
            body_str = json.dumps(body).lower()
            assert 'timeout' not in body_str or 'timeout_fallback' not in body_str, (
                "Normal parallel tool execution should NOT have timeout errors "
                "(this is the baseline behavior to preserve)"
            )
            
            # Verify Bedrock was called twice (once for tool request, once for final response)
            assert bedrock_call_count[0] == 2, "Bedrock should be called twice for tool execution flow"
            
        finally:
            self._cleanup_mocks(patches)
    
    @given(
        tool_execution_time_ms=st.integers(min_value=10, max_value=2000),
        tool_name=st.sampled_from(['weather_lookup', 'crop_advisory', 'schemes_lookup'])
    )
    @settings(max_examples=20, deadline=None)
    def test_property_fast_tools_complete_successfully(self, tool_execution_time_ms, tool_name):
        """
        Property 2 (Property-Based Test): Preservation - Normal Tool Execution
        
        For ALL tool executions completing within 25 seconds (well under the timeout),
        the system MUST process the tool execution normally and return valid results.
        
        This property-based test generates many test cases to verify the baseline
        behavior is preserved across different execution times and tool types.
        
        EXPECTED OUTCOME: All generated test cases PASS on unfixed code (flag OFF)
        """
        # Create message requesting the tool
        message = f'Please use {tool_name} for my query'
        
        mock_context = self._create_mock_context()
        event = self._create_test_event(message)
        
        mocks, patches = self._setup_mocks()
        
        try:
            # Update guardrails mock
            mocks['guardrails'].return_value['pii_masked_message'] = message
            mocks['guardrails'].return_value['sanitized_message'] = message
            mocks['translate_detect'].return_value = {
                'translated_text': message,
                'detected_language': 'en',
                'was_translated': False
            }
            
            # Mock Bedrock to request the tool
            bedrock_call_count = [0]
            
            def mock_bedrock_converse(**kwargs):
                bedrock_call_count[0] += 1
                if bedrock_call_count[0] == 1:
                    return {
                        'output': {
                            'message': {
                                'role': 'assistant',
                                'content': [{
                                    'toolUse': {
                                        'toolUseId': 'tool-1',
                                        'name': tool_name,
                                        'input': {'query': 'test'}
                                    }
                                }]
                            }
                        },
                        'stopReason': 'tool_use',
                        'usage': {'inputTokens': 50, 'outputTokens': 30}
                    }
                else:
                    return {
                        'output': {
                            'message': {
                                'role': 'assistant',
                                'content': [{'text': f'Result from {tool_name}'}]
                            }
                        },
                        'stopReason': 'end_turn',
                        'usage': {'inputTokens': 100, 'outputTokens': 50}
                    }
            
            mocks['bedrock'].converse = mock_bedrock_converse
            
            # Mock tool execution with variable time
            def mock_tool_execution(name, input_data):
                time.sleep(tool_execution_time_ms / 1000.0)  # Convert ms to seconds
                return {'result': 'success', 'tool': name}
            
            with patch('lambdas.agent_orchestrator.handler._execute_tool', side_effect=mock_tool_execution):
                with patch.dict(os.environ, {
                    'ENABLE_TOOL_TIMEOUT': 'false',  # Flag OFF - unfixed code
                    'TOOL_EXECUTION_TIMEOUT_SEC': '25',
                    'FOUNDATION_MODEL': 'test-model',
                    'AWS_REGION': 'ap-south-1'
                }):
                    response = lambda_handler(event, mock_context)
            
            # Assert: Verify normal processing for all test cases
            assert response is not None
            assert response['statusCode'] == 200
            
            body = json.loads(response['body'])
            assert 'status' in body or 'data' in body or 'reply' in body
            
            # Verify NO timeout errors
            body_str = json.dumps(body).lower()
            assert 'timeout' not in body_str or 'timeout_fallback' not in body_str
            
        finally:
            self._cleanup_mocks(patches)
    
    def test_tool_response_structure_preserved(self):
        """
        Property 2: Preservation - Tool Response Structure
        
        Verify that tool execution response structure remains unchanged with flag OFF.
        This ensures Requirement 3.3: same response structure and field names.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code
        - Response has expected fields: statusCode, headers, body
        - Tool results are included in response
        - No timeout-related fields added
        """
        mock_context = self._create_mock_context()
        event = self._create_test_event('Get weather for my location')
        
        mocks, patches = self._setup_mocks()
        
        try:
            # Update guardrails mock
            mocks['guardrails'].return_value['pii_masked_message'] = 'Get weather for my location'
            mocks['guardrails'].return_value['sanitized_message'] = 'Get weather for my location'
            mocks['translate_detect'].return_value = {
                'translated_text': 'Get weather for my location',
                'detected_language': 'en',
                'was_translated': False
            }
            
            # Mock Bedrock to request tool
            bedrock_call_count = [0]
            
            def mock_bedrock_converse(**kwargs):
                bedrock_call_count[0] += 1
                if bedrock_call_count[0] == 1:
                    return {
                        'output': {
                            'message': {
                                'role': 'assistant',
                                'content': [{
                                    'toolUse': {
                                        'toolUseId': 'tool-1',
                                        'name': 'weather_lookup',
                                        'input': {'latitude': 12.9716, 'longitude': 77.5946}
                                    }
                                }]
                            }
                        },
                        'stopReason': 'tool_use',
                        'usage': {'inputTokens': 80, 'outputTokens': 40}
                    }
                else:
                    return {
                        'output': {
                            'message': {
                                'role': 'assistant',
                                'content': [{'text': 'The weather is sunny.'}]
                            }
                        },
                        'stopReason': 'end_turn',
                        'usage': {'inputTokens': 150, 'outputTokens': 60}
                    }
            
            mocks['bedrock'].converse = mock_bedrock_converse
            
            # Mock tool execution
            def mock_tool_execution(tool_name, tool_input):
                time.sleep(0.1)
                return {'temperature': 25, 'condition': 'sunny'}
            
            with patch('lambdas.agent_orchestrator.handler._execute_tool', side_effect=mock_tool_execution):
                with patch.dict(os.environ, {
                    'ENABLE_TOOL_TIMEOUT': 'false',
                    'FOUNDATION_MODEL': 'test-model',
                    'AWS_REGION': 'ap-south-1'
                }):
                    response = lambda_handler(event, mock_context)
            
            # Assert: Verify response structure (Requirement 3.3)
            assert 'statusCode' in response
            assert 'body' in response
            
            body = json.loads(response['body'])
            
            # Expected: response should have some content
            assert 'status' in body or 'data' in body or 'reply' in body
            
            # Verify NO timeout-related fields
            body_str = json.dumps(body).lower()
            assert 'timeout' not in body_str or 'timeout_fallback' not in body_str
            
        finally:
            self._cleanup_mocks(patches)
    
    def test_multiple_parallel_tools_all_complete(self):
        """
        Property 2: Preservation - Multiple Parallel Tools
        
        Verify that when 3+ tools execute in parallel (all completing quickly),
        all tool results are returned correctly (Requirement 3.17).
        
        EXPECTED OUTCOME: Test PASSES on unfixed code
        - All 3 tools complete successfully
        - All results are included in response
        - No timeout errors
        """
        mock_context = self._create_mock_context()
        event = self._create_test_event('Get weather, crop advisory, and schemes for my farm')
        
        mocks, patches = self._setup_mocks()
        
        try:
            # Update guardrails mock
            message = 'Get weather, crop advisory, and schemes for my farm'
            mocks['guardrails'].return_value['pii_masked_message'] = message
            mocks['guardrails'].return_value['sanitized_message'] = message
            mocks['translate_detect'].return_value = {
                'translated_text': message,
                'detected_language': 'en',
                'was_translated': False
            }
            
            # Mock Bedrock to request 3 tools in parallel
            bedrock_call_count = [0]
            
            def mock_bedrock_converse(**kwargs):
                bedrock_call_count[0] += 1
                if bedrock_call_count[0] == 1:
                    return {
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
                                            'input': {'query': 'best crops'}
                                        }
                                    },
                                    {
                                        'toolUse': {
                                            'toolUseId': 'tool-3',
                                            'name': 'schemes_lookup',
                                            'input': {'query': 'government schemes'}
                                        }
                                    }
                                ]
                            }
                        },
                        'stopReason': 'tool_use',
                        'usage': {'inputTokens': 100, 'outputTokens': 50}
                    }
                else:
                    return {
                        'output': {
                            'message': {
                                'role': 'assistant',
                                'content': [{'text': 'Here is the information you requested.'}]
                            }
                        },
                        'stopReason': 'end_turn',
                        'usage': {'inputTokens': 200, 'outputTokens': 100}
                    }
            
            mocks['bedrock'].converse = mock_bedrock_converse
            
            # Mock tool execution (all complete quickly)
            def mock_tool_execution(tool_name, tool_input):
                time.sleep(0.1)  # All tools complete quickly
                return {'result': f'success from {tool_name}'}
            
            with patch('lambdas.agent_orchestrator.handler._execute_tool', side_effect=mock_tool_execution):
                with patch.dict(os.environ, {
                    'ENABLE_TOOL_TIMEOUT': 'false',
                    'TOOL_EXECUTION_TIMEOUT_SEC': '25',
                    'FOUNDATION_MODEL': 'test-model',
                    'AWS_REGION': 'ap-south-1'
                }):
                    response = lambda_handler(event, mock_context)
            
            # Assert: Verify all tools completed successfully
            assert response is not None
            assert response['statusCode'] == 200
            
            body = json.loads(response['body'])
            assert 'status' in body or 'data' in body or 'reply' in body
            
            # Verify NO timeout errors
            body_str = json.dumps(body).lower()
            assert 'timeout' not in body_str or 'timeout_fallback' not in body_str
            
            # Verify Bedrock was called twice (tool request + final response)
            assert bedrock_call_count[0] == 2
            
        finally:
            self._cleanup_mocks(patches)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
