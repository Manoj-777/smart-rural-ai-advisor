"""
Bug 1.5 Unit Tests: Thread-safe parallel tool execution.

Validates:
- Requirement 2.5 (thread-safe mutations for parallel tool execution)
- Requirement 3.17 (parallel execution behavior preserved)
"""

import os
import sys
import time
import random
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock optional modules used during handler import
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

from lambdas.agent_orchestrator.handler import _invoke_bedrock_direct


def _tool_use_response(tool_count=5):
    blocks = []
    for index in range(tool_count):
        blocks.append(
            {
                'toolUse': {
                    'toolUseId': f'tool-{index + 1}',
                    'name': f'tool_{index + 1}',
                    'input': {'index': index + 1},
                }
            }
        )
    return {
        'output': {'message': {'role': 'assistant', 'content': blocks}},
        'stopReason': 'tool_use',
    }


def _final_response():
    return {
        'output': {
            'message': {
                'role': 'assistant',
                'content': [{'text': 'Done'}],
            }
        },
        'stopReason': 'end_turn',
    }


def _mock_tool_execution(tool_name, tool_input):
    time.sleep(random.uniform(0.001, 0.02))
    return {'tool': tool_name, 'ok': True, 'index': tool_input.get('index')}


def test_thread_safe_tools_enabled_parallel_lists_have_all_entries():
    responses = [_tool_use_response(10), _final_response()]

    with patch.dict(
        os.environ,
        {
            'ENABLE_THREAD_SAFE_TOOLS': 'true',
            'ENABLE_TOOL_TIMEOUT': 'false',
            'FOUNDATION_MODEL': 'test-model',
        },
    ):
        with patch('lambdas.agent_orchestrator.handler._bedrock_converse_with_retry', side_effect=responses), \
             patch('lambdas.agent_orchestrator.handler._execute_tool', side_effect=_mock_tool_execution):
            result_text, tools_used, tool_data_log, _ = _invoke_bedrock_direct(
                prompt='Run all tools',
                model_id='test-model',
            )

    assert result_text == 'Done'
    assert len(tools_used) == 10
    assert len(tool_data_log) == 10
    assert len({entry['tool'] for entry in tool_data_log}) == 10


def test_thread_safe_tools_disabled_preserves_parallel_behavior():
    responses = [_tool_use_response(3), _final_response()]

    with patch.dict(
        os.environ,
        {
            'ENABLE_THREAD_SAFE_TOOLS': 'false',
            'ENABLE_TOOL_TIMEOUT': 'false',
            'FOUNDATION_MODEL': 'test-model',
        },
    ):
        with patch('lambdas.agent_orchestrator.handler._bedrock_converse_with_retry', side_effect=responses), \
             patch('lambdas.agent_orchestrator.handler._execute_tool', side_effect=_mock_tool_execution):
            result_text, tools_used, tool_data_log, _ = _invoke_bedrock_direct(
                prompt='Run selected tools',
                model_id='test-model',
            )

    assert result_text == 'Done'
    assert len(tools_used) == 3
    assert len(tool_data_log) == 3
