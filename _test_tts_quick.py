"""Quick test: just the generate_tts endpoint (skips slow soil analysis)."""
import json, requests, time

url = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/chat'

# Test the generate_tts fast path directly
print('TEST: generate_tts endpoint (Tamil)')
payload = {
    'generate_tts': True,
    'tts_text': 'வணக்கம்! இது ஒரு சோதனை செய்தி. உங்கள் மண் பகுப்பாய்வு முடிவுகள் தயாராக உள்ளன.',
    'tts_language': 'ta'
}
t0 = time.time()
r = requests.post(url, json=payload, timeout=60)
t1 = time.time()
d = r.json()
print(f'Status: {r.status_code} | Time: {t1-t0:.1f}s')
print(f'Response: {json.dumps(d, indent=2, ensure_ascii=False)[:500]}')
