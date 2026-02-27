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
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from utils.response_helper import success_response, error_response
from utils.translate_helper import detect_and_translate, translate_response
from utils.polly_helper import text_to_speech
from utils.dynamodb_helper import save_chat_message, get_farmer_profile

# ── AgentCore Runtime mode (preferred) ──
AGENTCORE_RUNTIME_ARN = os.environ.get('AGENTCORE_RUNTIME_ARN', '')
AGENTCORE_WEATHER_RUNTIME_ARN = os.environ.get('AGENTCORE_WEATHER_RUNTIME_ARN', '')
AGENTCORE_CROP_RUNTIME_ARN = os.environ.get('AGENTCORE_CROP_RUNTIME_ARN', '')
AGENTCORE_SCHEMES_RUNTIME_ARN = os.environ.get('AGENTCORE_SCHEMES_RUNTIME_ARN', '')
AGENTCORE_PROFILE_RUNTIME_ARN = os.environ.get('AGENTCORE_PROFILE_RUNTIME_ARN', '')
AGENTCORE_PEST_RUNTIME_ARN = os.environ.get('AGENTCORE_PEST_RUNTIME_ARN', '')
ENABLE_SPECIALIST_FANOUT = os.environ.get('ENABLE_SPECIALIST_FANOUT', 'true').lower() == 'true'
ENFORCE_CODE_POLICY = os.environ.get('ENFORCE_CODE_POLICY', 'true').lower() == 'true'

# ── Bedrock Agents mode (fallback) ──
AGENT_ID = os.environ.get('BEDROCK_AGENT_ID', '')
AGENT_ALIAS_ID = os.environ.get('BEDROCK_AGENT_ALIAS_ID', '')

# Auto-detect which mode to use
USE_AGENTCORE = bool(AGENTCORE_RUNTIME_ARN)

if USE_AGENTCORE:
    logger.info(f"Mode: AgentCore Runtime — ARN: {AGENTCORE_RUNTIME_ARN}")
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


def _is_on_topic_query(text):
    normalized = (text or '').lower().strip()
    if not normalized:
        return True
    if normalized in SAFE_CHITCHAT:
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


def _append_sources(reply_en, tools_used):
    text = (reply_en or '').strip()
    if not text or not tools_used:
        return text

    if 'sources:' in text.lower():
        return text

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
    return f"{text}\n\nSources: {', '.join(source_list)}"


def _apply_code_policy(user_query_en, intents, result_text, tools_used):
    policy_meta = {
        'code_policy_enforced': ENFORCE_CODE_POLICY,
        'off_topic_blocked': False,
        'grounding_required': _requires_grounded_tools(intents),
        'grounding_satisfied': bool(tools_used),
    }

    if not ENFORCE_CODE_POLICY:
        return result_text, tools_used, policy_meta

    if not _is_on_topic_query(user_query_en):
        policy_meta['off_topic_blocked'] = True
        return _off_topic_response(), [], policy_meta

    cleaned_tools = list(dict.fromkeys(tools_used or []))
    text = (result_text or '').strip()

    if not text:
        text = "I need a bit more farm context to provide a reliable advisory."

    if policy_meta['grounding_required'] and not cleaned_tools:
        policy_meta['grounding_satisfied'] = False
        text = (
            "I couldn't verify this with trusted tools right now. "
            "Please share your crop, location, season, and symptoms so I can provide a reliable advisory."
        )

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
        # Log the full error for debugging
        import traceback
        logger.error(traceback.format_exc())
        return f"I apologize, I encountered an error processing your request. Please try again.", []


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


def _classify_intents(message_en):
    text = (message_en or '').lower()
    intents = set()

    weather_kw = ['weather', 'rain', 'rainfall', 'temperature', 'humidity', 'forecast', 'monsoon', 'mausam']
    crop_kw = ['crop', 'seed', 'soil', 'fertilizer', 'irrigation', 'yield', 'harvest', 'variety', 'kharif', 'rabi']
    pest_kw = ['pest', 'disease', 'fungus', 'insect', 'blight', 'spot', 'rot', 'spray', 'infestation']
    schemes_kw = ['scheme', 'subsidy', 'loan', 'insurance', 'pm-kisan', 'government', 'yojana', 'benefit']
    profile_kw = ['profile', 'my farm', 'my details', 'my crop', 'my soil', 'my state', 'my district']

    if any(k in text for k in weather_kw):
        intents.add('weather')
    if any(k in text for k in crop_kw):
        intents.add('crop')
    if any(k in text for k in pest_kw):
        intents.add('pest')
    if any(k in text for k in schemes_kw):
        intents.add('schemes')
    if any(k in text for k in profile_kw):
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

        if not user_message:
            return error_response('Message is required', 400)

        logger.info(f"Query from farmer {farmer_id}: {user_message}")

        # --- Step 1: Detect language & translate to English ---
        detection = detect_and_translate(user_message, target_language='en')
        detected_lang = language or detection.get('detected_language', 'en')
        english_message = detection.get('translated_text', user_message)
        intents = _classify_intents(english_message)

        if ENFORCE_CODE_POLICY and not _is_on_topic_query(english_message):
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
        if USE_AGENTCORE:
            logger.info(f"Detected intents: {intents if intents else ['general']}")

            specialist_outputs = []

            if ENABLE_SPECIALIST_FANOUT and intents:
                jobs = []
                with ThreadPoolExecutor(max_workers=3) as executor:
                    for intent in intents:
                        runtime_arn = _get_specialist_runtime_for_intent(intent)
                        if runtime_arn:
                            specialist_session = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{session_id}:{intent}"))
                            jobs.append((intent, executor.submit(
                                _invoke_agentcore_runtime_with_arn,
                                runtime_arn,
                                english_message,
                                specialist_session,
                                farmer_context,
                            )))

                    for intent, future in jobs:
                        text, tools = future.result()
                        specialist_outputs.append({'intent': intent, 'text': text, 'tools': tools})

            if specialist_outputs:
                combined_text, combined_tools = _combine_specialist_outputs(english_message, specialist_outputs)
                if combined_text and combined_text.strip():
                    result_text, tools_used = combined_text, combined_tools
                else:
                    logger.warning("Specialist fanout returned empty content, falling back to master runtime")
                    result_text, tools_used = _invoke_agentcore_runtime(
                        english_message, session_id, farmer_context
                    )
            else:
                logger.info("Invoking master AgentCore Runtime...")
                result_text, tools_used = _invoke_agentcore_runtime(
                    english_message, session_id, farmer_context
                )
        else:
            logger.info("Invoking Bedrock Agent (fallback)...")
            result_text, tools_used = _invoke_bedrock_agent(
                english_message, session_id
            )

        # Clean up model thinking tags (Claude emits <thinking>...</thinking>)
        result_text = re.sub(r'<thinking>.*?</thinking>\s*', '', result_text, flags=re.DOTALL)
        result_text = result_text.strip()
        result_text, tools_used, policy_meta = _apply_code_policy(
            english_message,
            intents,
            result_text,
            tools_used,
        )

        logger.info(f"Agent response: {result_text[:200]}... tools={tools_used}")

        # --- Step 4: Translate response to farmer's language ---
        if detected_lang and detected_lang != 'en':
            translated_reply = translate_response(result_text, 'en', detected_lang)
        else:
            translated_reply = result_text

        # --- Step 5: Generate Polly audio ---
        audio_url = None
        polly_text_truncated = False
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
        except Exception as polly_err:
            logger.warning(f"Polly audio failed (non-fatal): {polly_err}")

        # --- Step 6: Save chat history ---
        save_chat_message(session_id, 'user', user_message, detected_lang)
        save_chat_message(session_id, 'assistant', translated_reply, detected_lang)

        # --- Step 7: Return response (matches API contract) ---
        return success_response({
            'reply': translated_reply,
            'reply_en': result_text,
            'detected_language': detected_lang,
            'tools_used': tools_used,
            'audio_url': audio_url,
            'polly_text_truncated': polly_text_truncated,
            'session_id': session_id,
            'mode': 'agentcore' if USE_AGENTCORE else 'bedrock-agents',
            'policy': policy_meta,
        }, message='Advisory generated successfully', language=detected_lang)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return error_response(str(e), 500)
