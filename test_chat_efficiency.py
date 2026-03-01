"""
Smart Rural AI Advisor - Chat Efficiency Test
===============================================
Tests ALL page capabilities through the chat interface to evaluate
how well the AI agent can provide information from every page.

Pages tested:
1. Weather Page       -> weather queries
2. Crop Recommend     -> crop advisory queries
3. Soil Analysis      -> soil/pest queries
4. Farm Calendar      -> seasonal planning queries
5. Govt Schemes       -> scheme/subsidy queries
6. Profile context    -> personalized queries using farmer profile
"""

import json
import time
import requests
import uuid

API_URL = "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod"
FARMER_ID = "test-farmer-001"
SESSION_BASE = str(uuid.uuid4())

# Ensure session_id is >= 33 chars (AgentCore requirement)
def make_session(tag):
    s = f"{SESSION_BASE}-{tag}"
    while len(s) < 33:
        s += "x"
    return s

TEST_QUERIES = [
    {
        "name": "1. WEATHER (Weather Page)",
        "message": "What is the current weather in Thanjavur, Tamil Nadu? Is it good for sowing paddy?",
        "expected_tools": ["get_weather"],
        "checks": ["temperature", "humidity", "rain", "wind"],
    },
    {
        "name": "2. CROP ADVISORY (Crop Recommend Page)",
        "message": "What are the best paddy varieties for Kharif season in Tamil Nadu with clay soil? Give me fertilizer schedule too.",
        "expected_tools": ["get_crop_advisory"],
        "checks": ["variety", "fertilizer", "season", "yield"],
    },
    {
        "name": "3. SOIL & PEST (Soil Analysis Page)",
        "message": "My paddy leaves are turning yellow with brown spots in Thanjavur. The soil is clay loam. What pest or disease is this and how to treat it?",
        "expected_tools": ["get_pest_alert"],
        "checks": ["disease", "treatment", "spray", "prevention"],
    },
    {
        "name": "4. IRRIGATION (Farm Calendar context)",
        "message": "How much water does paddy need per week in clay soil during Kharif in Tamil Nadu? What irrigation method is best?",
        "expected_tools": ["get_irrigation_advice"],
        "checks": ["water", "irrigation", "schedule", "method"],
    },
    {
        "name": "5. GOVT SCHEMES (Schemes Page)",
        "message": "What government schemes and subsidies are available for small farmers in Tamil Nadu? Tell me about PM Kisan and crop insurance.",
        "expected_tools": ["search_schemes"],
        "checks": ["PM Kisan", "subsidy", "insurance", "scheme"],
    },
    {
        "name": "6. COMBINED QUERY (Multi-intent)",
        "message": "I am a farmer in Thanjavur, Tamil Nadu growing paddy on 2 acres. Give me today's weather and available government schemes.",
        "expected_tools": ["get_weather", "search_schemes"],
        "checks": ["weather", "scheme"],
    },
    {
        "name": "7. REGIONAL LANGUAGE (Tamil)",
        "message": "தஞ்சாவூரில் நெல் பயிர் செய்ய இப்போது நல்ல நேரமா? வானிலை எப்படி இருக்கு?",
        "language": "ta-IN",
        "expected_tools": ["get_weather", "get_crop_advisory"],
        "checks": [],  # Response will be in Tamil
    },
    {
        "name": "8. REGIONAL LANGUAGE (Hindi)",
        "message": "मेरे गेहूं की फसल में पीले पत्ते दिख रहे हैं। उत्तर प्रदेश में क्या करूं?",
        "language": "hi-IN",
        "expected_tools": ["get_pest_alert"],
        "checks": [],  # Response will be in Hindi
    },
]

def run_test(test, index):
    print(f"\n{'='*70}")
    print(f"TEST {test['name']}")
    print(f"{'='*70}")
    print(f"QUERY: {test['message'][:100]}...")

    session_id = make_session(f"test{index}")
    test_lang = test.get("language", "en-IN")
    payload = {
        "message": test["message"],
        "session_id": session_id,
        "farmer_id": FARMER_ID,
        "language": test_lang
    }

    start = time.time()
    try:
        resp = requests.post(f"{API_URL}/chat", json=payload, timeout=120)
        elapsed = time.time() - start
        data = resp.json()

        status = data.get("status", "unknown")
        reply = data.get("data", {}).get("reply", "No reply")
        tools_used = data.get("data", {}).get("tools_used", [])
        detected_lang = data.get("data", {}).get("detected_language", "?")
        audio_url = data.get("data", {}).get("audio_url", None)

        print(f"\nSTATUS: {status}")
        print(f"RESPONSE TIME: {elapsed:.1f}s")
        print(f"DETECTED LANGUAGE: {detected_lang}")
        print(f"TOOLS USED: {tools_used if tools_used else 'None'}")
        print(f"AUDIO: {'Yes' if audio_url else 'No'}")

        # Check if expected tools were used
        expected = test.get("expected_tools", [])
        if expected and tools_used:
            tools_str = str(tools_used).lower()
            matched = [t for t in expected if t.lower() in tools_str]
            missed = [t for t in expected if t.lower() not in tools_str]
            print(f"EXPECTED TOOLS MATCH: {len(matched)}/{len(expected)} ", end="")
            if missed:
                print(f"(MISSED: {missed})")
            else:
                print("✓ ALL MATCHED")

        # Check if key terms appear in reply
        checks = test.get("checks", [])
        if checks and reply:
            reply_lower = reply.lower()
            found = [c for c in checks if c.lower() in reply_lower]
            missed = [c for c in checks if c.lower() not in reply_lower]
            print(f"CONTENT CHECKS: {len(found)}/{len(checks)} terms found ", end="")
            if missed:
                print(f"(MISSED: {missed})")
            else:
                print("✓ ALL FOUND")

        # Print reply (truncated)
        print(f"\nREPLY ({len(reply)} chars):")
        if len(reply) > 800:
            print(reply[:800] + "\n... [truncated]")
        else:
            print(reply)

        return {
            "name": test["name"],
            "status": status,
            "time": round(elapsed, 1),
            "tools_used": tools_used,
            "reply_length": len(reply),
            "detected_language": detected_lang,
            "has_audio": bool(audio_url),
            "success": status == "success" and len(reply) > 50,
        }

    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"\n⏰ TIMEOUT after {elapsed:.1f}s")
        return {"name": test["name"], "status": "timeout", "time": round(elapsed, 1), "success": False}
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n❌ ERROR: {e}")
        return {"name": test["name"], "status": "error", "time": round(elapsed, 1), "success": False}


def main():
    print("=" * 70)
    print("SMART RURAL AI ADVISOR - CHAT EFFICIENCY TEST")
    print("Testing if the AI chat can cover ALL page functionalities")
    print("=" * 70)
    print(f"API: {API_URL}")
    print(f"Farmer ID: {FARMER_ID}")
    print(f"Total tests: {len(TEST_QUERIES)}")

    results = []
    total_start = time.time()

    for i, test in enumerate(TEST_QUERIES):
        result = run_test(test, i)
        results.append(result)
        # Small delay between tests to avoid throttling
        if i < len(TEST_QUERIES) - 1:
            time.sleep(2)

    total_time = time.time() - total_start

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY - AI EFFICIENCY REPORT")
    print("=" * 70)
    
    passed = sum(1 for r in results if r.get("success"))
    failed = len(results) - passed
    avg_time = sum(r.get("time", 0) for r in results) / len(results) if results else 0

    print(f"\nTotal Tests:    {len(results)}")
    print(f"Passed:         {passed}/{len(results)}")
    print(f"Failed:         {failed}")
    print(f"Avg Response:   {avg_time:.1f}s")
    print(f"Total Time:     {total_time:.1f}s")
    
    print(f"\n{'Test':<45} {'Status':<10} {'Time':>6} {'Tools':<30}")
    print("-" * 95)
    for r in results:
        tools = str(r.get("tools_used", []))
        if len(tools) > 28:
            tools = tools[:28] + ".."
        status_icon = "✓" if r.get("success") else "✗"
        print(f"{status_icon} {r['name']:<43} {r.get('status','?'):<10} {r.get('time',0):>5.1f}s {tools:<30}")

    print("\n" + "=" * 70)
    print("CAPABILITY COVERAGE:")
    print("=" * 70)
    capabilities = {
        "Weather Info (Weather Page)": any("weather" in str(r.get("tools_used", [])).lower() for r in results if r.get("success")),
        "Crop Advisory (Crop Page)": any("crop" in str(r.get("tools_used", [])).lower() for r in results if r.get("success")),
        "Pest/Disease (Soil Page)": any("pest" in str(r.get("tools_used", [])).lower() for r in results if r.get("success")),
        "Irrigation (Calendar Page)": any("crop" in str(r.get("tools_used", [])).lower() for r in results if r.get("success") and "irrigation" in r.get("name", "").lower()),
        "Govt Schemes (Schemes Page)": any("scheme" in str(r.get("tools_used", [])).lower() for r in results if r.get("success")),
        "Regional Language Support": any(r.get("detected_language", "en") not in ("en", "en-IN") for r in results if r.get("success")),
        "Audio Response (TTS)": any(r.get("has_audio") for r in results),
    }
    
    for cap, covered in capabilities.items():
        icon = "✓" if covered else "✗"
        print(f"  {icon} {cap}")
    
    coverage = sum(1 for v in capabilities.values() if v)
    print(f"\nOverall Coverage: {coverage}/{len(capabilities)} capabilities accessible via chat")
    
    if coverage == len(capabilities):
        print("\n🎉 EXCELLENT! The AI chat provides ALL page functionalities!")
    elif coverage >= 5:
        print("\n👍 GOOD - Most features accessible via chat.")
    else:
        print("\n⚠️  Some capabilities are NOT reachable via chat.")

    # Save detailed results
    with open("chat_test_results.json", "w", encoding="utf-8") as f:
        json.dump({"results": results, "summary": {
            "passed": passed, "failed": failed, "avg_time": avg_time,
            "total_time": total_time, "capabilities": {k: v for k, v in capabilities.items()}
        }}, f, indent=2, ensure_ascii=False)
    print("\nDetailed results saved to chat_test_results.json")


if __name__ == "__main__":
    main()
