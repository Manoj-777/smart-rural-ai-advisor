"""Create Cognito Pre-SignUp Lambda trigger for auto-confirmation.
Avoids SMS sandbox issues while keeping real JWT auth."""
import boto3, json, time, zipfile, io

REGION = 'ap-south-1'
ACCOUNT = '948809294205'
PROJECT = 'smart-rural-ai'
FN_NAME = f'{PROJECT}-CognitoPreSignUp'
ROLE_NAME = f'{PROJECT}-CognitoPreSignUpRole'
POOL_ID = 'ap-south-1_X58lNMEcn'

lam = boto3.client('lambda', region_name=REGION)
iam = boto3.client('iam')
cognito = boto3.client('cognito-idp', region_name=REGION)

LAMBDA_CODE = '''
def handler(event, context):
    """Auto-confirm sign-up and auto-verify phone number."""
    event['response']['autoConfirmUser'] = True
    event['response']['autoVerifyPhone'] = True
    return event
'''

# 1. Create IAM role
print('[1/3] Creating IAM role...')
trust = {
    'Version': '2012-10-17',
    'Statement': [{
        'Effect': 'Allow',
        'Principal': {'Service': 'lambda.amazonaws.com'},
        'Action': 'sts:AssumeRole'
    }]
}
try:
    resp = iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust),
        Description='Role for Cognito Pre-SignUp trigger Lambda',
    )
    role_arn = resp['Role']['Arn']
    print(f'  Created: {role_arn}')
    iam.attach_role_policy(RoleName=ROLE_NAME,
        PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole')
    time.sleep(10)  # IAM propagation
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = f'arn:aws:iam::{ACCOUNT}:role/{ROLE_NAME}'
    print(f'  Exists: {role_arn}')

# 2. Create Lambda
print('[2/3] Creating Lambda...')
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as zf:
    zf.writestr('index.py', LAMBDA_CODE)
buf.seek(0)

try:
    lam.create_function(
        FunctionName=FN_NAME,
        Runtime='python3.12',
        Role=role_arn,
        Handler='index.handler',
        Code={'ZipFile': buf.read()},
        Timeout=5,
        MemorySize=128,
    )
    print(f'  Created: {FN_NAME}')
except lam.exceptions.ResourceConflictException:
    buf.seek(0)
    lam.update_function_code(FunctionName=FN_NAME, ZipFile=buf.read())
    print(f'  Updated: {FN_NAME}')

fn_arn = f'arn:aws:lambda:{REGION}:{ACCOUNT}:function:{FN_NAME}'

# Add permission for Cognito to invoke
try:
    lam.add_permission(
        FunctionName=FN_NAME,
        StatementId='CognitoPreSignUp',
        Action='lambda:InvokeFunction',
        Principal='cognito-idp.amazonaws.com',
        SourceArn=f'arn:aws:cognito-idp:{REGION}:{ACCOUNT}:userpool/{POOL_ID}',
    )
    print('  Added Cognito invoke permission')
except lam.exceptions.ResourceConflictException:
    print('  Cognito invoke permission already exists')

# 3. Attach trigger to User Pool
print('[3/3] Attaching Pre-SignUp trigger...')
cognito.update_user_pool(
    UserPoolId=POOL_ID,
    AutoVerifiedAttributes=['phone_number'],
    MfaConfiguration='OFF',
    SmsConfiguration={
        'SnsCallerArn': f'arn:aws:iam::{ACCOUNT}:role/{PROJECT}-CognitoSMSRole',
        'ExternalId': f'{PROJECT}-cognito-sms',
        'SnsRegion': REGION,
    },
    LambdaConfig={
        'PreSignUp': fn_arn,
    },
)
print(f'  Attached PreSignUp trigger: {fn_arn}')

print('\n✅ Done — Cognito will auto-confirm sign-ups (no SMS OTP needed)')
print('   Security: JWT tokens enforced on API Gateway')
