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

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from utils.response_helper import success_response, error_response
from utils.translate_helper import detect_and_translate, translate_response
from utils.polly_helper import text_to_speech
from utils.dynamodb_helper import save_chat_message, get_farmer_profile

# ── AgentCore Runtime mode (preferred) ──
AGENTCORE_RUNTIME_ARN = os.environ.get('AGENTCORE_RUNTIME_ARN', '')

# ── Bedrock Agents mode (fallback) ──
AGENT_ID = os.environ.get('BEDROCK_AGENT_ID', '')
AGENT_ALIAS_ID = os.environ.get('BEDROCK_AGENT_ALIAS_ID', '')

# Auto-detect which mode to use
USE_AGENTCORE = bool(AGENTCORE_RUNTIME_ARN)

if USE_AGENTCORE:
    agentcore_client = boto3.client('bedrock-agentcore', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
    logger.info(f"Mode: AgentCore Runtime — ARN: {AGENTCORE_RUNTIME_ARN}")
else:
    bedrock_agent = boto3.client('bedrock-agent-runtime')
    logger.info(f"Mode: Bedrock Agents — Agent: {AGENT_ID}, Alias: {AGENT_ALIAS_ID}")


def _invoke_agentcore_runtime(prompt, session_id, farmer_context=None):
    """
    Invoke the agent hosted on AgentCore Runtime.
    Uses the bedrock-agentcore SDK InvokeAgentRuntime API.
    """
    payload = {
        "prompt": prompt,
        "session_id": session_id,
    }
    if farmer_context:
        payload["context"] = farmer_context

    response = agentcore_client.invoke_agent_runtime(
        agentRuntimeArn=AGENTCORE_RUNTIME_ARN,
        runtimeSessionId=session_id,
        payload=json.dumps(payload).encode('utf-8'),
        qualifier="DEFAULT",
    )

    # Response is a single blob, not a stream
    raw_bytes = response.get("response", b'')
    if hasattr(raw_bytes, 'read'):
        raw_bytes = raw_bytes.read()
    raw_response = raw_bytes.decode('utf-8') if isinstance(raw_bytes, bytes) else str(raw_bytes)

    # Try to parse as JSON (our agent returns {result, tools_used})
    try:
        parsed = json.loads(raw_response)
        result_text = parsed.get('result', raw_response)
        tools_used = parsed.get('tools_used', [])
    except (json.JSONDecodeError, TypeError):
        result_text = raw_response
        tools_used = []

    return result_text, tools_used


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
            logger.info("Invoking AgentCore Runtime...")
            result_text, tools_used = _invoke_agentcore_runtime(
                english_message, session_id, farmer_context
            )
        else:
            logger.info("Invoking Bedrock Agent (fallback)...")
            result_text, tools_used = _invoke_bedrock_agent(
                english_message, session_id
            )

        logger.info(f"Agent response: {result_text[:200]}... tools={tools_used}")

        # --- Step 4: Translate response to farmer's language ---
        if detected_lang and detected_lang != 'en':
            translated_reply = translate_response(result_text, 'en', detected_lang)
        else:
            translated_reply = result_text

        # --- Step 5: Generate Polly audio ---
        audio_url = None
        try:
            audio_url = text_to_speech(translated_reply, detected_lang or 'en')
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
            'session_id': session_id,
            'mode': 'agentcore' if USE_AGENTCORE else 'bedrock-agents',
        }, message='Advisory generated successfully', language=detected_lang)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return error_response(str(e), 500)
