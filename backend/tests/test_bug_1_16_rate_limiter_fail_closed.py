import os
import sys
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import rate_limiter


def test_rate_limiter_dynamodb_error_fails_closed():
    with patch.object(rate_limiter, 'RATE_LIMITING_ENABLED', True):
        with patch('utils.rate_limiter._get_rate_table', side_effect=RuntimeError('dynamodb down')):
            result = rate_limiter.check_rate_limit('session-1', 'farmer-1')

    assert result['allowed'] is False
    assert result['reason'] is not None


def test_rate_limiter_normal_window_preserved_when_within_limits():
    table = Mock()
    table.update_item.side_effect = [
        {'Attributes': {'hit_count': 1}},
        {'Attributes': {'hit_count': 3}},
        {'Attributes': {'hit_count': 7}},
    ]

    with patch.object(rate_limiter, 'RATE_LIMITING_ENABLED', True):
        with patch('utils.rate_limiter._get_rate_table', return_value=table):
            result = rate_limiter.check_rate_limit('session-2', 'farmer-2')

    assert result['allowed'] is True
    assert result['reason'] is None
    assert result['remaining_rpm'] == max(0, rate_limiter.RATE_LIMIT_REQUESTS_PER_MINUTE - 1)
    assert result['remaining_rph'] == max(0, rate_limiter.RATE_LIMIT_REQUESTS_PER_HOUR - 3)
