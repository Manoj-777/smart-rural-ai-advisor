"""
Bug 1.4 Unit Tests: Model fallback must be feature-flag controlled.

Validates:
- Requirement 2.4 (fallback only when ENABLE_MODEL_FALLBACK=true)
- Requirement 3.1 (flag OFF preserves no-fallback path)
"""

import os
import sys
from unittest.mock import Mock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock optional modules used during handler import
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

from lambdas.agent_orchestrator.handler import (
    _bedrock_converse_with_retry,
    FOUNDATION_MODEL,
    FOUNDATION_MODEL_LITE,
)


def _throttling_error():
    return ClientError(
        {
            'Error': {
                'Code': 'ThrottlingException',
                'Message': 'Rate exceeded',
            }
        },
        'Converse',
    )


def test_fallback_disabled_raises_primary_error_without_fallback_attempt():
    """With flag OFF, no fallback call should be attempted."""
    mock_client = Mock()
    mock_client.converse.side_effect = [_throttling_error(), _throttling_error(), _throttling_error()]

    with patch.dict(os.environ, {'ENABLE_MODEL_FALLBACK': 'false'}):
        with pytest.raises(ClientError):
            _bedrock_converse_with_retry(mock_client, modelId=FOUNDATION_MODEL, messages=[])

    assert mock_client.converse.call_count == 3

    called_models = [call.kwargs.get('modelId') for call in mock_client.converse.call_args_list]
    assert called_models == [FOUNDATION_MODEL, FOUNDATION_MODEL, FOUNDATION_MODEL]


def test_fallback_enabled_pro_to_lite_after_retry_exhaustion():
    """With flag ON, primary Pro should fall back to Lite after retry exhaustion."""
    mock_client = Mock()

    state = {'pro_calls': 0, 'lite_calls': 0}

    def side_effect(**kwargs):
        model_id = kwargs.get('modelId')
        if model_id == FOUNDATION_MODEL:
            state['pro_calls'] += 1
            raise _throttling_error()
        if model_id == FOUNDATION_MODEL_LITE:
            state['lite_calls'] += 1
            return {'output': {'message': {'role': 'assistant', 'content': [{'text': 'ok-lite'}]}}}
        raise AssertionError(f'Unexpected model: {model_id}')

    mock_client.converse.side_effect = side_effect

    with patch.dict(os.environ, {'ENABLE_MODEL_FALLBACK': 'true'}):
        response = _bedrock_converse_with_retry(mock_client, modelId=FOUNDATION_MODEL, messages=[])

    assert state['pro_calls'] == 3
    assert state['lite_calls'] == 1
    assert response['output']['message']['content'][0]['text'] == 'ok-lite'


def test_fallback_enabled_lite_to_pro_after_retry_exhaustion():
    """With flag ON, primary Lite should fall back to Pro after retry exhaustion."""
    mock_client = Mock()

    state = {'lite_calls': 0, 'pro_calls': 0}

    def side_effect(**kwargs):
        model_id = kwargs.get('modelId')
        if model_id == FOUNDATION_MODEL_LITE:
            state['lite_calls'] += 1
            raise _throttling_error()
        if model_id == FOUNDATION_MODEL:
            state['pro_calls'] += 1
            return {'output': {'message': {'role': 'assistant', 'content': [{'text': 'ok-pro'}]}}}
        raise AssertionError(f'Unexpected model: {model_id}')

    mock_client.converse.side_effect = side_effect

    with patch.dict(os.environ, {'ENABLE_MODEL_FALLBACK': 'true'}):
        response = _bedrock_converse_with_retry(mock_client, modelId=FOUNDATION_MODEL_LITE, messages=[])

    assert state['lite_calls'] == 3
    assert state['pro_calls'] == 1
    assert response['output']['message']['content'][0]['text'] == 'ok-pro'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
