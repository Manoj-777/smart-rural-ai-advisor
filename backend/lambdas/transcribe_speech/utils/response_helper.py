# backend/utils/response_helper.py
# Standardized API response envelope + Bedrock Agent action group format
# Owner: Manoj RS
# See: Detailed_Implementation_Guide.md Section 6C (Integration Contracts)

import json


def success_response(data, message="Success", language="en", status_code=200):
    """
    Standard success response envelope for API Gateway.
    {
        "status": "success",
        "data": { ... },
        "message": "...",
        "language": "en"
    }
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
            "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS"
        },
        "body": json.dumps({
            "status": "success",
            "data": data,
            "message": message,
            "language": language
        })
    }


def error_response(message, status_code=500, language="en"):
    """
    Standard error response envelope for API Gateway.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
            "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS"
        },
        "body": json.dumps({
            "status": "error",
            "data": None,
            "message": message,
            "language": language
        })
    }


# --- Bedrock Agent Action Group helpers ---

def is_bedrock_event(event):
    """Check if this Lambda was invoked by a Bedrock Agent action group."""
    return 'actionGroup' in event and 'messageVersion' in event


def parse_bedrock_params(event):
    """
    Extract all parameters from a Bedrock Agent action group invocation.
    Handles both path/query 'parameters' and 'requestBody' properties.
    """
    params = {}
    # Path / query parameters
    for p in event.get('parameters', []):
        params[p['name']] = p.get('value', '')
    # Request body properties (for POST with requestBody in OpenAPI schema)
    rb = event.get('requestBody', {})
    content = rb.get('content', {})
    json_content = content.get('application/json', {})
    for prop in json_content.get('properties', []):
        params[prop['name']] = prop.get('value', '')
    return params


def bedrock_response(data, event):
    """
    Format a successful response for Bedrock Agent action group.
    Bedrock expects: messageVersion, response.actionGroup, response.apiPath,
    response.httpMethod, response.responseBody.
    """
    body = json.dumps(data) if isinstance(data, dict) else str(data)
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "POST"),
            "responseBody": {
                "application/json": {
                    "body": body
                }
            }
        }
    }


def bedrock_error_response(message, event):
    """Format an error response for Bedrock Agent action group."""
    return bedrock_response({"error": message}, event)
