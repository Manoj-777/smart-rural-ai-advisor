"""
Verification Test: Bug 1.1 Fix Works with Flag ON

This test verifies that the timeout protection fix works correctly
when ENABLE_TIMEOUT_PROTECTION='true'.
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


def test_timeout_protection_enabled():
    """
    Verify that with ENABLE_TIMEOUT_PROTECTION='true',
    the system returns graceful timeout response when time is low.
    """
    # Mock context with low remaining time
    mock_context = Mock()
    mock_context.get_remaining_time_in_millis.return_value = 4000  # 4s remaining
    mock_context.function_name = "test-agent-orchestrator"
    mock_context.invoked_function_arn = "arn:aws:lambda:ap-south-1:123456789012:function:test"
    mock_context.aws_request_id = "test-request-123"
    
    event = {
        'body': json.dumps({
            'message': 'What are the best crops?',
            'session_id': 'test-session',
            'farmer_id': 'test-farmer',
            'language': 'en'
        }),
        'headers': {'Content-Type': 'application/json'},
        'requestContext': {'requestId': 'test-request'}
    }
    
    # Enable timeout protection
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
                 'pii_masked_message': 'test', 
                 'sanitized_message': 'test',
                 'pii_detected': False,
                 'threat_details': None,
                 'blocked_reason': None,
                 'blocked_response': None
             }), \
             patch('lambdas.agent_orchestrator.handler.get_farmer_profile', return_value={'farmer_id': 'test', 'language': 'en'}), \
             patch('lambdas.agent_orchestrator.handler.save_chat_message'), \
             patch('lambdas.agent_orchestrator.handler.audit_request_start'), \
             patch('lambdas.agent_orchestrator.handler.audit_request_complete'), \
             patch('lambdas.agent_orchestrator.handler.get_cached_response', return_value=None), \
             patch('lambdas.agent_orchestrator.handler.cache_response'), \
             patch('lambdas.agent_orchestrator.handler.get_chat_history', return_value=[]), \
             patch('lambdas.agent_orchestrator.handler.text_to_speech', return_value=None):
            
            response = lambda_handler(event, mock_context)
            
            # Verify graceful timeout response
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            
            # THE FIX: Should return timeout_fallback=True
            assert body.get('timeout_fallback') is True, \
                "Expected timeout_fallback=True with flag ON and low remaining time"
            assert body.get('audio_url') is None
            assert 'reply' in body
            print("✓ Fix verified: Graceful timeout response returned")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
