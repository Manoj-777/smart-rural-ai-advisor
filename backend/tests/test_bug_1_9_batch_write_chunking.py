"""
Bug 1.9 Unit Tests: Batch write should not drop messages beyond 25.

Validates:
- Requirement 2.9 (all messages are written, including >25)
- Preservation for <=25 message behavior
"""

import os
import sys
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import dynamodb_helper


def _build_messages(count):
    return [
        {
            'session_id': 's-batch',
            'role': 'user' if idx % 2 == 0 else 'assistant',
            'message': f'msg-{idx}',
            'language': 'en',
        }
        for idx in range(count)
    ]


def _mock_batch_writer():
    writer = Mock()
    writer_cm = Mock()
    writer_cm.__enter__ = Mock(return_value=writer)
    writer_cm.__exit__ = Mock(return_value=False)
    return writer, writer_cm


def test_batch_write_writes_all_messages_when_count_exceeds_25():
    messages = _build_messages(30)
    writer, writer_cm = _mock_batch_writer()

    with patch.dict(os.environ, {'ENABLE_BATCH_CHAT_WRITES': 'true', 'ENABLE_CHAT_IDEMPOTENCY': 'false'}):
        with patch.object(dynamodb_helper, 'sessions_table') as mock_sessions:
            mock_sessions.batch_writer.return_value = writer_cm
            ok = dynamodb_helper.save_chat_messages_batch(messages)

    assert ok is True
    assert writer.put_item.call_count == 30


def test_batch_write_preserves_behavior_for_25_or_less_messages():
    messages = _build_messages(10)
    writer, writer_cm = _mock_batch_writer()

    with patch.dict(os.environ, {'ENABLE_BATCH_CHAT_WRITES': 'true', 'ENABLE_CHAT_IDEMPOTENCY': 'false'}):
        with patch.object(dynamodb_helper, 'sessions_table') as mock_sessions:
            mock_sessions.batch_writer.return_value = writer_cm
            ok = dynamodb_helper.save_chat_messages_batch(messages)

    assert ok is True
    assert writer.put_item.call_count == 10
