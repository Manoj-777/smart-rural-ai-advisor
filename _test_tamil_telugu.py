import requests, json, time

API = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod'

tests = [
    {
        "name": "Tamil",
        "msg": "தஞ்சாவூரில் என் நெல் இலைகள் மஞ்சளாக மாறுகின்றன. இன்று வானிலை எப்படி இருக்கிறது, என்ன மருந்து தெளிக்க வேண்டும்?",
        "lang": "ta-IN",
    },
    {
        "name": "Telugu",
        "msg": "నా వరి ఆకులు పసుపు రంగులోకి మారుతున్నాయి, తంజావూరులో. ఈరోజు వాతావరణం ఎలా ఉంది, ఏమి స్ప్రే చేయాలి?",
        "lang": "te-IN",
    },
]

for t in tests:
    print(f"\n{'='*60}")
    print(f"TEST: {t['name']}")
    print(f"{'='*60}")
    print(f"Q: {t['msg']}")
    start = time.time()
    r = requests.post(f"{API}/chat", json={
        "message": t["msg"],
        "session_id": f"test-{t['name'].lower()}-pest-001",
        "farmer_id": "test-farmer-001",
        "language": t["lang"],
    })
    elapsed = time.time() - start
    d = r.json()
    data = d.get("data", {})
    print(f"Time: {elapsed:.1f}s")
    print(f"Detected Language: {data.get('detected_language')}")
    print(f"Tools Used: {data.get('tools_used')}")
    print(f"Audio: {'Yes' if data.get('audio_url') else 'No'}")
    reply = data.get("reply", "")[:600]
    print(f"Reply ({len(data.get('reply', ''))} chars):\n{reply}")
    
    # Check capabilities
    tools = data.get("tools_used", [])
    has_weather = any("weather" in str(t_).lower() for t_ in tools)
    has_pest = any("pest" in str(t_).lower() or "crop" in str(t_).lower() for t_ in tools)
    print(f"\nCapabilities: Weather={'YES' if has_weather else 'NO'}, Pest/Crop={'YES' if has_pest else 'NO'}")

print(f"\n{'='*60}")
print("DONE")
