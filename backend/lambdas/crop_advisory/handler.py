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

        # Build a rich search query from all available params
        parts = [query] if query else []
        if crop:
            parts.append(f"crop: {crop}")
        if state:
            parts.append(f"state: {state}")
        if season:
            parts.append(f"season: {season}")
        if soil_type:
            parts.append(f"soil: {soil_type}")
        if symptoms:
            parts.append(f"symptoms: {symptoms}")
        if location:
            parts.append(f"location: {location}")
        search_query = " | ".join(parts) if parts else "general crop advisory India"

        if not KB_ID:
            msg = 'Bedrock Knowledge Base ID not configured'
            return bedrock_error_response(msg, event) if from_bedrock else error_response(msg, 500)

        # Query Knowledge Base
        response = bedrock_agent.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={'text': search_query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
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
