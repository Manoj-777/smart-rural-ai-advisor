import importlib
import os
import sys
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _reload_response_helper():
    import utils.response_helper as response_helper
    return importlib.reload(response_helper)


def test_success_response_allows_configured_origin():
    with patch.dict(os.environ, {'ALLOWED_ORIGIN': 'https://allowed.example.com'}):
        response_helper = _reload_response_helper()
        response = response_helper.success_response({'ok': True}, origin='https://allowed.example.com')

    assert response['statusCode'] == 200
    assert response['headers']['Access-Control-Allow-Origin'] == 'https://allowed.example.com'


def test_success_response_rejects_unauthorized_origin_with_403():
    with patch.dict(os.environ, {'ALLOWED_ORIGIN': 'https://allowed.example.com'}):
        response_helper = _reload_response_helper()
        response = response_helper.success_response({'ok': True}, origin='https://evil.example.com')

    assert response['statusCode'] == 403
    assert 'Access-Control-Allow-Origin' not in response['headers']


def test_error_response_rejects_unauthorized_origin_with_403():
    with patch.dict(os.environ, {'ALLOWED_ORIGIN': 'https://allowed.example.com'}):
        response_helper = _reload_response_helper()
        response = response_helper.error_response('some error', 500, origin='https://evil.example.com')

    assert response['statusCode'] == 403
    assert 'Access-Control-Allow-Origin' not in response['headers']


def test_success_response_without_origin_preserves_default_behavior():
    with patch.dict(os.environ, {'ALLOWED_ORIGIN': 'https://allowed.example.com'}):
        response_helper = _reload_response_helper()
        response = response_helper.success_response({'ok': True})

    assert response['statusCode'] == 200
    assert response['headers']['Access-Control-Allow-Origin'] == 'https://allowed.example.com'
