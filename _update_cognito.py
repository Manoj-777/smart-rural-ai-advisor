"""Update Pre-SignUp Lambda + Cognito for email recovery."""
import zipfile, io, boto3

# 1. Update Pre-SignUp Lambda to also auto-verify email
new_code = (
    "def handler(event, context):\n"
    '    """Auto-confirm sign-up, auto-verify phone and email."""\n'
    "    event['response']['autoConfirmUser'] = True\n"
    "    event['response']['autoVerifyPhone'] = True\n"
    "    event['response']['autoVerifyEmail'] = True\n"
    "    return event\n"
)

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('index.py', new_code)
zip_bytes = zip_buffer.getvalue()

client = boto3.client('lambda', region_name='ap-south-1')
resp = client.update_function_code(
    FunctionName='smart-rural-ai-CognitoPreSignUp',
    ZipFile=zip_bytes,
)
print(f"Lambda updated: {resp['LastModified']}")

# 2. Update Cognito User Pool: email recovery + auto-verified
cognito = boto3.client('cognito-idp', region_name='ap-south-1')
pool = cognito.describe_user_pool(UserPoolId='ap-south-1_X58lNMEcn')['UserPool']

cognito.update_user_pool(
    UserPoolId='ap-south-1_X58lNMEcn',
    AutoVerifiedAttributes=['phone_number', 'email'],
    AccountRecoverySetting={
        'RecoveryMechanisms': [
            {'Priority': 1, 'Name': 'verified_email'},
            {'Priority': 2, 'Name': 'verified_phone_number'},
        ]
    },
    SmsConfiguration=pool.get('SmsConfiguration', {}),
)
print("Cognito updated: email priority 1 recovery, auto-verify email+phone")
