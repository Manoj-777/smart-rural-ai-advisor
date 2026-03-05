"""
Bug 1.7 Unit Tests: Coordinate validation in weather lookup.
"""

import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.weather_lookup.handler import lambda_handler


def _event(location='Chennai', lat=None, lon=None):
    qsp = {}
    if lat is not None:
        qsp['lat'] = lat
    if lon is not None:
        qsp['lon'] = lon

    return {
        'httpMethod': 'GET',
        'pathParameters': {'location': location},
        'queryStringParameters': qsp,
        'headers': {},
    }


def test_coordinate_validation_enabled_returns_400_for_invalid_range():
    with patch.dict(os.environ, {'ENABLE_COORDINATE_VALIDATION': 'true'}):
        with patch('lambdas.weather_lookup.handler.OPENWEATHER_API_KEY', 'dummy'):
            response = lambda_handler(_event(lat='100', lon='77'), None)

    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Invalid latitude' in body.get('message', '') or 'Invalid latitude' in body.get('error', '')


def test_coordinate_validation_disabled_preserves_legacy_flow():
    # With validation OFF, invalid coords are dropped and normal flow continues to provider path.
    with patch.dict(os.environ, {'ENABLE_COORDINATE_VALIDATION': 'false'}):
        with patch('lambdas.weather_lookup.handler.OPENWEATHER_API_KEY', 'dummy'):
            with patch('lambdas.weather_lookup.handler._http_get_json', return_value={'cod': 404, 'message': 'city not found'}):
                response = lambda_handler(_event(lat='100', lon='77'), None)

    assert response['statusCode'] in (404, 502)
