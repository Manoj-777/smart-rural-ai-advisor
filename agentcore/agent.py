"""
Smart Rural AI Advisor - Lightweight AgentCore Runtime (boto3 converse)
======================================================================
Replaces heavy strands-agents SDK with direct boto3 bedrock-runtime converse()
to keep cold-start init under 10 seconds (strands-agents was exceeding 30s).

Architecture: 5 Cognitive agents + 1 Master (backward compat)
Each runtime uses the SAME agent.py + different AGENT_ROLE env var.

Owner: Manoj RS
"""

import json
import logging
import os
import time as _time
_t0 = _time.time()
# NOTE: boto3 and datetime are imported LAZILY inside functions to keep
# module-level init under the AgentCore 30-second cold-start limit.

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("smart-rural-agent")

# ==================== Configuration ====================

MODEL_ID = os.environ.get(
    "FOUNDATION_MODEL", "anthropic.claude-sonnet-4-5-20250929-v1:0"
)
AGENT_ROLE = os.environ.get("AGENT_ROLE", "master").strip().lower()
TOOLS_REGION = os.environ.get("AWS_REGION", "ap-south-1")

LAMBDA_NAMES = {
    "crop_advisory":  os.environ.get("LAMBDA_CROP",    "smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY"),
    "weather":        os.environ.get("LAMBDA_WEATHER",  "smart-rural-ai-WeatherFunction-dilSoHSLlXGN"),
    "govt_schemes":   os.environ.get("LAMBDA_SCHEMES",  "smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv"),
    "farmer_profile": os.environ.get("LAMBDA_PROFILE",  "smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt"),
}

logger.info(f"Config: role={AGENT_ROLE} | model={MODEL_ID}")

# ==================== Cognitive System Prompts ====================

COGNITIVE_PROMPTS = {

    "understanding": """You are the Understanding Agent in a multi-agent agricultural advisory system for Indian farmers.

YOUR COGNITIVE ROLE: Query comprehension, language detection, intent extraction, and entity recognition.

INPUT: Raw farmer query (may be in any Indian language: Tamil, Hindi, Telugu, Kannada, Malayalam, etc.)

YOUR TASKS:
1. LANGUAGE DETECTION: Identify the language of the query (return ISO code: ta, hi, te, kn, ml, en, etc.)
2. INTENT CLASSIFICATION: Classify into one or more categories:
   - weather, crop, pest, schemes, profile, general
3. ENTITY EXTRACTION: Pull out structured entities:
   - crop_name, location, season, symptoms, soil_type, farmer_id
4. CONFIDENCE SCORING: Rate your understanding confidence 0.0-1.0
5. ENRICHED QUERY: Rewrite the query in clear English for the Reasoning Agent

OUTPUT FORMAT (strict JSON - output ONLY valid JSON, nothing else):
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
  "enriched_query": "What paddy varieties are suitable for Kharif season in Thanjavur?",
  "original_language_summary": ""
}

RULES:
- ALWAYS output valid JSON, nothing else
- If context mentions farmer's known state/crops, use those for entity filling
- Never fabricate entities not mentioned or implied""",

    "reasoning": """You are the Reasoning Agent in a multi-agent agricultural advisory system for Indian farmers.

YOUR COGNITIVE ROLE: Data retrieval via tools, agricultural analysis, and recommendation synthesis.

YOUR TASKS:
1. TOOL SELECTION: Based on detected intents, call the appropriate tools:
   - weather intent -> get_weather(location)
   - crop intent -> get_crop_advisory(crop, state, season, soil_type)
   - pest intent -> get_pest_alert(crop, symptoms, state, season)
   - schemes intent -> search_schemes(keyword, category)
   - profile intent -> get_farmer_profile(farmer_id)
   - If multiple intents, call ALL relevant tools
2. DATA SYNTHESIS: Combine tool results into a comprehensive advisory
3. ACTIONABLE RECOMMENDATIONS: Provide specific, step-by-step farming actions
4. RISK ASSESSMENT: Flag any weather risks, pest threats, or time-sensitive actions

OUTPUT FORMAT:
- **Summary**: One-line answer
- **Detailed Advisory**: Full analysis with data from tools
- **Action Steps**: Numbered list of specific actions
- **Risks & Alerts**: Any warnings

RULES:
- ALWAYS call at least one tool before answering
- Use farmer context (state, crops, soil) to fill missing tool parameters
- Be specific to the farmer's region, crop, and season
- Include specific numbers (kg/hectare, cm of water, days to harvest, etc.)""",

    "fact_checking": """You are the Fact-Checking Agent in a multi-agent agricultural advisory system for Indian farmers.

YOUR COGNITIVE ROLE: Validate the Reasoning Agent's output against ground-truth tool data.

YOUR TASKS:
1. GROUNDING CHECK: Verify every factual claim in the advisory against the tool data
2. HALLUCINATION DETECTION: Flag any claims NOT supported by tool data
3. COMPLETENESS CHECK: Did the advisory address all detected intents?
4. SAFETY CHECK: Are recommendations safe for the farmer?
5. CONFIDENCE SCORING: Rate the advisory's reliability 0.0-1.0

OUTPUT FORMAT (strict JSON - output ONLY valid JSON, nothing else):
{
  "validated": true,
  "confidence": 0.95,
  "corrections": [],
  "warnings": [],
  "hallucinations_found": [],
  "final_advisory": "The corrected/validated advisory text...",
  "fact_check_summary": "All claims verified against tool data."
}

RULES:
- ALWAYS output valid JSON, nothing else
- If you find hallucinations, correct them in final_advisory
- Be strict about numbers: tool says 32C, advisory shouldn't say 35C
- Flag but don't block advisory if minor issues found""",

    "communication": """You are the Communication Agent in a multi-agent agricultural advisory system for Indian farmers.

YOUR COGNITIVE ROLE: Adapt the validated advisory for the target farmer's language, literacy level, and cultural context.

YOUR TASKS:
1. LANGUAGE ADAPTATION: Translate/adapt to the farmer's language using simple, conversational tone
2. CULTURAL LOCALIZATION: Use local measurement units, festival-based timing, familiar crop names
3. LITERACY ADAPTATION: Short sentences (max 15 words), bullet points, avoid jargon
4. FORMAT: Clear sections with headers, voice-ready natural speech patterns

OUTPUT: Return the adapted response as plain text in the target language.

RULES:
- NEVER use English terms when a good local equivalent exists
- Keep factual content identical - only change presentation/language
- Preserve all specific numbers, dates, and scheme names
- Maximum 500 words""",

    "memory": """You are the Memory Agent in a multi-agent agricultural advisory system for Indian farmers.

YOUR COGNITIVE ROLE: Manage conversation context, track farmer history, and recall relevant seasonal patterns.

YOUR TASKS:
1. CONTEXT ENRICHMENT: Fill in missing context from farmer's profile
2. SEASONAL AWARENESS: Know current farming activities and timing
3. HISTORY RECALL: Reference previous interactions if available

OUTPUT FORMAT (strict JSON - output ONLY valid JSON, nothing else):
{
  "enriched_context": {
    "state": "Tamil Nadu",
    "district": "Thanjavur",
    "crops": ["Paddy", "Banana"],
    "soil_type": "Clay loam",
    "season": "Kharif",
    "farming_type": "Irrigated"
  },
  "seasonal_context": "Currently Kharif sowing season in South India.",
  "context_gaps": [],
  "recommendations_for_reasoning": ""
}

RULES:
- ALWAYS output valid JSON, nothing else
- Use get_farmer_profile tool if farmer_id is available
- Infer season from current month if not specified
- Don't fabricate conversation history""",

    "master": """You are the Smart Rural AI Advisor, an expert Indian agricultural assistant \
helping small and marginal farmers across India. You are a trusted Krishi Mitra (farming friend).

You have access to specialized farming tools. ALWAYS use the relevant tools before answering:
- get_weather: For weather information (ALWAYS use when location is mentioned)
- get_crop_advisory: For crop guidance, varieties, growing conditions
- get_pest_alert: For pest/disease identification and treatment
- get_irrigation_advice: For irrigation scheduling, water requirements, drip/sprinkler methods
- search_schemes: For government schemes, subsidies, insurance
- get_farmer_profile: For farmer profile and personalized advice

IMPORTANT RULES:
1. ALWAYS call at least one tool - never answer purely from training data
2. If the farmer mentions a location, ALWAYS call get_weather first
3. Be specific to the farmer's region, crop, and season
4. Provide actionable step-by-step advice with specific numbers (kg/hectare, mm of water, litres/day)
5. Respond in the farmer's language if they write in a regional language
6. Include data sources in your response
7. For irrigation/water questions, ALWAYS call get_irrigation_advice — it has detailed crop water tables
8. For pest/disease questions with symptoms (yellow leaves, spots, wilting), ALWAYS call get_pest_alert
9. When farmer context is available (state, crops, soil_type), use it to fill missing tool parameters""",
}


# ==================== Lambda Invocation ====================

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


# ==================== Tool Definitions (for converse API) ====================

TOOL_SPECS = [
    {
        "toolSpec": {
            "name": "get_weather",
            "description": "Get real-time weather data with farming advisory for any location in India. Returns temperature, humidity, rainfall, wind, and agricultural recommendations.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City or location name in India"}
                    },
                    "required": ["location"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_crop_advisory",
            "description": "Get crop advisory for Indian agriculture including crop selection, growing conditions, varieties, fertilizers, and best practices based on region, soil type, and season.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "crop": {"type": "string", "description": "Crop name (e.g., Paddy, Wheat, Cotton)"},
                        "state": {"type": "string", "description": "Indian state name"},
                        "season": {"type": "string", "description": "Season: Kharif, Rabi, or Summer"},
                        "soil_type": {"type": "string", "description": "Soil type (e.g., Clay, Red soil, Black soil)"},
                        "query": {"type": "string", "description": "Free-text farming question"}
                    },
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_pest_alert",
            "description": "Identify crop pests and diseases with treatment recommendations for Indian agriculture. Provides both organic and chemical treatments.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "crop": {"type": "string", "description": "Crop name"},
                        "symptoms": {"type": "string", "description": "Visible symptoms on crop"},
                        "state": {"type": "string", "description": "Indian state name"},
                        "season": {"type": "string", "description": "Current season"}
                    },
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_irrigation_advice",
            "description": "Get irrigation recommendations including scheduling, water needs, and methods for specific crops in India.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "crop": {"type": "string", "description": "Crop name"},
                        "location": {"type": "string", "description": "Location in India"},
                        "soil_type": {"type": "string", "description": "Soil type"},
                        "query": {"type": "string", "description": "Specific irrigation question"}
                    },
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "search_schemes",
            "description": "Search Indian government agricultural schemes, subsidies, insurance, and loan programs available to farmers.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "Search keyword (e.g., kisan, insurance, subsidy)"},
                        "category": {"type": "string", "description": "Category filter"}
                    },
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_farmer_profile",
            "description": "Look up a farmer's saved profile including land details, crops, soil type, and advisory history for personalized recommendations.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "farmer_id": {"type": "string", "description": "Farmer ID"}
                    },
                    "required": ["farmer_id"]
                }
            }
        }
    },
]

# Tool dispatch: name -> (lambda_key, payload_builder)
def _build_weather_payload(args):
    return "weather", {
        "httpMethod": "GET",
        "pathParameters": {"location": args.get("location", "")},
        "queryStringParameters": {},
    }

def _build_crop_advisory_payload(args):
    return "crop_advisory", {
        "httpMethod": "GET", "pathParameters": {},
        "queryStringParameters": {
            "operation": "get_crop_advisory",
            "crop": args.get("crop", ""), "state": args.get("state", ""),
            "season": args.get("season", ""), "soil_type": args.get("soil_type", ""),
            "query": args.get("query", ""),
        },
    }

def _build_pest_alert_payload(args):
    return "crop_advisory", {
        "httpMethod": "GET", "pathParameters": {},
        "queryStringParameters": {
            "operation": "get_pest_alert",
            "crop": args.get("crop", ""), "symptoms": args.get("symptoms", ""),
            "state": args.get("state", ""), "season": args.get("season", ""),
        },
    }

def _build_irrigation_payload(args):
    return "crop_advisory", {
        "httpMethod": "GET", "pathParameters": {},
        "queryStringParameters": {
            "operation": "get_irrigation_advice",
            "crop": args.get("crop", ""), "location": args.get("location", ""),
            "soil_type": args.get("soil_type", ""), "query": args.get("query", ""),
        },
    }

def _build_schemes_payload(args):
    return "govt_schemes", {
        "httpMethod": "GET", "pathParameters": {},
        "queryStringParameters": {
            "keyword": args.get("keyword", ""), "category": args.get("category", ""),
        },
    }

def _build_profile_payload(args):
    return "farmer_profile", {
        "httpMethod": "GET",
        "pathParameters": {"farmerId": args.get("farmer_id", "")},
        "queryStringParameters": {},
    }

TOOL_DISPATCH = {
    "get_weather": _build_weather_payload,
    "get_crop_advisory": _build_crop_advisory_payload,
    "get_pest_alert": _build_pest_alert_payload,
    "get_irrigation_advice": _build_irrigation_payload,
    "search_schemes": _build_schemes_payload,
    "get_farmer_profile": _build_profile_payload,
}

# Which roles get tools
ROLE_TOOL_NAMES = {
    "understanding": [],
    "reasoning":     list(TOOL_DISPATCH.keys()),
    "fact_checking":  [],
    "communication": [],
    "memory":        ["get_farmer_profile"],
    "master":        list(TOOL_DISPATCH.keys()),
}


# ==================== Bedrock Converse Engine ====================

_bedrock_rt = None


def _get_bedrock_client():
    global _bedrock_rt
    if _bedrock_rt is None:
        import boto3
        _bedrock_rt = boto3.client("bedrock-runtime", region_name=TOOLS_REGION)
    return _bedrock_rt


def _converse(prompt, system_prompt, tool_names, max_turns=6):
    """
    Call Bedrock converse() with tool-use loop.
    Returns (response_text, tools_called_list).
    """
    client = _get_bedrock_client()
    tools_called = []

    # Build tool config if role has tools
    tool_config = None
    if tool_names:
        filtered = [t for t in TOOL_SPECS if t["toolSpec"]["name"] in tool_names]
        if filtered:
            tool_config = {"tools": filtered}

    messages = [{"role": "user", "content": [{"text": prompt}]}]
    system = [{"text": system_prompt}] if system_prompt else None

    for turn in range(max_turns):
        kwargs = {
            "modelId": MODEL_ID,
            "messages": messages,
            "inferenceConfig": {"maxTokens": 4096, "temperature": 0.3},
        }
        if system:
            kwargs["system"] = system
        if tool_config:
            kwargs["toolConfiguration"] = tool_config

        try:
            resp = client.converse(**kwargs)
        except Exception as e:
            logger.error(f"Converse error (turn {turn}): {e}")
            return f"Error calling model: {str(e)[:200]}", tools_called

        output = resp.get("output", {})
        msg = output.get("message", {})
        stop_reason = resp.get("stopReason", "end_turn")

        # Append assistant message to conversation
        if msg:
            messages.append(msg)

        # Check if model wants to use tools
        if stop_reason == "tool_use":
            tool_results = []
            for block in msg.get("content", []):
                if "toolUse" in block:
                    tool_use = block["toolUse"]
                    tool_name = tool_use["name"]
                    tool_id = tool_use["toolUseId"]
                    tool_input = tool_use.get("input", {})

                    logger.info(f"Tool call: {tool_name}({json.dumps(tool_input)[:200]})")
                    tools_called.append(tool_name)

                    # Execute the tool
                    builder = TOOL_DISPATCH.get(tool_name)
                    if builder:
                        lambda_key, payload = builder(tool_input)
                        result = _invoke_lambda(lambda_key, payload)
                        result_str = json.dumps(result, indent=2, default=str)
                        # Truncate very large results
                        if len(result_str) > 8000:
                            result_str = result_str[:8000] + "\n...(truncated)"
                    else:
                        result_str = json.dumps({"error": f"Unknown tool: {tool_name}"})

                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tool_id,
                            "content": [{"text": result_str}],
                        }
                    })

            # Send tool results back to model
            messages.append({"role": "user", "content": tool_results})
            continue

        # Model finished (end_turn or max_tokens) - extract text
        text_parts = []
        for block in msg.get("content", []):
            if "text" in block:
                text_parts.append(block["text"])
        return "\n".join(text_parts) if text_parts else "", tools_called

    # Exhausted turns - return last assistant text
    return "I was unable to complete the analysis within the allowed turns.", tools_called


# ==================== Helpers ====================

def _infer_india_season():
    import datetime
    month = datetime.datetime.utcnow().month
    if month in (6, 7, 8, 9, 10):
        return "Kharif"
    elif month in (11, 12, 1, 2, 3):
        return "Rabi"
    return "Summer"


def _parse_json_response(text):
    """Extract JSON from response, handling markdown fences."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        if first_newline >= 0:
            cleaned = cleaned[first_newline + 1:]
        cleaned = cleaned.rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def _append_sources(text, tools_used):
    """Append data source attribution to response."""
    cleaned = (text or "").strip()
    if not cleaned or not tools_used:
        return cleaned
    if "sources:" in cleaned.lower():
        return cleaned
    tool_labels = {
        "get_crop_advisory": "CropAdvisoryFunction(KB)",
        "get_pest_alert": "CropAdvisoryFunction(Pest)",
        "get_irrigation_advice": "CropAdvisoryFunction(Irrigation)",
        "get_weather": "WeatherFunction(OpenWeather)",
        "search_schemes": "GovtSchemesFunction",
        "get_farmer_profile": "FarmerProfileFunction",
    }
    unique = list(dict.fromkeys(tools_used))
    source_list = [tool_labels.get(t, t) for t in unique]
    return f"{cleaned}\n\nSources: {', '.join(source_list)}"


# ==================== Role-Specific Handlers ====================

def _invoke_understanding(payload):
    """Understanding Agent: Parse intent, extract entities, detect language."""
    prompt = payload.get("prompt", "")
    context = payload.get("context", {})

    parts = []
    if context.get("state"):
        parts.append(f"Farmer's state: {context['state']}")
    if context.get("district"):
        parts.append(f"Farmer's district: {context['district']}")
    if context.get("crops"):
        parts.append(f"Farmer's crops: {', '.join(context['crops'])}")
    if context.get("soil_type"):
        parts.append(f"Farmer's soil type: {context['soil_type']}")

    ctx_str = f"\n\nKnown farmer context:\n" + "\n".join(parts) if parts else ""
    full_prompt = f"Analyze this farmer's query and return structured JSON:\n\nQUERY: {prompt}{ctx_str}"

    sys_prompt = COGNITIVE_PROMPTS["understanding"]
    tool_names = ROLE_TOOL_NAMES.get("understanding", [])
    text, tools = _converse(full_prompt, sys_prompt, tool_names)
    parsed = _parse_json_response(text)

    if parsed:
        return {"result": json.dumps(parsed), "parsed": parsed, "agent_role": "understanding"}

    fallback = {
        "language": "en", "intents": ["general"], "entities": {},
        "confidence": 0.5, "enriched_query": prompt, "original_language_summary": "",
    }
    return {"result": json.dumps(fallback), "parsed": fallback, "agent_role": "understanding"}


def _invoke_reasoning(payload):
    """Reasoning Agent: Call tools and synthesize agricultural advice."""
    prompt = payload.get("prompt", "")
    context = payload.get("context", {})
    understanding = payload.get("understanding", {})

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
            f"[FARMER CONTEXT]\n{json.dumps(context)}\n\n"
            f"[ORIGINAL QUERY]\n{payload.get('prompt', '')}\n\n"
            f"Now call the appropriate tools and provide a comprehensive agricultural advisory."
        )

    sys_prompt = COGNITIVE_PROMPTS["reasoning"]
    tool_names = ROLE_TOOL_NAMES.get("reasoning", [])
    text, tools = _converse(reasoning_prompt, sys_prompt, tool_names)

    return {
        "result": _append_sources(text, tools),
        "tools_used": list(tools),
        "agent_role": "reasoning",
    }


def _invoke_fact_checking(payload):
    """Fact-Checking Agent: Validate reasoning output against tool data."""
    advisory_text = payload.get("advisory_text", "")
    tool_outputs = payload.get("tool_outputs", {})
    understanding = payload.get("understanding", {})

    tool_data_str = json.dumps(tool_outputs, indent=2)
    if len(tool_data_str) > 4000:
        tool_data_str = tool_data_str[:4000] + "\n... (truncated)"

    prompt = (
        f"[REASONING AGENT ADVISORY]\n{advisory_text}\n\n"
        f"[RAW TOOL DATA]\n{tool_data_str}\n\n"
        f"[UNDERSTANDING CONTEXT]\n"
        f"Intents: {json.dumps(understanding.get('intents', []))}\n"
        f"Entities: {json.dumps(understanding.get('entities', {}))}\n\n"
        f"Validate the advisory against the tool data. Return strict JSON."
    )

    sys_prompt = COGNITIVE_PROMPTS["fact_checking"]
    tool_names = ROLE_TOOL_NAMES.get("fact_checking", [])
    text, tools = _converse(prompt, sys_prompt, tool_names)
    parsed = _parse_json_response(text)

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

    return {
        "result": advisory_text,
        "validated": True, "confidence": 0.7,
        "corrections": [], "warnings": ["Fact-check output not parseable - advisory passed through"],
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

    prompt = (
        f"[VALIDATED ADVISORY]\n{advisory_text}\n\n"
        f"[TARGET LANGUAGE]: {target_language} ({lang_name})\n"
        f"[FARMER CONTEXT]: {json.dumps(farmer_context)}\n\n"
        f"Adapt this advisory for the farmer in simple, conversational {lang_name}. "
        f"Use local farming terms and measurement units. Keep it under 500 words."
    )

    sys_prompt = COGNITIVE_PROMPTS["communication"]
    tool_names = ROLE_TOOL_NAMES.get("communication", [])
    text, tools = _converse(prompt, sys_prompt, tool_names)

    return {"result": text, "target_language": target_language, "agent_role": "communication"}


def _invoke_memory(payload):
    """Memory Agent: Enrich context from farmer profile and history."""
    prompt = payload.get("prompt", "")
    context = payload.get("context", {})
    farmer_id = payload.get("farmer_id", "anonymous")

    import datetime
    memory_prompt = (
        f"[FARMER QUERY]: {prompt}\n"
        f"[FARMER ID]: {farmer_id}\n"
        f"[EXISTING CONTEXT]: {json.dumps(context)}\n"
        f"[CURRENT DATE]: {datetime.datetime.utcnow().strftime('%Y-%m-%d')}\n"
        f"[CURRENT SEASON]: {_infer_india_season()}\n\n"
        f"Enrich the farmer's context. If farmer_id is available and not 'anonymous', "
        f"call get_farmer_profile. Return structured JSON."
    )

    sys_prompt = COGNITIVE_PROMPTS["memory"]
    tool_names = ROLE_TOOL_NAMES.get("memory", [])
    text, tools = _converse(memory_prompt, sys_prompt, tool_names)
    parsed = _parse_json_response(text)

    if parsed:
        return {"result": json.dumps(parsed), "parsed": parsed, "agent_role": "memory"}

    fallback = {
        "enriched_context": context or {},
        "seasonal_context": f"Current season: {_infer_india_season()}",
        "context_gaps": [], "recommendations_for_reasoning": "",
    }
    return {"result": json.dumps(fallback), "parsed": fallback, "agent_role": "memory"}


def _invoke_master(payload):
    """Master Agent: Full pipeline in a single agent (backward compatible)."""
    prompt = payload.get("prompt", "")
    context = payload.get("context", {})

    ctx_str = ""
    if context:
        ctx_str = f"\n\nFarmer context: {json.dumps(context)}"

    sys_prompt = COGNITIVE_PROMPTS["master"]
    tool_names = ROLE_TOOL_NAMES.get("master", [])
    text, tools = _converse(f"{prompt}{ctx_str}", sys_prompt, tool_names)

    return {
        "result": _append_sources(text, tools),
        "tools_used": list(tools),
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
            "result": f"I apologize, I encountered an error processing your request. "
                      f"Please try again. ({str(e)[:200]})",
            "agent_role": AGENT_ROLE,
            "session_id": session_id,
            "farmer_id": farmer_id,
        }


# ==================== Runtime Registration ====================

logger.info(f"TIMING: pre-agentcore-import {_time.time()-_t0:.2f}s")
from bedrock_agentcore import BedrockAgentCoreApp
logger.info(f"TIMING: post-agentcore-import {_time.time()-_t0:.2f}s")

app = BedrockAgentCoreApp()
app.entrypoint(invoke)

logger.info(f"TIMING: entrypoint-registered {_time.time()-_t0:.2f}s | role={AGENT_ROLE}")

if __name__ == "__main__":
    logger.info(f"Starting locally (role={AGENT_ROLE})...")
    app.run()
