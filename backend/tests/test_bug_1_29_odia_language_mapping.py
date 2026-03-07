import os
import sys
import io
import json
import base64
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.transcribe_speech import handler as transcribe_handler


def _build_event(language_code):
    audio_b64 = base64.b64encode(b'fake-audio-bytes').decode('ascii')
    return {
        'body': json.dumps({
            'audio': audio_b64,
            'language': language_code,
            'format': 'audio/webm',
        })
    }


def _run_handler_and_get_language_code(language_code):
    event = _build_event(language_code)

    with patch.object(transcribe_handler, 's3') as mock_s3, patch.object(transcribe_handler, 'transcribe') as mock_transcribe:
        mock_s3.put_object = Mock()
        mock_s3.get_object = Mock(return_value={
            'Body': io.BytesIO(json.dumps({'results': {'transcripts': [{'transcript': 'hello farmer'}]}}).encode('utf-8'))
        })
        mock_s3.delete_object = Mock()

        mock_transcribe.start_transcription_job = Mock()
        mock_transcribe.get_transcription_job = Mock(return_value={
            'TranscriptionJob': {'TranscriptionJobStatus': 'COMPLETED'}
        })

        response = transcribe_handler.lambda_handler(event, None)

        assert response['statusCode'] == 200
        kwargs = mock_transcribe.start_transcription_job.call_args.kwargs
        return kwargs['LanguageCode']


def test_odia_maps_to_or_in_for_transcribe_job():
    language_code = _run_handler_and_get_language_code('or-IN')

    assert language_code == 'or-IN'


def test_tamil_mapping_remains_unchanged():
    language_code = _run_handler_and_get_language_code('ta-IN')

    assert language_code == 'ta-IN'


def test_unsupported_language_still_falls_back_to_hindi():
    language_code = _run_handler_and_get_language_code('as-IN')

    assert language_code == 'hi-IN'
