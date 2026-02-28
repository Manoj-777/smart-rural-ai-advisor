"""Verify all backend API endpoints are properly connected."""
import urllib.request, json

BASE = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod'

def test(name, url, method='GET', body=None):
    try:
        req = urllib.request.Request(url, method=method)
        if body:
            req.data = json.dumps(body).encode()
            req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            keys = list(data.keys())[:4]
            print(f'  ✅ {name}: {r.status} OK — keys={keys}')
            return data
    except Exception as e:
        print(f'  ❌ {name}: ERROR — {e}')
        return None

print('=== API Connectivity Check ===\n')

test('Health', f'{BASE}/health')
test('Profile GET', f'{BASE}/profile/ph_1234567890')
test('Weather GET', f'{BASE}/weather/Thanjavur')
test('Schemes GET', f'{BASE}/schemes?state=Tamil+Nadu')
test('Crop Advisory POST', f'{BASE}/crop-advisory', 'POST', {'query': 'rice pest management', 'language': 'en-IN'})

print('\n--- Chat (4-agent pipeline) ---')
chat = test('Chat POST', f'{BASE}/chat', 'POST', {'message': 'hello', 'language': 'en-IN', 'farmer_id': 'ph_test'})
if chat:
    reply_len = len(chat.get('reply', ''))
    stages = list(chat.get('pipeline_metadata', {}).get('stages', {}).keys())
    print(f'     reply_len={reply_len}, stages={stages}')

# Profile PUT
print('\n--- Profile Write ---')
test('Profile PUT', f'{BASE}/profile/ph_test_verify', 'PUT', {
    'name': 'Test Farmer', 'state': 'Tamil Nadu', 'district': 'Thanjavur',
    'crops': ['Rice'], 'soil_type': 'Alluvial', 'land_size_acres': 2.5, 'language': 'ta-IN'
})

print('\n=== All checks done ===')
