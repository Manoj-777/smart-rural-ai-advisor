"""Quick STT test for the /transcribe endpoint."""
import base64, json, requests, os, tempfile, sys
from gtts import gTTS

URL = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/transcribe'

tests = [
    ('en-IN', 'en', 'Tell me about paddy farming in Tamil Nadu'),
    ('hi-IN', 'hi', 'मेरी फसल में कीड़े लग रहे हैं'),
    ('ta-IN', 'ta', 'சென்னையில் இன்றைய வானிலை என்ன'),
]

for lang_code, tts_lang, text in tests:
    print(f'\n--- {lang_code} ---')
    print(f'Input:  {text}')
    
    tts = gTTS(text, lang=tts_lang)
    path = os.path.join(tempfile.gettempdir(), f'stt_test_{tts_lang}.mp3')
    tts.save(path)
    
    with open(path, 'rb') as f:
        audio_b64 = base64.b64encode(f.read()).decode()
    
    try:
        r = requests.post(URL, json={
            'audio': audio_b64,
            'language': lang_code,
            'format': 'audio/mp3'
        }, timeout=60)
        
        d = r.json()
        transcript = d.get('data', {}).get('transcript', 'NO TRANSCRIPT')
        print(f'Status: {r.status_code}')
        print(f'Output: {transcript}')
    except requests.exceptions.Timeout:
        print('TIMEOUT (>60s)')
    except Exception as e:
        print(f'ERROR: {e}')

print('\n=== Done ===')
