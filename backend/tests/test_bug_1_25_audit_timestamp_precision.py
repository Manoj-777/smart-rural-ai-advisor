import os
import sys
import json
from datetime import datetime, UTC
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import audit_logger


def _extract_entry(mock_logger_call):
    log_line = mock_logger_call.call_args[0][0]
    assert log_line.startswith('AUDIT|')
    return json.loads(log_line.split('AUDIT|', 1)[1])


def test_audit_timestamp_is_utc_without_microseconds():
    fixed_now = datetime(2026, 3, 7, 12, 34, 56, 123456, tzinfo=UTC)

    with patch.object(audit_logger, 'datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        mock_datetime.UTC = UTC

        with patch.object(audit_logger.audit_logger, 'info') as mock_info:
            audit_logger.audit_log(
                category=audit_logger.AuditEvent.ACCESS,
                action=audit_logger.AuditEvent.REQUEST_STARTED,
                farmer_id='farmer-1',
                session_id='session-1',
                details={'k': 'v'},
            )

    entry = _extract_entry(mock_info)
    assert entry['timestamp'].endswith('Z')
    assert '.' not in entry['timestamp']


def test_audit_log_preserves_required_schema_fields():
    fixed_now = datetime(2026, 3, 7, 8, 0, 1, 999999, tzinfo=UTC)

    with patch.object(audit_logger, 'datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        mock_datetime.UTC = UTC

        with patch.object(audit_logger.audit_logger, 'warning') as mock_warning:
            audit_logger.audit_log(
                category=audit_logger.AuditEvent.SECURITY,
                action=audit_logger.AuditEvent.TOXICITY_BLOCKED,
                farmer_id='farmer-2',
                session_id='session-2',
                severity='warning',
                details={'block_type': 'toxicity'},
                pii_safe_message='masked message',
            )

    entry = _extract_entry(mock_warning)
    assert entry['audit'] is True
    assert entry['category'] == audit_logger.AuditEvent.SECURITY
    assert entry['action'] == audit_logger.AuditEvent.TOXICITY_BLOCKED
    assert entry['severity'] == 'warning'
    assert entry['farmer_id'] == 'farmer-2'
    assert entry['session_id'] == 'session-2'
    assert 'epoch' in entry
    assert entry['message_preview'] == 'masked message'
    assert entry['details']['block_type'] == 'toxicity'
    assert entry['timestamp'].endswith('Z')
    assert '.' not in entry['timestamp']
