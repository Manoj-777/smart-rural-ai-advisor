"""Add DELETE method to /profile/{farmerId} API Gateway resource."""
import boto3
import json

apigw = boto3.client('apigateway', region_name='ap-south-1')
lambda_client = boto3.client('lambda', region_name='ap-south-1')

REST_API_ID = 'zuadk9l1nc'
RESOURCE_ID = '2ncve6'
LAMBDA_NAME = 'smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt'
REGION = 'ap-south-1'
ACCOUNT_ID = '948809294205'
STAGE = 'Prod'

# Get Lambda ARN
lambda_info = lambda_client.get_function(FunctionName=LAMBDA_NAME)
lambda_arn = lambda_info['Configuration']['FunctionArn']
print(f"Lambda ARN: {lambda_arn}")

# 1. Create DELETE method (no auth for now, matches GET/PUT)
try:
    apigw.put_method(
        restApiId=REST_API_ID,
        resourceId=RESOURCE_ID,
        httpMethod='DELETE',
        authorizationType='NONE',
        requestParameters={'method.request.path.farmerId': True}
    )
    print("✅ DELETE method created")
except apigw.exceptions.ConflictException:
    print("⚠️ DELETE method already exists")

# 2. Set Lambda proxy integration
apigw.put_integration(
    restApiId=REST_API_ID,
    resourceId=RESOURCE_ID,
    httpMethod='DELETE',
    type='AWS_PROXY',
    integrationHttpMethod='POST',
    uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
)
print("✅ Lambda integration set")

# 3. Add Lambda permission for API Gateway to invoke
try:
    lambda_client.add_permission(
        FunctionName=LAMBDA_NAME,
        StatementId='apigateway-delete-profile',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f'arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{REST_API_ID}/*/DELETE/profile/*'
    )
    print("✅ Lambda permission added")
except lambda_client.exceptions.ResourceConflictException:
    print("⚠️ Lambda permission already exists")

# 4. Deploy to Prod stage
apigw.create_deployment(
    restApiId=REST_API_ID,
    stageName=STAGE,
    description='Add DELETE /profile/{farmerId} method'
)
print(f"✅ Deployed to {STAGE} stage")

# 5. Update OPTIONS CORS to include DELETE
# Get current OPTIONS integration response
try:
    resp = apigw.get_integration_response(
        restApiId=REST_API_ID,
        resourceId=RESOURCE_ID,
        httpMethod='OPTIONS',
        statusCode='200'
    )
    current_headers = resp.get('responseParameters', {})
    # Update Allow-Methods to include DELETE
    current_headers["method.response.header.Access-Control-Allow-Methods"] = "'GET,PUT,DELETE,POST,OPTIONS'"
    apigw.update_integration_response(
        restApiId=REST_API_ID,
        resourceId=RESOURCE_ID,
        httpMethod='OPTIONS',
        statusCode='200',
        patchOperations=[
            {
                'op': 'replace',
                'path': '/responseParameters/method.response.header.Access-Control-Allow-Methods',
                'value': "'GET,PUT,DELETE,POST,OPTIONS'"
            }
        ]
    )
    print("✅ OPTIONS CORS updated to include DELETE")
    
    # Re-deploy after CORS update
    apigw.create_deployment(
        restApiId=REST_API_ID,
        stageName=STAGE,
        description='Update CORS to include DELETE'
    )
    print("✅ Re-deployed with CORS update")
except Exception as e:
    print(f"⚠️ CORS update: {e}")

print("\n🎉 Done! DELETE /profile/{{farmerId}} is now live.")
