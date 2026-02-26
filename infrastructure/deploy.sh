#!/bin/bash
# Smart Rural AI Advisor — One-Command Deploy
# Run from project root: bash infrastructure/deploy.sh

set -e

echo "========================================="
echo "  Smart Rural AI Advisor — SAM Deploy"
echo "========================================="

cd "$(dirname "$0")"

echo "Building SAM application..."
sam build

echo ""
echo "Deploying to AWS..."
sam deploy \
    --stack-name smart-rural-ai-advisor \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --region ap-south-1 \
    --no-confirm-changeset

echo ""
echo "========================================="
echo "  Deploy complete!"
echo "  Check API Gateway URL in outputs above"
echo "========================================="
