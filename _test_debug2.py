import json, time, urllib.request
API = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod'

payload = json.dumps({'message': 'What is PM Kisan scheme?', 'session_id': 'chat-hindi-debug3', 'language': 'hi'}).encode()
req = urllib.request.Request(f'{API}/chat', data=payload, headers={'Content-Type': 'application/json'})
t0 = time.time()
with urllib.request.urlopen(req, timeout=35) as resp:
    raw = resp.read()
elapsed = time.time() - t0
data = json.loads(raw)
print(f'Time: {elapsed:.1f}s')
print(f'Top-level keys: {list(data.keys())}')
inner = data.get('data', data)
print(f'Inner keys: {list(inner.keys())}')
print(f'Reply ({len(inner.get("reply", ""))} chars): {inner.get("reply", "")[:200]}')
print(f'Audio URL: {inner.get("audio_url")}')
print(f'Detected language: {inner.get("detected_language")}')
print(f'Pipeline mode: {inner.get("pipeline_mode")}')
print(f'Tools used: {inner.get("tools_used")}')
