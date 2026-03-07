import os
import sys
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.govt_schemes import handler as schemes_handler


def _response_data(response):
    assert response['statusCode'] == 200
    payload = json.loads(response['body'])
    assert payload['status'] == 'success'
    return payload['data']


def test_farmer_state_filters_state_schemes_to_requested_state():
    event = {
        'queryStringParameters': {
            'name': 'all',
            'farmer_state': 'Tamil Nadu',
        }
    }

    data = _response_data(schemes_handler.lambda_handler(event, None))

    assert 'pm_kisan' in data['schemes']
    assert list(data['state_schemes'].keys()) == ['Tamil Nadu']


def test_farmer_state_filter_is_case_insensitive():
    event = {
        'queryStringParameters': {
            'name': 'all',
            'farmer_state': 'tamil nadu',
        }
    }

    data = _response_data(schemes_handler.lambda_handler(event, None))

    assert list(data['state_schemes'].keys()) == ['Tamil Nadu']


def test_no_farmer_state_preserves_full_state_schemes_listing():
    event = {
        'queryStringParameters': {
            'name': 'all',
        }
    }

    data = _response_data(schemes_handler.lambda_handler(event, None))

    assert 'Tamil Nadu' in data['state_schemes']
    assert 'Karnataka' in data['state_schemes']
    assert len(data['state_schemes']) > 1
