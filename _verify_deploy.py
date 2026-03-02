"""Quick verification of the deployed site and API."""
import requests
import time

API = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod'
CF = 'https://d80ytlzsrax1n.cloudfront.net'

print('=== 1. Health Check ===')
r = requests.get(f'{API}/health', timeout=10)
print(f'  Status: {r.status_code} - {r.json()}')

print()
print('=== 2. CloudFront site ===')
r = requests.get(CF, timeout=10)
print(f'  Status: {r.status_code}, Content-Length: {len(r.text)} bytes')
has_react = 'root' in r.text
print(f'  Has React app: {has_react}')

print()
print('=== 3. GET /schemes ===')
start = time.time()
r = requests.get(f'{API}/schemes', timeout=15)
print(f'  Status: {r.status_code} ({time.time()-start:.1f}s)')

print()
print('=== 4. Chat (English test) ===')
start = time.time()
r = requests.post(f'{API}/chat',
    json={'message': 'What crops grow in Tamil Nadu?', 'language': 'en-IN', 'session_id': 'verify-test'},
    timeout=35)
elapsed = time.time() - start
print(f'  Status: {r.status_code} ({elapsed:.1f}s)')
if r.status_code == 200:
    d = r.json().get('data', {})
    reply = d.get('reply', '')
    print(f'  Reply: {reply[:200]}...')
else:
    print(f'  Error: {r.text[:200]}')

print()
print('=== All checks complete ===')
