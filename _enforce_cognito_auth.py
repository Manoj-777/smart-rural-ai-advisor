"""Enforce Cognito authorizer on API Gateway protected routes.
Public routes (health, OTP) stay open. All others require JWT."""
import boto3, json

REGION = 'ap-south-1'
API_ID = 'zuadk9l1nc'
AUTHORIZER_ID = 'eoegxr'

apigw = boto3.client('apigateway', region_name=REGION)

# Get all resources
resources = apigw.get_resources(restApiId=API_ID, limit=500)['items']

# Public routes that should NOT require auth
PUBLIC_PATHS = {'/', '/health', '/otp/send', '/otp/verify'}

print(f'API Gateway: {API_ID}')
print(f'Authorizer: {AUTHORIZER_ID}')
print(f'Public (no auth): {PUBLIC_PATHS}')
print()

updated = 0
skipped = 0

for resource in resources:
    path = resource.get('path', '')
    methods = resource.get('resourceMethods', {})

    for method_name in methods:
        if method_name == 'OPTIONS':
            continue  # Never put auth on CORS preflight

        # Check if this route should be public
        if path in PUBLIC_PATHS:
            print(f'  SKIP (public) {method_name} {path}')
            skipped += 1
            continue

        # Get current method config
        try:
            method = apigw.get_method(
                restApiId=API_ID,
                resourceId=resource['id'],
                httpMethod=method_name,
            )
        except Exception as e:
            print(f'  ERROR reading {method_name} {path}: {e}')
            continue

        current_auth = method.get('authorizationType', 'NONE')
        current_auth_id = method.get('authorizerId', '')

        if current_auth == 'COGNITO_USER_POOLS' and current_auth_id == AUTHORIZER_ID:
            print(f'  OK (already) {method_name} {path}')
            skipped += 1
            continue

        # Attach Cognito authorizer
        try:
            apigw.update_method(
                restApiId=API_ID,
                resourceId=resource['id'],
                httpMethod=method_name,
                patchOperations=[
                    {
                        'op': 'replace',
                        'path': '/authorizationType',
                        'value': 'COGNITO_USER_POOLS',
                    },
                    {
                        'op': 'replace',
                        'path': '/authorizerId',
                        'value': AUTHORIZER_ID,
                    },
                ],
            )
            print(f'  ✓ PROTECTED {method_name} {path} (was: {current_auth})')
            updated += 1
        except Exception as e:
            print(f'  ERROR updating {method_name} {path}: {e}')

print(f'\n{updated} routes protected, {skipped} skipped')

# Deploy the API to apply changes
if updated > 0:
    print('\nDeploying API to Prod stage...')
    apigw.create_deployment(restApiId=API_ID, stageName='Prod')
    print('✅ API deployed — Cognito authorizer is now enforced!')
else:
    print('\nNo changes needed — all routes already configured.')
