"""
Bug 1.6 Unit Tests: KB retrieve retry on throttling.
"""

import os
import sys
from unittest.mock import Mock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.crop_advisory.handler import _kb_retrieve_with_retry


class ThrottlingException(Exception):
    pass


def test_kb_retry_disabled_calls_once_and_raises():
    client = Mock()
    client.retrieve.side_effect = ThrottlingException('ThrottlingException: throttled')

    with patch.dict(os.environ, {'ENABLE_KB_RETRY': 'false'}):
        with pytest.raises(ThrottlingException):
            _kb_retrieve_with_retry(client, knowledgeBaseId='kb', retrievalQuery={'text': 'q'})

    assert client.retrieve.call_count == 1


def test_kb_retry_enabled_retries_then_succeeds():
    client = Mock()
    client.retrieve.side_effect = [
        ThrottlingException('ThrottlingException: throttled'),
        ThrottlingException('ThrottlingException: throttled'),
        {'retrievalResults': []},
    ]

    with patch.dict(
        os.environ,
        {
            'ENABLE_KB_RETRY': 'true',
            'KB_RETRY_MAX_ATTEMPTS': '3',
            'KB_RETRY_BASE_DELAY': '0',
        },
    ):
        with patch('lambdas.crop_advisory.handler.time.sleep', return_value=None):
            response = _kb_retrieve_with_retry(client, knowledgeBaseId='kb', retrievalQuery={'text': 'q'})

    assert client.retrieve.call_count == 3
    assert response == {'retrievalResults': []}
