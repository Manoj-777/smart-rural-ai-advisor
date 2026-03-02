"""Test async TTS flow: main request returns text fast, then separate TTS call."""
import json, requests, time

url = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/chat'

# --- Test 1: Main Tamil soil analysis request (should return fast, audio_pending=true) ---
print('='*60)
print('TEST 1: Tamil soil analysis (main request)')
print('='*60)
payload = {
    'message': (
        'Analyze the following soil test data and provide a detailed agricultural '
        'soil health report for an Indian farmer.\n\n'
        'Soil Data:\n'
        '- pH Level: 5.5 - 6.5 (Slightly Acidic)\n'
        '- Nitrogen (N): Low\n'
        '- Phosphorus (P): Medium\n'
        '- Potassium (K): Medium\n'
        '- Soil Color/Appearance: Dark Brown/Black\n'
        '- Water Drainage: Drains in few hours\n'
        '- Target Crop: Pulses (Dal varieties)\n'
        '- Location: India\n\n'
        'Provide these sections:\n'
        '1. Soil Health Rating\n'
        '2. Key Issues Found\n'
        '3. Fertilizer Recommendation\n'
        '4. Organic Amendments\n'
        '5. 3-Month Soil Improvement Plan\n'
        '6. Best Crops for This Soil\n'
        '7. Warning Signs to Watch\n'
        '8. Estimated Cost'
    ),
    'session_id': 'soil-analysis-' + str(int(time.time() * 1000)),
    'farmer_id': 'test-farmer',
    'language': 'ta'
}

t0 = time.time()
r = requests.post(url, json=payload, timeout=60)
t1 = time.time()
data = r.json()

print(f'Status: {r.status_code} | Time: {t1-t0:.1f}s')
print(f'Response status: {data.get("status")}')
if data.get('status') == 'success':
    d = data['data']
    print(f'Reply length: {len(d.get("reply", ""))}')
    print(f'audio_url present: {bool(d.get("audio_url"))}')
    print(f'audio_key: {d.get("audio_key")}')
    print(f'audio_pending: {d.get("audio_pending")}')
    print(f'detected_language: {d.get("detected_language")}')
    
    # --- Test 2: Async TTS call (should generate full audio) ---
    if d.get('audio_pending'):
        print()
        print('='*60)
        print('TEST 2: Async TTS generation')
        print('='*60)
        tts_payload = {
            'generate_tts': True,
            'tts_text': d['reply'],
            'tts_language': d.get('detected_language', 'ta')
        }
        t2 = time.time()
        r2 = requests.post(url, json=tts_payload, timeout=60)
        t3 = time.time()
        data2 = r2.json()
        print(f'Status: {r2.status_code} | Time: {t3-t2:.1f}s')
        print(f'Response status: {data2.get("status")}')
        if data2.get('status') == 'success':
            print(f'audio_url present: {bool(data2["data"].get("audio_url"))}')
            print(f'audio_key: {data2["data"].get("audio_key")}')
            print(f'truncated: {data2["data"].get("truncated")}')
        else:
            print(f'Error: {data2.get("message")}')
else:
    print(f'Error: {data.get("message")}')
    print(json.dumps(data, indent=2, ensure_ascii=False)[:500])

# --- Test 3: English test (should still have inline audio) ---
print()
print('='*60)
print('TEST 3: English chat (inline Polly — no async)')
print('='*60)
payload_en = {
    'message': 'What crops grow well in red soil?',
    'session_id': 'test-en-' + str(int(time.time() * 1000)),
    'farmer_id': 'test-farmer',
    'language': 'en'
}
t4 = time.time()
r3 = requests.post(url, json=payload_en, timeout=60)
t5 = time.time()
data3 = r3.json()
print(f'Status: {r3.status_code} | Time: {t5-t4:.1f}s')
if data3.get('status') == 'success':
    d3 = data3['data']
    print(f'audio_url present: {bool(d3.get("audio_url"))}')
    print(f'audio_pending: {d3.get("audio_pending")}')
    print(f'audio_key: {d3.get("audio_key")}')
