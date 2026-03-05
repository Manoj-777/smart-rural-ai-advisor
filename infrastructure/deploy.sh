#!/bin/bash
# Smart Rural AI Advisor — One-Command Deploy
# Run from project root: bash infrastructure/deploy.sh

set -e

if [ -z "${OPENWEATHER_API_KEY}" ] || [ "${OPENWEATHER_API_KEY}" = "CHANGE_ME" ]; then
    echo "ERROR: OPENWEATHER_API_KEY is missing or set to CHANGE_ME."
    echo "Set it before deploy: export OPENWEATHER_API_KEY='<real-key>'"
    exit 1
fi

BEDROCK_KB_ID_VALUE="${BEDROCK_KB_ID:-9X1YUTXNOQ}"
ENFORCE_CODE_POLICY_VALUE="${ENFORCE_CODE_POLICY:-true}"
CLOUD_STACK_NAME="${STACK_NAME:-smart-rural-ai}"

echo "========================================="
echo "  Smart Rural AI Advisor — SAM Deploy"
echo "========================================="

cd "$(dirname "$0")"

echo "Building SAM application..."
sam build

echo ""
echo "Deploying to AWS..."
sam deploy \
        --stack-name "${CLOUD_STACK_NAME}" \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --region ap-south-1 \
        --parameter-overrides \
            "BedrockKBId=${BEDROCK_KB_ID_VALUE}" \
            "OpenWeatherApiKey=${OPENWEATHER_API_KEY}" \
            "EnforceCodePolicy=${ENFORCE_CODE_POLICY_VALUE}" \
    --no-confirm-changeset

echo ""
echo "========================================="
echo "  Deploy complete!"
echo "  Check API Gateway URL in outputs above"
echo "========================================="
