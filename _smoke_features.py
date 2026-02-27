import json, sys, io, boto3

# Force UTF-8 stdout so ₹ and Tamil chars don't crash on Windows cp1252
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REGION = "ap-south-1"
client = boto3.client("lambda", region_name=REGION)
fn = [f["FunctionName"] for f in client.list_functions(MaxItems=100)["Functions"] if "AgentOrchestrator" in f["FunctionName"]][0]

cases = [
    ("weather", "What is weather in Chennai for next 3 days?"),
    ("crop", "Which crop should I grow in Tamil Nadu this Kharif season?"),
    ("pest", "My paddy leaves have brown spots. What pest or disease and treatment?"),
    ("schemes", "Tell me govt schemes for small farmers in Tamil Nadu"),
    ("profile", "Get my farmer profile advice", "farmer_001"),
    ("tamil", "நான் எந்த பயிர் வளர்த்தால் நல்ல பலன் இருக்கும்?", "test_farmer"),
]

for case in cases:
    tag = case[0]
    msg = case[1]
    farmer = case[2] if len(case) > 2 else "test_farmer"
    event = {
        "httpMethod": "POST",
        "body": json.dumps({"message": msg, "farmer_id": farmer, "language": "ta" if tag=="tamil" else "en"}, ensure_ascii=False)
    }
    resp = client.invoke(FunctionName=fn, Payload=json.dumps(event, ensure_ascii=False).encode("utf-8"))
    out = json.loads(resp["Payload"].read().decode("utf-8"))
    body = json.loads(out.get("body", "{}"))
    data = body.get("data", {})
    print("\n===", tag.upper(), "===")
    print("status:", out.get("statusCode"), "mode:", data.get("mode"))
    print("off_topic:", data.get("policy", {}).get("off_topic_blocked"), "grounding_required:", data.get("policy", {}).get("grounding_required"), "grounding_satisfied:", data.get("policy", {}).get("grounding_satisfied"))
    print("tools:", data.get("tools_used"))
    print("audio:", bool(data.get("audio_url")))
    reply = data.get("reply_en") or data.get("reply") or ""
    print("reply:", reply[:260].replace("\n", " "))
