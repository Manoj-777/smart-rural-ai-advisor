import os
import sys
import importlib
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_language_validation_logging_for_invalid_code():
    from utils import translate_helper

    with patch.dict(os.environ, {'ENABLE_LANGUAGE_VALIDATION_LOGGING': 'true'}):
        with patch.object(translate_helper, 'logger') as mock_logger:
            normalized = translate_helper.normalize_language_code('xx-INVALID', default='en')

    assert normalized == 'en'
    assert mock_logger.warning.called


def test_tts_list_formatting_rewrites_numbered_items():
    from utils import polly_helper

    text = "1. Apply neem oil\n2. Check leaves daily"
    with patch.dict(os.environ, {'ENABLE_TTS_LIST_FORMATTING': 'true'}):
        output = polly_helper._strip_markdown_for_tts(text)

    assert 'First, Apply neem oil' in output
    assert 'Second, Check leaves daily' in output


def test_weather_https_flag_keeps_https_scheme():
    from lambdas.weather_lookup import handler as weather_handler

    with patch.dict(os.environ, {'ENABLE_HTTPS_WEATHER_API': 'true'}):
        base = weather_handler._openweather_base_url()

    assert base.startswith('https://')


def test_profile_cache_returns_cached_item():
    from utils import dynamodb_helper

    fake_item = {'farmer_id': 'f-123', 'name': 'Farmer'}
    dynamodb_helper._profile_cache.clear()

    with patch.dict(os.environ, {'ENABLE_PROFILE_CACHE': 'true', 'PROFILE_CACHE_TTL_SEC': '120'}):
        with patch.object(dynamodb_helper, 'profiles_table') as mock_table:
            mock_table.get_item.return_value = {'Item': fake_item}
            first = dynamodb_helper.get_farmer_profile('f-123')
            second = dynamodb_helper.get_farmer_profile('f-123')

    assert first == fake_item
    assert second == fake_item
    assert mock_table.get_item.call_count == 1


def test_chat_batch_write_uses_batch_writer_when_enabled():
    from utils import dynamodb_helper

    messages = [
        {'session_id': 's1', 'role': 'user', 'message': 'hello', 'language': 'en'},
        {'session_id': 's1', 'role': 'assistant', 'message': 'hi', 'language': 'en'},
    ]

    writer = Mock()
    writer_cm = Mock()
    writer_cm.__enter__ = Mock(return_value=writer)
    writer_cm.__exit__ = Mock(return_value=False)

    with patch.dict(os.environ, {'ENABLE_BATCH_CHAT_WRITES': 'true', 'ENABLE_CHAT_IDEMPOTENCY': 'false'}):
        with patch.object(dynamodb_helper, 'sessions_table') as mock_sessions:
            mock_sessions.batch_writer.return_value = writer_cm
            ok = dynamodb_helper.save_chat_messages_batch(messages)

    assert ok is True
    assert writer.put_item.call_count == 2


def test_unified_cors_preflight_uses_shared_middleware_when_enabled():
    from lambdas.weather_lookup import handler as weather_handler

    with patch.dict(os.environ, {'ENABLE_UNIFIED_CORS': 'true'}):
        weather_handler = importlib.reload(weather_handler)
        response = weather_handler.lambda_handler({'httpMethod': 'OPTIONS', 'headers': {'Origin': 'https://example.com'}}, None)

    assert response['statusCode'] == 200
    assert response['body'] == ''
    assert response['headers']['Access-Control-Allow-Methods'] == 'GET,POST,OPTIONS'
