"""
Bug 1.1 Exploration Test: Verify Fix Works (Flag ON)

This test verifies that the exploration test now PASSES with the fix enabled.
It's the same test as test_bug_1_1_timeout_exploration.py but with ENABLE_TIMEOUT_PROTECTION='true'.
"""

import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock missing modules
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

from lambdas.agent_orchestrator.handler import lambda_handler


def test_exploration_test_passes_with_fix():
    """
    Verify that the exploration test now PASSES with ENABLE_TIMEOUT_PROTECTION='true'.
    
    This is the same test as in test_bug_1_1_timeout_exploration.py but with the fix enabled.
    The test should now PASS, confirming the bug is fixed.
    """
    # Mock context with low remaining time (4s)
    mock_context = Mock()
    mock_context.get_remaining_time_in_millis.return_value = 4000
    mock_context.function_name = "test-agent-orchestrator"
    mock_context.invoked_function_arn = "arn:aws:lambda:ap-south-1:123456789012:function:test"
    mock_context.aws_request_id = "test-request-123"
    
    event = {
        'body': json.dumps({
            'message': 'What are the best crops for my farm?',
            'session_id': 'test-session-123',
            'farmer_id': 'test-farmer-456',
            'language': 'en'
        }),
        'headers': {'Content-Type': 'application/json'},
        'requestContext': {'requestId': 'test-request-789'}
    }
    
    # Enable timeout protection (FIX ENABLED)
    with patch.dict(os.environ, {
        'ENABLE_TIMEOUT_PROTECTION': 'true',  # FIX ENABLED
        'TIMEOUT_BUFFER_MS': '5000',
        'FOUNDATION_MODEL': 'test-model',
        'AWS_REGION': 'ap-south-1'
    }):
        with patch('lambdas.agent_orchestrator.handler.bedrock_rt'), \
             patch('lambdas.agent_orchestrator.handler.lambda_client'), \
             patch('lambdas.agent_orchestrator.handler.check_rate_limit', return_value={'allowed': True}), \
             patch('lambdas.agent_orchestrator.handler.run_all_guardrails', return_value={
                 'passed': True,
                 'pii_masked_message': 'What are the best crops for my farm?',
                 'sanitized_message': 'What are the best crops for my farm?',
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
                 'translated_text': 'What are the best crops for my farm?'
             }):
            
            response = lambda_handler(event, mock_context)
            
            # Verify the fix works
            assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
            body = json.loads(response['body'])
            
            # The response is wrapped in a 'data' field
            data = body.get('data', body)
            
            # The fix should return timeout_fallback=True
            assert data.get('timeout_fallback') is True, \
                f"Expected timeout_fallback=True with fix enabled. Got: {body}"
            
            print("✓ Exploration test PASSES with fix enabled")
            print(f"✓ Response includes timeout_fallback: {data.get('timeout_fallback')}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
