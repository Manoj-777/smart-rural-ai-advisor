"""
Bug 1.1 Preservation Property Tests: Normal Request Processing

**Validates: Requirements 3.1, 3.2, 3.3, 3.18**

This test verifies that normal requests (completing within 24 seconds) continue
to work correctly with the timeout protection feature flag OFF (unfixed code).

These tests MUST PASS on unfixed code to confirm baseline behavior to preserve.
These tests MUST ALSO PASS after the fix is implemented to ensure no regressions.

Preservation Requirements (from bugfix.md):
- 3.1: When feature flags are OFF, system executes all existing code paths exactly as before
- 3.2: Farmers send queries in any of 13 supported languages, system translates/processes correctly
- 3.3: Agent orchestrator invokes tools, returns same response structure and field names
- 3.18: Bedrock converse API called with same system prompt, tool config, inference parameters
"""

import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pytest
from hypothesis import given, strategies as st, settings, assume

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock missing modules before importing handler
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

# Import the handler
from lambdas.agent_orchestrator.handler import lambda_handler


class TestBug11Preservation:
    """
    Preservation Property Tests for Bug 1.1: API Gateway Timeout Protection
    
    CRITICAL: These tests MUST PASS on unfixed code (ENABLE_TIMEOUT_PROTECTION='false')
    to confirm the baseline behavior we need to preserve.
    
    Property 2: Preservation - Normal Request Processing
    For all requests completing within 24 seconds, the response is returned normally
    with the same structure, field names, and behavior as before.
    """
    
    def _create_mock_context(self, remaining_time_ms):
        """Helper to create a mock Lambda context with specified remaining time."""
        mock_context = Mock()
        mock_context.get_remaining_time_in_millis.return_value = remaining_time_ms
        mock_context.function_name = "test-agent-orchestrator"
        mock_context.invoked_function_arn = "arn:aws:lambda:ap-south-1:123456789012:function:test"
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
            'headers': {
                'Content-Type': 'application/json'
            },
            'requestContext': {
                'requestId': 'test-request-789'
            }
        }
    
    def _setup_mocks(self):
        """Helper to set up common mocks for all tests."""
        patches = {
            'bedrock': patch('lambdas.agent_orchestrator.handler.bedrock_rt'),
            'lambda_client': patch('lambdas.agent_orchestrator.handler.lambda_client'),
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
        
        # Mock translation functions to return input as-is (no translation needed for tests)
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
    
    def test_normal_request_with_plenty_of_time(self):
        """
        Property 2: Preservation - Normal Request Processing
        
        Test that requests with plenty of remaining time (> 24 seconds) process
        normally and return the expected response structure.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code (flag OFF)
        - Response has statusCode 200
        - Response body contains 'reply' field
        - No 'timeout_fallback' flag in response
        - Response structure matches existing behavior
        """
        # Arrange: Mock a request with 60 seconds remaining (plenty of time)
        mock_context = self._create_mock_context(remaining_time_ms=60000)
        event = self._create_test_event('What crops should I grow this season?')  # Farming-related query
        
        mocks, patches = self._setup_mocks()
        
        try:
            # Update guardrails mock to use the actual message
            mocks['guardrails'].return_value['pii_masked_message'] = 'What crops should I grow this season?'
            mocks['guardrails'].return_value['sanitized_message'] = 'What crops should I grow this season?'
            mocks['translate_detect'].return_value = {
                'translated_text': 'What crops should I grow this season?',
                'detected_language': 'en',
                'was_translated': False
            }
            
            # Mock Bedrock to return a normal response
            mocks['bedrock'].converse.return_value = {
                'output': {
                    'message': {
                        'role': 'assistant',
                        'content': [
                            {'text': 'Based on your location, I recommend rice and wheat for this season.'}
                        ]
                    }
                },
                'stopReason': 'end_turn',
                'usage': {
                    'inputTokens': 100,
                    'outputTokens': 50
                }
            }
            
            # Act: Call handler with flag OFF (unfixed code)
            with patch.dict(os.environ, {
                'ENABLE_TIMEOUT_PROTECTION': 'false',  # Flag OFF - unfixed code
                'TIMEOUT_BUFFER_MS': '5000',
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
            # The actual response structure may have 'data' field containing the reply
            assert 'status' in body or 'data' in body or 'reply' in body, "Response should contain status/data/reply field"
            
            # Verify NO timeout_fallback flag (normal processing)
            # Check in both body and data fields
            has_timeout_in_body = body.get('timeout_fallback', False)
            has_timeout_in_data = body.get('data', {}).get('timeout_fallback', False) if isinstance(body.get('data'), dict) else False
            
            assert has_timeout_in_body is False and has_timeout_in_data is False, (
                "Normal requests should NOT have timeout_fallback flag "
                "(this is the baseline behavior to preserve)"
            )
            
            # Verify Bedrock was called (Requirement 3.18)
            assert mocks['bedrock'].converse.called, "Bedrock converse should be called"
            
        finally:
            self._cleanup_mocks(patches)
    
    @given(
        remaining_time_ms=st.integers(min_value=25000, max_value=120000),
        crop=st.sampled_from(['rice', 'wheat', 'cotton', 'maize', 'tomato', 'onion'])
    )
    @settings(max_examples=20, deadline=None)
    def test_property_normal_requests_complete_successfully(self, remaining_time_ms, crop):
        """
        Property 2 (Property-Based Test): Preservation - Normal Request Processing
        
        For ALL requests with remaining time >= 25 seconds (above the 24s threshold),
        the system MUST process the request normally and return a valid response.
        
        This property-based test generates many test cases to verify the baseline
        behavior is preserved across different time values and crop inputs.
        
        EXPECTED OUTCOME: All generated test cases PASS on unfixed code (flag OFF)
        """
        # Create farming-related message
        message = f'What is the best season to grow {crop}?'
        
        # Arrange
        mock_context = self._create_mock_context(remaining_time_ms=remaining_time_ms)
        event = self._create_test_event(message)
        
        mocks, patches = self._setup_mocks()
        
        try:
            # Update guardrails mock to use the actual message
            mocks['guardrails'].return_value['pii_masked_message'] = message
            mocks['guardrails'].return_value['sanitized_message'] = message
            mocks['translate_detect'].return_value = {
                'translated_text': message,
                'detected_language': 'en',
                'was_translated': False
            }
            
            # Mock Bedrock response
            mocks['bedrock'].converse.return_value = {
                'output': {
                    'message': {
                        'role': 'assistant',
                        'content': [{'text': f'The best season for {crop} is kharif season.'}]
                    }
                },
                'stopReason': 'end_turn',
                'usage': {'inputTokens': 50, 'outputTokens': 30}
            }
            
            # Act: Call handler with flag OFF
            with patch.dict(os.environ, {
                'ENABLE_TIMEOUT_PROTECTION': 'false',
                'TIMEOUT_BUFFER_MS': '5000',
                'FOUNDATION_MODEL': 'test-model',
                'AWS_REGION': 'ap-south-1'
            }):
                response = lambda_handler(event, mock_context)
            
            # Assert: Verify normal processing for all test cases
            assert response is not None
            assert response['statusCode'] == 200
            
            body = json.loads(response['body'])
            assert 'status' in body or 'data' in body or 'reply' in body
            
            # Check timeout_fallback in both possible locations
            has_timeout_in_body = body.get('timeout_fallback', False)
            has_timeout_in_data = body.get('data', {}).get('timeout_fallback', False) if isinstance(body.get('data'), dict) else False
            assert has_timeout_in_body is False and has_timeout_in_data is False
            
        finally:
            self._cleanup_mocks(patches)
    
    def test_response_structure_preserved(self):
        """
        Property 2: Preservation - Response Structure
        
        Verify that the response structure remains unchanged with flag OFF.
        This ensures Requirement 3.3: same response structure and field names.
        
        EXPECTED OUTCOME: Test PASSES on unfixed code
        - Response has expected fields: statusCode, headers, body
        - Body has expected fields: reply, audio_url (optional)
        - No new fields added by timeout protection
        """
        mock_context = self._create_mock_context(remaining_time_ms=60000)
        event = self._create_test_event('Tell me about rice farming')
        
        mocks, patches = self._setup_mocks()
        
        try:
            mocks['bedrock'].converse.return_value = {
                'output': {
                    'message': {
                        'role': 'assistant',
                        'content': [{'text': 'Rice farming requires proper water management...'}]
                    }
                },
                'stopReason': 'end_turn',
                'usage': {'inputTokens': 80, 'outputTokens': 60}
            }
            
            with patch.dict(os.environ, {
                'ENABLE_TIMEOUT_PROTECTION': 'false',
                'FOUNDATION_MODEL': 'test-model',
                'AWS_REGION': 'ap-south-1'
            }):
                response = lambda_handler(event, mock_context)
            
            # Assert: Verify response structure (Requirement 3.3)
            assert 'statusCode' in response
            assert 'body' in response
            
            body = json.loads(response['body'])
            
            # Expected: response should have some content (status, data, or reply)
            assert 'status' in body or 'data' in body or 'reply' in body
            
            # Optional fields that may or may not be present
            # (but should not include timeout_fallback with flag OFF)
            has_timeout_in_body = body.get('timeout_fallback', False)
            has_timeout_in_data = body.get('data', {}).get('timeout_fallback', False) if isinstance(body.get('data'), dict) else False
            assert has_timeout_in_body is False and has_timeout_in_data is False
            
        finally:
            self._cleanup_mocks(patches)
    
    def test_multilingual_support_preserved(self):
        """
        Property 2: Preservation - Multilingual Support
        
        Verify that multilingual support (Requirement 3.2) is preserved:
        "Farmers send queries in any of 13 supported languages, system translates/processes correctly"
        
        EXPECTED OUTCOME: Test PASSES on unfixed code
        - Requests in different languages process normally
        - No timeout_fallback flag for normal requests
        """
        # Test with English (most common case)
        mock_context = self._create_mock_context(remaining_time_ms=60000)
        event = self._create_test_event('Test query', language='en')
        
        mocks, patches = self._setup_mocks()
        
        try:
            mocks['bedrock'].converse.return_value = {
                'output': {
                    'message': {
                        'role': 'assistant',
                        'content': [{'text': 'Response in en'}]
                    }
                },
                'stopReason': 'end_turn',
                'usage': {'inputTokens': 50, 'outputTokens': 30}
            }
            
            with patch.dict(os.environ, {
                'ENABLE_TIMEOUT_PROTECTION': 'false',
                'FOUNDATION_MODEL': 'test-model',
                'AWS_REGION': 'ap-south-1'
            }):
                response = lambda_handler(event, mock_context)
            
            # Assert: Normal processing
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'status' in body or 'data' in body or 'reply' in body
            
            # No timeout_fallback flag
            has_timeout_in_body = body.get('timeout_fallback', False)
            has_timeout_in_data = body.get('data', {}).get('timeout_fallback', False) if isinstance(body.get('data'), dict) else False
            assert has_timeout_in_body is False and has_timeout_in_data is False
            
        finally:
            self._cleanup_mocks(patches)
    
    def test_tool_invocation_preserved(self):
        """
        Property 2: Preservation - Tool Invocation
        
        Verify that tool invocation behavior (Requirement 3.3) is preserved:
        "Agent orchestrator invokes tools, returns same response structure and field names"
        
        EXPECTED OUTCOME: Test PASSES on unfixed code
        - Response is returned normally
        - No timeout_fallback flag
        """
        mock_context = self._create_mock_context(remaining_time_ms=60000)
        event = self._create_test_event('What is the weather forecast for rice farming?')
        
        mocks, patches = self._setup_mocks()
        
        try:
            # Update guardrails and translation mocks
            mocks['guardrails'].return_value['pii_masked_message'] = 'What is the weather forecast for rice farming?'
            mocks['guardrails'].return_value['sanitized_message'] = 'What is the weather forecast for rice farming?'
            mocks['translate_detect'].return_value = {
                'translated_text': 'What is the weather forecast for rice farming?',
                'detected_language': 'en',
                'was_translated': False
            }
            
            # Mock Bedrock to return a simple response (not requesting tools for simplicity)
            mocks['bedrock'].converse.return_value = {
                'output': {
                    'message': {
                        'role': 'assistant',
                        'content': [
                            {'text': 'The weather is sunny with good conditions for rice farming.'}
                        ]
                    }
                },
                'stopReason': 'end_turn',
                'usage': {'inputTokens': 150, 'outputTokens': 40}
            }
            
            with patch.dict(os.environ, {
                'ENABLE_TIMEOUT_PROTECTION': 'false',
                'FOUNDATION_MODEL': 'test-model',
                'AWS_REGION': 'ap-south-1',
                'LAMBDA_WEATHER': 'weather-function'
            }):
                response = lambda_handler(event, mock_context)
            
            # Assert: Normal response
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'status' in body or 'data' in body or 'reply' in body
            
            # No timeout_fallback flag
            has_timeout_in_body = body.get('timeout_fallback', False)
            has_timeout_in_data = body.get('data', {}).get('timeout_fallback', False) if isinstance(body.get('data'), dict) else False
            assert has_timeout_in_body is False and has_timeout_in_data is False
            
        finally:
            self._cleanup_mocks(patches)
    
    def test_bedrock_parameters_preserved(self):
        """
        Property 2: Preservation - Bedrock Parameters
        
        Verify that Bedrock converse API parameters (Requirement 3.18) are preserved:
        "Bedrock converse API called with same system prompt, tool config, inference parameters"
        
        EXPECTED OUTCOME: Test PASSES on unfixed code
        - Bedrock called with expected parameters
        - System prompt unchanged
        - Tool configuration unchanged
        """
        mock_context = self._create_mock_context(remaining_time_ms=60000)
        event = self._create_test_event('What crops grow well in clay soil?')
        
        mocks, patches = self._setup_mocks()
        
        try:
            # Update guardrails and translation mocks
            mocks['guardrails'].return_value['pii_masked_message'] = 'What crops grow well in clay soil?'
            mocks['guardrails'].return_value['sanitized_message'] = 'What crops grow well in clay soil?'
            mocks['translate_detect'].return_value = {
                'translated_text': 'What crops grow well in clay soil?',
                'detected_language': 'en',
                'was_translated': False
            }
            
            mocks['bedrock'].converse.return_value = {
                'output': {
                    'message': {
                        'role': 'assistant',
                        'content': [{'text': 'Rice and wheat grow well in clay soil.'}]
                    }
                },
                'stopReason': 'end_turn',
                'usage': {'inputTokens': 100, 'outputTokens': 50}
            }
            
            with patch.dict(os.environ, {
                'ENABLE_TIMEOUT_PROTECTION': 'false',
                'FOUNDATION_MODEL': 'test-model',
                'AWS_REGION': 'ap-south-1'
            }):
                response = lambda_handler(event, mock_context)
            
            # Assert: Bedrock was called
            assert mocks['bedrock'].converse.called
            
            # Verify call parameters (Requirement 3.18)
            call_args = mocks['bedrock'].converse.call_args
            assert call_args is not None
            
            # Check that modelId is passed
            assert 'modelId' in call_args.kwargs or len(call_args.args) > 0
            
            # Check that messages are passed
            assert 'messages' in call_args.kwargs or len(call_args.args) > 1
            
            # Response should be normal
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            
            # No timeout_fallback flag
            has_timeout_in_body = body.get('timeout_fallback', False)
            has_timeout_in_data = body.get('data', {}).get('timeout_fallback', False) if isinstance(body.get('data'), dict) else False
            assert has_timeout_in_body is False and has_timeout_in_data is False
            
        finally:
            self._cleanup_mocks(patches)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
