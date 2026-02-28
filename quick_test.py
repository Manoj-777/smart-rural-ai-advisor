#!/usr/bin/env python3
"""Quick test of the production API"""

import requests
import json
import time

API_URL = "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod"

def test_chat():
    payload = {
        "message": "What is the weather in Chennai?",
        "session_id": f"test-{int(time.time())}",
        "farmer_id": "test-farmer",
        "language": "en"
    }
    
    print(f"Testing: {payload['message']}")
    print(f"URL: {API_URL}/chat\n")
    
    try:
        start = time.time()
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        elapsed = time.time() - start
        
        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed:.2f}s\n")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Success!")
            print(f"\nReply: {data.get('data', {}).get('reply', 'N/A')}")
            print(f"Tools used: {data.get('data', {}).get('tools_used', [])}")
            print(f"Mode: {data.get('data', {}).get('mode', 'N/A')}")
            print(f"Pipeline: {data.get('data', {}).get('pipeline_mode', 'N/A')}")
        else:
            print(f"✗ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("✗ Timeout after 60s")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_chat()
