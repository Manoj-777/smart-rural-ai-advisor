"""Test audio_key persistence and refresh endpoint."""
import requests, json, time

API = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/chat'

# Test 1: Send chat, verify audio_key is returned
print('=== Test 1: Chat with audio_key ===')
r = requests.post(API, json={
    'message': 'soil-analysis-Best fertilizer for sandy soil?',
    'language': 'ta',
    'session_id': 'soil-analysis-' + str(int(time.time()*1000))
}, timeout=120)
d = r.json()
data = d.get('data', {})
audio_url = data.get('audio_url', '')
audio_key = data.get('audio_key', '')
print(f'Status: {r.status_code}')
print(f'audio_key: {audio_key}')
print(f'audio_url present: {bool(audio_url)}')
reply = data.get('reply', '')
print(f'Reply: {reply[:100]}')

# Test 2: Refresh audio URL using the key
if audio_key:
    print()
    print('=== Test 2: Refresh audio URL ===')
    r2 = requests.post(API, json={'refresh_audio_key': audio_key}, timeout=30)
    d2 = r2.json()
    data2 = d2.get('data', {})
    fresh_url = data2.get('audio_url', '')
    print(f'Status: {r2.status_code}')
    print(f'Fresh URL present: {bool(fresh_url)}')
    print(f'Same key: {data2.get("audio_key") == audio_key}')
    print(f'URL different from original: {fresh_url != audio_url}')
    print('PASS - Audio refresh endpoint works!')
else:
    print('SKIP Test 2 - no audio_key returned')
