# backend/lambdas/weather_lookup/handler.py
# Lambda Tool: OpenWeatherMap integration
# Owner: Manoj RS
# Endpoint: GET /weather/{location}
# See: Detailed_Implementation_Guide.md Section 9

import json
import os
import logging
import re
import socket
import urllib.request
import urllib.error
from utils.response_helper import success_response, error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')

# ── Security: Input validation constants ──
MAX_LOCATION_LENGTH = 100
LOCATION_PATTERN = re.compile(r'^[\w\s\-\.,\'()]+$', re.UNICODE)

# Common India district/city spelling variants across data sources
LOCATION_ALIASES = {
    'Viluppuram': 'Villupuram',
    'Villupuram': 'Viluppuram',
}


def _http_get_json(url, timeout=8):
    """HTTP GET JSON using stdlib only (no third-party dependency)."""
    req = urllib.request.Request(url, headers={'User-Agent': 'smart-rural-ai-weather/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _validate_location(location):
    """Validate and sanitize location input. Returns (clean_location, error_msg)."""
    if not location or not location.strip():
        return None, 'Location is required'
    location = location.strip()[:MAX_LOCATION_LENGTH]
    # Block obvious injection attempts
    if any(ch in location for ch in ['<', '>', '{', '}', '|', ';', '`', '$', '\\']):
        return None, 'Invalid characters in location name'
    return location, None

def clean_location(name):
    """Strip administrative suffixes that confuse weather APIs."""
    if not name:
        return name
    import urllib.parse
    name = urllib.parse.unquote(name)  # decode %20 etc.
    name = re.sub(
        r'\b(Tahsil|Tehsil|Block|Mandal|Taluk[ua]?|Sub-?district|District|Division|'
        r'Sub-?Division|Municipality|Corporation|Cantonment|Nagar Panchayat|Town|'
        r'Circle|Range|Panchayat|Samiti|Gram|Assembly|Constituency|Revenue|Hobli|Firka|'
        r'Community Development)\b',
        '', name, flags=re.IGNORECASE
    )
    return re.sub(r'\s{2,}', ' ', name).strip()


def _get_location_candidates(location):
    """Return ordered location candidates for weather lookup retries."""
    candidates = [location]
    alias = LOCATION_ALIASES.get(location)
    if alias:
        candidates.append(alias)
    # Heuristic fallback: common double-letter variation (e.g., Viluppuram/Villupuram)
    if 'll' in location:
        candidates.append(location.replace('ll', 'l'))
    elif 'l' in location:
        candidates.append(location.replace('l', 'll', 1))

    # Preserve order while removing duplicates/empties
    seen = set()
    ordered = []
    for cand in candidates:
        if cand and cand not in seen:
            ordered.append(cand)
            seen.add(cand)
    return ordered


def lambda_handler(event, context):
    """
    Fetches current weather + 5-day forecast for a given location.
    Called by orchestrator Lambda or directly via API Gateway.
    Response shape matches API contract in Section 2b.
    """
    try:
        headers = event.get('headers') or {}
        origin = headers.get('origin') or headers.get('Origin')

        # CORS preflight: return immediately (do not run weather logic)
        if event.get('httpMethod') == 'OPTIONS':
            return success_response({}, message='OK', origin=origin)

        # Handle API Gateway call
        if 'parameters' in event:
            # Legacy Bedrock format (fallback)
            params = {p['name']: p['value'] for p in event['parameters']}
            location = params.get('location', 'Chennai')
        else:
            # Called via API Gateway
            location = event.get('pathParameters', {}).get('location', 'Chennai')

        # Extract optional lat/lon from query params (fallback for unknown cities)
        qsp = event.get('queryStringParameters') or {}
        lat = qsp.get('lat')
        lon = qsp.get('lon')

        # Security: validate location input
        location, val_err = _validate_location(location)
        if val_err:
            return error_response(val_err, 400, origin=origin)

        # Validate lat/lon if provided
        if lat:
            try:
                lat_f = float(lat)
                if not (-90 <= lat_f <= 90):
                    lat = None
            except (ValueError, TypeError):
                lat = None
        if lon:
            try:
                lon_f = float(lon)
                if not (-180 <= lon_f <= 180):
                    lon = None
            except (ValueError, TypeError):
                lon = None

        # Clean administrative suffixes (e.g. "Igatpuri Subdistrict" -> "Igatpuri")
        location = clean_location(location)
        logger.info(f"Cleaned location: {location}")

        if not OPENWEATHER_API_KEY:
            logger.error("OPENWEATHER_API_KEY not configured")
            return error_response('OpenWeather API key not configured', 500, origin=origin)

        # Current weather with retry logic and spelling-variant candidates
        location_candidates = _get_location_candidates(location)
        max_retries = 2
        current = None
        matched_location = location

        for candidate in location_candidates:
            current_url = (
                f"http://api.openweathermap.org/data/2.5/weather"
                f"?q={candidate},IN&appid={OPENWEATHER_API_KEY}&units=metric"
            )
            for attempt in range(max_retries):
                try:
                    logger.info(f"Fetching current weather for {candidate} (attempt {attempt + 1}/{max_retries})")
                    current = _http_get_json(current_url, timeout=8)

                    if current.get('cod') == 200:
                        matched_location = candidate
                        break
                    elif current.get('cod') == 429:
                        logger.warning(f"Rate limit hit for {candidate}")
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(1)
                            continue
                    else:
                        logger.warning(f"OpenWeather miss for {candidate}: {current.get('message', 'Unknown')}")
                        break
                except (TimeoutError, socket.timeout, urllib.error.URLError):
                    logger.warning(f"Timeout on attempt {attempt + 1} for {candidate}")
                    if attempt == max_retries - 1:
                        raise
                except Exception as e:
                    logger.error(f"Request error on attempt {attempt + 1} for {candidate}: {str(e)}")
                    if attempt == max_retries - 1:
                        raise

            if current and current.get('cod') == 200:
                break

        # If city name lookup failed and we have lat/lon, retry with coordinates
        if (not current or current.get('cod') != 200) and lat and lon:
            logger.info(f"City name '{location}' not found, falling back to lat={lat}, lon={lon}")
            coord_url = (
                f"http://api.openweathermap.org/data/2.5/weather"
                f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
            )
            try:
                coord_data = _http_get_json(coord_url, timeout=8)
                if coord_data.get('cod') == 200:
                    current = coord_data
                    logger.info(f"Coordinate fallback succeeded for {location}")
            except Exception as e:
                logger.warning(f"Coordinate fallback also failed: {str(e)}")

        if not current or current.get('cod') != 200:
            error_msg = current.get('message', 'Unknown error') if current else 'No response'
            logger.error(f"Failed to get weather for {location}: {error_msg}")
            # Security: never expose raw API error details to client
            return error_response(
                f"Weather data not available for '{location}'. Please check the location name and try again.",
                404 if current and current.get('cod') == '404' else 500
                , origin=origin
            )

        # 5-day forecast with retry — use coordinates if city name failed earlier
        if lat and lon and current.get('coord'):
            forecast_url = (
                f"http://api.openweathermap.org/data/2.5/forecast"
                f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&cnt=40"
            )
        else:
            forecast_url = (
                f"http://api.openweathermap.org/data/2.5/forecast"
                f"?q={matched_location},IN&appid={OPENWEATHER_API_KEY}&units=metric&cnt=40"
            )
        
        forecast_raw = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching forecast for {location} (attempt {attempt + 1}/{max_retries})")
                forecast_raw = _http_get_json(forecast_url, timeout=8)
                if forecast_raw.get('cod') == '200':
                    break
            except (TimeoutError, socket.timeout, urllib.error.URLError):
                logger.warning(f"Forecast timeout on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    # Continue without forecast if it fails
                    forecast_raw = {'list': []}
                    break
            except Exception as e:
                logger.error(f"Forecast error on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    forecast_raw = {'list': []}
                    break

        # Build response matching API contract field names
        weather_data = {
            "location": matched_location,
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

        return success_response(weather_data)

    except requests.exceptions.Timeout:
        logger.error(f"Weather API timeout for {location}")
        return error_response("Weather service timed out. Please try again.", 504)
    except Exception as e:
        logger.error(f"Weather error: {str(e)}", exc_info=True)
        # Security: never expose internal error details to client
        return error_response("Weather service is temporarily unavailable. Please try again.", 500)
