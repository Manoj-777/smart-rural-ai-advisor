# backend/lambdas/agent_orchestrator/handler.py
# Main Lambda: API Gateway → Amazon Bedrock AgentCore Runtime → Format Response
# Owner: Manoj RS
# Endpoints: POST /chat, POST /voice
# See: Detailed_Implementation_Guide.md Section 9
#
# Supports two modes (auto-detected from env vars):
#   1. AgentCore Runtime — invoke_agent_runtime() via bedrock-agentcore client
#   2. Bedrock Agents (fallback) — invoke_agent() via bedrock-agent-runtime client

import json
import uuid
import boto3
import logging
import os
import re
import time as _time
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# API Gateway hard timeout is 29s. We must return before that.
API_GW_TIMEOUT_SEC = 29
TTS_TIME_BUDGET_SEC = 18  # skip TTS if elapsed > this

# Feature-page session prefixes: pre-structured prompts that
# don't need the 4-agent cognitive pipeline.
FAST_PATH_PREFIXES = ('crop-recommend-', 'soil-analysis-', 'farm-calendar-')

from utils.response_helper import success_response, error_response
from utils.translate_helper import detect_and_translate, translate_response, normalize_language_code
from utils.polly_helper import text_to_speech
from utils.dynamodb_helper import save_chat_message, get_farmer_profile

# Enterprise Guardrails (Gaps #1-#4, #6-#7)
from utils.guardrails import run_all_guardrails, mask_pii_in_log, run_output_guardrails
from utils.rate_limiter import check_rate_limit
from utils.audit_logger import (
    audit_request_start, audit_guardrail_block, audit_pii_detected,
    audit_tool_invocation, audit_policy_decision, audit_request_complete,
    audit_bedrock_guardrail,
)

# ── AgentCore Runtime mode (preferred) ──
# Legacy domain-specialist ARNs (backward compatible)
AGENTCORE_RUNTIME_ARN = os.environ.get('AGENTCORE_RUNTIME_ARN', '')
AGENTCORE_WEATHER_RUNTIME_ARN = os.environ.get('AGENTCORE_WEATHER_RUNTIME_ARN', '')
AGENTCORE_CROP_RUNTIME_ARN = os.environ.get('AGENTCORE_CROP_RUNTIME_ARN', '')
AGENTCORE_SCHEMES_RUNTIME_ARN = os.environ.get('AGENTCORE_SCHEMES_RUNTIME_ARN', '')
AGENTCORE_PROFILE_RUNTIME_ARN = os.environ.get('AGENTCORE_PROFILE_RUNTIME_ARN', '')
AGENTCORE_PEST_RUNTIME_ARN = os.environ.get('AGENTCORE_PEST_RUNTIME_ARN', '')

# ── Cognitive Multi-Agent Pipeline ARNs (new architecture) ──
AGENTCORE_UNDERSTANDING_ARN = os.environ.get('AGENTCORE_UNDERSTANDING_RUNTIME_ARN', '')
AGENTCORE_REASONING_ARN = os.environ.get('AGENTCORE_REASONING_RUNTIME_ARN', '')
AGENTCORE_FACTCHECK_ARN = os.environ.get('AGENTCORE_FACTCHECK_RUNTIME_ARN', '')
AGENTCORE_COMMUNICATION_ARN = os.environ.get('AGENTCORE_COMMUNICATION_RUNTIME_ARN', '')
AGENTCORE_MEMORY_ARN = os.environ.get('AGENTCORE_MEMORY_RUNTIME_ARN', '')

# Pipeline mode: 'cognitive' (new multi-agent) or 'specialist' (legacy domain fan-out)
PIPELINE_MODE = os.environ.get('PIPELINE_MODE', 'cognitive')
ENABLE_SPECIALIST_FANOUT = os.environ.get('ENABLE_SPECIALIST_FANOUT', 'true').lower() == 'true'
ENFORCE_CODE_POLICY = os.environ.get('ENFORCE_CODE_POLICY', 'true').lower() == 'true'

# ── Bedrock Guardrail (Gap #5: AWS-native content/PII/topic filtering) ──
BEDROCK_GUARDRAIL_ID = os.environ.get('BEDROCK_GUARDRAIL_ID', '')
BEDROCK_GUARDRAIL_VERSION = os.environ.get('BEDROCK_GUARDRAIL_VERSION', '')

def _guardrail_config():
    """Return guardrailConfig dict for Bedrock converse() if guardrail is set up."""
    if BEDROCK_GUARDRAIL_ID and BEDROCK_GUARDRAIL_VERSION:
        return {
            'guardrailIdentifier': BEDROCK_GUARDRAIL_ID,
            'guardrailVersion': BEDROCK_GUARDRAIL_VERSION,
        }
    return None

# ── Bedrock Agents mode (fallback) ──
AGENT_ID = os.environ.get('BEDROCK_AGENT_ID', '')
AGENT_ALIAS_ID = os.environ.get('BEDROCK_AGENT_ALIAS_ID', '')

# Auto-detect which mode to use
USE_AGENTCORE = bool(AGENTCORE_RUNTIME_ARN)

FOUNDATION_MODEL = os.environ.get('FOUNDATION_MODEL', 'apac.amazon.nova-pro-v1:0')
LAMBDA_WEATHER = os.environ.get('LAMBDA_WEATHER', 'smart-rural-ai-WeatherFunction-dilSoHSLlXGN')
LAMBDA_CROP = os.environ.get('LAMBDA_CROP', 'smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY')
LAMBDA_SCHEMES = os.environ.get('LAMBDA_SCHEMES', 'smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv')
LAMBDA_PROFILE = os.environ.get('LAMBDA_PROFILE', 'smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt')

# Bedrock Runtime client for direct model invocation (fallback when AgentCore is cold)
bedrock_rt = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
lambda_client = boto3.client('lambda', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))

if USE_AGENTCORE:
    logger.info(f"Mode: AgentCore Runtime — ARN: {AGENTCORE_RUNTIME_ARN} | Pipeline: {PIPELINE_MODE}")
    if PIPELINE_MODE == 'cognitive':
        logger.info(
            f"Cognitive ARNs: Understanding={bool(AGENTCORE_UNDERSTANDING_ARN)}, "
            f"Reasoning={bool(AGENTCORE_REASONING_ARN)}, "
            f"FactCheck={bool(AGENTCORE_FACTCHECK_ARN)}, "
            f"Communication={bool(AGENTCORE_COMMUNICATION_ARN)}, "
            f"Memory={bool(AGENTCORE_MEMORY_ARN)}"
        )
    agentcore_runtime = boto3.client('bedrock-agentcore', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
else:
    bedrock_agent = boto3.client('bedrock-agent-runtime')
    logger.info(f"Mode: Bedrock Agents — Agent: {AGENT_ID}, Alias: {AGENT_ALIAS_ID}")


AGRI_POLICY_KEYWORDS = {
    'crop', 'farming', 'farm', 'farmer', 'weather', 'rain', 'rainfall', 'monsoon',
    'temperature', 'soil', 'irrigation', 'seed', 'sowing', 'harvest', 'yield',
    'fertilizer', 'manure', 'pest', 'disease', 'fungus', 'insect', 'spray',
    'scheme', 'subsidy', 'loan', 'insurance', 'pm-kisan', 'kisan', 'yojana',
    'kharif', 'rabi', 'cotton', 'rice', 'wheat', 'maize', 'paddy', 'vegetable',
    'horticulture', 'agri', 'cattle', 'dairy', 'goat', 'poultry'
}

SAFE_CHITCHAT = {'hi', 'hello', 'hey', 'thanks', 'thank you', 'ok', 'okay'}


def _sanitize_user_message(text):
    cleaned = (text or '').strip()
    if not cleaned:
        return cleaned
    cleaned = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', cleaned)
    cleaned = re.sub(r'([,.;:!?()\-])\1{2,}', r'\1', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def _contains_indic_chars(text):
    if not text:
        return False
    return bool(re.search(r'[\u0900-\u0D7F]', text))


def _is_on_topic_query(text):
    normalized = (text or '').lower().strip()
    if not normalized:
        return True
    if normalized in SAFE_CHITCHAT:
        return True
    if _contains_indic_chars(normalized):
        return True
    return any(keyword in normalized for keyword in AGRI_POLICY_KEYWORDS)


def _off_topic_response():
    return (
        "I can help only with agriculture and rural livelihood topics, such as crops, pests, weather, "
        "irrigation, market prices, and government schemes. Please ask a farming-related question."
    )


def _requires_grounded_tools(intents):
    required = {'weather', 'crop', 'pest', 'schemes', 'profile'}
    return bool(set(intents or []) & required)


def _grounding_prompt_for_intents(intents):
    intent_set = set(intents or [])
    if 'weather' in intent_set:
        return "Please share your location (village/town/city) so I can fetch a weather update."
    if 'pest' in intent_set:
        return "Please share your crop, location, and visible symptoms so I can give a reliable pest advisory."
    if 'crop' in intent_set:
        return "Please share your location, season, and crop preference so I can give a reliable crop advisory."
    if 'schemes' in intent_set:
        return "Please share your state and farmer category so I can find relevant government schemes."
    if 'profile' in intent_set:
        return "Please share your farmer ID or profile details so I can give profile-based advice."
    return (
        "Please share your crop, location, season, and symptoms so I can provide a reliable advisory."
    )


def _strip_sources_line(text):
    """Remove any 'Sources: ...' line from the text (agent.py may have added it).
    Returns (cleaned_text, extracted_sources_str_or_None)."""
    if not text:
        return text, None
    import re as _re
    match = _re.search(r'\n\s*Sources:\s*(.+)$', text)
    if match:
        return text[:match.start()].rstrip(), match.group(1).strip()
    return text, None


def _build_sources_line(tools_used):
    """Build a sources attribution string from tool names (never translated)."""
    if not tools_used:
        return None
    tool_labels = {
        'get_weather': 'WeatherFunction(OpenWeather)',
        'get_crop_advisory': 'CropAdvisoryFunction(KB)',
        'get_pest_alert': 'CropAdvisoryFunction(Pest Tool)',
        'get_irrigation_advice': 'CropAdvisoryFunction(Irrigation Tool)',
        'search_schemes': 'GovtSchemesFunction',
        'get_farmer_profile': 'FarmerProfileFunction',
    }
    unique_tools = list(dict.fromkeys(tools_used))
    source_list = [tool_labels.get(tool, tool) for tool in unique_tools]
    return ', '.join(source_list)


def _append_sources(reply_en, tools_used):
    """Append sources line to English text. Only used for reply_en field."""
    text = (reply_en or '').strip()
    if not text or not tools_used:
        return text

    # Strip any existing sources line first (avoid duplicates from agent.py)
    text, _ = _strip_sources_line(text)

    sources = _build_sources_line(tools_used)
    if sources:
        return f"{text}\n\nSources: {sources}"
    return text


def _apply_code_policy(user_query_en, intents, result_text, tools_used, original_query=None):
    policy_meta = {
        'code_policy_enforced': ENFORCE_CODE_POLICY,
        'off_topic_blocked': False,
        'grounding_required': _requires_grounded_tools(intents),
        'grounding_satisfied': bool(tools_used),
    }

    if not ENFORCE_CODE_POLICY:
        return result_text, tools_used, policy_meta

    if not (_is_on_topic_query(user_query_en) or _is_on_topic_query(original_query)):
        policy_meta['off_topic_blocked'] = True
        return _off_topic_response(), [], policy_meta

    cleaned_tools = list(dict.fromkeys(tools_used or []))
    text = (result_text or '').strip()

    if not text:
        text = "I need a bit more farm context to provide a reliable advisory."

    is_warmup_or_runtime_msg = any(token in text.lower() for token in [
        'warming up',
        'runtime initialization',
        'please try again in a minute',
        'runtimeclienterror',
        'timeout',
        'error processing',
        'error calling model',
        'apologize',
    ])

    # If it's a runtime error/warm-up message, pass it through instead of masking
    if is_warmup_or_runtime_msg:
        logger.warning(f"Runtime message detected (passing through): {text[:200]}")
        return text, cleaned_tools, policy_meta

    if policy_meta['grounding_required'] and not cleaned_tools:
        # If the AI already generated a substantive response (>200 chars),
        # allow it through — the query itself contained enough data
        if len(text) > 200:
            logger.info("Grounding: no tools but response is substantive — passing through")
            policy_meta['grounding_satisfied'] = True
        else:
            policy_meta['grounding_satisfied'] = False
            text = _grounding_prompt_for_intents(intents)

    text = _append_sources(text, cleaned_tools)

    if len(text) > 5000:
        text = text[:5000].rsplit(' ', 1)[0] + '...'

    return text, cleaned_tools, policy_meta


def _invoke_agentcore_runtime(prompt, session_id, farmer_context=None):
    """
    Invoke the agent hosted on AgentCore Runtime.
    """
    payload = {
        "prompt": prompt,
        "session_id": session_id,
        "farmer_id": farmer_context.get("name", "anonymous") if farmer_context else "anonymous",
    }
    if farmer_context:
        payload["context"] = farmer_context

    try:
        response = agentcore_runtime.invoke_agent_runtime(
            agentRuntimeArn=AGENTCORE_RUNTIME_ARN,
            runtimeSessionId=session_id,
            payload=json.dumps(payload).encode('utf-8'),
            qualifier='DEFAULT',
        )
        
        # Parse the response (SDKs may return payload or response field)
        response_payload = response.get('response', response.get('payload', ''))
        if response_payload:
            if isinstance(response_payload, bytes):
                response_payload = response_payload.decode('utf-8')
            elif hasattr(response_payload, 'read'):
                response_payload = response_payload.read().decode('utf-8')
            
            # Parse JSON response
            try:
                parsed = json.loads(response_payload)
                result_text = parsed.get('result', response_payload)
                tools_used = parsed.get('tools_used', [])
            except (json.JSONDecodeError, TypeError):
                result_text = response_payload
                tools_used = []
        else:
            result_text = "I apologize, I received an unexpected response format."
            tools_used = []

        return result_text, tools_used
        
    except Exception as e:
        logger.error(f"AgentCore invocation error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # AgentCore may be cold-starting — return friendly retry message
        error_msg = str(e)
        if 'RuntimeClientError' in error_msg or 'timeout' in error_msg.lower():
            return ("I'm warming up the AI advisor — this takes about 60 seconds on first use. "
                    "Please try again in a minute!"), []
        return f"I apologize, I encountered an error processing your request. Please try again.", []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DIRECT BEDROCK FALLBACK (bypasses AgentCore when runtimes are cold)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DIRECT_SYSTEM_PROMPT = """You are the Smart Rural AI Advisor — a cognitive agricultural assistant for Indian farmers.
You combine 5 cognitive roles: Understanding, Reasoning, Fact-Checking, Communication, and Memory.

CRITICAL RULES:
1. Use tools for EVERY weather, crop, pest, irrigation, or scheme query — NEVER guess data
2. Always ground answers in real tool outputs
3. Keep advice practical, region-specific, and season-aware
4. Be culturally sensitive to Indian farming practices
5. If data is unavailable, say so honestly
6. For irrigation/water queries, always call get_crop_advisory with query_type='irrigation' — the Knowledge Base has detailed water tables, drip/sprinkler guides, and crop water needs
7. For pest/disease queries with symptoms (yellow leaves, spots, wilting), always call get_pest_alert — the KB has pesticide guides, dosages, and treatment protocols
8. When farmer context is provided, use it to fill missing parameters (state, crop, soil_type) for better results
9. Provide specific numbers: kg/hectare, mm of water, litres/day, days to harvest, etc.

You have access to tools for weather lookup, crop advisory (including irrigation), pest alerts, government schemes, and farmer profiles.
Always call the relevant tool first, then synthesize the response from tool data."""

DIRECT_TOOLS = [
    {
        "toolSpec": {
            "name": "get_weather",
            "description": "Get current weather for a location in India. Returns temperature, humidity, rainfall, wind, and forecast.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City or village name in India (e.g., 'Coimbatore', 'Pune')"},
                        "days": {"type": "integer", "description": "Number of forecast days (1-7)", "default": 3}
                    },
                    "required": ["location"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_crop_advisory",
            "description": "Get crop recommendations, growing advice, varieties, fertilizer schedules, and irrigation guidance from the Knowledge Base. Use query_type='irrigation' specifically for water requirements, irrigation scheduling, drip/sprinkler methods, and water management queries.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "Farmer's location (district/state)"},
                        "crop": {"type": "string", "description": "Crop name (e.g., 'Rice', 'Cotton')"},
                        "season": {"type": "string", "description": "Season: kharif, rabi, or summer"},
                        "soil_type": {"type": "string", "description": "Soil type (e.g., 'Clay', 'Loam', 'Red soil')"},
                        "query_type": {"type": "string", "description": "One of: recommendation, pest, irrigation, general. Use 'irrigation' for water/watering queries."}
                    },
                    "required": ["location"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "search_schemes",
            "description": "Search Indian government agricultural schemes, subsidies, loans, and insurance programs.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query for schemes"},
                        "state": {"type": "string", "description": "Indian state name"},
                        "category": {"type": "string", "description": "Category: subsidy, loan, insurance, general"}
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_farmer_profile",
            "description": "Retrieve a farmer's profile including crops, soil type, location, and preferences.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "farmer_id": {"type": "string", "description": "The farmer's ID"}
                    },
                    "required": ["farmer_id"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_pest_alert",
            "description": "Get pesticide product guides, pest alerts, disease identification, and treatment recommendations from the Knowledge Base. Use this for: yellow leaves, brown spots, wilting, rotting, insect damage, fungal infections, and any crop health problems. Returns specific pesticide names, dosages, organic alternatives, and prevention methods.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Detailed pest/disease/pesticide query describing symptoms and crop"},
                        "crop": {"type": "string", "description": "Crop name (e.g., Rice, Wheat, Cotton)"},
                        "symptoms": {"type": "string", "description": "Visible symptoms: yellow leaves, brown spots, wilting, holes, etc."},
                        "location": {"type": "string", "description": "Farmer location (state/district)"},
                        "season": {"type": "string", "description": "Current season: kharif, rabi, summer"}
                    },
                    "required": ["query"]
                }
            }
        }
    }
]

# Map tool names to Lambda function names
TOOL_TO_LAMBDA = {
    "get_weather": LAMBDA_WEATHER,
    "get_crop_advisory": LAMBDA_CROP,
    "get_pest_alert": LAMBDA_CROP,
    "search_schemes": LAMBDA_SCHEMES,
    "get_farmer_profile": LAMBDA_PROFILE,
}


def _execute_tool(tool_name, tool_input):
    """Execute a tool by invoking the corresponding Lambda function."""
    lambda_name = TOOL_TO_LAMBDA.get(tool_name)
    if not lambda_name:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        # Build Lambda payload based on tool
        if tool_name == "get_weather":
            # Weather Lambda reads from pathParameters.location (API Gateway: /weather/{location})
            lambda_payload = {"pathParameters": {"location": tool_input.get("location", "Chennai")}}
        elif tool_name == "get_crop_advisory":
            lambda_payload = {"queryStringParameters": tool_input}
        elif tool_name == "get_pest_alert":
            # Route pest queries to crop advisory Lambda with KB lookup
            lambda_payload = {"queryStringParameters": tool_input}
        elif tool_name == "search_schemes":
            lambda_payload = {"queryStringParameters": tool_input}
        elif tool_name == "get_farmer_profile":
            lambda_payload = {"pathParameters": {"farmerId": tool_input.get("farmer_id", "")}}
        else:
            lambda_payload = {"body": json.dumps(tool_input)}

        response = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(lambda_payload).encode(),
        )
        resp_payload = json.loads(response["Payload"].read().decode())

        # Parse Lambda response
        if isinstance(resp_payload, dict) and "body" in resp_payload:
            body = resp_payload["body"]
            if isinstance(body, str):
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    return {"result": body}
            return body
        return resp_payload
    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {str(e)}")
        return {"error": str(e)}


def _invoke_bedrock_direct(prompt, farmer_context=None):
    """
    Call Bedrock model directly with tool use (converse API).
    Fallback when AgentCore runtimes are cold-starting.
    Returns: (result_text, tools_used, tool_data_log)
    """
    tools_used = []
    tool_data_log = []  # raw tool results for fact-checking

    # Build messages
    system_prompt = DIRECT_SYSTEM_PROMPT
    if farmer_context:
        system_prompt += f"\n\nFarmer context: {json.dumps(farmer_context)}"

    messages = [{"role": "user", "content": [{"text": prompt}]}]

    try:
        # Multi-turn tool use loop (max 5 turns)
        for turn in range(5):
            converse_kwargs = {
                "modelId": FOUNDATION_MODEL,
                "messages": messages,
                "system": [{"text": system_prompt}],
                "toolConfig": {"tools": DIRECT_TOOLS},
                "inferenceConfig": {"maxTokens": 2048, "temperature": 0.3},
            }
            # Gap #5: Attach Bedrock native guardrail if configured
            gc = _guardrail_config()
            if gc:
                converse_kwargs['guardrailConfig'] = gc

            response = bedrock_rt.converse(**converse_kwargs)
            output = response.get("output", {})
            message = output.get("message", {})
            stop_reason = response.get("stopReason", "")

            # Add assistant message to conversation
            messages.append(message)

            # Check if model wants to use a tool
            if stop_reason == "tool_use":
                tool_results = []
                for block in message.get("content", []):
                    if "toolUse" in block:
                        tool_use = block["toolUse"]
                        tool_name = tool_use["name"]
                        tool_input = tool_use.get("input", {})
                        tool_id = tool_use["toolUseId"]

                        logger.info(f"Direct Bedrock tool call: {tool_name}({json.dumps(tool_input)[:100]})")
                        tools_used.append(tool_name)
                        result = _execute_tool(tool_name, tool_input)

                        # Save raw tool data for fact-checking
                        tool_data_log.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "output": result,
                        })

                        tool_results.append({
                            "toolResult": {
                                "toolUseId": tool_id,
                                "content": [{"json": result}],
                            }
                        })

                # Add tool results to messages
                messages.append({"role": "user", "content": tool_results})
                continue

            # Model is done — extract final text
            result_text = ""
            for block in message.get("content", []):
                if "text" in block:
                    result_text += block["text"]

            logger.info(f"Direct Bedrock response: {len(result_text)} chars, tools={tools_used}")
            return result_text, tools_used, tool_data_log

        # Exhausted turns
        return "I'm having trouble processing your request. Please try again.", tools_used, tool_data_log

    except Exception as e:
        logger.error(f"Direct Bedrock invocation error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return f"I apologize, I encountered an error. Please try again.", [], []


def _invoke_agentcore_runtime_with_arn(runtime_arn, prompt, session_id, farmer_context=None):
    if not runtime_arn:
        return "", []

    payload = {
        "prompt": prompt,
        "session_id": session_id,
        "farmer_id": farmer_context.get("name", "anonymous") if farmer_context else "anonymous",
    }
    if farmer_context:
        payload["context"] = farmer_context

    try:
        response = agentcore_runtime.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            runtimeSessionId=session_id,
            payload=json.dumps(payload).encode('utf-8'),
            qualifier='DEFAULT',
        )

        response_payload = response.get('response', response.get('payload', ''))
        if isinstance(response_payload, bytes):
            response_payload = response_payload.decode('utf-8')
        elif hasattr(response_payload, 'read'):
            response_payload = response_payload.read().decode('utf-8')

        try:
            parsed = json.loads(response_payload)
            result_text = parsed.get('result', response_payload)
            tools_used = parsed.get('tools_used', [])
        except (json.JSONDecodeError, TypeError):
            result_text = str(response_payload)
            tools_used = []

        return result_text, tools_used
    except Exception as e:
        logger.error(f"Specialist runtime invocation failed ({runtime_arn}): {str(e)}")
        return "", []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COGNITIVE MULTI-AGENT PIPELINE  (4 Bedrock converse() agents)
#  Flow: Understanding → Reasoning (with tools) → Fact-Checking → Communication
#  Each agent = separate Bedrock converse() call with role-specific system prompt
#  Total pipeline ~12-19s, fits within 29s API Gateway limit
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Agent 1: Understanding Agent ──
UNDERSTANDING_SYSTEM_PROMPT = """You are the Understanding Agent in a multi-agent agricultural advisory system for Indian farmers.

Your ONLY job is to analyze the farmer's query and produce a structured JSON analysis.
Do NOT answer the question. Do NOT give advice. ONLY analyze.

Output STRICT JSON (no markdown, no ```):
{
  "intents": ["weather", "crop", "pest", "schemes", "profile", "irrigation", "general"],
  "entities": {
    "location": "extracted city/village/district or null",
    "crop": "extracted crop name or null",
    "season": "kharif/rabi/summer or null",
    "state": "Indian state or null",
    "pest_symptom": "described symptom or null"
  },
  "tools_needed": ["get_weather", "get_crop_advisory", "get_pest_alert", "search_schemes", "get_farmer_profile"],
  "urgency": "high/medium/low",
  "summary": "One-line summary of what the farmer needs"
}

Rules:
- intents: list ALL relevant intents from the query
- tools_needed: list which tools the Reasoning Agent should call
- Extract entities even if implicit (e.g., "my paddy has yellow spots" → crop=paddy, pest_symptom=yellow spots)
- If location is missing but needed, note it in summary
- For weather queries, get_weather is always needed
- For crop/variety/fertilizer queries, get_crop_advisory is always needed
- For irrigation/water/watering queries, get_crop_advisory with query_type='irrigation' is always needed — add "irrigation" to intents
- For pest/disease/pesticide queries, get_pest_alert is always needed (queries Knowledge Base for pesticide guides, dosage, safety, treatment)
- For scheme queries, search_schemes is always needed
- ALWAYS include get_farmer_profile in tools_needed when farmer_id is available — personalized advice requires the farmer's profile data"""

# ── Agent 3: Fact-Checking Agent ──
FACTCHECK_SYSTEM_PROMPT = """You are the Fact-Checking Agent in a multi-agent agricultural advisory system for Indian farmers.

You receive:
1. The Reasoning Agent's draft advisory
2. The raw tool data it was based on

Your job is to VALIDATE the advisory against the tool data and fix any issues.

Output STRICT JSON (no markdown, no ```):
{
  "validated": true/false,
  "corrected_advisory": "The corrected advisory text (or original if no changes needed)",
  "confidence": 0.0-1.0,
  "corrections": ["list of corrections made, empty if none"],
  "warnings": ["any warnings for the farmer"],
  "hallucinations_found": ["any claims not supported by tool data"]
}

Rules:
- Check that temperature/weather numbers match the tool output exactly
- Check that crop advice matches the region and season from tool data
- Check that scheme names and details match the tool output
- Flag any advice that is NOT grounded in tool data
- If advisory is mostly correct, set validated=true and return it unchanged
- If tool data is empty/error, note that the advisory lacks grounding
- NEVER add new information — only validate what the Reasoning Agent wrote
- Be strict: farmers depend on accurate data for their livelihood"""

# ── Agent 4: Communication Agent ──
COMMUNICATION_SYSTEM_PROMPT = """You are the Communication Agent in a multi-agent agricultural advisory system for Indian farmers.

You receive a fact-checked agricultural advisory. Your job is to rewrite it for an Indian farmer audience.

Rules:
1. Keep ALL factual data (numbers, temperatures, dates, scheme names) EXACTLY as given
2. Use simple, practical language a rural farmer would understand
3. Organize with clear sections if the response covers multiple topics
4. Add actionable next steps where appropriate (e.g., "Apply urea at 2 bags/acre before next rainfall")
5. Be respectful and encouraging — farming is hard work
6. Keep response concise (under 300 words) — farmers need quick answers
7. If weather data is included, highlight what matters for farming (rainfall, temperature extremes)
8. For pest/disease, always include: identify → treat → prevent
9. For schemes, include: eligibility → how to apply → deadline if known
10. End with a brief, helpful closing line
11. ALWAYS write your response in English — translation to the farmer's language is handled separately
12. For irrigation queries, include specific water amounts (mm/day, litres/acre) and scheduling

Do NOT add information that wasn't in the original advisory.
Do NOT use technical jargon unless explaining it.
Output ONLY the rewritten advisory text (no JSON, no metadata)."""


def _invoke_cognitive_converse(system_prompt, user_prompt, label="agent", max_tokens=1024, temperature=0.2):
    """
    Invoke a cognitive agent via Bedrock converse() API.
    No tools — just system prompt + user prompt → text response.
    """
    try:
        converse_kwargs = {
            "modelId": FOUNDATION_MODEL,
            "messages": [{"role": "user", "content": [{"text": user_prompt}]}],
            "system": [{"text": system_prompt}],
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
        }
        # Gap #5: Attach Bedrock native guardrail if configured
        gc = _guardrail_config()
        if gc:
            converse_kwargs['guardrailConfig'] = gc

        response = bedrock_rt.converse(**converse_kwargs)
        output = response.get("output", {})
        message = output.get("message", {})
        result_text = ""
        for block in message.get("content", []):
            if "text" in block:
                result_text += block["text"]
        logger.info(f"[{label}] Response: {len(result_text)} chars")
        return result_text
    except Exception as e:
        logger.error(f"[{label}] Bedrock converse error: {str(e)}")
        return None


def _run_cognitive_pipeline(user_message, english_message, session_id,
                            farmer_id, farmer_context, detected_lang):
    """
    4-Agent Cognitive Pipeline using Bedrock converse() API.

    Flow: Understanding → Reasoning (with tools) → Fact-Checking → Communication

    Each agent is a separate Bedrock converse() call with a role-specific system prompt.
    The Reasoning Agent is the only one with tool access.
    Total pipeline ~12-19s, fits within 29s API Gateway limit.

    Returns: (result_text_en, tools_used, pipeline_metadata)
    """
    pipeline_meta = {
        'pipeline_mode': 'cognitive',
        'agents_invoked': [],
        'understanding': None,
        'fact_check': None,
    }

    # ══════════════════════════════════════════════════════════
    #  AGENT 1: Understanding Agent (~2-3s)
    #  Analyzes query → extracts intents, entities, tools needed
    # ══════════════════════════════════════════════════════════
    logger.info("Pipeline Step 1/4: Understanding Agent")
    understanding_input = f"Farmer query: {english_message}"
    if farmer_context:
        understanding_input += f"\nFarmer context: {json.dumps(farmer_context)}"

    understanding_raw = _invoke_cognitive_converse(
        UNDERSTANDING_SYSTEM_PROMPT,
        understanding_input,
        label="understanding",
        max_tokens=512,
        temperature=0.1,
    )

    understanding = None
    if understanding_raw:
        pipeline_meta['agents_invoked'].append('understanding')
        try:
            # Strip markdown code fences if present
            cleaned = re.sub(r'^```(?:json)?\s*', '', understanding_raw.strip())
            cleaned = re.sub(r'\s*```$', '', cleaned.strip())
            understanding = json.loads(cleaned)
            pipeline_meta['understanding'] = {
                'intents': understanding.get('intents', []),
                'entities': understanding.get('entities', {}),
                'tools_needed': understanding.get('tools_needed', []),
                'urgency': understanding.get('urgency', 'medium'),
                'summary': understanding.get('summary', ''),
            }
            logger.info(f"Understanding: intents={understanding.get('intents')}, "
                        f"tools={understanding.get('tools_needed')}, "
                        f"entities={json.dumps(understanding.get('entities', {}))[:150]}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Understanding agent returned non-JSON: {str(e)}")
            understanding = None

    # ══════════════════════════════════════════════════════════
    #  AGENT 2: Reasoning Agent (~5-10s)  — HAS TOOL ACCESS
    #  Calls tools based on understanding, synthesizes raw data
    # ══════════════════════════════════════════════════════════
    logger.info("Pipeline Step 2/4: Reasoning Agent (with tools)")

    # Build an enriched prompt for the Reasoning Agent
    reasoning_prompt = english_message
    if understanding:
        entities = understanding.get('entities', {})
        tools_needed = understanding.get('tools_needed', [])
        summary = understanding.get('summary', '')

        reasoning_context = f"\n\n[Understanding Agent Analysis]\n"
        reasoning_context += f"Summary: {summary}\n"
        reasoning_context += f"Tools to call: {', '.join(tools_needed)}\n"
        if entities.get('location'):
            reasoning_context += f"Location: {entities['location']}\n"
        if entities.get('crop'):
            reasoning_context += f"Crop: {entities['crop']}\n"
        if entities.get('season'):
            reasoning_context += f"Season: {entities['season']}\n"
        if entities.get('pest_symptom'):
            reasoning_context += f"Pest symptom: {entities['pest_symptom']}\n"
        reasoning_context += f"\nIMPORTANT: Call the following tools first: {', '.join(tools_needed)}"
        reasoning_prompt = english_message + reasoning_context

    reasoning_text, tools_used, tool_data_log = _invoke_bedrock_direct(
        reasoning_prompt, farmer_context
    )
    pipeline_meta['agents_invoked'].append('reasoning')
    logger.info(f"Reasoning result: {len(reasoning_text or '')} chars, tools={tools_used}")

    # If reasoning returned empty/error, return early
    if not reasoning_text or len(reasoning_text.strip()) < 15:
        logger.warning("Reasoning agent returned empty — returning raw result")
        return reasoning_text or "", tools_used, pipeline_meta

    # ══════════════════════════════════════════════════════════
    #  AGENT 3: Fact-Checking Agent (~2-3s)
    #  Validates reasoning output against tool data
    # ══════════════════════════════════════════════════════════
    logger.info("Pipeline Step 3/4: Fact-Checking Agent")

    # Build raw tool data summary for fact-checker (truncated to stay within token limits)
    tool_data_summary = "None"
    if tool_data_log:
        tool_entries = []
        for td in tool_data_log:
            entry = f"Tool: {td['tool']}\nInput: {json.dumps(td['input'])}\nOutput: {json.dumps(td['output'])[:800]}"
            tool_entries.append(entry)
        tool_data_summary = "\n---\n".join(tool_entries)

    factcheck_input = (
        f"## Draft Advisory (from Reasoning Agent):\n{reasoning_text}\n\n"
        f"## Tools Used: {', '.join(tools_used) if tools_used else 'None'}\n\n"
        f"## Raw Tool Data (ground truth):\n{tool_data_summary}\n\n"
        f"## Original Query: {english_message}\n"
    )
    if understanding:
        factcheck_input += f"\n## Understanding Analysis: {json.dumps(understanding)[:500]}\n"

    factcheck_raw = _invoke_cognitive_converse(
        FACTCHECK_SYSTEM_PROMPT,
        factcheck_input,
        label="fact_check",
        max_tokens=1024,
        temperature=0.1,
    )

    fact_checked_text = reasoning_text  # default: use reasoning output as-is
    if factcheck_raw:
        pipeline_meta['agents_invoked'].append('fact_check')
        try:
            cleaned = re.sub(r'^```(?:json)?\s*', '', factcheck_raw.strip())
            cleaned = re.sub(r'\s*```$', '', cleaned.strip())
            fc_result = json.loads(cleaned)
            corrected = fc_result.get('corrected_advisory', '').strip()
            if corrected and len(corrected) > 20:
                fact_checked_text = corrected
            pipeline_meta['fact_check'] = {
                'validated': fc_result.get('validated', True),
                'confidence': fc_result.get('confidence', 0.8),
                'corrections': fc_result.get('corrections', []),
                'warnings': fc_result.get('warnings', []),
                'hallucinations_found': fc_result.get('hallucinations_found', []),
            }
            logger.info(f"Fact-check: validated={fc_result.get('validated')}, "
                        f"corrections={len(fc_result.get('corrections', []))}, "
                        f"confidence={fc_result.get('confidence')}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Fact-check agent returned non-JSON: {str(e)}")
            # Use reasoning text as-is

    # ══════════════════════════════════════════════════════════
    #  AGENT 4: Communication Agent (~2-3s)
    #  Rewrites for farmer audience, clear and actionable
    # ══════════════════════════════════════════════════════════
    logger.info("Pipeline Step 4/4: Communication Agent")

    # Map language codes to language names for better LLM understanding
    LANG_NAMES = {
        'en': 'English', 'hi': 'Hindi', 'ta': 'Tamil', 'te': 'Telugu',
        'kn': 'Kannada', 'ml': 'Malayalam', 'mr': 'Marathi', 'bn': 'Bengali',
        'gu': 'Gujarati', 'pa': 'Punjabi', 'or': 'Odia', 'as': 'Assamese', 'ur': 'Urdu',
    }
    lang_name = LANG_NAMES.get(detected_lang, 'English')

    comm_input = (
        f"Rewrite this fact-checked advisory for an Indian farmer.\n"
        f"Write in clear, simple English. Translation will be handled separately.\n"
        f"\n{fact_checked_text}"
    )
    if farmer_context:
        comm_input += f"\n\nFarmer profile: {json.dumps(farmer_context)}"

    final_text = _invoke_cognitive_converse(
        COMMUNICATION_SYSTEM_PROMPT,
        comm_input,
        label="communication",
        max_tokens=1500,
        temperature=0.3,
    )

    if final_text and len(final_text.strip()) > 20:
        pipeline_meta['agents_invoked'].append('communication')
        logger.info(f"Communication agent rewrote: {len(final_text)} chars")
    else:
        logger.warning("Communication agent returned empty — using fact-checked text")
        final_text = fact_checked_text

    logger.info(f"Pipeline complete: agents={pipeline_meta['agents_invoked']}, tools={tools_used}")
    return final_text, tools_used, pipeline_meta


def _classify_intents(message_en, original_message=None):
    """Classify intents from English translation AND original Indic text."""
    text = (message_en or '').lower()
    orig = (original_message or '').lower()
    combined = text + ' ' + orig
    intents = set()

    weather_kw = ['weather', 'rain', 'rainfall', 'temperature', 'humidity', 'forecast', 'monsoon', 'mausam',
                  # Tamil/Hindi/Telugu weather words
                  'வானிலை', 'மழை', 'வெப்பநிலை', 'मौसम', 'बारिश', 'तापमान',
                  'వాతావరణం', 'వర్షం', 'ఉష్ణోగ్రత']
    crop_kw = ['crop', 'seed', 'soil', 'fertilizer', 'irrigation', 'yield', 'harvest', 'variety',
               'kharif', 'rabi', 'grow', 'plant', 'sow', 'cultivat',
               # Tamil crop words
               'பயிர்', 'விதை', 'மண்', 'உரம்', 'நெல்', 'நிலம்', 'வளர்', 'விவசாய',
               # Hindi crop words
               'फसल', 'बीज', 'मिट्टी', 'खाद', 'उगा', 'खेती',
               # Telugu crop words
               'పంట', 'విత్తనం', 'నేల', 'ఎరువు', 'వ్యవసాయ']
    pest_kw = ['pest', 'disease', 'fungus', 'insect', 'blight', 'spot', 'rot', 'spray', 'infestation',
               'yellow', 'brown', 'wilt', 'curling', 'dying', 'damage', 'attack', 'infection',
               'fungicide', 'pesticide', 'medicine', 'treatment', 'cure', 'leaves turning',
               # Tamil pest/symptom words
               'பூச்சி', 'நோய்', 'கீடம்', 'மஞ்சள்', 'மருந்து', 'தெளிக்க', 'தெளி',
               'பழுப்பு', 'வாடி', 'அழுகல்', 'இலைகள்',
               # Hindi pest/symptom words
               'कीट', 'रोग', 'पीला', 'पीले', 'दवा', 'छिड़काव', 'फफूंद', 'कीटनाशक',
               'भूरा', 'मुरझा', 'सड़',
               # Telugu pest/symptom words
               'పురుగు', 'వ్యాధి', 'పసుపు', 'మందు', 'స్ప్రే', 'ఆకులు',
               'గోధుమ', 'వాడి', 'కుళ్ళు']
    schemes_kw = ['scheme', 'subsidy', 'loan', 'insurance', 'pm-kisan', 'government', 'yojana', 'benefit',
                  # Tamil/Hindi/Telugu scheme words
                  'திட்டம்', 'மானியம்', 'கடன்', 'योजना', 'सब्सिडी', 'ऋण',
                  'పథకం', 'రాయితీ', 'రుణం']
    profile_kw = ['profile', 'my farm', 'my details', 'my crop', 'my soil', 'my state', 'my district']

    if any(k in combined for k in weather_kw):
        intents.add('weather')
    if any(k in combined for k in crop_kw):
        intents.add('crop')
    if any(k in combined for k in pest_kw):
        intents.add('pest')
    if any(k in combined for k in schemes_kw):
        intents.add('schemes')
    if any(k in combined for k in profile_kw):
        intents.add('profile')

    return list(intents)


def _get_specialist_runtime_for_intent(intent):
    mapping = {
        'weather': AGENTCORE_WEATHER_RUNTIME_ARN,
        'crop': AGENTCORE_CROP_RUNTIME_ARN,
        'pest': AGENTCORE_PEST_RUNTIME_ARN or AGENTCORE_CROP_RUNTIME_ARN,
        'schemes': AGENTCORE_SCHEMES_RUNTIME_ARN,
        'profile': AGENTCORE_PROFILE_RUNTIME_ARN or AGENTCORE_RUNTIME_ARN,
    }
    return mapping.get(intent, '')


def _build_tool_first_prompt(message_en, intents, farmer_context=None):
    """Force tool-first behavior for known intents to reduce empty/non-grounded replies."""
    text = (message_en or '').strip()
    if not text:
        return text

    intent_order = ['pest', 'weather', 'irrigation', 'crop', 'schemes', 'profile']
    selected = [i for i in intent_order if i in (intents or [])]
    if not selected:
        return text

    # Limit to 3 intents max to avoid API Gateway timeout (29s)
    if len(selected) > 3:
        logger.warning(f"Too many intents ({len(selected)}), trimming to top 3: {selected[:3]}")
        selected = selected[:3]

    tool_map = {
        'pest': 'get_pest_alert',
        'weather': 'get_weather',
        'irrigation': 'get_crop_advisory',
        'crop': 'get_crop_advisory',
        'schemes': 'search_schemes',
        'profile': 'get_farmer_profile',
    }
    required_tools = [tool_map[i] for i in selected if i in tool_map]
    first_tool = required_tools[0]

    context_hint = ""
    if farmer_context:
        known = []
        if farmer_context.get('state'):
            known.append(f"state={farmer_context['state']}")
        if farmer_context.get('district'):
            known.append(f"district={farmer_context['district']}")
        if farmer_context.get('soil_type'):
            known.append(f"soil_type={farmer_context['soil_type']}")
        if farmer_context.get('crops'):
            known.append(f"crops={', '.join(farmer_context['crops'])}")
        if known:
            context_hint = f"Known farmer context: {'; '.join(known)}."

    # For irrigation intent, add specific instruction
    irrigation_hint = ""
    if 'irrigation' in selected:
        irrigation_hint = (
            "For the irrigation query, call get_crop_advisory with query_type='irrigation' "
            "and include the crop name, location, and soil_type in the parameters. "
            "The Knowledge Base has detailed irrigation schedules, water requirements, "
            "drip/sprinkler/flood methods, and crop water need tables.\n"
        )

    routing = (
        "[ROUTING POLICY - STRICT]\n"
        f"Detected intents: {', '.join(selected)}.\n"
        f"You MUST call this tool first: {first_tool}.\n"
        f"Then use these tools as needed: {', '.join(required_tools)}.\n"
        "Do not answer with generic text before at least one tool call.\n"
        "If required parameters are missing, make a best-effort call with available context first, "
        "then ask only the minimum missing fields.\n"
        f"{irrigation_hint}"
        f"{context_hint}\n"
        "[/ROUTING POLICY]\n\n"
    )
    return routing + text


def _combine_specialist_outputs(english_message, specialist_outputs):
    sections = []
    tools = []
    for item in specialist_outputs:
        label = item.get('intent', 'specialist').upper()
        text = (item.get('text') or '').strip()
        if text:
            cleaned = re.sub(r'<thinking>.*?</thinking>\s*', '', text, flags=re.DOTALL).strip()
            sections.append(f"[{label}]\n{cleaned}")
        tools.extend(item.get('tools', []))

    combined_text = "\n\n".join(sections).strip()

    if not combined_text:
        return "", []

    synthesis_prompt = (
        "Synthesize the following specialist advisories into one concise, farmer-friendly final answer. "
        "Remove duplication, keep actionable steps, and preserve important warnings.\n\n"
        f"Farmer question: {english_message}\n\n"
        f"Specialist outputs:\n{combined_text}"
    )

    final_text, master_tools = _invoke_agentcore_runtime_with_arn(
        AGENTCORE_RUNTIME_ARN,
        synthesis_prompt,
        str(uuid.uuid4()),
        None,
    )

    if not final_text:
        final_text = combined_text

    return final_text, list(dict.fromkeys(tools + master_tools))


def _invoke_bedrock_agent(prompt, session_id):
    """
    Invoke the agent via traditional Bedrock Agents API (fallback).
    """
    response = bedrock_agent.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=prompt,
    )

    result_text = ""
    for event_stream in response['completion']:
        if 'chunk' in event_stream:
            chunk = event_stream['chunk']
            result_text += chunk['bytes'].decode('utf-8')

    return result_text, []


def lambda_handler(event, context):
    """
    Main orchestrator — full flow:
    1. Detect language → translate to English
    2. Invoke AgentCore Runtime (or Bedrock Agent fallback)
    3. Translate response back to farmer's language
    4. Generate Polly audio
    5. Return {reply, reply_en, detected_language, tools_used, audio_url, session_id}
    """
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return success_response({}, message='OK')

    try:
        body = json.loads(event.get('body', '{}'))
        user_message = body.get('message', '')
        session_id = body.get('session_id', str(uuid.uuid4()))
        farmer_id = body.get('farmer_id', 'anonymous')
        language = body.get('language', None)  # Auto-detect if not provided

        # AgentCore runtimeSessionId requires min 33 chars
        if len(session_id) < 33:
            session_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, session_id))

        _t_start = _time.time()
        _is_feature_page = any(session_id.startswith(p) or body.get('session_id', '').startswith(p) for p in FAST_PATH_PREFIXES)
        logger.info(f'Session {session_id} | feature_page={_is_feature_page}')

        if not user_message:
            return error_response('Message is required', 400)

        # ══════ ENTERPRISE GUARDRAILS (Pre-processing) ══════
        # Gap #1 (PII), #2 (Injection), #4 (Input Length), #7 (Toxicity)
        guardrail_result = run_all_guardrails(user_message)
        pii_safe_msg = guardrail_result.get('pii_masked_message', user_message[:200])

        if not guardrail_result['passed']:
            block_type = guardrail_result['blocked_reason']
            block_response = guardrail_result['blocked_response']
            audit_guardrail_block(
                block_type=block_type,
                farmer_id=farmer_id,
                session_id=session_id,
                pii_safe_message=pii_safe_msg,
                threat_details=guardrail_result.get('threat_details'),
            )
            return success_response({
                'reply': block_response,
                'reply_en': block_response,
                'detected_language': 'en',
                'tools_used': [],
                'audio_url': None,
                'session_id': session_id,
                'mode': 'agentcore' if USE_AGENTCORE else 'bedrock-agents',
                'policy': {
                    'code_policy_enforced': True,
                    'guardrail_blocked': True,
                    'block_type': block_type,
                },
            }, message='Guardrail blocked', language='en')

        # Log PII detection (types only, never raw data)
        if guardrail_result['pii_detected']:
            audit_pii_detected(farmer_id, session_id, guardrail_result['pii_detected'])

        # Gap #3: Rate limiting
        rate_result = check_rate_limit(session_id, farmer_id)
        if not rate_result['allowed']:
            audit_guardrail_block(
                block_type='rate_limit',
                farmer_id=farmer_id,
                session_id=session_id,
                pii_safe_message=pii_safe_msg,
                threat_details={'reason': rate_result['reason']},
            )
            return success_response({
                'reply': rate_result['reason'],
                'reply_en': rate_result['reason'],
                'detected_language': 'en',
                'tools_used': [],
                'audio_url': None,
                'session_id': session_id,
                'mode': 'agentcore' if USE_AGENTCORE else 'bedrock-agents',
                'policy': {
                    'code_policy_enforced': True,
                    'rate_limited': True,
                    'retry_after_seconds': rate_result.get('retry_after_seconds'),
                },
            }, message='Rate limited', language='en')

        user_message = _sanitize_user_message(guardrail_result['sanitized_message'])
        # Gap #6: Audit log — request start (PII-safe)
        audit_request_start(farmer_id, session_id, pii_safe_msg)
        logger.info(f"Query from farmer {farmer_id}: {pii_safe_msg}")

        # --- Step 1: Detect language & translate to English ---
        detection = detect_and_translate(user_message, target_language='en')
        detected_lang = normalize_language_code(
            language or detection.get('detected_language', 'en'),
            default='en'
        )
        english_message = detection.get('translated_text', user_message)
        intents = _classify_intents(english_message, original_message=user_message)

        # If user speaks in an Indic language but no specific intents detected,
        # default to 'crop' (most common farmer query) so it gets routed to a tool
        if not intents and _contains_indic_chars(user_message):
            logger.info("Indic-language query with no detected intents — defaulting to 'crop' intent")
            intents = ['crop']

        on_topic = _is_on_topic_query(english_message) or _is_on_topic_query(user_message)
        if ENFORCE_CODE_POLICY and not on_topic:
            policy_reply_en = _off_topic_response()
            translated_policy_reply = (
                translate_response(policy_reply_en, 'en', detected_lang)
                if detected_lang and detected_lang != 'en'
                else policy_reply_en
            )

            audio_url = None
            polly_text_truncated = False
            try:
                polly_result = text_to_speech(
                    translated_policy_reply,
                    detected_lang or 'en',
                    return_metadata=True,
                )
                if isinstance(polly_result, dict):
                    audio_url = polly_result.get('audio_url')
                    polly_text_truncated = bool(polly_result.get('truncated', False))
                else:
                    audio_url = polly_result
            except Exception as polly_err:
                logger.warning(f"Polly audio failed (non-fatal): {polly_err}")

            save_chat_message(session_id, 'user', user_message, detected_lang)
            save_chat_message(session_id, 'assistant', translated_policy_reply, detected_lang)

            return success_response({
                'reply': translated_policy_reply,
                'reply_en': policy_reply_en,
                'detected_language': detected_lang,
                'tools_used': [],
                'audio_url': audio_url,
                'polly_text_truncated': polly_text_truncated,
                'session_id': session_id,
                'mode': 'agentcore' if USE_AGENTCORE else 'bedrock-agents',
                'policy': {
                    'code_policy_enforced': True,
                    'off_topic_blocked': True,
                    'grounding_required': False,
                    'grounding_satisfied': True,
                },
            }, message='Policy-safe advisory generated', language=detected_lang)

        # --- Step 2: Enrich with farmer profile (optional) ---
        farmer_context = None
        profile = get_farmer_profile(farmer_id) if farmer_id != 'anonymous' else None
        if profile:
            farmer_context = {
                'name': profile.get('name', ''),
                'state': profile.get('state', ''),
                'crops': profile.get('crops', []),
                'soil_type': profile.get('soil_type', ''),
                'district': profile.get('district', ''),
            }
            context_prefix = (
                f"[Farmer context: {farmer_context['name']}, "
                f"State={farmer_context['state']}, Crops={farmer_context['crops']}, "
                f"Soil={farmer_context['soil_type']}] "
            )
            english_message = context_prefix + english_message

        # --- Step 3: Invoke AI Agent ---
        pipeline_meta_extra = {}

        if _is_feature_page:
            # FAST PATH: feature pages skip 4-agent pipeline, use single Bedrock call
            logger.info(f'FAST PATH for feature page (elapsed {_time.time()-_t_start:.1f}s)')
            routed_prompt = _build_tool_first_prompt(english_message, intents, farmer_context)
            result_text, tools_used, _ = _invoke_bedrock_direct(routed_prompt, farmer_context)

        elif USE_AGENTCORE and PIPELINE_MODE == 'cognitive':
            # ═══ NEW: Cognitive Multi-Agent Pipeline ═══
            logger.info(f"Pipeline mode: COGNITIVE | intents={intents}")
            result_text, tools_used, pipeline_meta_extra = _run_cognitive_pipeline(
                user_message=user_message,
                english_message=english_message,
                session_id=session_id,
                farmer_id=farmer_id,
                farmer_context=farmer_context,
                detected_lang=detected_lang,
            )

        elif USE_AGENTCORE:
            # Specialist mode: use direct Bedrock converse() with tool routing
            logger.info(f"Specialist mode: direct Bedrock converse() | intents={intents}")
            routed_prompt = _build_tool_first_prompt(
                english_message,
                intents,
                farmer_context,
            )
            result_text, tools_used, _ = _invoke_bedrock_direct(
                routed_prompt, farmer_context
            )
        else:
            logger.info("Invoking Bedrock Agent (fallback)...")
            result_text, tools_used = _invoke_bedrock_agent(
                english_message, session_id
            )

        # Clean up model thinking tags (Claude emits <thinking>...</thinking>)
        result_text = re.sub(r'<thinking>.*?</thinking>\s*', '', result_text, flags=re.DOTALL)
        result_text = result_text.strip()

        # Guard: if agent returned garbled/empty content, provide a fallback
        # Remove punctuation/spaces and check if any real text remains
        _stripped = re.sub(r'[\s\(\)\,\.\?\!\;\:\-\[\]\{\}\"\']+', '', result_text)
        if len(_stripped) < 10:
            logger.warning(f"Agent returned near-empty/garbled response: {repr(result_text[:100])}")
            result_text = (
                "I couldn't get a complete answer right now. "
                "Please share more details like your crop, location, and season so I can help better."
            )
            tools_used = []

        result_text, tools_used, policy_meta = _apply_code_policy(
            english_message,
            intents,
            result_text,
            tools_used,
            original_query=user_message,
        )

        # Gap #6: Audit policy decision
        audit_policy_decision(farmer_id, session_id, policy_meta)
        logger.info(f"Agent response: {mask_pii_in_log(result_text[:200])}... tools={tools_used}")

        # --- Step 4: Translate response to farmer's language ---
        # Strip sources line BEFORE translation so function names don't get garbled
        text_for_translation, _ = _strip_sources_line(result_text)
        sources_line = _build_sources_line(tools_used)

        if detected_lang and detected_lang != 'en':
            translated_reply = translate_response(text_for_translation, 'en', detected_lang)
        else:
            translated_reply = text_for_translation

        # Re-append sources in English AFTER translation only to reply_en (debug)
        # Do NOT append sources to translated_reply — frontend shows sources separately
        if sources_line:
            result_text = f"{text_for_translation}\n\nSources: {sources_line}"

        # --- Step 4b: Output guardrails (PII leakage, prompt leakage, length cap) ---
        output_guard = run_output_guardrails(translated_reply, context={
            'farmer_id': farmer_id, 'session_id': session_id,
        })
        if output_guard['modified']:
            translated_reply = output_guard['text']
            logger.info(
                f"Output guardrail applied | pii={output_guard['pii_masked']} "
                f"prompt_leak={output_guard['prompt_leaked']} truncated={output_guard['truncated']}"
            )

        # --- Step 5: Generate TTS audio ---
        _elapsed = _time.time() - _t_start
        audio_url = None
        polly_text_truncated = False
        if _is_feature_page:
            logger.info(f'Feature page - skipping TTS for speed (elapsed {_elapsed:.1f}s)')
        elif _elapsed > TTS_TIME_BUDGET_SEC:
            logger.warning(f'Skipping TTS - elapsed {_elapsed:.1f}s > {TTS_TIME_BUDGET_SEC}s budget')
        else:
            try:
                polly_result = text_to_speech(
                    translated_reply,
                    detected_lang or 'en',
                    return_metadata=True,
                )
                if isinstance(polly_result, dict):
                    audio_url = polly_result.get('audio_url')
                    polly_text_truncated = bool(polly_result.get('truncated', False))
                else:
                    audio_url = polly_result
                logger.info(f'TTS completed in {_time.time()-_t_start-_elapsed:.1f}s, audio={bool(audio_url)}')
            except Exception as polly_err:
                logger.warning(f"Polly audio failed (non-fatal): {polly_err}")

        # --- Step 6: Save chat history ---
        save_chat_message(session_id, 'user', user_message, detected_lang, farmer_id=farmer_id)
        save_chat_message(session_id, 'assistant', translated_reply, detected_lang, farmer_id=farmer_id)

        # --- Step 7: Return response (matches API contract) ---
        _total_elapsed = _time.time() - _t_start
        logger.info(f'Total handler time: {_total_elapsed:.1f}s | feature_page={_is_feature_page} | audio={bool(audio_url)}')

        # Gap #6: Audit request completion
        audit_request_complete(
            farmer_id=farmer_id,
            session_id=session_id,
            tools_used=tools_used,
            pipeline_mode=PIPELINE_MODE if not _is_feature_page else 'fast_path',
            response_length=len(translated_reply or ''),
            elapsed_seconds=_total_elapsed,
            bedrock_guardrail_triggered=False,
            output_guardrail=output_guard if output_guard.get('modified') else None,
        )

        return success_response({
            'reply': translated_reply,
            'reply_en': result_text,
            'detected_language': detected_lang,
            'tools_used': tools_used,
            'sources': sources_line or None,
            'audio_url': audio_url,
            'polly_text_truncated': polly_text_truncated,
            'session_id': session_id,
            'mode': 'agentcore' if USE_AGENTCORE else 'bedrock-agents',
            'pipeline_mode': PIPELINE_MODE,
            'pipeline': pipeline_meta_extra if pipeline_meta_extra else None,
            'policy': policy_meta,
        }, message='Advisory generated successfully', language=detected_lang)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return error_response(str(e), 500)
