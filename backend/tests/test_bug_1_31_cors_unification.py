import os
import sys
import json
from unittest.mock import MagicMock
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock optional modules before importing handler
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

from lambdas.agent_orchestrator import handler as orchestrator_handler


def test_timeout_http_response_uses_shared_cors_helper_headers():
    shared_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': 'https://shared.example.com',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    }

    with patch('lambdas.agent_orchestrator.handler.get_cors_headers', return_value=shared_headers, create=True):
        response = orchestrator_handler._timeout_http_response('session-123', language='en')

    assert response['statusCode'] == 200
    assert response['headers'] == shared_headers


def test_timeout_http_response_payload_shape_preserved():
    response = orchestrator_handler._timeout_http_response('session-xyz', language='en')

    body = json.loads(response['body'])
    assert body['session_id'] == 'session-xyz'
    assert body['timeout_fallback'] is True
    assert body['mode'] == 'bedrock-direct'
    assert isinstance(body['reply'], str) and body['reply']
