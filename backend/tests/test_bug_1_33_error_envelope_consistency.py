import os
import sys
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.farmer_profile import handler as farmer_profile_handler


def test_lambda_handler_missing_farmer_id_uses_canonical_error_envelope():
    event = {
        'httpMethod': 'GET',
        'path': '/profile',
        'pathParameters': {},
    }

    response = farmer_profile_handler.lambda_handler(event, None)

    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['status'] == 'error'
    assert body['data'] is None
    assert body['message'] == 'Missing farmerId in path'
    assert body['language'] == 'en'
    assert body['error'] == 'Missing farmerId in path'


def test_verify_otp_invalid_format_uses_canonical_error_envelope():
    response = farmer_profile_handler.verify_otp({'phone': '9876543210', 'otp': '12'})

    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['status'] == 'error'
    assert body['data'] is None
    assert body['message'] == 'Invalid OTP format. Must be 6 digits.'
    assert body['language'] == 'en'
    assert body['error'] == 'Invalid OTP format. Must be 6 digits.'
