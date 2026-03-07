import os
import sys
import json
from types import SimpleNamespace

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.farmer_profile import handler as farmer_profile_handler


def _valid_profile_payload():
    return {
        'name': 'Test Farmer',
        'state': 'Tamil Nadu',
        'district': 'Coimbatore',
        'crops': ['Rice'],
        'soil_type': 'Alluvial',
        'land_size_acres': 2,
        'language': 'en-IN',
    }


def test_put_profile_rejects_empty_state(monkeypatch):
    monkeypatch.setattr(farmer_profile_handler, '_find_conflicting_profile_ids', lambda *_args, **_kwargs: [])

    body = _valid_profile_payload()
    body['state'] = '   '

    response = farmer_profile_handler.put_profile('ph_9876543210', body)

    assert response['statusCode'] == 400
    payload = json.loads(response['body'])
    assert payload['status'] == 'error'
    assert payload['message'] == 'State is required'


def test_put_profile_rejects_empty_district(monkeypatch):
    monkeypatch.setattr(farmer_profile_handler, '_find_conflicting_profile_ids', lambda *_args, **_kwargs: [])

    body = _valid_profile_payload()
    body['district'] = ''

    response = farmer_profile_handler.put_profile('ph_9876543210', body)

    assert response['statusCode'] == 400
    payload = json.loads(response['body'])
    assert payload['status'] == 'error'
    assert payload['message'] == 'District is required'


def test_put_profile_accepts_when_state_and_district_present(monkeypatch):
    monkeypatch.setattr(farmer_profile_handler, '_find_conflicting_profile_ids', lambda *_args, **_kwargs: [])

    calls = {'count': 0}

    def _update_item(**_kwargs):
        calls['count'] += 1
        return {}

    monkeypatch.setattr(farmer_profile_handler, 'table', SimpleNamespace(update_item=_update_item))

    response = farmer_profile_handler.put_profile('ph_9876543210', _valid_profile_payload())

    assert response['statusCode'] == 200
    assert calls['count'] == 1
