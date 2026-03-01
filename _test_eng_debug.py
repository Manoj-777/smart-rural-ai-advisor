import requests, json, time

API = "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod"
msg = "My tomato plant leaves are curling and wilting in Coimbatore. What is the weather today? What pesticide should I spray?"

start = time.time()
r = requests.post(f"{API}/chat", json={
    "message": msg,
    "session_id": "test-eng-pest-002",
    "farmer_id": "test-farmer-001",
    "language": "en-IN",
})
elapsed = time.time() - start
d = r.json()
data = d.get("data", {})

print(f"Time: {elapsed:.1f}s")
print(f"Lang: {data.get('detected_language')}")
print(f"Tools: {data.get('tools_used')}")
print(f"Pipeline: {json.dumps(data.get('pipeline_meta', {}), indent=2)[:600]}")
print(f"\nReply ({len(data.get('reply', ''))} chars):")
print(data.get("reply", "")[:1000])
