import json, time, urllib.request
API = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod'

# Quick test: Hindi chat (should have audio via Polly)
payload = json.dumps({'message': 'What is PM Kisan scheme?', 'session_id': 'chat-hindi-debug2', 'language': 'hi'}).encode()
req = urllib.request.Request(f'{API}/chat', data=payload, headers={'Content-Type': 'application/json'})
t0 = time.time()
with urllib.request.urlopen(req, timeout=35) as resp:
    raw = resp.read()
elapsed = time.time() - t0
data = json.loads(raw)
print(f'Time: {elapsed:.1f}s')
print(f'Top-level keys: {list(data.keys())}')
if 'body' in data:
    body = json.loads(data['body']) if isinstance(data['body'], str) else data['body']
    print(f'Body keys: {list(body.keys())}')
    if 'data' in body:
        inner = body['data']
        print(f'Data keys: {list(inner.keys())}')
        print(f'Reply ({len(inner.get("reply", ""))} chars): {inner.get("reply", "")[:150]}...')
        print(f'Audio URL present: {bool(inner.get("audio_url"))}')
        if inner.get('audio_url'):
            print(f'Audio URL: {inner["audio_url"][:100]}')
    else:
        print(f'Reply: {body.get("reply", "")[:150]}')
        print(f'Audio: {body.get("audio_url")}')
else:
    print(f'Reply: {data.get("reply", "")[:150]}')
    print(f'Audio: {data.get("audio_url")}')
