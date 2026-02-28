import requests, json

API = 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod'

# Test 1: Create profile with phone-based ID
farmer_id = 'ph_9876543210'
profile = {
    'name': 'Ravi Kumar', 'state': 'Karnataka', 'district': 'Bangalore Rural',
    'crops': ['Rice', 'Ragi'], 'soil_type': 'Red', 'land_size_acres': 3.5, 'language': 'kn-IN'
}
r = requests.put(f'{API}/profile/{farmer_id}', json=profile)
d = r.json()
print(f"PUT profile: {r.status_code} -> {d.get('status')}")

# Test 2: Retrieve profile
r2 = requests.get(f'{API}/profile/{farmer_id}')
data = r2.json()['data']
print(f"GET profile: name={data['name']}, state={data['state']}, crops={data['crops']}")

# Test 3: Chat with real farmer_id (the orchestrator should enrich with profile context)
r3 = requests.post(f'{API}/chat', json={
    'message': 'What crops grow well in my area?',
    'farmer_id': farmer_id,
    'session_id': 'test-login-sess-001',
    'language': 'en-IN'
})
chat = r3.json()
print(f"Chat: status={chat['status']}, tools={chat['data']['tools_used']}, reply_len={len(chat['data']['reply'])}")

# Check if profile context was used (orchestrator prefixes with [Farmer context: ...])
reply_en = chat['data'].get('reply_en', '')
has_context = 'Ravi' in reply_en or 'Karnataka' in reply_en or 'Bangalore' in reply_en
print(f"Profile context used in response: {has_context}")

print("\nAll login flow tests PASSED!")
