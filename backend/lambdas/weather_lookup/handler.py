# backend/lambdas/weather_lookup/handler.py
# AgentCore Tool: OpenWeatherMap integration
# Owner: Manoj RS
# Endpoint: GET /weather/{location}
# See: Detailed_Implementation_Guide.md Section 9

import json
import requests
import os
import logging
from utils.response_helper import (
    success_response, error_response,
    is_bedrock_event, parse_bedrock_params, bedrock_response, bedrock_error_response
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')


def lambda_handler(event, context):
    """
    Fetches current weather + 5-day forecast for a given location.
    Called by Bedrock Agent as a tool OR directly via API Gateway.
    Response shape matches API contract in Section 2b.
    """
    try:
        from_bedrock = is_bedrock_event(event)

        # Handle both Bedrock Agent tool call and direct API call
        if from_bedrock:
            params = parse_bedrock_params(event)
            location = params.get('location', 'Chennai')
        elif 'parameters' in event:
            # Legacy Bedrock format (fallback)
            params = {p['name']: p['value'] for p in event['parameters']}
            location = params.get('location', 'Chennai')
        else:
            # Called via API Gateway
            location = event.get('pathParameters', {}).get('location', 'Chennai')

        if not OPENWEATHER_API_KEY:
            return error_response('OpenWeather API key not configured', 500)

        # Current weather
        current_url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={location},IN&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        current = requests.get(current_url, timeout=10).json()

        if current.get('cod') != 200:
            return error_response(
                f"Weather data not found for '{location}': {current.get('message', 'Unknown error')}",
                404
            )

        # 5-day forecast
        forecast_url = (
            f"http://api.openweathermap.org/data/2.5/forecast"
            f"?q={location},IN&appid={OPENWEATHER_API_KEY}&units=metric&cnt=40"
        )
        forecast_raw = requests.get(forecast_url, timeout=10).json()

        # Build response matching API contract field names
        weather_data = {
            "location": location,
            "current": {
                "temp_celsius": current.get("main", {}).get("temp"),
                "humidity": current.get("main", {}).get("humidity"),
                "description": current.get("weather", [{}])[0].get("description", ""),
                "wind_speed_kmh": round(
                    (current.get("wind", {}).get("speed", 0)) * 3.6, 1
                ),  # m/s → km/h
                "rain_mm": current.get("rain", {}).get("1h", 0)
            },
            "forecast": [],
            "farming_advisory": ""
        }

        # Aggregate to daily forecast (group by date)
        daily = {}
        for item in forecast_raw.get("list", []):
            date = item.get("dt_txt", "")[:10]  # "2026-02-27"
            temp = item.get("main", {}).get("temp", 0)
            if date not in daily:
                daily[date] = {"temps": [], "descriptions": [], "rain": 0}
            daily[date]["temps"].append(temp)
            daily[date]["descriptions"].append(
                item.get("weather", [{}])[0].get("description", "")
            )
            daily[date]["rain"] += item.get("rain", {}).get("3h", 0)

        for date, info in list(daily.items())[:5]:  # Cap at 5 days
            weather_data["forecast"].append({
                "date": date,
                "temp_min": round(min(info["temps"]), 1),
                "temp_max": round(max(info["temps"]), 1),
                "description": max(
                    set(info["descriptions"]),
                    key=info["descriptions"].count
                ),
                "rain_probability": min(
                    100, int((info["rain"] / 5) * 100)
                )  # rough estimate
            })

        # Simple farming advisory based on conditions
        temp = weather_data["current"]["temp_celsius"] or 0
        humidity = weather_data["current"]["humidity"] or 0
        rain = weather_data["current"]["rain_mm"] or 0
        advisories = []
        if humidity > 80:
            advisories.append(
                "High humidity — risk of fungal infections. Monitor crops."
            )
        if temp > 38:
            advisories.append(
                "Extreme heat — ensure adequate irrigation."
            )
        if rain > 10:
            advisories.append(
                "Heavy rain expected — avoid pesticide spraying today."
            )
        if not advisories:
            advisories.append(
                "Conditions are normal. Good day for regular farm activities."
            )
        weather_data["farming_advisory"] = " ".join(advisories)

        logger.info(
            f"Weather for {location}: {weather_data['current']['temp_celsius']}°C"
        )

        if from_bedrock:
            return bedrock_response(weather_data, event)
        return success_response(weather_data)

    except requests.exceptions.Timeout:
        logger.error(f"Weather API timeout for {location}")
        msg = "Weather service timed out. Please try again."
        if is_bedrock_event(event):
            return bedrock_error_response(msg, event)
        return error_response(msg, 504)
    except Exception as e:
        logger.error(f"Weather error: {str(e)}")
        if is_bedrock_event(event):
            return bedrock_error_response(str(e), event)
        return error_response(str(e), 500)
