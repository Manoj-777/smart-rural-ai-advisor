"""
Targeted tests for HIGH severity utility fixes:
- Bug 1.8 translation chunking
- Bug 1.10 chat pagination
- Bug 1.11 extended audio expiry
"""

import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.agent_orchestrator.utils import translate_helper, dynamodb_helper, polly_helper


def test_translation_chunking_splits_long_text_when_enabled():
    long_text = ('This is a long line for translation. ' * 1200).strip()

    def fake_translate_text(Text, SourceLanguageCode, TargetLanguageCode):
        # Return Devanagari text so localization quality checks pass.
        return {'TranslatedText': 'अ' * max(50, min(500, len(Text) // 4))}

    with patch.dict(
        os.environ,
        {
            'ENABLE_TRANSLATION_CHUNKING': 'true',
            'TRANSLATE_MAX_BYTES': '500',
        },
    ):
        with patch.object(translate_helper.translate, 'translate_text', side_effect=fake_translate_text) as mocked:
            out = translate_helper.translate_response(long_text, source_language='en', target_language='hi')

    assert out
    assert mocked.call_count > 1


def test_chat_history_pagination_fetches_multiple_pages_when_enabled():
    page_1 = {
        'Items': [
            {'session_id': 's1', 'timestamp': '2026-01-01T00:00:03', 'message': 'm3'},
            {'session_id': 's1', 'timestamp': '2026-01-01T00:00:02', 'message': 'm2'},
        ],
        'LastEvaluatedKey': {'session_id': 's1', 'timestamp': '2026-01-01T00:00:02'},
    }
    page_2 = {
        'Items': [
            {'session_id': 's1', 'timestamp': '2026-01-01T00:00:01', 'message': 'm1'},
        ]
    }

    with patch.dict(os.environ, {'ENABLE_CHAT_PAGINATION': 'true'}):
        with patch.object(dynamodb_helper.sessions_table, 'query', side_effect=[page_1, page_2]) as mocked_query:
            items = dynamodb_helper.get_chat_history('s1', limit=3)

    assert mocked_query.call_count == 2
    # Returned oldest -> newest
    assert [item['message'] for item in items] == ['m1', 'm2', 'm3']


def test_extended_audio_expiry_uses_7200_seconds_when_enabled():
    with patch.dict(os.environ, {'ENABLE_EXTENDED_AUDIO_EXPIRY': 'true'}):
        with patch.object(polly_helper.s3, 'put_object'):
            with patch.object(polly_helper.s3, 'generate_presigned_url', return_value='https://example.com/audio.mp3') as mocked_url:
                result = polly_helper._upload_audio_bytes(b'audio-bytes')

    assert result['url'].startswith('https://')
    assert result['key'].startswith('audio/')
    assert mocked_url.call_args.kwargs['ExpiresIn'] == 7200
