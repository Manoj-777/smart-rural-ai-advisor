import os
import sys
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock optional modules before importing handler
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

from lambdas.agent_orchestrator import handler as orchestrator_handler


def test_startup_env_validator_reports_missing_required_vars():
    with patch.dict(os.environ, {
        'LAMBDA_WEATHER': '',
        'LAMBDA_CROP': '',
        'LAMBDA_SCHEMES': '',
        'LAMBDA_PROFILE': '',
    }, clear=False):
        with patch.object(orchestrator_handler, 'logger') as mock_logger:
            missing = orchestrator_handler._validate_required_env_vars()

    assert set(missing) == {
        'LAMBDA_WEATHER',
        'LAMBDA_CROP',
        'LAMBDA_SCHEMES',
        'LAMBDA_PROFILE',
    }
    assert mock_logger.error.called


def test_startup_env_validator_passes_when_required_vars_present():
    with patch.dict(os.environ, {
        'LAMBDA_WEATHER': 'weather-fn',
        'LAMBDA_CROP': 'crop-fn',
        'LAMBDA_SCHEMES': 'schemes-fn',
        'LAMBDA_PROFILE': 'profile-fn',
    }, clear=False):
        with patch.object(orchestrator_handler, 'logger') as mock_logger:
            missing = orchestrator_handler._validate_required_env_vars()

    assert missing == []
    assert not mock_logger.error.called
