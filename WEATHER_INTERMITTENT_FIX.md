# Fixing Intermittent Weather API Issues

## Problem
Weather API works sometimes but fails intermittently with "Could not fetch weather" error.

## Common Causes & Solutions

### 1. Rate Limiting (Most Common)
**Symptoms:** Works initially, then fails after multiple requests

**OpenWeatherMap Free Tier Limits:**
- 60 calls per minute
- 1,000 calls per day

**Solutions:**
- ✅ Added retry logic with exponential backoff (already done)
- ✅ Reduced timeout from 10s to 8s (already done)
- Consider caching weather data in DynamoDB for 10-15 minutes

### 2. Lambda Cold Starts
**Symptoms:** First request after idle period is slow/fails

**Solutions:**
- ✅ Added retry logic (already done)
- Consider provisioned concurrency (costs money)
- Use Lambda SnapStart (if available for Python 3.13)

### 3. Network Timeouts
**Symptoms:** Random failures, especially during peak times

**Solutions:**
- ✅ Reduced timeout to 8s (already done)
- ✅ Added retry logic (already done)
- Consider using VPC endpoints if Lambda is in VPC

### 4. OpenWeatherMap API Issues
**Symptoms:** Consistent failures for specific locations

**Solutions:**
- Check OpenWeatherMap status: https://status.openweathermap.org/
- Verify API key is active in dashboard
- Try different location names

## Testing

### Test API Reliability
Run multiple requests to check success rate:
```powershell
.\test_weather_reliability.ps1 -TestCount 20 -Location "Chennai"
```

### Check Lambda Logs
```bash
aws logs tail /aws/lambda/smart-rural-ai-WeatherFunction --follow
```

### Test Specific Location
```powershell
curl "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/weather/Chennai"
```

## Improvements Made

### Backend (handler.py)
- ✅ Added retry logic (2 attempts)
- ✅ Better error logging
- ✅ Reduced timeout from 10s to 8s
- ✅ Graceful degradation (continues without forecast if it fails)
- ✅ Rate limit detection (HTTP 429)

### Frontend (WeatherPage.jsx)
- ✅ Better error messages
- ✅ Network error detection
- ✅ Timeout detection
- ✅ More detailed console logging

## Deploy Changes
```bash
cd infrastructure
sam build
sam deploy
```

## Monitoring
Watch for patterns in failures:
- Time of day (rate limits?)
- Specific locations (API issues?)
- After idle periods (cold starts?)

## Next Steps (Optional)

### Add Caching Layer
Create a DynamoDB table to cache weather data:
```yaml
WeatherCacheTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: weather_cache
    AttributeDefinitions:
      - AttributeName: location
        AttributeType: S
    KeySchema:
      - AttributeName: location
        KeyType: HASH
    TimeToLiveSpecification:
      AttributeName: ttl
      Enabled: true
```

### Add CloudWatch Alarms
Monitor failure rate:
```yaml
WeatherErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: WeatherAPIErrors
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 5
```

## Expected Behavior After Fix
- Success rate should be >95%
- Occasional failures are normal (network issues, API limits)
- Retries should handle most transient failures
- Users see specific error messages instead of generic ones
