import os
import sys
import types
import importlib
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _load_orchestrator_handler_with_stubbed_chat_history():
    fake_chat_history = types.ModuleType('utils.chat_history')
    fake_chat_history.list_sessions = lambda *args, **kwargs: []
    fake_chat_history.get_session_messages = lambda *args, **kwargs: []
    fake_chat_history.save_session = lambda *args, **kwargs: True
    fake_chat_history.delete_session = lambda *args, **kwargs: True
    fake_chat_history.rename_session = lambda *args, **kwargs: True

    fake_response_cache = types.ModuleType('utils.response_cache')
    fake_response_cache.get_cached_response = lambda *args, **kwargs: None
    fake_response_cache.cache_response = lambda *args, **kwargs: None

    with patch.dict(sys.modules, {
        'utils.chat_history': fake_chat_history,
        'utils.response_cache': fake_response_cache,
    }):
        module = importlib.import_module('lambdas.agent_orchestrator.handler')
        return importlib.reload(module)


def test_local_language_preserves_indentation_and_avoids_heading_auto_numbering():
    orchestrator_handler = _load_orchestrator_handler_with_stubbed_chat_history()

    text = (
        "### முதல் தலைப்பு\n"
        "### இரண்டாம் தலைப்பு\n"
        "### மூன்றாம் தலைப்பு\n"
        "  - உள்ளீடு ஒன்று\n"
        "    1) உள்ளீடு இரண்டு"
    )

    output = orchestrator_handler._strip_local_markdown_symbols(text, 'ta')
    lines = output.split('\n')

    assert lines[0] == 'முதல் தலைப்பு'
    assert lines[1] == 'இரண்டாம் தலைப்பு'
    assert lines[2] == 'மூன்றாம் தலைப்பு'
    assert lines[3] == '  - உள்ளீடு ஒன்று'
    assert lines[4] == '    1. உள்ளீடு இரண்டு'


def test_english_heading_auto_numbering_remains_enabled():
    orchestrator_handler = _load_orchestrator_handler_with_stubbed_chat_history()

    text = "### One\n### Two\n### Three"
    output = orchestrator_handler._strip_local_markdown_symbols(text, 'en')

    assert output.split('\n') == ['1. One', '2. Two', '3. Three']


def test_tts_local_language_keeps_numeric_points_when_list_formatting_enabled():
    from utils import polly_helper

    with patch.dict(os.environ, {'ENABLE_TTS_LIST_FORMATTING': 'true'}):
        output = polly_helper._strip_markdown_for_tts("1. முதல் படி\n2. இரண்டாம் படி")

    assert output.split('\n') == ['1. முதல் படி', '2. இரண்டாம் படி']


def test_tts_english_still_uses_ordinals_when_enabled():
    from utils import polly_helper

    with patch.dict(os.environ, {'ENABLE_TTS_LIST_FORMATTING': 'true'}):
        output = polly_helper._strip_markdown_for_tts("1. First step\n2. Second step")

    assert output.split('\n') == ['First, First step', 'Second, Second step']


def test_hindi_danda_numbering_is_normalized_to_markdown_points():
    orchestrator_handler = _load_orchestrator_handler_with_stubbed_chat_history()

    text = "1। कपास\n2। सूरजमुखी\n3। तिल"
    output = orchestrator_handler._strip_local_markdown_symbols(text, 'hi')

    assert output.split('\n') == ['1. कपास', '2. सूरजमुखी', '3. तिल']


def test_urdu_fullstop_numbering_is_normalized_to_markdown_points():
    orchestrator_handler = _load_orchestrator_handler_with_stubbed_chat_history()

    text = "1۔ کپاس\n2۔ گندم"
    output = orchestrator_handler._strip_local_markdown_symbols(text, 'ur')

    assert output.split('\n') == ['1. کپاس', '2. گندم']


def test_repeated_hindi_number_marker_is_renumbered_sequentially():
    orchestrator_handler = _load_orchestrator_handler_with_stubbed_chat_history()

    text = "1। कपास\n1। सूरजमुखी\n1। तिल"
    output = orchestrator_handler._strip_local_markdown_symbols(text, 'hi')

    assert output.split('\n') == ['1. कपास', '2. सूरजमुखी', '3. तिल']


def test_repeated_english_number_marker_is_renumbered_sequentially():
    orchestrator_handler = _load_orchestrator_handler_with_stubbed_chat_history()

    text = "1. Cotton\n1. Sunflower\n1. Sesame"
    output = orchestrator_handler._strip_local_markdown_symbols(text, 'en')

    assert output.split('\n') == ['1. Cotton', '2. Sunflower', '3. Sesame']
