"""
Smart Rural AI Advisor — Cognitive Multi-Agent AgentCore Runtime
================================================================
Architecture: 5 Cognitive agents (not tool-wrapper specialists)

  ┌─────────────────────────────────────────────────────────────────┐
  │  Orchestrator Lambda (pipeline controller)                      │
  │                                                                 │
  │  User Query                                                     │
  │    ↓                                                            │
  │  ┌──────────────┐   ┌───────────────┐   ┌─────────────────┐    │
  │  │ Understanding │ → │   Reasoning   │ → │  Fact-Checking  │    │
  │  │    Agent      │   │    Agent      │   │     Agent       │    │
  │  │              │   │ (tools here)  │   │                 │    │
  │  └──────────────┘   └───────────────┘   └─────────────────┘    │
  │    ↑                                          ↓                │
  │  ┌──────────────┐                      ┌──────────────┐        │
  │  │ Memory Agent  │                      │Communication │        │
  │  │              │                      │    Agent     │        │
  │  └──────────────┘                      └──────────────┘        │
  │                                               ↓                │
  │                                         Final Response          │
  └─────────────────────────────────────────────────────────────────┘

Each runtime uses the SAME agent.py + different AGENT_ROLE env var.
Cognitive roles:
  - understanding : Query parsing, language detection, intent & entity extraction
  - reasoning     : Tool-calling agent, fetches data, synthesizes agricultural advice
  - fact_checking : Validates grounding against tool data, detects hallucinations
  - communication : Adapts response to farmer's language/literacy/dialect
  - memory        : Manages conversation context, farmer history, seasonal recall
  - master        : Legacy/fallback — full pipeline in a single agent (backward compat)

Owner: Manoj RS
"""

import json
import logging
import os
import sys
import time
import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("smart-rural-agent")

_start = time.time()
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
logger.info(f"App created in {time.time()-_start:.1f}s")

# ==================== Configuration ====================

MODEL_REGION = os.environ.get("MODEL_REGION", "ap-south-1")
FOUNDATION_MODEL = os.environ.get(
    "FOUNDATION_MODEL", "anthropic.claude-sonnet-4-5-20250929-v1:0"
)
FALLBACK_FOUNDATION_MODEL = os.environ.get(
    "FALLBACK_FOUNDATION_MODEL", "amazon.nova-lite-v1:0"
)
BEDROCK_API_KEY = os.environ.get("BEDROCK_API_KEY", "").strip()
USE_API_KEY = bool(BEDROCK_API_KEY)
BEDROCK_GUARDRAIL_ID = os.environ.get("BEDROCK_GUARDRAIL_ID", "").strip()
BEDROCK_GUARDRAIL_VERSION = os.environ.get("BEDROCK_GUARDRAIL_VERSION", "DRAFT").strip() or "DRAFT"
MAX_TURNS = int(os.environ.get("MAX_TURNS", "8"))
TOOLS_REGION = os.environ.get("AWS_REGION", "ap-south-1")

# ── Cognitive Role (set per runtime via env var) ──
AGENT_ROLE = os.environ.get("AGENT_ROLE", "master").strip().lower()

# Lambda function names (only used by reasoning + master + memory roles)
LAMBDA_NAMES = {
    "crop_advisory":  os.environ.get("LAMBDA_CROP",    "smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY"),
    "weather":        os.environ.get("LAMBDA_WEATHER",  "smart-rural-ai-WeatherFunction-dilSoHSLlXGN"),
    "govt_schemes":   os.environ.get("LAMBDA_SCHEMES",  "smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv"),
    "farmer_profile": os.environ.get("LAMBDA_PROFILE",  "smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt"),
}

logger.info(
    f"Cognitive role={AGENT_ROLE} | auth={'API_KEY' if USE_API_KEY else 'IAM'} | "
    f"model={FOUNDATION_MODEL} | region={MODEL_REGION}"
)


# ==================== Cognitive System Prompts ====================

COGNITIVE_PROMPTS = {

    # ────────── 1. UNDERSTANDING AGENT ──────────
    "understanding": """You are the Understanding Agent in a multi-agent agricultural advisory system for Indian farmers.

YOUR COGNITIVE ROLE: Query comprehension, language detection, intent extraction, and entity recognition.

INPUT: Raw farmer query (may be in any Indian language: Tamil, Hindi, Telugu, Kannada, Malayalam, etc.)

YOUR TASKS:
1. LANGUAGE DETECTION: Identify the language of the query (return ISO code: ta, hi, te, kn, ml, en, etc.)
2. INTENT CLASSIFICATION: Classify into one or more categories:
   - weather: Weather forecasts, rainfall, temperature, monsoon timing
   - crop: Crop selection, varieties, growing conditions, fertilizers, irrigation
   - pest: Pest identification, disease diagnosis, treatment recommendations
   - schemes: Government schemes, subsidies, insurance, loans, PM-KISAN
   - profile: Farmer profile lookup, personalized recommendations
   - general: General farming advice, greetings, chitchat
3. ENTITY EXTRACTION: Pull out structured entities:
   - crop_name: Specific crop mentioned (Rice, Wheat, Cotton, etc.)
   - location: Village/district/state mentioned
   - season: Kharif, Rabi, Summer, or inferred from date
   - symptoms: Pest/disease symptoms described
   - soil_type: Soil type mentioned
   - farmer_id: Farmer ID if mentioned
4. CONFIDENCE SCORING: Rate your understanding confidence 0.0-1.0
5. ENRICHED QUERY: Rewrite the query in clear English for the Reasoning Agent, preserving all farmer-specific details

OUTPUT FORMAT (strict JSON — output ONLY valid JSON, nothing else):
{
  "language": "ta",
  "intents": ["crop", "weather"],
  "entities": {
    "crop_name": "Paddy",
    "location": "Thanjavur, Tamil Nadu",
    "season": "Kharif",
    "symptoms": "",
    "soil_type": "Clay loam",
    "farmer_id": ""
  },
  "confidence": 0.92,
  "enriched_query": "What paddy varieties are suitable for Kharif season in Thanjavur, Tamil Nadu with clay loam soil, and what is the current weather outlook?",
  "original_language_summary": "நெல் சாகுபடி மற்றும் வானிலை பற்றிய கேள்வி"
}

RULES:
- ALWAYS output valid JSON, nothing else — no markdown fences, no explanation
- If the query is in an Indian language, still extract entities correctly
- If context mentions farmer's known state/crops, use those for entity filling
- For ambiguous intents, include all likely ones
- Never fabricate entities not mentioned or implied""",

    # ────────── 2. REASONING AGENT ──────────
    "reasoning": """You are the Reasoning Agent in a multi-agent agricultural advisory system for Indian farmers.

YOUR COGNITIVE ROLE: Data retrieval via tools, agricultural analysis, and recommendation synthesis.

INPUT: You receive a structured understanding from the Understanding Agent containing:
- Detected intents (weather, crop, pest, schemes, profile)
- Extracted entities (crop, location, season, symptoms, soil type)
- Enriched English query

YOUR TASKS:
1. TOOL SELECTION: Based on detected intents, call the appropriate tools:
   - weather intent → get_weather(location)
   - crop intent → get_crop_advisory(crop, state, season, soil_type)
   - pest intent → get_pest_alert(crop, symptoms, state, season)
   - schemes intent → search_schemes(keyword, category)
   - profile intent → get_farmer_profile(farmer_id)
   - If multiple intents, call ALL relevant tools
2. DATA SYNTHESIS: Combine tool results into a comprehensive advisory
3. ACTIONABLE RECOMMENDATIONS: Provide specific, step-by-step farming actions
4. RISK ASSESSMENT: Flag any weather risks, pest threats, or time-sensitive actions
5. CROSS-REFERENCE: If weather and crop data intersect, synthesize (e.g., "monsoon delay means postpone sowing")

OUTPUT FORMAT:
Provide a detailed agricultural advisory in English. Structure it as:
- **Summary**: One-line answer to the farmer's question
- **Detailed Advisory**: Full analysis with data from tools
- **Action Steps**: Numbered list of specific actions
- **Risks & Alerts**: Any warnings or time-sensitive info

RULES:
- ALWAYS call at least one tool before answering (never answer from general knowledge alone)
- Use farmer context (state, crops, soil) to fill missing tool parameters
- If a tool returns an error, note it and provide best-effort advice
- Be specific to the farmer's region, crop, and season — no generic advice
- Include specific numbers (kg/hectare, cm of water, days to harvest, etc.)""",

    # ────────── 3. FACT-CHECKING AGENT ──────────
    "fact_checking": """You are the Fact-Checking Agent in a multi-agent agricultural advisory system for Indian farmers.

YOUR COGNITIVE ROLE: Validate the Reasoning Agent's output against ground-truth tool data.

INPUT: You receive:
1. The Reasoning Agent's advisory text
2. The raw tool data (JSON from Lambda functions)
3. The Understanding Agent's parsed intents and entities

YOUR TASKS:
1. GROUNDING CHECK: Verify every factual claim in the advisory against the tool data
   - Weather numbers (temperature, rainfall) match get_weather output?
   - Crop recommendations align with get_crop_advisory data?
   - Pest treatments match get_pest_alert output?
   - Scheme details (amounts, eligibility) match search_schemes data?
2. HALLUCINATION DETECTION: Flag any claims NOT supported by tool data
   - Made-up statistics or numbers
   - Schemes or programs not in the data
   - Treatment recommendations not from the pest tool
3. COMPLETENESS CHECK: Did the advisory address all detected intents?
4. SAFETY CHECK: Are recommendations safe for the farmer?
   - Chemical dosages reasonable?
   - No harmful advice?
   - Government scheme eligibility criteria accurate?
5. CONFIDENCE SCORING: Rate the advisory's reliability 0.0-1.0

OUTPUT FORMAT (strict JSON — output ONLY valid JSON, nothing else):
{
  "validated": true,
  "confidence": 0.95,
  "corrections": [],
  "warnings": ["Rainfall data is 3 hours old — conditions may have changed"],
  "hallucinations_found": [],
  "completeness": {
    "intents_addressed": ["weather", "crop"],
    "intents_missed": [],
    "data_gaps": []
  },
  "final_advisory": "The corrected/validated advisory text goes here...",
  "fact_check_summary": "All claims verified against tool data. Weather data is current."
}

RULES:
- ALWAYS output valid JSON, nothing else — no markdown fences, no explanation
- If you find hallucinations, correct them in final_advisory
- If tool data is missing for a claim, mark it as a data gap (not necessarily wrong)
- Be strict about numbers: if the tool says 32°C, the advisory shouldn't say 35°C
- Flag but don't block advisory if minor issues found (farmer needs an answer)
- If the advisory is severely wrong, set validated=false and provide corrections""",

    # ────────── 4. COMMUNICATION AGENT ──────────
    "communication": """You are the Communication Agent in a multi-agent agricultural advisory system for Indian farmers.

YOUR COGNITIVE ROLE: Adapt the validated advisory for the target farmer's language, literacy level, and cultural context.

INPUT: You receive:
1. The fact-checked advisory text (in English)
2. Target language code (ta, hi, te, kn, ml, en, etc.)
3. Farmer context (location, crops, preferences)

YOUR TASKS:
1. LANGUAGE ADAPTATION: Translate/adapt the advisory to the farmer's language
   - Use simple, conversational language (not formal/literary)
   - Use local farming terminology (not textbook terms)
   - For Tamil: use spoken Tamil (பேச்சு தமிழ்), not formal (செய்யுள் தமிழ்)
   - For Hindi: use common Hindi (हिंदी), not Sanskritized
2. CULTURAL LOCALIZATION:
   - Use local measurement units (bigha, guntha, acre — not hectare for small farmers)
   - Reference local festivals/seasons for timing ("sow after Pongal" vs "sow in January")
   - Use familiar crop names in local language
3. LITERACY ADAPTATION:
   - Use short sentences (max 15 words)
   - Use bullet points for action steps
   - Avoid technical jargon unless the farmer asked in technical terms
4. FORMAT FOR CHANNEL:
   - Text: Clear sections with headers
   - Voice-ready: Remove markdown, use natural speech patterns

OUTPUT: Return the adapted response as plain text in the target language.
If the target language is English, still simplify and localize.

RULES:
- NEVER use English terms when a good local equivalent exists
- Keep the factual content identical — only change presentation/language
- If unsure about a local term, use the English term with local script transliteration
- Preserve all specific numbers, dates, and scheme names
- Maximum 500 words in the adapted response""",

    # ────────── 5. MEMORY AGENT ──────────
    "memory": """You are the Memory Agent in a multi-agent agricultural advisory system for Indian farmers.

YOUR COGNITIVE ROLE: Manage conversation context, track farmer history, and recall relevant seasonal patterns.

INPUT: You receive:
1. Current query context
2. Farmer ID and profile data (if available)
3. Conversation history (if available)

YOUR TASKS:
1. CONTEXT ENRICHMENT: Fill in missing context from farmer's profile
   - If farmer asks "how's my crop?" → recall their registered crops
   - If no location specified → use their registered district/state
   - If no season specified → infer from current date
2. CONVERSATION CONTINUITY: Track multi-turn context
   - "And what about pests?" → recall the crop from previous turn
   - "Same for wheat" → apply previous advice pattern to wheat
3. SEASONAL AWARENESS: Know what farming activities are timely
   - Is it sowing time for Kharif crops? Harvest time for Rabi?
   - Are there upcoming weather events (monsoon onset, cyclone season)?
4. HISTORY RECALL: What advice was given before
   - Avoid repeating identical advice
   - Reference previous interactions

OUTPUT FORMAT (strict JSON — output ONLY valid JSON, nothing else):
{
  "enriched_context": {
    "state": "Tamil Nadu",
    "district": "Thanjavur",
    "crops": ["Paddy", "Banana"],
    "soil_type": "Clay loam",
    "season": "Kharif",
    "farming_type": "Irrigated"
  },
  "conversation_notes": "Farmer previously asked about paddy pest control",
  "seasonal_context": "Currently Kharif sowing season in South India.",
  "context_gaps": ["No soil test data available"],
  "recommendations_for_reasoning": "Prioritize weather and pest data since Kharif sowing is imminent"
}

RULES:
- ALWAYS output valid JSON, nothing else — no markdown fences
- Use get_farmer_profile tool if farmer_id is available
- Infer season from current month if not specified
- Don't fabricate conversation history — only use what's provided
- Flag context gaps that should be asked about""",

    # ────────── LEGACY: Full-pipeline single agent ──────────
    "master": """You are the Smart Rural AI Advisor, an expert Indian agricultural assistant \
helping small and marginal farmers across India. You are a trusted Krishi Mitra (farming friend).

You have access to specialized farming tools. ALWAYS use the relevant tools before answering:
- get_weather: For weather information (ALWAYS use when location is mentioned)
- get_crop_advisory: For crop guidance, varieties, growing conditions
- get_pest_alert: For pest/disease identification and treatment
- get_irrigation_advice: For irrigation scheduling and methods
- search_schemes: For government schemes, subsidies, insurance
- get_farmer_profile: For farmer profile and personalized advice

IMPORTANT RULES:
1. ALWAYS call at least one tool — never answer purely from training data
2. If the farmer mentions a location, ALWAYS call get_weather first
3. Be specific to the farmer's region, crop, and season
4. Provide actionable step-by-step advice with specific numbers
5. Respond in the farmer's language if they write in a regional language
6. Include data sources in your response""",
}


# ==================== Tool Definitions ====================

TOOL_DEFINITIONS = [
    {
        "name": "get_crop_advisory",
        "description": "Get crop advisory guidance for Indian agriculture including crop selection, growing conditions, varieties, and best practices based on region, soil type, and season.",
        "input_schema": {
            "type": "object",
            "properties": {
                "crop": {"type": "string", "description": "Crop name (e.g., Rice, Wheat, Cotton)"},
                "state": {"type": "string", "description": "Indian state (e.g., Tamil Nadu)"},
                "season": {"type": "string", "description": "Growing season (Kharif, Rabi, Summer)"},
                "soil_type": {"type": "string", "description": "Soil type (Clay loam, Sandy, Red soil)"},
                "query": {"type": "string", "description": "Free-text farming question"},
            },
        },
    },
    {
        "name": "get_pest_alert",
        "description": "Identify crop pests and diseases with treatment recommendations. Provides both organic and chemical treatments.",
        "input_schema": {
            "type": "object",
            "properties": {
                "crop": {"type": "string", "description": "Name of affected crop"},
                "symptoms": {"type": "string", "description": "Symptom description (yellow leaves, brown spots)"},
                "state": {"type": "string", "description": "Indian state for regional pest data"},
                "season": {"type": "string", "description": "Current season"},
            },
        },
    },
    {
        "name": "get_irrigation_advice",
        "description": "Get irrigation recommendations including scheduling, water needs, and methods for specific crops.",
        "input_schema": {
            "type": "object",
            "properties": {
                "crop": {"type": "string", "description": "Crop name"},
                "location": {"type": "string", "description": "Location for weather-based advice"},
                "soil_type": {"type": "string", "description": "Soil type"},
                "query": {"type": "string", "description": "Irrigation-specific question"},
            },
        },
    },
    {
        "name": "get_weather",
        "description": "Get real-time weather data with farming advisory for any Indian location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or district in India"},
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
                "keyword": {"type": "string", "description": "Search term"},
                "category": {"type": "string", "description": "Category filter"},
            },
        },
    },
    {
        "name": "get_farmer_profile",
        "description": "Look up a farmer's saved profile for personalized advice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "farmer_id": {"type": "string", "description": "Unique farmer identifier"},
            },
            "required": ["farmer_id"],
        },
    },
]

# Memory Agent only has profile tool
MEMORY_TOOL_DEFINITIONS = [
    td for td in TOOL_DEFINITIONS if td["name"] == "get_farmer_profile"
]


def _get_tools_for_role(role):
    """Return tool definitions appropriate for the cognitive role."""
    if role in ("reasoning", "master"):
        return TOOL_DEFINITIONS
    elif role == "memory":
        return MEMORY_TOOL_DEFINITIONS
    else:
        # understanding, fact_checking, communication — no tools needed
        return []


def _get_system_prompt(role):
    """Return the system prompt for the given cognitive role."""
    return COGNITIVE_PROMPTS.get(role, COGNITIVE_PROMPTS["master"])


SYSTEM_PROMPT = _get_system_prompt(AGENT_ROLE)
ACTIVE_TOOLS = _get_tools_for_role(AGENT_ROLE)

logger.info(f"Cognitive Role: {AGENT_ROLE} | Tools: {len(ACTIVE_TOOLS)}")


# ==================== Season & Context Helpers ====================

def _infer_india_season():
    month = datetime.datetime.utcnow().month
    if month in (6, 7, 8, 9, 10):
        return "Kharif"
    elif month in (11, 12, 1, 2, 3):
        return "Rabi"
    return "Summer"


def _normalize_context_defaults(context):
    context = context or {}
    crops = context.get("crops") or []
    primary_crop = crops[0] if isinstance(crops, list) and crops else ""
    state = (context.get("state") or "").strip()
    district = (context.get("district") or "").strip()
    soil_type = (context.get("soil_type") or "").strip()
    season = (context.get("season") or "").strip() or _infer_india_season()
    weather_location = ", ".join([p for p in [district, state] if p])

    return {
        "state": state,
        "district": district,
        "soil_type": soil_type,
        "season": season,
        "primary_crop": primary_crop,
        "weather_location": weather_location,
    }


def _fill_tool_input_from_context(tool_name, tool_input, context_defaults):
    merged = dict(tool_input or {})
    defaults = context_defaults or {}

    def use_default(field, key=None):
        target_key = key or field
        if not str(merged.get(field, "")).strip():
            value = str(defaults.get(target_key, "")).strip()
            if value:
                merged[field] = value

    if tool_name in ("get_crop_advisory", "get_pest_alert"):
        use_default("state")
        use_default("season")
        use_default("crop", "primary_crop")

    if tool_name in ("get_crop_advisory", "get_irrigation_advice"):
        use_default("soil_type")

    if tool_name == "get_irrigation_advice":
        use_default("location", "weather_location")
        use_default("crop", "primary_crop")

    if tool_name == "get_weather":
        use_default("location", "weather_location")

    logger.info(f"Tool input after context fill ({tool_name}): {json.dumps(merged)[:250]}")
    return merged


# ==================== Tool Execution (Lambda Invocation) ====================

_lambda_client = None


def _get_lambda_client():
    global _lambda_client
    if _lambda_client is None:
        import boto3
        _lambda_client = boto3.client("lambda", region_name=TOOLS_REGION)
    return _lambda_client


def _invoke_lambda(function_key, payload):
    """Invoke a Lambda function and return parsed response body."""
    function_name = LAMBDA_NAMES.get(function_key)
    if not function_name:
        return {"error": f"Unknown function key: {function_key}"}

    client = _get_lambda_client()
    try:
        resp = client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode("utf-8"),
        )
        body = json.loads(resp["Payload"].read().decode("utf-8"))
        if isinstance(body, dict) and "body" in body:
            inner = body["body"]
            if isinstance(inner, str):
                try:
                    return json.loads(inner)
                except json.JSONDecodeError:
                    return {"raw": inner}
            return inner
        return body
    except Exception as e:
        logger.error(f"Lambda invoke error ({function_key}): {e}")
        return {"error": str(e)}


def _execute_tool(tool_name, tool_input, context_defaults=None):
    """Execute a tool and return the result string."""
    effective_input = _fill_tool_input_from_context(tool_name, tool_input, context_defaults)
    logger.info(f"Executing tool: {tool_name} with input: {json.dumps(effective_input)[:200]}")

    if tool_name == "get_crop_advisory":
        payload = {
            "httpMethod": "GET", "pathParameters": {},
            "queryStringParameters": {
                "operation": "get_crop_advisory",
                "crop": effective_input.get("crop", ""),
                "state": effective_input.get("state", ""),
                "season": effective_input.get("season", ""),
                "soil_type": effective_input.get("soil_type", ""),
                "query": effective_input.get("query", ""),
            },
        }
        return json.dumps(_invoke_lambda("crop_advisory", payload), indent=2)

    elif tool_name == "get_pest_alert":
        payload = {
            "httpMethod": "GET", "pathParameters": {},
            "queryStringParameters": {
                "operation": "get_pest_alert",
                "crop": effective_input.get("crop", ""),
                "symptoms": effective_input.get("symptoms", ""),
                "state": effective_input.get("state", ""),
                "season": effective_input.get("season", ""),
            },
        }
        return json.dumps(_invoke_lambda("crop_advisory", payload), indent=2)

    elif tool_name == "get_irrigation_advice":
        payload = {
            "httpMethod": "GET", "pathParameters": {},
            "queryStringParameters": {
                "operation": "get_irrigation_advice",
                "crop": effective_input.get("crop", ""),
                "location": effective_input.get("location", ""),
                "soil_type": effective_input.get("soil_type", ""),
                "query": effective_input.get("query", ""),
            },
        }
        return json.dumps(_invoke_lambda("crop_advisory", payload), indent=2)

    elif tool_name == "get_weather":
        payload = {
            "httpMethod": "GET",
            "pathParameters": {"location": effective_input.get("location", "")},
            "queryStringParameters": {},
        }
        return json.dumps(_invoke_lambda("weather", payload), indent=2)

    elif tool_name == "search_schemes":
        payload = {
            "httpMethod": "GET", "pathParameters": {},
            "queryStringParameters": {
                "keyword": effective_input.get("keyword", ""),
                "category": effective_input.get("category", ""),
            },
        }
        return json.dumps(_invoke_lambda("govt_schemes", payload), indent=2)

    elif tool_name == "get_farmer_profile":
        payload = {
            "httpMethod": "GET",
            "pathParameters": {"farmerId": effective_input.get("farmer_id", "")},
            "queryStringParameters": {},
        }
        return json.dumps(_invoke_lambda("farmer_profile", payload), indent=2)

    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ==================== Claude Invocation (IAM / API Key) ====================

_bedrock_client = None


def _get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        import boto3
        _bedrock_client = boto3.client("bedrock-runtime", region_name=MODEL_REGION)
    return _bedrock_client


def _anthropic_tools_to_converse(tools):
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
            for t in tools
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
    """Convert Converse response to Anthropic-compatible dict."""
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


def _call_claude_iam(messages, system_prompt=None, tools=None, model_id=None):
    """Call Claude via boto3 converse API with IAM role credentials."""
    client = _get_bedrock_client()
    converse_msgs = _anthropic_msgs_to_converse(messages)
    target_model = model_id or FOUNDATION_MODEL
    sys_prompt = system_prompt or SYSTEM_PROMPT

    converse_kwargs = {
        "modelId": target_model,
        "system": [{"text": sys_prompt}],
        "messages": converse_msgs,
        "inferenceConfig": {"maxTokens": 4096, "temperature": 0.3},
    }

    # Only include toolConfig if tools are provided
    if tools:
        converse_kwargs["toolConfig"] = _anthropic_tools_to_converse(tools)

    if BEDROCK_GUARDRAIL_ID:
        converse_kwargs["guardrailConfig"] = {
            "guardrailIdentifier": BEDROCK_GUARDRAIL_ID,
            "guardrailVersion": BEDROCK_GUARDRAIL_VERSION,
        }

    resp = client.converse(**converse_kwargs)
    return _converse_to_anthropic(resp)


_http_session = None


def _get_http_session():
    global _http_session
    if _http_session is None:
        import urllib3
        _http_session = urllib3.PoolManager(timeout=urllib3.Timeout(total=120.0))
    return _http_session


def _call_claude_apikey(messages, system_prompt=None, tools=None):
    """Call Claude via invoke_model with Bearer API key auth."""
    url = f"https://bedrock-runtime.{MODEL_REGION}.amazonaws.com/model/{FOUNDATION_MODEL}/invoke"
    sys_prompt = system_prompt or SYSTEM_PROMPT

    body_dict = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.3,
        "system": sys_prompt,
        "messages": messages,
    }
    if tools:
        body_dict["tools"] = tools

    body = json.dumps(body_dict).encode("utf-8")
    pool = _get_http_session()
    resp = pool.request(
        "POST", url, body=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {BEDROCK_API_KEY}",
        },
    )

    if resp.status != 200:
        raise Exception(f"Bedrock API error {resp.status}: {resp.data.decode()[:500]}")

    return json.loads(resp.data.decode("utf-8"))


def _call_claude(messages, system_prompt=None, tools=None):
    """Call Claude using the configured auth method. Returns Anthropic-format response dict."""
    if USE_API_KEY:
        logger.info("Calling Claude via API key (invoke_model)")
        return _call_claude_apikey(messages, system_prompt, tools)
    else:
        logger.info("Calling Claude via IAM role (converse)")
        try:
            return _call_claude_iam(messages, system_prompt, tools)
        except Exception as e:
            err = str(e)
            should_fallback = (
                "INVALID_PAYMENT_INSTRUMENT" in err
                or "AccessDeniedException" in err
                or "Model access is denied" in err
            )
            if should_fallback and FALLBACK_FOUNDATION_MODEL and FALLBACK_FOUNDATION_MODEL != FOUNDATION_MODEL:
                logger.warning(
                    f"Primary model failed ({FOUNDATION_MODEL}): {err[:180]} | "
                    f"Falling back to {FALLBACK_FOUNDATION_MODEL}"
                )
                return _call_claude_iam(messages, system_prompt, tools, model_id=FALLBACK_FOUNDATION_MODEL)
            raise


# ==================== Agent Loops ====================

def _append_sources_to_result(text, tools_used):
    """Append data source attribution to response."""
    cleaned = (text or "").strip()
    if not cleaned or not tools_used:
        return cleaned
    if "sources:" in cleaned.lower():
        return cleaned

    tool_labels = {
        "get_crop_advisory": "CropAdvisoryFunction(KB)",
        "get_pest_alert": "CropAdvisoryFunction(Pest Tool)",
        "get_irrigation_advice": "CropAdvisoryFunction(Irrigation Tool)",
        "get_weather": "WeatherFunction(OpenWeather)",
        "search_schemes": "GovtSchemesFunction",
        "get_farmer_profile": "FarmerProfileFunction",
    }
    unique_tools = list(dict.fromkeys(tools_used))
    source_list = [tool_labels.get(tool, tool) for tool in unique_tools]
    return f"{cleaned}\n\nSources: {', '.join(source_list)}"


def _run_tool_agent_loop(prompt, context=None, system_prompt=None, tools=None):
    """Run an agent loop WITH tool calling (for reasoning / master / memory roles).

    Returns: (result_text, tools_used, tool_outputs_dict)
    """
    messages = []
    tools_used = []
    tool_outputs = {}
    context_defaults = _normalize_context_defaults(context)
    active_tools = tools if tools is not None else ACTIVE_TOOLS
    sys_prompt = system_prompt or SYSTEM_PROMPT

    # Build enriched prompt with farmer context
    enriched = prompt
    if context:
        parts = []
        if context.get("state"):
            parts.append(f"State: {context['state']}")
        if context.get("district"):
            parts.append(f"District: {context['district']}")
        if context.get("crops"):
            parts.append(f"Crops: {', '.join(context['crops'])}")
        if context.get("soil_type"):
            parts.append(f"Soil: {context['soil_type']}")
        if parts:
            enriched = f"[Farmer context: {'; '.join(parts)}]\n\n{prompt}"

    messages.append({"role": "user", "content": enriched})

    for turn in range(MAX_TURNS):
        t0 = time.time()
        response = _call_claude(messages, system_prompt=sys_prompt, tools=active_tools if active_tools else None)
        logger.info(f"Claude response in {time.time()-t0:.1f}s, stop={response.get('stop_reason')}")

        content = response.get("content", [])
        stop_reason = response.get("stop_reason", "end_turn")

        if stop_reason in ("end_turn", "max_tokens"):
            text_parts = [block["text"] for block in content if block.get("type") == "text"]
            final_text = "\n".join(text_parts)
            return final_text, tools_used, tool_outputs

        if stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": content})

            tool_results = []
            for block in content:
                if block.get("type") == "tool_use":
                    tool_name = block["name"]
                    tool_input = block["input"]
                    tool_id = block["id"]

                    tools_used.append(tool_name)
                    result_str = _execute_tool(tool_name, tool_input, context_defaults)
                    tool_outputs[f"{tool_name}_{len(tools_used)}"] = result_str

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result_str,
                    })

            messages.append({"role": "user", "content": tool_results})
            continue

        # Unknown stop reason — extract text
        text_parts = [block["text"] for block in content if block.get("type") == "text"]
        fallback = "\n".join(text_parts) if text_parts else "I couldn't process your request."
        return fallback, tools_used, tool_outputs

    return "I reached the maximum number of tool calls.", tools_used, tool_outputs


def _run_cognitive_agent(prompt, system_prompt=None):
    """Run a single-turn cognitive agent WITHOUT tools (understanding/fact_checking/communication).

    Returns: text response string
    """
    sys_prompt = system_prompt or SYSTEM_PROMPT
    messages = [{"role": "user", "content": prompt}]

    t0 = time.time()
    response = _call_claude(messages, system_prompt=sys_prompt, tools=None)
    logger.info(f"Cognitive agent response in {time.time()-t0:.1f}s")

    content = response.get("content", [])
    text_parts = [block["text"] for block in content if block.get("type") == "text"]
    return "\n".join(text_parts)


def _parse_json_response(text):
    """Extract JSON from agent response, handling markdown fences."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        # Remove ```json or ``` prefix
        first_newline = cleaned.find("\n")
        if first_newline >= 0:
            cleaned = cleaned[first_newline + 1:]
        cleaned = cleaned.rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


# ==================== Role-Specific Handlers ====================

def _invoke_understanding(payload):
    """Understanding Agent: Parse intent, extract entities, detect language."""
    prompt = payload.get("prompt", "")
    context = payload.get("context", {})

    context_hint = ""
    if context:
        parts = []
        if context.get("state"):
            parts.append(f"Farmer's state: {context['state']}")
        if context.get("district"):
            parts.append(f"Farmer's district: {context['district']}")
        if context.get("crops"):
            parts.append(f"Farmer's crops: {', '.join(context['crops'])}")
        if context.get("soil_type"):
            parts.append(f"Farmer's soil_type: {context['soil_type']}")
        if parts:
            context_hint = f"\n\nKnown farmer context:\n" + "\n".join(parts)

    full_prompt = f"Analyze this farmer's query and return structured JSON:\n\nQUERY: {prompt}{context_hint}"

    result = _run_cognitive_agent(full_prompt)
    parsed = _parse_json_response(result)

    if parsed:
        return {
            "result": json.dumps(parsed),
            "parsed": parsed,
            "agent_role": "understanding",
        }
    else:
        logger.warning(f"Understanding agent returned non-JSON: {result[:200]}")
        fallback = {
            "language": "en",
            "intents": ["general"],
            "entities": {},
            "confidence": 0.5,
            "enriched_query": prompt,
            "original_language_summary": "",
        }
        return {
            "result": json.dumps(fallback),
            "parsed": fallback,
            "agent_role": "understanding",
        }


def _invoke_reasoning(payload):
    """Reasoning Agent: Call tools and synthesize agricultural advice."""
    prompt = payload.get("prompt", "")
    context = payload.get("context", {})
    understanding = payload.get("understanding", {})

    # Build reasoning-specific prompt enriched with Understanding output
    reasoning_prompt = prompt
    if understanding:
        intents = understanding.get("intents", [])
        entities = understanding.get("entities", {})
        enriched = understanding.get("enriched_query", prompt)

        reasoning_prompt = (
            f"[UNDERSTANDING AGENT OUTPUT]\n"
            f"Detected intents: {', '.join(intents)}\n"
            f"Entities: {json.dumps(entities)}\n"
            f"Enriched query: {enriched}\n\n"
            f"[ORIGINAL QUERY]\n{prompt}\n\n"
            f"Now call the appropriate tools and provide a comprehensive agricultural advisory."
        )

    result_text, tools_used, tool_outputs = _run_tool_agent_loop(reasoning_prompt, context)

    return {
        "result": _append_sources_to_result(result_text, tools_used),
        "tools_used": tools_used,
        "tool_outputs": tool_outputs,
        "agent_role": "reasoning",
    }


def _invoke_fact_checking(payload):
    """Fact-Checking Agent: Validate reasoning output against tool data."""
    advisory_text = payload.get("advisory_text", "")
    tool_outputs = payload.get("tool_outputs", {})
    understanding = payload.get("understanding", {})

    # Truncate tool outputs to fit context window
    tool_data_str = json.dumps(tool_outputs, indent=2)
    if len(tool_data_str) > 4000:
        tool_data_str = tool_data_str[:4000] + "\n... (truncated)"

    fact_check_prompt = (
        f"[REASONING AGENT ADVISORY]\n{advisory_text}\n\n"
        f"[RAW TOOL DATA]\n{tool_data_str}\n\n"
        f"[UNDERSTANDING CONTEXT]\n"
        f"Intents: {json.dumps(understanding.get('intents', []))}\n"
        f"Entities: {json.dumps(understanding.get('entities', {}))}\n\n"
        f"Validate the advisory against the tool data. Return strict JSON."
    )

    result = _run_cognitive_agent(fact_check_prompt)
    parsed = _parse_json_response(result)

    if parsed:
        return {
            "result": parsed.get("final_advisory", advisory_text),
            "validated": parsed.get("validated", True),
            "confidence": parsed.get("confidence", 0.8),
            "corrections": parsed.get("corrections", []),
            "warnings": parsed.get("warnings", []),
            "hallucinations_found": parsed.get("hallucinations_found", []),
            "fact_check_summary": parsed.get("fact_check_summary", ""),
            "agent_role": "fact_checking",
        }
    else:
        logger.warning(f"Fact-checking agent returned non-JSON: {result[:200]}")
        return {
            "result": advisory_text,  # Pass through unchanged
            "validated": True,
            "confidence": 0.7,
            "corrections": [],
            "warnings": ["Fact-check output was not parseable — advisory passed through"],
            "hallucinations_found": [],
            "fact_check_summary": "Unable to parse fact-check output",
            "agent_role": "fact_checking",
        }


def _invoke_communication(payload):
    """Communication Agent: Adapt response for farmer's language and literacy."""
    advisory_text = payload.get("advisory_text", "")
    target_language = payload.get("target_language", "en")
    farmer_context = payload.get("farmer_context", {})

    lang_names = {
        "ta": "Tamil", "hi": "Hindi", "te": "Telugu", "kn": "Kannada",
        "ml": "Malayalam", "mr": "Marathi", "bn": "Bengali", "gu": "Gujarati",
        "pa": "Punjabi", "or": "Odia", "as": "Assamese", "ur": "Urdu", "en": "English",
    }
    lang_name = lang_names.get(target_language, target_language)

    comm_prompt = (
        f"[VALIDATED ADVISORY]\n{advisory_text}\n\n"
        f"[TARGET LANGUAGE]: {target_language} ({lang_name})\n"
        f"[FARMER CONTEXT]: {json.dumps(farmer_context)}\n\n"
        f"Adapt this advisory for the farmer. Use simple, conversational {lang_name} language. "
        f"Use local farming terms and measurement units. Keep it under 500 words."
    )

    result = _run_cognitive_agent(comm_prompt)

    return {
        "result": result,
        "target_language": target_language,
        "agent_role": "communication",
    }


def _invoke_memory(payload):
    """Memory Agent: Enrich context from farmer profile and history."""
    prompt = payload.get("prompt", "")
    context = payload.get("context", {})
    farmer_id = payload.get("farmer_id", "anonymous")

    memory_prompt = (
        f"[FARMER QUERY]: {prompt}\n"
        f"[FARMER ID]: {farmer_id}\n"
        f"[EXISTING CONTEXT]: {json.dumps(context)}\n"
        f"[CURRENT DATE]: {datetime.datetime.utcnow().strftime('%Y-%m-%d')}\n"
        f"[CURRENT SEASON]: {_infer_india_season()}\n\n"
        f"Enrich the farmer's context. If farmer_id is available and not 'anonymous', "
        f"call get_farmer_profile. Return structured JSON with enriched context."
    )

    if farmer_id and farmer_id != "anonymous":
        # Use tool loop to call get_farmer_profile
        result_text, tools_used, tool_outputs = _run_tool_agent_loop(
            memory_prompt, context,
            system_prompt=COGNITIVE_PROMPTS["memory"],
            tools=MEMORY_TOOL_DEFINITIONS
        )
    else:
        result_text = _run_cognitive_agent(
            memory_prompt,
            system_prompt=COGNITIVE_PROMPTS["memory"]
        )
        tools_used = []
        tool_outputs = {}

    parsed = _parse_json_response(result_text)

    if parsed:
        return {
            "result": json.dumps(parsed),
            "parsed": parsed,
            "tools_used": tools_used,
            "agent_role": "memory",
        }
    else:
        logger.warning(f"Memory agent returned non-JSON: {result_text[:200]}")
        fallback = {
            "enriched_context": context or {},
            "seasonal_context": f"Current season: {_infer_india_season()}",
            "context_gaps": [],
            "recommendations_for_reasoning": "",
        }
        return {
            "result": json.dumps(fallback),
            "parsed": fallback,
            "tools_used": tools_used,
            "agent_role": "memory",
        }


def _invoke_master(payload):
    """Master Agent: Full pipeline in a single agent (backward compatible)."""
    prompt = payload.get("prompt", "")
    context = payload.get("context", {})

    result_text, tools_used, tool_outputs = _run_tool_agent_loop(prompt, context)

    return {
        "result": _append_sources_to_result(result_text, tools_used),
        "tools_used": tools_used,
        "agent_role": "master",
    }


# ==================== AgentCore Entrypoint ====================

ROLE_DISPATCH = {
    "understanding":  _invoke_understanding,
    "reasoning":      _invoke_reasoning,
    "fact_checking":  _invoke_fact_checking,
    "communication":  _invoke_communication,
    "memory":         _invoke_memory,
    "master":         _invoke_master,
}


@app.entrypoint
def invoke(payload: dict) -> dict:
    prompt = payload.get("prompt", "Hello!")
    farmer_id = payload.get("farmer_id", "anonymous")
    session_id = payload.get("session_id", "default")

    logger.info(f"Invoke [{AGENT_ROLE}]: farmer={farmer_id}, prompt={prompt[:100]}")

    handler = ROLE_DISPATCH.get(AGENT_ROLE, _invoke_master)

    try:
        result = handler(payload)
        result["session_id"] = session_id
        result["farmer_id"] = farmer_id
        return result
    except Exception as e:
        logger.error(f"Agent error [{AGENT_ROLE}]: {e}", exc_info=True)
        return {
            "result": f"I apologize, I encountered an error processing your request. Please try again. Error: {str(e)[:200]}",
            "tools_used": [],
            "session_id": session_id,
            "farmer_id": farmer_id,
            "agent_role": AGENT_ROLE,
        }


if __name__ == "__main__":
    logger.info(f"Starting locally on port 8080... (role={AGENT_ROLE})")
    app.run()
