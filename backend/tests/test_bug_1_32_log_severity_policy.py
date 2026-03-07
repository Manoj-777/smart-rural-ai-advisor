import os
import sys
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock optional modules before importing handler
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

from lambdas.agent_orchestrator import handler as orchestrator_handler


def test_invalid_model_override_logs_info_not_warning():
    with patch.dict(os.environ, {'ENABLE_MODEL_VALIDATION': 'true'}):
        with patch.object(orchestrator_handler, 'logger') as mock_logger:
            selected = orchestrator_handler._validated_model_id('invalid-model-id')

    assert selected == orchestrator_handler.FOUNDATION_MODEL
    assert mock_logger.info.called
    assert not mock_logger.warning.called


def test_runtime_passthrough_logs_info_not_warning():
    with patch.object(orchestrator_handler, 'logger') as mock_logger:
        with patch.object(orchestrator_handler, 'ENFORCE_CODE_POLICY', True):
            text, _, _ = orchestrator_handler._apply_code_policy(
                user_query_en='what is weather',
                intents=['weather'],
                result_text='Runtime initialization in progress, please try again in a minute.',
                tools_used=[],
            )

    assert 'Runtime initialization' in text
    assert mock_logger.info.called
    assert not mock_logger.warning.called
