"""Test the /chat endpoint with AgentCore Runtime."""
import requests
import json

API_URL = "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod"

def test_chat(message, farmer_id="farmer_001"):
    print(f"\n{'='*60}")
    print(f"  Query: {message}")
    print(f"{'='*60}")
    
    resp = requests.post(
        f"{API_URL}/chat",
        json={
            "message": message,
            "farmer_id": farmer_id,
            "session_id": "test-session-001",
        },
        timeout=60,
    )
    
    print(f"  Status: {resp.status_code}")
    
    try:
        data = resp.json()
        d = data.get("data")
        if d:
            print(f"  Mode: {d.get('mode', '?')}")
            print(f"  Language: {d.get('detected_language', '?')}")
            print(f"  Tools Used: {d.get('tools_used', [])}")
            print(f"  Reply (first 500 chars):")
            reply = d.get("reply", d.get("reply_en", ""))
            print(f"    {reply[:500]}")
            if d.get("audio_url"):
                print(f"  Audio URL: {d['audio_url']}")
        else:
            print(f"  Message: {data.get('message', '')}")
            print(f"  Response: {json.dumps(data, indent=2)[:500]}")
    except Exception as e:
        print(f"  Error parsing: {e}")
        print(f"  Raw: {resp.text[:500]}")


# Test 1: Basic crop question
test_chat("What crops should I plant in Tamil Nadu during Kharif season?")

# Test 2: Weather
test_chat("What is the weather in Chennai today?")

# Test 3: Government schemes
test_chat("What government subsidies are available for drip irrigation?")
