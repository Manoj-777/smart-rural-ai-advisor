"""Test Tamil soil analysis to reproduce connection error."""
import json, requests, time

url = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/chat'
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
        '1. Soil Health Rating (Good / Moderate / Poor) with brief explanation\n'
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

print('Calling API for Tamil soil analysis...')
t0 = time.time()
try:
    r = requests.post(url, json=payload, timeout=60)
    elapsed = time.time() - t0
    print(f'Status: {r.status_code} | Time: {elapsed:.1f}s')
    try:
        data = r.json()
    except Exception:
        print(f'Non-JSON response: {r.text[:500]}')
        raise SystemExit(1)

    status = data.get('status')
    print(f'Response status: {status}')
    if status == 'success':
        reply = data['data'].get('reply', '')
        print(f'Reply length: {len(reply)}')
        print(f'Reply (first 500 chars):\n{reply[:500]}')
        print(f'Audio URL present: {bool(data["data"].get("audio_url"))}')
        print(f'Audio Key: {data["data"].get("audio_key")}')
        print(f'Tools used: {data["data"].get("tools_used")}')
    else:
        print(f'Error message: {data.get("message")}')
        print(json.dumps(data, indent=2, ensure_ascii=False)[:800])
except requests.exceptions.Timeout:
    elapsed = time.time() - t0
    print(f'TIMEOUT after {elapsed:.1f}s')
except requests.exceptions.ConnectionError as e:
    elapsed = time.time() - t0
    print(f'CONNECTION ERROR after {elapsed:.1f}s: {e}')
except Exception as e:
    elapsed = time.time() - t0
    print(f'FAILED after {elapsed:.1f}s: {type(e).__name__}: {e}')
