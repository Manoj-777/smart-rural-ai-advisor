# backend/lambdas/crop_advisory/handler.py
# AgentCore Tool: Crop + Pest + Irrigation advisory
# Owner: Manoj RS
# See: Detailed_Implementation_Guide.md Section 9

import json
import boto3
import os
import logging
from utils.response_helper import (
    success_response, error_response,
    is_bedrock_event, parse_bedrock_params, bedrock_response, bedrock_error_response
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_agent = boto3.client('bedrock-agent-runtime')
KB_ID = os.environ.get('BEDROCK_KB_ID', '')


def lambda_handler(event, context):
    """
    Retrieves crop advisory from Knowledge Base.
    Called by Bedrock Agent as an action group tool.
    Handles operations: get_crop_advisory, get_pest_alert, get_irrigation_advice.
    """
    try:
        from_bedrock = is_bedrock_event(event)
        params = parse_bedrock_params(event) if from_bedrock else {
            p['name']: p['value'] for p in event.get('parameters', [])
        }

        query = params.get('query', '')
        crop = params.get('crop', '')
        state = params.get('state', '')
        season = params.get('season', '')
        soil_type = params.get('soil_type', '')
        symptoms = params.get('symptoms', '')
        location = params.get('location', '')
        query_type = params.get('query_type', '')

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
            return bedrock_error_response(msg, event) if from_bedrock else error_response(msg, 500)

        # Query Knowledge Base with natural language query
        response = bedrock_agent.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={'text': search_query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 8
                }
            }
        )

        # Extract relevant chunks
        results = []
        for item in response.get('retrievalResults', []):
            results.append({
                'content': item['content']['text'],
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

        if from_bedrock:
            return bedrock_response(result_data, event)
        return success_response(result_data)

    except Exception as e:
        logger.error(f"Crop advisory error: {str(e)}")
        if is_bedrock_event(event):
            return bedrock_error_response(str(e), event)
        return error_response(str(e), 500)
