#!/bin/bash
# Check if the weather Lambda has the API key configured

echo "Checking Weather Lambda Environment Variables..."
echo ""

# Get the Lambda function name from the stack
FUNCTION_NAME=$(aws cloudformation describe-stack-resources \
  --stack-name smart-rural-ai \
  --region ap-south-1 \
  --query "StackResources[?LogicalResourceId=='WeatherFunction'].PhysicalResourceId" \
  --output text)

if [ -z "$FUNCTION_NAME" ]; then
  echo "❌ Could not find WeatherFunction in stack"
  exit 1
fi

echo "✅ Found Lambda: $FUNCTION_NAME"
echo ""

# Get environment variables
echo "Environment Variables:"
aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --region ap-south-1 \
  --query 'Environment.Variables' \
  --output json

echo ""
echo "Checking if OPENWEATHER_API_KEY is set..."
API_KEY=$(aws lambda get-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --region ap-south-1 \
  --query 'Environment.Variables.OPENWEATHER_API_KEY' \
  --output text)

if [ "$API_KEY" == "None" ] || [ -z "$API_KEY" ]; then
  echo "❌ OPENWEATHER_API_KEY is NOT set!"
  echo ""
  echo "To fix this, redeploy the stack:"
  echo "  cd infrastructure"
  echo "  sam build && sam deploy"
else
  echo "✅ OPENWEATHER_API_KEY is set: ${API_KEY:0:10}..."
  echo ""
  echo "Testing the API key with OpenWeatherMap..."
  curl -s "http://api.openweathermap.org/data/2.5/weather?q=Chennai,IN&appid=$API_KEY&units=metric" | jq -r '.cod, .message // "Success"'
fi
