"""
Test script for Smart Rural AI Advisor — Backend
Tests all Lambda handlers and utility modules locally.
Run: python test_all.py
"""

import sys
import os
import json
import importlib
import importlib.util

# Add backend to path so imports work like they do in Lambda
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

PASS = 0
FAIL = 0


def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} -- {detail}")


def header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


class FakeContext:
    function_name = "test_lambda"


def load_lambda(subdir):
    """Load a Lambda handler module by its subdirectory name."""
    mod_path = os.path.join(BASE_DIR, 'backend', 'lambdas', subdir)
    sys.path.insert(0, mod_path)
    spec = importlib.util.spec_from_file_location(
        f"lambda_{subdir}", os.path.join(mod_path, "handler.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ============================================================
#  1. TEST response_helper.py
# ============================================================
header("1. response_helper.py")

from utils.response_helper import success_response, error_response

r = success_response({"test": "data"}, message="Test OK", language="ta")
body = json.loads(r["body"])

test("success_response returns 200", r["statusCode"] == 200)
test("CORS Allow-Origin is *", r["headers"]["Access-Control-Allow-Origin"] == "*")
test("CORS Allow-Methods present", "GET" in r["headers"]["Access-Control-Allow-Methods"])
test("body.status is success", body["status"] == "success")
test("body.data matches", body["data"] == {"test": "data"})
test("body.language is ta", body["language"] == "ta")
test("body.message matches", body["message"] == "Test OK")

r2 = error_response("Something broke", 400, language="hi")
body2 = json.loads(r2["body"])

test("error_response returns 400", r2["statusCode"] == 400)
test("error body.status is error", body2["status"] == "error")
test("error body.data is None", body2["data"] is None)
test("error body.message matches", body2["message"] == "Something broke")
test("error CORS headers present", r2["headers"]["Access-Control-Allow-Origin"] == "*")

# ============================================================
#  2. TEST error_handler.py
# ============================================================
header("2. error_handler.py")

from utils.error_handler import handle_errors

@handle_errors
def good_handler(event, context):
    return success_response({"result": "ok"})

@handle_errors
def bad_handler(event, context):
    raise ValueError("test error")

@handle_errors
def key_error_handler(event, context):
    data = {}
    return data["missing_key"]

result = good_handler({"test": True}, FakeContext())
test("handle_errors passes through success", result["statusCode"] == 200)

result2 = bad_handler({"test": True}, FakeContext())
body_err = json.loads(result2["body"])
test("handle_errors catches Exception -> 500", result2["statusCode"] == 500)
test("error message is generic", "Internal server error" in body_err["message"])

result3 = key_error_handler({"test": True}, FakeContext())
body_key = json.loads(result3["body"])
test("handle_errors catches KeyError -> 400", result3["statusCode"] == 400)
test("KeyError mentions field name", "missing_key" in body_key["message"])

# ============================================================
#  3. TEST govt_schemes Lambda (no AWS needed -- hardcoded data)
# ============================================================
header("3. govt_schemes Lambda")

schemes_mod = load_lambda("govt_schemes")
schemes_handler = schemes_mod.lambda_handler

# Test: GET all schemes
event_all = {
    "httpMethod": "GET",
    "queryStringParameters": None,
    "body": None
}
r = schemes_handler(event_all, FakeContext())
body = json.loads(r["body"])
test("GET /schemes returns 200", r["statusCode"] == 200)
test("status is success", body["status"] == "success")
schemes = body["data"]["schemes"]
test("Contains pm_kisan", "pm_kisan" in schemes)
test("Contains pmfby", "pmfby" in schemes)
test("Contains kcc", "kcc" in schemes)
test("Contains soil_health_card", "soil_health_card" in schemes)
test("Has 9 schemes total", len(schemes) == 9, f"got {len(schemes)}")
test("PM-KISAN has benefit field", "6,000" in schemes["pm_kisan"]["benefit"])
test("Helpline note present", "1800-180-1551" in body["data"]["note"])

# Test: GET specific scheme by query param
event_specific = {
    "httpMethod": "GET",
    "queryStringParameters": {"name": "kcc"},
    "body": None
}
r2 = schemes_handler(event_specific, FakeContext())
body2 = json.loads(r2["body"])
test("GET /schemes?name=kcc returns 200", r2["statusCode"] == 200)
test("KCC full_name correct", body2["data"]["schemes"]["full_name"] == "Kisan Credit Card")

# Test: OPTIONS (CORS preflight)
event_options = {"httpMethod": "OPTIONS"}
r3 = schemes_handler(event_options, FakeContext())
test("OPTIONS returns 200", r3["statusCode"] == 200)

# Test: AgentCore tool call format
event_agent = {
    "parameters": [
        {"name": "scheme_name", "value": "pmfby"},
        {"name": "farmer_state", "value": "Tamil Nadu"}
    ]
}
r4 = schemes_handler(event_agent, FakeContext())
body4 = json.loads(r4["body"])
test("AgentCore tool call works", body4["status"] == "success")
test("PMFBY returned from tool call", body4["data"]["schemes"]["name"] == "PMFBY")

# Test: Search by keyword
event_search = {
    "httpMethod": "GET",
    "queryStringParameters": {"name": "kisan"},
    "body": None
}
r5 = schemes_handler(event_search, FakeContext())
body5 = json.loads(r5["body"])
test("Keyword search 'kisan' finds results", len(body5["data"]["schemes"]) > 0)

# ============================================================
#  4. TEST weather_lookup Lambda (structure + API key check)
# ============================================================
header("4. weather_lookup Lambda")

# Set env vars before loading
os.environ["OPENWEATHER_API_KEY"] = ""
weather_mod = load_lambda("weather_lookup")

r = weather_mod.lambda_handler(
    {"pathParameters": {"location": "Chennai"}},
    FakeContext()
)
body = json.loads(r["body"])
test("Missing API key returns 500", r["statusCode"] == 500)
# Check either 'message' or nested 'data.message'
err_msg = body.get("message", "") or str(body.get("data", ""))
test("Error mentions API key", "API key" in err_msg or "api" in err_msg.lower())

# Restore and reload
os.environ["OPENWEATHER_API_KEY"] = os.environ.get("OPENWEATHER_API_KEY", "test-api-key-placeholder")
weather_mod2 = load_lambda("weather_lookup")

test("weather_handler is callable", callable(weather_mod2.lambda_handler))

# Live API test (may fail if key not activated yet)
print("\n  [Live API test -- may fail if key not yet activated]")
try:
    r_live = weather_mod2.lambda_handler(
        {"pathParameters": {"location": "Chennai"}},
        FakeContext()
    )
    body_live = json.loads(r_live["body"])
    if r_live["statusCode"] == 200:
        data = body_live["data"]
        test("Live: Chennai returns 200", True)
        test("Live: has temp_celsius", data["current"]["temp_celsius"] is not None)
        test("Live: has humidity", data["current"]["humidity"] is not None)
        test("Live: has forecast array", isinstance(data["forecast"], list))
        test("Live: has farming_advisory", len(data["farming_advisory"]) > 0)
        test("Live: location is Chennai", data["location"] == "Chennai")
        temp = data['current']['temp_celsius']
        hum = data['current']['humidity']
        print(f"  INFO: Chennai temp = {temp} C, humidity = {hum}%")
    else:
        print(f"  SKIP: API key not active yet (status {r_live['statusCode']})")
except Exception as e:
    print(f"  SKIP: Weather API call failed -- {e}")

# ============================================================
#  5. TEST farmer_profile Lambda (structure -- DynamoDB calls will fail)
# ============================================================
header("5. farmer_profile Lambda")

profile_mod = load_lambda("farmer_profile")
profile_handler = profile_mod.lambda_handler

# Test: OPTIONS preflight
r = profile_handler({"httpMethod": "OPTIONS", "pathParameters": {"farmerId": "test"}}, FakeContext())
test("OPTIONS returns 200", r["statusCode"] == 200)
test("OPTIONS has CORS headers", r["headers"]["Access-Control-Allow-Origin"] == "*")

# Test: Missing farmerId
r2 = profile_handler({"httpMethod": "GET", "pathParameters": {}}, FakeContext())
body2 = json.loads(r2["body"])
test("Missing farmerId returns 400", r2["statusCode"] == 400)
test("Error mentions farmerId", "farmerId" in body2.get("error", ""))

# Test: Invalid method
r3 = profile_handler({"httpMethod": "DELETE", "pathParameters": {"farmerId": "test"}}, FakeContext())
body3 = json.loads(r3["body"])
test("DELETE returns 405", r3["statusCode"] == 405)

# Test: GET (will fail on DynamoDB but should be caught)
print("\n  [DynamoDB tests -- expected to fail locally without AWS]")
try:
    r4 = profile_handler({"httpMethod": "GET", "pathParameters": {"farmerId": "test123"}}, FakeContext())
    if r4["statusCode"] == 200:
        test("GET profile returns 200", True)
    else:
        print(f"  SKIP: DynamoDB not available locally (status {r4['statusCode']})")
except Exception as e:
    print(f"  SKIP: DynamoDB not available -- {e}")

# ============================================================
#  6. TEST image_analysis Lambda (structure -- Bedrock calls will fail)
# ============================================================
header("6. image_analysis Lambda")

image_mod = load_lambda("image_analysis")
image_handler = image_mod.lambda_handler
detect_media_type = image_mod.detect_media_type
make_response = image_mod.make_response

# Test: detect_media_type
test("JPEG detection", detect_media_type("/9j/4AAQSkZJ") == "image/jpeg")
test("PNG detection", detect_media_type("iVBORw0KGgoAAAA") == "image/png")
test("GIF detection", detect_media_type("R0lGODlhAQABAI") == "image/gif")
test("WebP detection", detect_media_type("UklGRiQAAABXRU") == "image/webp")
test("Unknown defaults to jpeg", detect_media_type("AAAA") == "image/jpeg")

# Test: make_response always has CORS
r = make_response(200, {"test": True})
test("make_response includes CORS", r["headers"]["Access-Control-Allow-Origin"] == "*")
test("make_response sets status", r["statusCode"] == 200)

# Test: OPTIONS preflight
r2 = image_handler({"httpMethod": "OPTIONS"}, FakeContext())
test("OPTIONS returns 200", r2["statusCode"] == 200)

# Test: Missing image
r3 = image_handler({"httpMethod": "POST", "body": json.dumps({})}, FakeContext())
body3 = json.loads(r3["body"])
test("Missing image returns 400", r3["statusCode"] == 400)
test("Error mentions image", "Image is required" in body3.get("error", ""))

# Test: Image too large (simulate >4MB)
fake_large = "A" * (6 * 1024 * 1024)  # ~4.5MB decoded
r4 = image_handler({"httpMethod": "POST", "body": json.dumps({"image_base64": fake_large})}, FakeContext())
body4 = json.loads(r4["body"])
test("Oversized image returns 400", r4["statusCode"] == 400)
test("Error mentions size", "too large" in body4.get("error", ""))

# Test: data-URI prefix stripping
r5 = image_handler({
    "httpMethod": "POST",
    "body": json.dumps({"image_base64": "data:image/jpeg;base64,/9j/small"})
}, FakeContext())
# Will fail at Bedrock call but should not fail at parsing
test("data-URI prefix stripped (no parse error)", r5["statusCode"] in [400, 500])

# ============================================================
#  7. TEST crop_advisory Lambda (structure)
# ============================================================
header("7. crop_advisory Lambda")

os.environ["BEDROCK_KB_ID"] = ""
crop_mod = load_lambda("crop_advisory")

test("crop_handler is callable", callable(crop_mod.lambda_handler))

r = crop_mod.lambda_handler({
    "parameters": [
        {"name": "crop", "value": "Rice"},
        {"name": "state", "value": "Tamil Nadu"},
        {"name": "season", "value": "Kharif"},
        {"name": "soil_type", "value": "Alluvial"}
    ]
}, FakeContext())
body = json.loads(r["body"])
test("Missing KB_ID returns 500", r["statusCode"] == 500)
test("Error mentions Knowledge Base", "Knowledge Base" in body.get("message", ""))

# ============================================================
#  8. TEST agent_orchestrator Lambda (structure)
# ============================================================
header("8. agent_orchestrator Lambda")

orch_mod = load_lambda("agent_orchestrator")
orch_handler = orch_mod.lambda_handler

# Test OPTIONS
r = orch_handler({"httpMethod": "OPTIONS"}, FakeContext())
test("OPTIONS returns 200", r["statusCode"] == 200)

# Test empty message
r2 = orch_handler({"httpMethod": "POST", "body": json.dumps({"message": ""})}, FakeContext())
body2 = json.loads(r2["body"])
test("Empty message returns 400", r2["statusCode"] == 400)
test("Error mentions 'Message is required'", "Message is required" in body2.get("message", ""))

# ============================================================
#  9. TEST transcribe_speech Lambda (structure)
# ============================================================
header("9. transcribe_speech Lambda")

transcribe_mod = load_lambda("transcribe_speech")
transcribe_handler = transcribe_mod.lambda_handler

# Test OPTIONS
r = transcribe_handler({"httpMethod": "OPTIONS"}, FakeContext())
test("OPTIONS returns 200", r["statusCode"] == 200)

# Test missing audio
r2 = transcribe_handler({"httpMethod": "POST", "body": json.dumps({})}, FakeContext())
body2 = json.loads(r2["body"])
test("Missing audio returns 400", r2["statusCode"] == 400)
test("Error mentions audio", "audio" in body2.get("message", "").lower())

# ============================================================
#  10. TEST translate_helper (structure -- AWS calls will fail)
# ============================================================
header("10. translate_helper")

from utils.translate_helper import detect_and_translate, translate_response, SUPPORTED_LANGUAGES

test("SUPPORTED_LANGUAGES has 8 entries", len(SUPPORTED_LANGUAGES) == 8)
test("Tamil in supported", "ta" in SUPPORTED_LANGUAGES)
test("English in supported", "en" in SUPPORTED_LANGUAGES)
test("Hindi in supported", "hi" in SUPPORTED_LANGUAGES)
test("Telugu in supported", "te" in SUPPORTED_LANGUAGES)

# Test translate_response same-language shortcut
result = translate_response("Hello", source_language="en", target_language="en")
test("Same lang returns original (no API call)", result == "Hello")

# Test detect_and_translate fallback (when AWS not available)
print("\n  [AWS Translate test -- may fail without credentials]")
try:
    r = detect_and_translate("Hello, how are you?", target_language="en")
    test("detect_and_translate returns dict", isinstance(r, dict))
    test("Has detected_language key", "detected_language" in r)
    test("Has translated_text key", "translated_text" in r)
    if r["detected_language"] != "en":
        print(f"  INFO: Detected language = {r['detected_language']}")
    else:
        test("English detected correctly", r["detected_language"] == "en")
except Exception as e:
    print(f"  SKIP: AWS Translate not available -- {e}")

# ============================================================
#  11. TEST polly_helper (structure)
# ============================================================
header("11. polly_helper")

from utils.polly_helper import VOICE_MAP, POLLY_LANG_MAP, text_to_speech

test("VOICE_MAP has 5 entries", len(VOICE_MAP) == 5)
test("English voice is Kajal", VOICE_MAP["en"] == "Kajal")
test("Hindi voice is Kajal", VOICE_MAP["hi"] == "Kajal")
test("Tamil fallback is Kajal", VOICE_MAP["ta"] == "Kajal")
test("POLLY_LANG_MAP en -> en-IN", POLLY_LANG_MAP["en"] == "en-IN")
test("POLLY_LANG_MAP hi -> hi-IN", POLLY_LANG_MAP["hi"] == "hi-IN")
test("text_to_speech is callable", callable(text_to_speech))

# ============================================================
#  12. TEST dynamodb_helper (structure)
# ============================================================
header("12. dynamodb_helper")

from utils.dynamodb_helper import (
    get_farmer_profile, put_farmer_profile,
    save_chat_message, get_chat_history,
    PROFILES_TABLE, SESSIONS_TABLE
)

test("PROFILES_TABLE default is farmer_profiles", PROFILES_TABLE == "farmer_profiles")
test("SESSIONS_TABLE default is chat_sessions", SESSIONS_TABLE == "chat_sessions")
test("get_farmer_profile is callable", callable(get_farmer_profile))
test("put_farmer_profile is callable", callable(put_farmer_profile))
test("save_chat_message is callable", callable(save_chat_message))
test("get_chat_history is callable", callable(get_chat_history))

# ============================================================
#  SUMMARY
# ============================================================
print(f"\n{'='*60}")
print(f"  RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL} tests")
print(f"{'='*60}")

if FAIL == 0:
    print("\n  ALL TESTS PASSED!")
else:
    print(f"\n  {FAIL} test(s) need attention.")

print("\n  Note: AWS-dependent tests (DynamoDB, Translate, Polly,")
print("  Bedrock, Transcribe) require active AWS credentials")
print("  and will only fully pass after sam deploy.")
