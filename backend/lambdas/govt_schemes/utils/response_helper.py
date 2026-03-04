# backend/utils/response_helper.py
# Standardized API response envelope
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
            "Access-Control-Allow-Origin": "https://d80ytlzsrax1n.cloudfront.net",
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
            "Access-Control-Allow-Origin": "https://d80ytlzsrax1n.cloudfront.net",
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

