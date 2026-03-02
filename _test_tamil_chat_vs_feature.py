import json, time, urllib.request
API = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod'

# Test Tamil chat - should attempt gTTS if within time budget
payload = json.dumps({'message': 'What government schemes help small farmers?', 'session_id': 'chat-tamil-debug3', 'language': 'ta'}).encode()
req = urllib.request.Request(f'{API}/chat', data=payload, headers={'Content-Type': 'application/json'})
t0 = time.time()
with urllib.request.urlopen(req, timeout=35) as resp:
    raw = resp.read()
elapsed = time.time() - t0
data = json.loads(raw)
inner = data.get('data', data)
print(f'Time: {elapsed:.1f}s')
print(f'Reply ({len(inner.get("reply", ""))} chars): {inner.get("reply", "")[:200]}')
print(f'Audio URL: {"YES" if inner.get("audio_url") else "NO"}')
print(f'Detected language: {inner.get("detected_language")}')
print(f'Pipeline: {inner.get("pipeline_mode")}')

# Test Tamil crop-recommend - should be fast with NO audio
print("\n--- Tamil CropRecommend (feature page) ---")
payload2 = json.dumps({'message': 'Best crop for red soil in Tamil Nadu summer?', 'session_id': 'crop-recommend-tamil-debug3', 'language': 'ta'}).encode()
req2 = urllib.request.Request(f'{API}/chat', data=payload2, headers={'Content-Type': 'application/json'})
t0 = time.time()
with urllib.request.urlopen(req2, timeout=35) as resp:
    raw = resp.read()
elapsed = time.time() - t0
data2 = json.loads(raw)
inner2 = data2.get('data', data2)
print(f'Time: {elapsed:.1f}s')
print(f'Reply ({len(inner2.get("reply", ""))} chars): {inner2.get("reply", "")[:200]}')
print(f'Audio URL: {"YES" if inner2.get("audio_url") else "NO (correct for feature page)"}')
