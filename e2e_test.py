"""E2E Backend Test Suite for Smart Rural AI Advisor"""
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

def test_chat_schemes():
    print("=" * 60)
    print("TEST 7: Chat + Schemes Tool")
    print("  Query: 'Tell me about PM-KISAN scheme'")
    result, elapsed = post_json("/chat", {
        "message": "Tell me about PM-KISAN scheme",
        "session_id": "e2e7",
        "farmer_id": "test1",
        "language": "en-IN"
    })
    data = result.get("data", {})
    print(f"  Status     : {result.get('status')}")
    print(f"  Pipeline   : {data.get('pipeline_mode')}")
    print(f"  Tools Used : {data.get('tools_used')}")
    print(f"  Audio      : {'YES' if data.get('audio_url') else 'No'}")
    print(f"  Latency    : {elapsed:.1f}s")
    reply = data.get("reply", "")
    print(f"  Reply(300) : {reply[:300]}")
    if result.get("status") == "success":
        print("  RESULT     : PASS")
    else:
        print("  RESULT     : FAIL")
    print()

def test_chat_hindi():
    print("=" * 60)
    print("TEST 8: Chat in Hindi (multi-language pipeline)")
    hindi_msg = "\u092e\u0947\u0930\u0940 \u0917\u0947\u0939\u0942\u0902 \u0915\u0940 \u092b\u0938\u0932 \u092e\u0947\u0902 \u0915\u0940\u091f \u0932\u0917\u0947 \u0939\u0948\u0902, \u0915\u094d\u092f\u093e \u0915\u0930\u0942\u0902?"
    print(f"  Query: '{hindi_msg}'")
    result, elapsed = post_json("/chat", {
        "message": hindi_msg,
        "session_id": "e2e8",
        "farmer_id": "test1",
        "language": "hi-IN"
    })
    data = result.get("data", {})
    print(f"  Status     : {result.get('status')}")
    print(f"  Pipeline   : {data.get('pipeline_mode')}")
    print(f"  Detected   : {data.get('detected_language')}")
    print(f"  Tools Used : {data.get('tools_used')}")
    print(f"  Audio      : {'YES' if data.get('audio_url') else 'No'}")
    print(f"  Latency    : {elapsed:.1f}s")
    reply = data.get("reply", "")
    print(f"  Reply(300) : {reply[:300]}")
    if result.get("status") == "success" and data.get("detected_language") == "hi":
        print("  RESULT     : PASS (Hindi detected + translated)")
    elif result.get("status") == "success":
        print(f"  RESULT     : PARTIAL (lang={data.get('detected_language')})")
    else:
        print("  RESULT     : FAIL")
    print()

def test_image_analysis():
    print("=" * 60)
    print("TEST 9: Image Analysis Lambda (POST /image-analysis)")
    # Use a small test base64 image (1x1 red pixel PNG)
    import base64
    # Minimal valid PNG (1x1 red pixel)
    tiny_png = base64.b64encode(bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
        0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
        0x44, 0xAE, 0x42, 0x60, 0x82
    ])).decode("ascii")
    
    try:
        result, elapsed = post_json("/image-analysis", {
            "image": tiny_png,
            "language": "en-IN"
        }, timeout=60)
        data = result.get("data", {})
        print(f"  Status     : {result.get('status')}")
        print(f"  Analysis   : {str(data.get('analysis', ''))[:200]}")
        print(f"  Confidence : {data.get('confidence')}")
        print(f"  Latency    : {elapsed:.1f}s")
        if result.get("status") == "success":
            print("  RESULT     : PASS")
        else:
            print(f"  RESULT     : FAIL ({result.get('message', 'unknown')})")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP Error : {e.code}")
        print(f"  Body       : {body[:300]}")
        print("  RESULT     : FAIL")
    except Exception as ex:
        print(f"  Error      : {ex}")
        print("  RESULT     : FAIL")
    print()

if __name__ == "__main__":
    import io
    tests = sys.argv[1:] if len(sys.argv) > 1 else ["7", "8", "9"]
    # Tee output to file
    class Tee:
        def __init__(self, *streams):
            self.streams = streams
        def write(self, data):
            for s in self.streams:
                s.write(data)
                s.flush()
        def flush(self):
            for s in self.streams:
                s.flush()
    
    logfile = open("e2e_results.txt", "w", encoding="utf-8")
    # Also fix stdout encoding for Windows
    if sys.platform == "win32":
        sys.__stdout__ = io.TextIOWrapper(sys.__stdout__.buffer, encoding="utf-8", errors="replace")
    sys.stdout = Tee(sys.__stdout__, logfile)
    
    if "7" in tests:
        test_chat_schemes()
    if "8" in tests:
        test_chat_hindi()
    if "9" in tests:
        test_image_analysis()
    print("=" * 60)
    print("All requested tests complete.")
    logfile.close()
