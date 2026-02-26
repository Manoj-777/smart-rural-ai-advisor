"""
Smart Rural AI Advisor — Tool Definitions for Strands Agent

These tools are Python functions decorated with @tool that the Strands Agent
can call. Each tool invokes our existing deployed Lambda function via boto3.

When AgentCore Gateway is set up, these will be replaced by MCP tool connections
to the Gateway. For now, direct Lambda invocation serves as the working
implementation.

Tools:
    1. get_crop_advisory   — Crop guidance from Knowledge Base
    2. get_pest_alert      — Pest/disease identification + treatments
    3. get_irrigation_advice — Irrigation scheduling + methods
    4. get_weather         — Real-time weather + farming advisory
    5. search_schemes      — Government scheme search
    6. get_farmer_profile  — Farmer profile lookup from DynamoDB
"""

import json
import os
import logging

import boto3
from strands import tool

logger = logging.getLogger("smart-rural-tools")

REGION = os.environ.get("AWS_REGION", "ap-south-1")

# Lambda function names from SAM deployment
LAMBDA_NAMES = {
    "crop_advisory": os.environ.get(
        "CROP_ADVISORY_FUNCTION",
        "smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY",
    ),
    "weather": os.environ.get(
        "WEATHER_FUNCTION",
        "smart-rural-ai-WeatherFunction-dilSoHSLlXGN",
    ),
    "govt_schemes": os.environ.get(
        "GOVT_SCHEMES_FUNCTION",
        "smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv",
    ),
    "farmer_profile": os.environ.get(
        "FARMER_PROFILE_FUNCTION",
        "smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt",
    ),
}

# Shared Lambda client (reused across invocations)
lambda_client = boto3.client("lambda", region_name=REGION)


def _invoke_lambda(function_key: str, payload: dict) -> dict:
    """
    Invoke a Lambda function and return parsed response body.

    Args:
        function_key: Key into LAMBDA_NAMES dict
        payload: API Gateway-style event to send

    Returns:
        Parsed response body dict
    """
    function_name = LAMBDA_NAMES.get(function_key)
    if not function_name:
        return {"error": f"Lambda function not configured for: {function_key}"}

    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode("utf-8"),
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))

        # Parse the API Gateway response envelope
        if isinstance(response_payload, dict) and "body" in response_payload:
            body = json.loads(response_payload["body"])
            return body.get("data", body)
        return response_payload

    except Exception as e:
        logger.error(f"Lambda invocation failed for {function_key}: {e}")
        return {"error": str(e)}


# ━━━━━━━━━━━━━━━━━━━━━━ Crop Advisory Tools ━━━━━━━━━━━━━━━━━━━━━━


@tool
def get_crop_advisory(
    crop: str = "",
    state: str = "",
    season: str = "",
    soil_type: str = "",
    query: str = "",
) -> str:
    """Get crop advisory guidance for Indian agriculture. Provides recommendations
    on crop selection, growing conditions, varieties, and best practices based on
    the farmer's region, soil type, and season.

    Args:
        crop: Name of the crop (e.g., 'Rice', 'Wheat', 'Cotton')
        state: Indian state (e.g., 'Tamil Nadu', 'Andhra Pradesh')
        season: Growing season (e.g., 'Kharif', 'Rabi', 'Summer')
        soil_type: Soil type (e.g., 'Clay loam', 'Sandy', 'Red soil')
        query: Additional free-text farming question
    """
    payload = {
        "httpMethod": "GET",
        "pathParameters": {},
        "queryStringParameters": {
            "operation": "get_crop_advisory",
            "crop": crop,
            "state": state,
            "season": season,
            "soil_type": soil_type,
            "query": query,
        },
    }
    result = _invoke_lambda("crop_advisory", payload)
    return json.dumps(result, indent=2)


@tool
def get_pest_alert(
    crop: str = "",
    symptoms: str = "",
    state: str = "",
    season: str = "",
) -> str:
    """Identify crop pests and diseases, and get treatment recommendations.
    Provides both organic and chemical treatment options with application methods.

    Args:
        crop: Name of the affected crop (e.g., 'Rice', 'Tomato')
        symptoms: Description of symptoms (e.g., 'yellow leaves', 'brown spots', 'wilting')
        state: Indian state for region-specific pest patterns
        season: Current season for seasonal pest alerts
    """
    payload = {
        "httpMethod": "GET",
        "pathParameters": {},
        "queryStringParameters": {
            "operation": "get_pest_alert",
            "crop": crop,
            "symptoms": symptoms,
            "state": state,
            "season": season,
        },
    }
    result = _invoke_lambda("crop_advisory", payload)
    return json.dumps(result, indent=2)


@tool
def get_irrigation_advice(
    crop: str = "",
    location: str = "",
    soil_type: str = "",
    query: str = "",
) -> str:
    """Get irrigation recommendations including scheduling, water requirements,
    and best irrigation methods (drip, sprinkler, flood) for specific crops.

    Args:
        crop: Name of the crop (e.g., 'Rice', 'Sugarcane')
        location: Location for weather-based irrigation advice
        soil_type: Soil type affecting water retention
        query: Additional irrigation-specific question
    """
    payload = {
        "httpMethod": "GET",
        "pathParameters": {},
        "queryStringParameters": {
            "operation": "get_irrigation_advice",
            "crop": crop,
            "location": location,
            "soil_type": soil_type,
            "query": query,
        },
    }
    result = _invoke_lambda("crop_advisory", payload)
    return json.dumps(result, indent=2)


# ━━━━━━━━━━━━━━━━━━━━━━ Weather Tool ━━━━━━━━━━━━━━━━━━━━━━


@tool
def get_weather(location: str) -> str:
    """Get real-time weather data with farming advisory for any location in India.
    Returns current conditions, 5-day forecast, and farming-specific recommendations
    for field work, irrigation, and crop protection.

    Args:
        location: City or district name in India (e.g., 'Chennai', 'Coimbatore', 'Guntur')
    """
    payload = {
        "httpMethod": "GET",
        "pathParameters": {"location": location},
        "queryStringParameters": {},
    }
    result = _invoke_lambda("weather", payload)
    return json.dumps(result, indent=2)


# ━━━━━━━━━━━━━━━━━━━━━━ Government Schemes Tool ━━━━━━━━━━━━━━━━━━━━━━


@tool
def search_schemes(keyword: str = "", category: str = "") -> str:
    """Search Indian government agricultural schemes, subsidies, insurance,
    and loan programs. Returns eligibility criteria, benefits, and step-by-step
    application process.

    Args:
        keyword: Search term (e.g., 'insurance', 'subsidy', 'drip irrigation', 'loan')
        category: Optional scheme category filter (e.g., 'insurance', 'credit', 'irrigation')
    """
    payload = {
        "httpMethod": "GET",
        "pathParameters": {},
        "queryStringParameters": {
            "keyword": keyword,
            "category": category,
        },
    }
    result = _invoke_lambda("govt_schemes", payload)
    return json.dumps(result, indent=2)


# ━━━━━━━━━━━━━━━━━━━━━━ Farmer Profile Tool ━━━━━━━━━━━━━━━━━━━━━━


@tool
def get_farmer_profile(farmer_id: str) -> str:
    """Look up a farmer's saved profile including their location, crops, soil type,
    and farming details. Use this to personalize advice for returning farmers.

    Args:
        farmer_id: The unique farmer identifier
    """
    payload = {
        "httpMethod": "GET",
        "pathParameters": {"farmerId": farmer_id},
        "queryStringParameters": {},
    }
    result = _invoke_lambda("farmer_profile", payload)
    return json.dumps(result, indent=2)
