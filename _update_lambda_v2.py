"""Update Pre-SignUp Lambda: keep autoConfirmUser but REMOVE autoVerifyEmail.
This way Cognito will allow us to send email verification codes after signup."""
import zipfile, io, boto3

new_code = (
    "def handler(event, context):\n"
    '    """Auto-confirm sign-up and auto-verify phone number.\n'
    "    Email is NOT auto-verified — we verify it via OTP after signup.\"\"\"\n"
    "    event['response']['autoConfirmUser'] = True\n"
    "    event['response']['autoVerifyPhone'] = True\n"
    "    # autoVerifyEmail intentionally omitted — verified via email OTP\n"
    "    return event\n"
)

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('index.py', new_code)

client = boto3.client('lambda', region_name='ap-south-1')
resp = client.update_function_code(
    FunctionName='smart-rural-ai-CognitoPreSignUp',
    ZipFile=zip_buffer.getvalue(),
)
print(f"Lambda updated: {resp['LastModified']}")
print("autoVerifyEmail REMOVED - email will be verified via OTP after signup")
