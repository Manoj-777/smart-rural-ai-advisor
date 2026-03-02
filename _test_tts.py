"""Quick test: soil analysis in Tamil — verifies gTTS audio generation."""
import requests, json, time

API = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/chat'

payload = {
    'message': 'soil-analysis-What is the best fertilizer for clay soil with low nitrogen?',
    'language': 'ta',
    'session_id': f'soil-analysis-{int(time.time()*1000)}'
}

print(f'Testing Tamil soil analysis with session_id={payload["session_id"]}...')
r = requests.post(API, json=payload, timeout=120)
d = r.json()
data = d.get('data', d)  # handle both nested and flat responses

print(f'Status: {r.status_code}')
print(f'Feature page: {data.get("policy", {}).get("feature_page")}')
print(f'Audio URL: {data.get("audio_url", "NONE")}')
print(f'Tools used: {data.get("tools_used", [])}')
print(f'Reply (first 300 chars): {data.get("reply", "")[:300]}')
