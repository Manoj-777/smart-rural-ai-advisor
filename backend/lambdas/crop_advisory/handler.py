# backend/lambdas/crop_advisory/handler.py
# Lambda Tool: Crop + Pest + Irrigation advisory
# Owner: Manoj RS
# See: Detailed_Implementation_Guide.md Section 9

import json
import boto3
import os
import logging
import re
from utils.response_helper import success_response, error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_kb = boto3.client('bedrock-agent-runtime')
KB_ID = os.environ.get('BEDROCK_KB_ID', '')

# ── Security: Input validation ──
MAX_FIELD_LENGTH = 200
MAX_QUERY_LENGTH = 500

def _sanitize_field(value, max_len=MAX_FIELD_LENGTH):
    """Sanitize a text field: strip, truncate, remove dangerous chars."""
    if not value:
        return ''
    value = str(value).strip()[:max_len]
    # Remove characters that could be used for injection
    value = re.sub(r'[<>{}\[\]|;`$\\]', '', value)
    return value

def _check_injection(text):
    """Check for prompt injection patterns in user input."""
    if not text:
        return False
    lower = text.lower()
    INJECTION_PATTERNS = [
        r'ignore\s+(all\s+)?previous\s+instructions',
        r'you\s+are\s+now\s+a',
        r'system\s*prompt',
        r'act\s+as\s+(a\s+)?',
        r'new\s+instructions?\s*:',
        r'forget\s+(your|all)\s+',
        r'override\s+',
        r'repeat\s+the\s+above',
        r'what\s+(is|are)\s+your\s+(instructions|rules|prompt)',
    ]
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower):
            logger.warning(f"Injection pattern detected: {pattern}")
            return True
    return False


def lambda_handler(event, context):
    """
    Retrieves crop advisory from Bedrock Knowledge Base.
    Called by orchestrator Lambda via direct invocation.
    Handles operations: get_crop_advisory, get_pest_alert, get_irrigation_advice.
    """
    try:
        # Support both Bedrock agent format (parameters[]) and
        # orchestrator invocation format (queryStringParameters{})
        if 'parameters' in event and isinstance(event['parameters'], list):
            params = {p['name']: p['value'] for p in event['parameters']}
        elif event.get('queryStringParameters'):
            params = event['queryStringParameters']
        elif event.get('body'):
            params = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            params = {}

        query = _sanitize_field(params.get('query', ''), MAX_QUERY_LENGTH)
        crop = _sanitize_field(params.get('crop', ''))
        state = _sanitize_field(params.get('state', ''))
        season = _sanitize_field(params.get('season', ''))
        soil_type = _sanitize_field(params.get('soil_type', ''))
        symptoms = _sanitize_field(params.get('symptoms', ''))
        location = _sanitize_field(params.get('location', ''))
        query_type = _sanitize_field(params.get('query_type', ''))

        # Security: check for prompt injection
        combined_input = f"{query} {crop} {state} {symptoms} {location}"
        if _check_injection(combined_input):
            return error_response("I can only help with agriculture-related queries. Please rephrase your question.", 400)

        # Build a natural language search query for better KB vector retrieval
        # Natural language queries work much better than pipe-separated keywords
        if query_type == 'irrigation' or 'irrigation' in (query or '').lower() or 'water' in (query or '').lower():
            # Irrigation-specific query
            nl_parts = []
            if crop:
                nl_parts.append(f"{crop} irrigation water requirement schedule")
            if location or state:
                nl_parts.append(f"in {location or state}")
            if soil_type:
                nl_parts.append(f"for {soil_type} soil")
            if season:
                nl_parts.append(f"during {season} season")
            nl_parts.append("drip sprinkler flood irrigation method water need per day")
            if query:
                nl_parts.append(query)
            search_query = " ".join(nl_parts)
        elif symptoms or 'pest' in (query_type or '').lower():
            # Pest/disease query
            nl_parts = []
            if crop:
                nl_parts.append(f"{crop}")
            if symptoms:
                nl_parts.append(f"showing {symptoms}")
            if state or location:
                nl_parts.append(f"in {state or location}")
            if season:
                nl_parts.append(f"during {season}")
            nl_parts.append("pest disease treatment pesticide spray prevention")
            if query:
                nl_parts.append(query)
            search_query = " ".join(nl_parts)
        else:
            # General crop advisory — use natural language format
            nl_parts = []
            if query:
                nl_parts.append(query)
            if crop:
                nl_parts.append(f"{crop} crop advisory varieties fertilizer yield")
            if state or location:
                nl_parts.append(f"in {state or location}")
            if season:
                nl_parts.append(f"during {season} season")
            if soil_type:
                nl_parts.append(f"for {soil_type} soil")
            search_query = " ".join(nl_parts) if nl_parts else "crop advisory recommendations India farming"

        if not KB_ID:
            msg = 'Bedrock Knowledge Base ID not configured'
            return error_response(msg, 500)

        # Query Knowledge Base with natural language query
        response = bedrock_kb.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={'text': search_query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 8
                }
            }
        )

        # Extract relevant chunks — sanitize content
        results = []
        for item in response.get('retrievalResults', []):
            content = item['content']['text']
            # Security: strip any HTML/script from KB content
            content = re.sub(r'<[^>]+>', '', content)
            results.append({
                'content': content[:2000],  # Cap individual chunk size
                'score': item.get('score', 0),
                'source': item.get('location', {}).get('s3Location', {}).get('uri', '')
            })

        result_data = {
            'query': search_query,
            'crop': crop,
            'state': state,
            'season': season,
            'advisory_data': results
        }

        return success_response(result_data)

    except Exception as e:
        logger.error(f"Crop advisory error: {str(e)}", exc_info=True)
        # Security: never expose internal error details
        return error_response("Crop advisory service is temporarily unavailable. Please try again.", 500)
