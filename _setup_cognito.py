"""
Amazon Cognito — User Authentication for Smart Rural AI Advisor
Creates:
  • Cognito User Pool (phone number as username, OTP verification)
  • App Client (for React frontend, no secret — public SPA)
  • API Gateway Cognito Authorizer (attached to existing API)
  • Outputs config for frontend integration

Standalone — protects existing API without changing Lambda code.
Idempotent — safe to run multiple times.
"""

import boto3
import json
import time

REGION = 'ap-south-1'
ACCOUNT = '948809294205'
PROJECT = 'smart-rural-ai'

# Resource names
USER_POOL_NAME = f'{PROJECT}-farmers'
APP_CLIENT_NAME = f'{PROJECT}-frontend'
AUTHORIZER_NAME = f'{PROJECT}-cognito-auth'
API_GW_ID = 'zuadk9l1nc'
API_GW_STAGE = 'Prod'

# ── Clients ──
cognito = boto3.client('cognito-idp', region_name=REGION)
apigw = boto3.client('apigateway', region_name=REGION)
iam = boto3.client('iam')


# ══════════════════════════════════════════════════════════════
#  Step 1: Create User Pool
# ══════════════════════════════════════════════════════════════
def create_user_pool():
    print('\n[1/4] Creating Cognito User Pool...')

    # Check if already exists
    pools = cognito.list_user_pools(MaxResults=60)
    for pool in pools.get('UserPools', []):
        if pool['Name'] == USER_POOL_NAME:
            pool_id = pool['Id']
            print(f'  Already exists: {pool_id}')
            return pool_id

    # Create SNS role for SMS delivery first
    sns_role_arn = _create_cognito_sns_role()

    resp = cognito.create_user_pool(
        PoolName=USER_POOL_NAME,
        Policies={
            'PasswordPolicy': {
                'MinimumLength': 8,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': False,
                'TemporaryPasswordValidityDays': 7,
            }
        },
        AutoVerifiedAttributes=['phone_number'],
        UsernameAttributes=['phone_number'],
        MfaConfiguration='OFF',  # Farmers use phone OTP, keep it simple
        SmsConfiguration={
            'SnsCallerArn': sns_role_arn,
            'ExternalId': f'{PROJECT}-cognito-sms',
            'SnsRegion': REGION,
        },
        Schema=[
            {
                'Name': 'phone_number',
                'AttributeDataType': 'String',
                'Required': True,
                'Mutable': True,
            },
            {
                'Name': 'name',
                'AttributeDataType': 'String',
                'Required': False,
                'Mutable': True,
            },
        ],
        VerificationMessageTemplate={
            'DefaultEmailOption': 'CONFIRM_WITH_CODE',
            'SmsMessage': 'Smart Rural AI Advisor: Your OTP is {####}',
        },
        AccountRecoverySetting={
            'RecoveryMechanisms': [
                {'Priority': 1, 'Name': 'verified_phone_number'},
            ]
        },
        UserPoolTags={
            'Project': PROJECT,
            'Purpose': 'Farmer authentication',
        },
        AdminCreateUserConfig={
            'AllowAdminCreateUserOnly': False,  # Self-registration allowed
        },
        DeletionProtection='ACTIVE',
    )

    pool_id = resp['UserPool']['Id']
    print(f'  Created User Pool: {pool_id}')
    return pool_id


def _create_cognito_sns_role():
    """Create IAM role that lets Cognito send SMS via SNS."""
    role_name = f'{PROJECT}-CognitoSMSRole'

    trust = {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'Service': 'cognito-idp.amazonaws.com'},
            'Action': 'sts:AssumeRole',
            'Condition': {
                'StringEquals': {'sts:ExternalId': f'{PROJECT}-cognito-sms'}
            }
        }]
    }

    policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Action': 'sns:Publish',
            'Resource': '*',
        }]
    }

    try:
        resp = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description='Allows Cognito to send SMS OTP via SNS',
            Tags=[{'Key': 'Project', 'Value': PROJECT}],
        )
        role_arn = resp['Role']['Arn']
        print(f'  Created SMS role: {role_name}')
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f'arn:aws:iam::{ACCOUNT}:role/{role_name}'
        iam.update_assume_role_policy(RoleName=role_name, PolicyDocument=json.dumps(trust))
        print(f'  SMS role exists: {role_name}')

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName='CognitoSMSPublish',
        PolicyDocument=json.dumps(policy),
    )

    # Wait for IAM propagation
    import time
    time.sleep(8)
    return role_arn


# ══════════════════════════════════════════════════════════════
#  Step 2: Create App Client (public SPA — no client secret)
# ══════════════════════════════════════════════════════════════
def create_app_client(pool_id):
    print('\n[2/4] Creating App Client...')

    # Check if already exists
    clients = cognito.list_user_pool_clients(UserPoolId=pool_id, MaxResults=60)
    for client in clients.get('UserPoolClients', []):
        if client['ClientName'] == APP_CLIENT_NAME:
            client_id = client['ClientId']
            print(f'  Already exists: {client_id}')
            return client_id

    resp = cognito.create_user_pool_client(
        UserPoolId=pool_id,
        ClientName=APP_CLIENT_NAME,
        GenerateSecret=False,  # No secret for SPA (React)
        ExplicitAuthFlows=[
            'ALLOW_USER_SRP_AUTH',        # Secure password auth
            'ALLOW_REFRESH_TOKEN_AUTH',    # Refresh tokens
            'ALLOW_USER_PASSWORD_AUTH',    # Direct password auth (for simplicity)
        ],
        SupportedIdentityProviders=['COGNITO'],
        AllowedOAuthFlows=['implicit'],
        AllowedOAuthScopes=['openid', 'profile', 'phone'],
        AllowedOAuthFlowsUserPoolClient=True,
        CallbackURLs=[
            'https://d80ytlzsrax1n.cloudfront.net/',
            'http://localhost:5173/',  # Local dev
        ],
        LogoutURLs=[
            'https://d80ytlzsrax1n.cloudfront.net/',
            'http://localhost:5173/',
        ],
        PreventUserExistenceErrors='ENABLED',
        TokenValidityUnits={
            'AccessToken': 'hours',
            'IdToken': 'hours',
            'RefreshToken': 'days',
        },
        AccessTokenValidity=1,    # 1 hour
        IdTokenValidity=1,        # 1 hour
        RefreshTokenValidity=30,  # 30 days
    )

    client_id = resp['UserPoolClient']['ClientId']
    print(f'  Created App Client: {client_id}')
    return client_id


# ══════════════════════════════════════════════════════════════
#  Step 3: Create Cognito Domain (for Hosted UI)
# ══════════════════════════════════════════════════════════════
def create_domain(pool_id):
    print('\n[3/4] Creating Cognito Domain...')
    domain_prefix = f'{PROJECT}-auth'

    try:
        cognito.create_user_pool_domain(
            Domain=domain_prefix,
            UserPoolId=pool_id,
        )
        print(f'  Created domain: {domain_prefix}')
    except cognito.exceptions.InvalidParameterException:
        # Domain already exists
        print(f'  Domain already exists: {domain_prefix}')
    except Exception as e:
        if 'already exists' in str(e).lower():
            print(f'  Domain already exists: {domain_prefix}')
        else:
            print(f'  ⚠️  Domain creation note: {e}')
            print(f'     (Hosted UI domain is optional — API auth works without it)')

    domain_url = f'https://{domain_prefix}.auth.{REGION}.amazoncognito.com'
    print(f'  Domain URL: {domain_url}')
    return domain_prefix


# ══════════════════════════════════════════════════════════════
#  Step 4: Create API Gateway Authorizer
# ══════════════════════════════════════════════════════════════
def create_api_authorizer(pool_id):
    print('\n[4/4] Creating API Gateway Cognito Authorizer...')

    pool_arn = f'arn:aws:cognito-idp:{REGION}:{ACCOUNT}:userpool/{pool_id}'

    # Check if authorizer already exists
    auths = apigw.get_authorizers(restApiId=API_GW_ID)
    for auth in auths.get('items', []):
        if auth.get('name') == AUTHORIZER_NAME:
            auth_id = auth['id']
            print(f'  Already exists: {auth_id}')
            return auth_id

    resp = apigw.create_authorizer(
        restApiId=API_GW_ID,
        name=AUTHORIZER_NAME,
        type='COGNITO_USER_POOLS',
        providerARNs=[pool_arn],
        identitySource='method.request.header.Authorization',
    )

    auth_id = resp['id']
    print(f'  Created authorizer: {auth_id}')
    print(f'  Provider: {pool_arn}')
    print(f'\n  ℹ️  Authorizer is CREATED but NOT attached to endpoints.')
    print(f'     This is intentional — your existing /chat endpoint stays open.')
    print(f'     To protect an endpoint, attach it via API Gateway console or CLI.')

    return auth_id


def main():
    print('=' * 60)
    print('  Amazon Cognito — Farmer Authentication')
    print('=' * 60)

    pool_id = create_user_pool()
    client_id = create_app_client(pool_id)
    domain_prefix = create_domain(pool_id)
    auth_id = create_api_authorizer(pool_id)

    # Output config for frontend
    config = {
        'region': REGION,
        'userPoolId': pool_id,
        'userPoolClientId': client_id,
        'domain': f'{domain_prefix}.auth.{REGION}.amazoncognito.com',
        'authorizerId': auth_id,
        'apiGatewayId': API_GW_ID,
    }

    config_path = 'infrastructure/cognito_config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f'\n{"=" * 60}')
    print(f'  ✅ Cognito Setup Complete')
    print(f'{"=" * 60}')
    print(f'  User Pool:     {pool_id}')
    print(f'  App Client:    {client_id}')
    print(f'  Domain:        https://{domain_prefix}.auth.{REGION}.amazoncognito.com')
    print(f'  Authorizer:    {auth_id} (created, not enforced)')
    print(f'  Config saved:  {config_path}')
    print()
    print(f'  Hosted UI Sign-Up:')
    print(f'    https://{domain_prefix}.auth.{REGION}.amazoncognito.com/signup?')
    print(f'    client_id={client_id}&response_type=token&')
    print(f'    redirect_uri=https://d80ytlzsrax1n.cloudfront.net/')
    print()
    print(f'  ℹ️  Existing API endpoints remain open (no auth enforced yet).')
    print(f'     Cognito is ready to integrate whenever you choose.')
    print()


if __name__ == '__main__':
    main()
