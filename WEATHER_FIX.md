# Weather API Error Fix

## Problem
The weather page shows: "Could not fetch weather. Please try again."

## Root Cause
The `OPENWEATHER_API_KEY` environment variable is not configured in the Lambda function.

## Solution

### Step 1: Get OpenWeatherMap API Key
1. Go to https://openweathermap.org/api
2. Sign up for a free account
3. Navigate to API Keys section
4. Copy your API key

### Step 2: Configure the API Key

**Option A: Using SAM Deploy Parameter**
```bash
sam deploy --parameter-overrides OpenWeatherApiKey=YOUR_ACTUAL_API_KEY
```

**Option B: Update samconfig.toml**
Add to your `samconfig.toml`:
```toml
[default.deploy.parameters]
parameter_overrides = "OpenWeatherApiKey=YOUR_ACTUAL_API_KEY BedrockAgentId=... BedrockAgentAliasId=..."
```

**Option C: Manual Lambda Configuration (Quick Test)**
1. Go to AWS Lambda Console
2. Find the `weather_lookup` function
3. Go to Configuration → Environment variables
4. Add: `OPENWEATHER_API_KEY` = `your_api_key`
5. Save

### Step 3: Test
1. Refresh the weather page
2. Click on any city or search for a location
3. Weather data should now load successfully

## Verification
Check Lambda logs in CloudWatch to see if the API key is being used:
```bash
sam logs -n WeatherLookupFunction --tail
```

## Notes
- Free tier allows 1,000 API calls per day
- API key may take 10-15 minutes to activate after signup
- The Lambda expects the key in environment variable `OPENWEATHER_API_KEY`
