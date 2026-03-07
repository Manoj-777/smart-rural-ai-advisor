import os
import sys
import json
import base64
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.image_analysis import handler as image_handler


def _event_with_image(image_base64):
    return {
        'body': json.dumps({
            'image_base64': image_base64,
            'crop_name': 'paddy',
            'state': 'Tamil Nadu',
            'language': 'en',
        })
    }


def test_detect_media_type_unknown_signature_is_rejected():
    unknown_base64 = base64.b64encode(b'NOT_AN_IMAGE_PAYLOAD').decode('ascii')

    media_type = image_handler.detect_media_type(unknown_base64)

    assert media_type is None


def test_detect_media_type_preserves_known_signatures():
    assert image_handler.detect_media_type('/9j/abc') == 'image/jpeg'
    assert image_handler.detect_media_type('iVBORw0KGgoXYZ') == 'image/png'
    assert image_handler.detect_media_type('R0lGODfoo') == 'image/gif'
    assert image_handler.detect_media_type('UklGRbar') == 'image/webp'


def test_lambda_handler_returns_400_for_unknown_signature():
    unknown_base64 = base64.b64encode(b'NOT_AN_IMAGE_PAYLOAD').decode('ascii')
    event = _event_with_image(unknown_base64)

    with patch.object(image_handler, 'bedrock') as mock_bedrock:
        mock_bedrock.converse = Mock()
        response = image_handler.lambda_handler(event, None)

    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'unsupported' in body['error'].lower() or 'invalid' in body['error'].lower()
    assert not mock_bedrock.converse.called
