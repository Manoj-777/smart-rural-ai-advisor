"""
Smart Rural AI Advisor - AgentCore Runtime Entry Point

Hybrid auth approach:
  - If BEDROCK_API_KEY is set → invoke_model via Bearer token (Anthropic Messages API)
  - If BEDROCK_API_KEY is empty → boto3 converse API with IAM role credentials
"""

import os
import json
import logging
import sys
import time

_start = time.time()

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("smart-rural-agent")
logger.info(f"Module load start (Python {sys.version_info.major}.{sys.version_info.minor})")

from bedrock_agentcore import BedrockAgentCoreApp

logger.info(f"BedrockAgentCoreApp imported in {time.time()-_start:.1f}s")

# Config
MODEL_REGION = os.environ.get("MODEL_REGION", "us-east-1")
FOUNDATION_MODEL = os.environ.get(
    "FOUNDATION_MODEL", "us.anthropic.claude-sonnet-4-20250514-v1:0"
)
BEDROCK_API_KEY = os.environ.get("BEDROCK_API_KEY", "").strip()
TOOLS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
MAX_TURNS = 10
USE_API_KEY = bool(BEDROCK_API_KEY)

app = BedrockAgentCoreApp()
logger.info(
    f"App created in {time.time()-_start:.1f}s | auth={'API_KEY' if USE_API_KEY else 'IAM'} | "
    f"model={FOUNDATION_MODEL} | region={MODEL_REGION}"
)

SYSTEM_PROMPT = """You are the Smart Rural AI Advisor, an expert Indian agricultural assistant \
helping small and marginal farmers across India. You are a trusted Krishi Mitra (farming friend).

Provide actionable advice about crops, pests, weather, irrigation, and government schemes.
Use Indian context: Kharif/Rabi seasons, Indian soil types, local crop varieties.
Only discuss agriculture and farming-related topics.

When a farmer asks about crops, weather, pests, irrigation, schemes, or their profile, \
use the available tools to get accurate data before answering."""

# ==================== Tool Definitions (Anthropic format) ====================

TOOL_DEFINITIONS = [
    {
        "name": "get_crop_advisory",
        "description": "Get crop advisory guidance for Indian agriculture. Provides recommendations on crop selection, growing conditions, varieties, and best practices based on the farmer's region, soil type, and season.",
        "input_schema": {
            "type": "object",
            "properties": {
                "crop": {"type": "string", "description": "Name of the crop (e.g., 'Rice', 'Wheat', 'Cotton')"},
                "state": {"type": "string", "description": "Indian state (e.g., 'Tamil Nadu', 'Andhra Pradesh')"},
                "season": {"type": "string", "description": "Growing season (e.g., 'Kharif', 'Rabi', 'Summer')"},
                "soil_type": {"type": "string", "description": "Soil type (e.g., 'Clay loam', 'Sandy', 'Red soil')"},
                "query": {"type": "string", "description": "Additional free-text farming question"},
            },
            "required": [],
        },
    },
    {
        "name": "get_pest_alert",
        "description": "Identify crop pests and diseases, and get treatment recommendations. Provides both organic and chemical treatment options.",
        "input_schema": {
            "type": "object",
            "properties": {
                "crop": {"type": "string", "description": "Name of the affected crop"},
                "symptoms": {"type": "string", "description": "Description of symptoms (e.g., 'yellow leaves', 'brown spots')"},
                "state": {"type": "string", "description": "Indian state for region-specific pest patterns"},
                "season": {"type": "string", "description": "Current season for seasonal pest alerts"},
            },
            "required": [],
        },
    },
    {
        "name": "get_irrigation_advice",
        "description": "Get irrigation recommendations including scheduling, water requirements, and best irrigation methods for specific crops.",
        "input_schema": {
            "type": "object",
            "properties": {
                "crop": {"type": "string", "description": "Name of the crop"},
                "location": {"type": "string", "description": "Location for weather-based irrigation advice"},
                "soil_type": {"type": "string", "description": "Soil type affecting water retention"},
                "query": {"type": "string", "description": "Additional irrigation-specific question"},
            },
            "required": [],
        },
    },
    {
        "name": "get_weather",
        "description": "Get real-time weather data with farming advisory for any location in India. Returns current conditions, forecast, and farming-specific recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or district name in India (e.g., 'Chennai', 'Guntur')"},
            },
            "required": ["location"],
        },
    },
    {
        "name": "search_schemes",
        "description": "Search Indian government agricultural schemes, subsidies, insurance, and loan programs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search term (e.g., 'insurance', 'subsidy', 'loan')"},
                "category": {"type": "string", "description": "Optional scheme category filter"},
            },
            "required": [],
        },
    },
    {
        "name": "get_farmer_profile",
        "description": "Look up a farmer's saved profile including their location, crops, soil type, and farming details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "farmer_id": {"type": "string", "description": "The unique farmer identifier"},
            },
            "required": ["farmer_id"],
        },
    },
]

# ==================== Lambda Tool Execution ====================

_lambda_client = None

LAMBDA_NAMES = {
    "crop_advisory": os.environ.get("CROP_ADVISORY_FUNCTION", "smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY"),
    "weather": os.environ.get("WEATHER_FUNCTION", "smart-rural-ai-WeatherFunction-dilSoHSLlXGN"),
    "govt_schemes": os.environ.get("GOVT_SCHEMES_FUNCTION", "smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv"),
    "farmer_profile": os.environ.get("FARMER_PROFILE_FUNCTION", "smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt"),
}


def _get_lambda_client():
    global _lambda_client
    if _lambda_client is None:
        import boto3
        _lambda_client = boto3.client("lambda", region_name=TOOLS_REGION)
    return _lambda_client


def _invoke_lambda(function_key, payload):
    function_name = LAMBDA_NAMES.get(function_key)
    if not function_name:
        return {"error": f"Lambda not configured for: {function_key}"}
    try:
        resp = _get_lambda_client().invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode("utf-8"),
        )
        resp_payload = json.loads(resp["Payload"].read().decode("utf-8"))
        if isinstance(resp_payload, dict) and "body" in resp_payload:
            body = json.loads(resp_payload["body"])
            return body.get("data", body)
        return resp_payload
    except Exception as e:
        logger.error(f"Lambda error for {function_key}: {e}")
        return {"error": str(e)}


def _execute_tool(tool_name, tool_input):
    """Execute a tool and return the result string."""
    logger.info(f"Executing tool: {tool_name} with input: {json.dumps(tool_input)[:200]}")

    if tool_name == "get_crop_advisory":
        payload = {
            "httpMethod": "GET", "pathParameters": {},
            "queryStringParameters": {
                "operation": "get_crop_advisory",
                "crop": tool_input.get("crop", ""),
                "state": tool_input.get("state", ""),
                "season": tool_input.get("season", ""),
                "soil_type": tool_input.get("soil_type", ""),
                "query": tool_input.get("query", ""),
            },
        }
        return json.dumps(_invoke_lambda("crop_advisory", payload), indent=2)

    elif tool_name == "get_pest_alert":
        payload = {
            "httpMethod": "GET", "pathParameters": {},
            "queryStringParameters": {
                "operation": "get_pest_alert",
                "crop": tool_input.get("crop", ""),
                "symptoms": tool_input.get("symptoms", ""),
                "state": tool_input.get("state", ""),
                "season": tool_input.get("season", ""),
            },
        }
        return json.dumps(_invoke_lambda("crop_advisory", payload), indent=2)

    elif tool_name == "get_irrigation_advice":
        payload = {
            "httpMethod": "GET", "pathParameters": {},
            "queryStringParameters": {
                "operation": "get_irrigation_advice",
                "crop": tool_input.get("crop", ""),
                "location": tool_input.get("location", ""),
                "soil_type": tool_input.get("soil_type", ""),
                "query": tool_input.get("query", ""),
            },
        }
        return json.dumps(_invoke_lambda("crop_advisory", payload), indent=2)

    elif tool_name == "get_weather":
        payload = {
            "httpMethod": "GET",
            "pathParameters": {"location": tool_input.get("location", "")},
            "queryStringParameters": {},
        }
        return json.dumps(_invoke_lambda("weather", payload), indent=2)

    elif tool_name == "search_schemes":
        payload = {
            "httpMethod": "GET", "pathParameters": {},
            "queryStringParameters": {
                "keyword": tool_input.get("keyword", ""),
                "category": tool_input.get("category", ""),
            },
        }
        return json.dumps(_invoke_lambda("govt_schemes", payload), indent=2)

    elif tool_name == "get_farmer_profile":
        payload = {
            "httpMethod": "GET",
            "pathParameters": {"farmerId": tool_input.get("farmer_id", "")},
            "queryStringParameters": {},
        }
        return json.dumps(_invoke_lambda("farmer_profile", payload), indent=2)

    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ==================== Path A: API Key → invoke_model (Bearer token) ====================

_http_session = None


def _get_http_session():
    global _http_session
    if _http_session is None:
        import urllib3
        _http_session = urllib3.PoolManager(timeout=urllib3.Timeout(total=120.0))
    return _http_session


def _call_claude_apikey(messages):
    """Call Claude via invoke_model with Bearer API key auth. Returns Anthropic response dict."""
    url = f"https://bedrock-runtime.{MODEL_REGION}.amazonaws.com/model/{FOUNDATION_MODEL}/invoke"

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.3,
        "system": SYSTEM_PROMPT,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
    }).encode("utf-8")

    pool = _get_http_session()
    resp = pool.request(
        "POST", url,
        body=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {BEDROCK_API_KEY}",
        },
    )

    if resp.status != 200:
        raise Exception(f"Bedrock API error {resp.status}: {resp.data.decode()[:500]}")

    return json.loads(resp.data.decode("utf-8"))


# ==================== Path B: IAM → boto3 converse API ====================

_bedrock_client = None


def _get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        import boto3
        _bedrock_client = boto3.client("bedrock-runtime", region_name=MODEL_REGION)
    return _bedrock_client


def _anthropic_tools_to_converse():
    """Convert Anthropic tool format to Converse toolConfig."""
    return {
        "tools": [
            {
                "toolSpec": {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": {"json": t["input_schema"]},
                }
            }
            for t in TOOL_DEFINITIONS
        ]
    }


def _anthropic_msgs_to_converse(messages):
    """Convert Anthropic-format messages to Converse-format messages."""
    out = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if isinstance(content, str):
            out.append({"role": role, "content": [{"text": content}]})
            continue

        blocks = []
        for item in content:
            t = item.get("type", "")
            if t == "text":
                blocks.append({"text": item["text"]})
            elif t == "tool_use":
                blocks.append({
                    "toolUse": {
                        "toolUseId": item["id"],
                        "name": item["name"],
                        "input": item["input"],
                    }
                })
            elif t == "tool_result":
                blocks.append({
                    "toolResult": {
                        "toolUseId": item["tool_use_id"],
                        "content": [{"text": item["content"] if isinstance(item["content"], str) else json.dumps(item["content"])}],
                    }
                })
            else:
                blocks.append({"text": json.dumps(item)})
        out.append({"role": role, "content": blocks})
    return out


def _converse_to_anthropic(response):
    """Convert Converse response to Anthropic-compatible dict (content, stop_reason)."""
    msg = response.get("output", {}).get("message", {})
    stop_map = {"end_turn": "end_turn", "tool_use": "tool_use", "max_tokens": "max_tokens"}
    stop_reason = stop_map.get(response.get("stopReason", "end_turn"), "end_turn")

    content = []
    for block in msg.get("content", []):
        if "text" in block:
            content.append({"type": "text", "text": block["text"]})
        elif "toolUse" in block:
            tu = block["toolUse"]
            content.append({
                "type": "tool_use",
                "id": tu["toolUseId"],
                "name": tu["name"],
                "input": tu["input"],
            })

    return {"content": content, "stop_reason": stop_reason}


def _call_claude_iam(messages):
    """Call Claude via boto3 converse API with IAM role credentials. Returns Anthropic-compatible dict."""
    client = _get_bedrock_client()
    converse_msgs = _anthropic_msgs_to_converse(messages)
    tool_config = _anthropic_tools_to_converse()

    resp = client.converse(
        modelId=FOUNDATION_MODEL,
        system=[{"text": SYSTEM_PROMPT}],
        messages=converse_msgs,
        toolConfig=tool_config,
        inferenceConfig={"maxTokens": 4096, "temperature": 0.3},
    )

    return _converse_to_anthropic(resp)


# ==================== Unified Claude Dispatch ====================


def _call_claude(messages):
    """Call Claude using the configured auth method. Returns Anthropic-format response dict."""
    if USE_API_KEY:
        logger.info("Calling Claude via API key (invoke_model)")
        return _call_claude_apikey(messages)
    else:
        logger.info("Calling Claude via IAM role (converse)")
        return _call_claude_iam(messages)


def _run_agent_loop(prompt, context=None):
    """Run the agent loop: send prompt, handle tool calls, return final text."""
    messages = []
    tools_used = []

    # Build enriched prompt
    enriched = prompt
    if context:
        parts = []
        if context.get("state"):
            parts.append(f"State: {context['state']}")
        if context.get("crops"):
            parts.append(f"Crops: {', '.join(context['crops'])}")
        if context.get("soil_type"):
            parts.append(f"Soil: {context['soil_type']}")
        if parts:
            enriched = f"[Farmer context: {'; '.join(parts)}]\n\n{prompt}"

    messages.append({"role": "user", "content": enriched})

    for turn in range(MAX_TURNS):
        t0 = time.time()
        response = _call_claude(messages)
        logger.info(f"Claude response in {time.time()-t0:.1f}s, stop={response.get('stop_reason')}")

        content = response.get("content", [])
        stop_reason = response.get("stop_reason", "end_turn")

        if stop_reason == "end_turn" or stop_reason == "max_tokens":
            text_parts = [block["text"] for block in content if block.get("type") == "text"]
            return "\n".join(text_parts), tools_used

        if stop_reason == "tool_use":
            # Add assistant's response to messages
            messages.append({"role": "assistant", "content": content})

            # Execute each tool call
            tool_results = []
            for block in content:
                if block.get("type") == "tool_use":
                    tool_name = block["name"]
                    tool_input = block["input"]
                    tool_id = block["id"]

                    tools_used.append(tool_name)
                    result_str = _execute_tool(tool_name, tool_input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result_str,
                    })

            messages.append({"role": "user", "content": tool_results})
            continue

        # Unknown stop reason — extract text
        text_parts = [block["text"] for block in content if block.get("type") == "text"]
        return "\n".join(text_parts) if text_parts else "I couldn't process your request.", tools_used

    return "I reached the maximum number of tool calls. Here's what I found so far.", tools_used


# ==================== AgentCore Entrypoint ====================


@app.entrypoint
def invoke(payload: dict) -> dict:
    prompt = payload.get("prompt", "Hello!")
    farmer_id = payload.get("farmer_id", "anonymous")
    session_id = payload.get("session_id", "default")
    context = payload.get("context", {})

    logger.info(f"Invoke: farmer={farmer_id}, prompt={prompt[:100]}")

    try:
        result_text, tools_used = _run_agent_loop(prompt, context)
        return {
            "result": result_text,
            "tools_used": tools_used,
            "session_id": session_id,
            "farmer_id": farmer_id,
        }
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        return {
            "result": f"I apologize, I encountered an error processing your request. Please try again. Error: {str(e)[:200]}",
            "tools_used": [],
            "session_id": session_id,
            "farmer_id": farmer_id,
        }


if __name__ == "__main__":
    logger.info("Starting locally on port 8080...")
    app.run()
