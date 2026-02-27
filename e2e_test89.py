"""E2E Tests 8+9: Hindi chat and Image Analysis"""
import urllib.request
import json
import time
import sys

API = "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod"

def post_json(path, body, timeout=120):
    url = f"{API}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    resp = urllib.request.urlopen(req, timeout=timeout)
    elapsed = time.time() - t0
    result = json.loads(resp.read().decode("utf-8"))
    return result, elapsed

results = []

# TEST 8: Hindi
try:
    hindi_msg = "\u092e\u0947\u0930\u0940 \u0917\u0947\u0939\u0942\u0902 \u0915\u0940 \u092b\u0938\u0932 \u092e\u0947\u0902 \u0915\u0940\u091f \u0932\u0917\u0947 \u0939\u0948\u0902, \u0915\u094d\u092f\u093e \u0915\u0930\u0942\u0902?"
    result, elapsed = post_json("/chat", {
        "message": hindi_msg,
        "session_id": "e2e8",
        "farmer_id": "test1",
        "language": "hi-IN"
    })
    data = result.get("data", {})
    reply = data.get("reply", "")
    # Transliterate reply for safe ASCII output
    results.append({
        "test": "TEST 8: Chat Hindi",
        "status": result.get("status"),
        "pipeline": data.get("pipeline_mode"),
        "detected_lang": data.get("detected_language"),
        "tools_used": data.get("tools_used"),
        "has_audio": bool(data.get("audio_url")),
        "latency_s": round(elapsed, 1),
        "reply_len": len(reply),
        "reply_preview_ascii": reply.encode("ascii", "replace").decode("ascii")[:300],
        "passed": result.get("status") == "success"
    })
except Exception as ex:
    results.append({"test": "TEST 8: Chat Hindi", "error": str(ex), "passed": False})

# TEST 9: Image Analysis
try:
    import base64
    tiny_png = base64.b64encode(bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
        0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
        0x44, 0xAE, 0x42, 0x60, 0x82
    ])).decode("ascii")
    
    result, elapsed = post_json("/image-analysis", {
        "image": tiny_png,
        "language": "en-IN"
    }, timeout=60)
    data = result.get("data", {})
    results.append({
        "test": "TEST 9: Image Analysis",
        "status": result.get("status"),
        "analysis_preview": str(data.get("analysis", ""))[:200],
        "confidence": data.get("confidence"),
        "latency_s": round(elapsed, 1),
        "passed": result.get("status") == "success"
    })
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    results.append({
        "test": "TEST 9: Image Analysis",
        "http_error": e.code,
        "body": body[:300],
        "passed": False
    })
except Exception as ex:
    results.append({"test": "TEST 9: Image Analysis", "error": str(ex), "passed": False})

# Write results as JSON
with open("e2e_test89_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=True)
print("DONE")
