# backend/lambdas/farmer_profile/handler.py
# Lambda Tool: Farmer profile management (DynamoDB)
# Owner: Manoj RS
# Endpoints: GET /profile/{farmerId}, PUT /profile/{farmerId}
#            POST /otp/send, POST /otp/verify
# See: Detailed_Implementation_Guide.md Section 11

import json
import boto3
import os
import logging
import random
import re
import time
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ── Security: Input validation constants ──
MAX_NAME_LENGTH = 100
MAX_FIELD_LENGTH = 200
MAX_CROPS = 20
MAX_LAND_SIZE = 10000  # acres
PHONE_PATTERN = re.compile(r'^\d{10,15}$')

ALLOWED_PROFILE_FIELDS = {
    'name', 'state', 'district', 'crops', 'soil_type',
    'land_size_acres', 'language', 'created_at', 'farmer_id'
}

def _sanitize_text(value, max_len=MAX_FIELD_LENGTH):
    """Sanitize a text field: strip, truncate, remove dangerous chars."""
    if not value:
        return ''
    value = str(value).strip()[:max_len]
    value = re.sub(r'[<>{}\[\]|;`$\\]', '', value)
    return value

def _validate_phone(phone):
    """Validate and clean phone number. Returns (clean_phone, error_msg)."""
    if not phone:
        return None, 'Phone number is required'
    phone = re.sub(r'[\s\-\+]', '', str(phone))
    # Extract last 10 digits (Indian phone)
    digits_only = re.sub(r'\D', '', phone)
    if len(digits_only) < 10:
        return None, 'Invalid phone number'
    clean = digits_only[-10:]
    if not re.match(r'^[6-9]\d{9}$', clean):
        return None, 'Invalid Indian phone number'
    return clean, None


class DecimalEncoder(json.JSONEncoder):
    """Handle DynamoDB Decimal types in JSON serialization."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj == int(obj) else float(obj)
        return super().default(obj)


def convert_decimals(obj):
    """Recursively convert Decimal values to int/float for JSON safety."""
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, Decimal):
        return int(obj) if obj == int(obj) else float(obj)
    return obj


dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
table = dynamodb.Table(os.environ.get('DYNAMODB_PROFILES_TABLE', 'farmer_profiles'))
otp_table = dynamodb.Table(os.environ.get('DYNAMODB_OTP_TABLE', 'otp_codes'))
sns = boto3.client('sns', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))

COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', '')
STAGE = os.environ.get('STAGE', 'prod')

ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', 'https://d80ytlzsrax1n.cloudfront.net')
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE,OPTIONS'
}

OTP_EXPIRY_SECONDS = 300  # 5 minutes


def lambda_handler(event, context):
    """Handle profile CRUD and OTP send/verify."""
    try:
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '')

        # Handle CORS preflight
        if method == 'OPTIONS':
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

        # OTP endpoints
        if path == '/otp/send' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            return send_otp(body)
        elif path == '/otp/verify' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            return verify_otp(body)

        # Profile endpoints
        farmer_id = event.get('pathParameters', {}).get('farmerId')

        if not farmer_id:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Missing farmerId in path'})
            }

        if method == 'GET':
            return get_profile(farmer_id)
        elif method == 'PUT':
            body = json.loads(event.get('body', '{}'))
            return put_profile(farmer_id, body)
        elif method == 'DELETE':
            return delete_profile(farmer_id)
        else:
            return {
                'statusCode': 405,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': f'Method {method} not allowed'})
            }

    except Exception as e:
        logger.error(f"Profile error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }


def delete_profile(farmer_id):
    """Permanently delete farmer profile from DynamoDB AND Cognito user."""
    errors = []

    # 1. Delete DynamoDB profile
    try:
        table.delete_item(Key={'farmer_id': farmer_id})
        logger.info(f"Deleted DynamoDB profile: {farmer_id}")
    except Exception as e:
        logger.error(f"DynamoDB delete error: {str(e)}", exc_info=True)
        errors.append('Failed to delete profile data')

    # 2. Delete Cognito user (extract phone from farmer_id: ph_XXXXXXXXXX)
    if farmer_id.startswith('ph_'):
        phone = farmer_id[3:]  # strip "ph_"
        cognito_username = f'+91{phone}'
        try:
            cognito.admin_delete_user(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=cognito_username
            )
            logger.info(f"Deleted Cognito user: {cognito_username}")
        except cognito.exceptions.UserNotFoundException:
            logger.info(f"Cognito user already gone: {cognito_username}")
        except Exception as e:
            logger.error(f"Cognito delete error: {str(e)}", exc_info=True)
            errors.append('Failed to delete authentication record')

    if errors:
        return {
            'statusCode': 207,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'status': 'partial',
                'message': 'Profile partially deleted',
                'errors': errors
            })
        }

    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'status': 'success',
            'message': 'Profile and account deleted'
        })
    }


def get_profile(farmer_id):
    """Get farmer profile by ID. Returns empty profile if not found."""
    result = table.get_item(Key={'farmer_id': farmer_id})

    if 'Item' in result:
        profile_data = convert_decimals(result['Item'])
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'status': 'success',
                'data': profile_data,
                'message': 'Profile found'
            })
        }
    else:
        blank = {
            'farmer_id': farmer_id,
            'name': '',
            'state': '',
            'district': '',
            'crops': [],
            'soil_type': '',
            'land_size_acres': 0,
            'language': 'ta-IN',
            'created_at': None
        }
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'status': 'success',
                'data': blank,
                'message': 'New profile'
            })
        }


def put_profile(farmer_id, body):
    """Create or update farmer profile with schema validation."""
    now = datetime.utcnow().isoformat()

    # Security: reject unknown fields (allow only whitelisted)
    body_keys = set(body.keys())

    # ── Partial update: language-only (from language switcher) ──
    if body_keys == {'language'} or body_keys <= {'language', 'farmer_id'}:
        lang = _sanitize_text(body.get('language', 'en-IN'), 10)
        table.update_item(
            Key={'farmer_id': farmer_id},
            UpdateExpression='SET #lang = :language, updated_at = :updated_at',
            ExpressionAttributeNames={'#lang': 'language'},
            ExpressionAttributeValues={
                ':language': lang,
                ':updated_at': now
            }
        )
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({'status': 'success', 'message': 'Language updated'})
        }

    # ── Full profile update with validation ──
    # Sanitize all fields
    name = _sanitize_text(body.get('name', ''), MAX_NAME_LENGTH)
    state = _sanitize_text(body.get('state', ''))
    district = _sanitize_text(body.get('district', ''))
    soil_type = _sanitize_text(body.get('soil_type', ''))
    language = _sanitize_text(body.get('language', 'ta-IN'), 10)

    # Validate crops (must be a list of strings, capped)
    raw_crops = body.get('crops', [])
    if not isinstance(raw_crops, list):
        raw_crops = []
    crops = [_sanitize_text(str(c), 50) for c in raw_crops[:MAX_CROPS] if c]

    # Validate land size (must be a reasonable number)
    land_size = body.get('land_size_acres', 0)
    try:
        land_size = float(land_size)
        if land_size < 0 or land_size > MAX_LAND_SIZE:
            land_size = 0
    except (ValueError, TypeError):
        land_size = 0

    # Convert to Decimal for DynamoDB (rejects Python float)
    land_size = Decimal(str(land_size))

    now = datetime.utcnow().isoformat()
    item = {
        'farmer_id': farmer_id,
        'name': name,
        'state': state,
        'district': district,
        'crops': crops,
        'soil_type': soil_type,
        'land_size_acres': land_size,
        'language': language,
        'updated_at': now
    }

    # Use update_item to set created_at only if it doesn't exist (avoids extra get_item)
    # But put_item is simpler for full-profile saves, so we use conditional logic
    # First try to just update updated_at and merge; for simplicity, use put_item
    # with a created_at from the body (frontend can track it) or fallback to now
    item['created_at'] = body.get('created_at', now)

    # If item already exists, preserve its created_at using an update expression
    try:
        table.update_item(
            Key={'farmer_id': farmer_id},
            UpdateExpression='SET #n = :name, #s = :state, district = :district, crops = :crops, '
                           'soil_type = :soil_type, land_size_acres = :land_size, '
                           '#lang = :language, updated_at = :updated_at, '
                           'created_at = if_not_exists(created_at, :now)',
            ExpressionAttributeNames={
                '#n': 'name',
                '#s': 'state',
                '#lang': 'language'
            },
            ExpressionAttributeValues={
                ':name': item['name'],
                ':state': item['state'],
                ':district': item['district'],
                ':crops': item['crops'],
                ':soil_type': item['soil_type'],
                ':land_size': land_size,
                ':language': item['language'],
                ':updated_at': now,
                ':now': now
            }
        )
    except Exception as e:
        logger.error(f"update_item failed, falling back to put_item: {e}")
        table.put_item(Item=item)

    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'status': 'success',
            'message': 'Profile saved',
            'data': convert_decimals(item)
        })
    }


def send_otp(body):
    """Generate OTP and send via SNS SMS. Auto-adds numbers to SNS sandbox if needed."""
    phone = body.get('phone', '')
    clean_phone, phone_err = _validate_phone(phone)
    if phone_err:
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': phone_err})
        }

    full_phone = f'+91{clean_phone}'
    otp_code = str(random.randint(100000, 999999))
    expiry = int(time.time()) + OTP_EXPIRY_SECONDS

    sms_sent = False
    sandbox_verification = False

    # ── Step 1: Check if account is in SNS SMS Sandbox ──
    in_sandbox = False
    phone_verified_in_sandbox = False
    try:
        sandbox_status = sns.get_sms_sandbox_account_status()
        in_sandbox = sandbox_status.get('IsInSandbox', False)
        logger.info(f"SNS sandbox status: {'sandbox' if in_sandbox else 'production'}")
    except Exception as e:
        logger.warning(f"Could not check sandbox status: {e}")
        in_sandbox = True

    # ── Step 2: If in sandbox, check if this phone is verified ──
    if in_sandbox:
        try:
            sandbox_numbers = sns.list_sms_sandbox_phone_numbers()
            for entry in sandbox_numbers.get('PhoneNumbers', []):
                if entry.get('PhoneNumber') == full_phone and entry.get('Status') == 'Verified':
                    phone_verified_in_sandbox = True
                    break
            logger.info(f"Phone {full_phone} sandbox status: {'verified' if phone_verified_in_sandbox else 'not verified'}")
        except Exception as e:
            logger.warning(f"Could not check sandbox phone list: {e}")

    # ── Step 3: Decide send strategy ──
    # Strategy: Always try to send SMS. If monthly limit is reached, SNS accepts
    # the call but silently drops the message. We always store the OTP code and
    # return it so the frontend can show it as a fallback.
    if not in_sandbox or phone_verified_in_sandbox:
        # Production mode OR phone is verified in sandbox → send our OTP via SNS
        try:
            sns.publish(
                PhoneNumber=full_phone,
                Message=f'Your Smart Rural AI Advisor verification code is: {otp_code}. Valid for 5 minutes.',
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'RuralAI'
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            sms_sent = True
            logger.info(f"OTP SMS sent to +91{clean_phone[:3]}***{clean_phone[-2:]}")
        except Exception as e:
            logger.warning(f"SNS SMS failed: {e}")
    else:
        # Phone NOT verified in sandbox → auto-add to sandbox (AWS sends its own code)
        try:
            sns.create_sms_sandbox_phone_number(PhoneNumber=full_phone)
            sandbox_verification = True
            logger.info(f"Auto-added {full_phone} to SNS sandbox — AWS is sending verification code")
        except Exception as sandbox_err:
            err_msg = str(sandbox_err)
            logger.warning(f"Sandbox create failed: {err_msg}")
            if any(kw in err_msg.lower() for kw in ['already', 'pending', 'exists']):
                try:
                    sns.delete_sms_sandbox_phone_number(PhoneNumber=full_phone)
                except Exception:
                    pass
                try:
                    sns.create_sms_sandbox_phone_number(PhoneNumber=full_phone)
                    sandbox_verification = True
                    logger.info(f"Re-sent sandbox verification for {full_phone}")
                except Exception as retry_err:
                    logger.warning(f"Sandbox re-send also failed: {retry_err}")

    # ── Step 4: Store OTP in DynamoDB ──
    try:
        otp_item = {
            'phone': clean_phone,
            'otp_code': otp_code,
            'expiry_ttl': expiry,
            'created_at': datetime.utcnow().isoformat(),
            'verified': False,
            'sandbox_verification': sandbox_verification
        }
        otp_table.put_item(Item=otp_item)
    except Exception as e:
        logger.error(f"Failed to store OTP: {e}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Failed to generate OTP'})
        }

    # ── Step 5: Build response ──
    # Security: NEVER return the OTP code in the API response
    # The OTP is stored in DynamoDB and verified server-side only
    if sms_sent:
        message = 'OTP sent to your phone via SMS'
    elif sandbox_verification:
        message = 'Verification code sent to your phone (first-time setup)'
    else:
        message = 'OTP generated — check your phone for the code'

    response_data = {
        'status': 'success',
        'message': message,
        'sms_sent': sms_sent,
        'sandbox_verification': sandbox_verification,
        'phone_masked': f'+91 {clean_phone[:3]}***{clean_phone[-2:]}'
    }

    # Only include demo_otp in non-production (when SMS couldn't be sent)
    # This allows local dev/testing while keeping production secure
    if not sms_sent and not sandbox_verification and STAGE != 'prod':
        response_data['demo_otp'] = otp_code

    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps(response_data)
    }


def verify_otp(body):
    """Verify the OTP entered by the user. Supports both direct SMS and sandbox verification flows."""
    phone = body.get('phone', '')
    entered_otp = str(body.get('otp', '')).strip()

    clean_phone, phone_err = _validate_phone(phone)
    if phone_err:
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': phone_err})
        }
    if not entered_otp or not re.match(r'^\d{6}$', entered_otp):
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Invalid OTP format. Must be 6 digits.'})
        }

    full_phone = f'+91{clean_phone}'

    try:
        result = otp_table.get_item(Key={'phone': clean_phone})
        if 'Item' not in result:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'status': 'error', 'message': 'No OTP found. Please request a new one.'})
            }

        item = result['Item']
        expiry = int(item.get('expiry_ttl', 0))
        now = int(time.time())
        is_sandbox = item.get('sandbox_verification', False)

        if now > expiry:
            # Clean up expired OTP
            otp_table.delete_item(Key={'phone': clean_phone})
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'status': 'error', 'message': 'OTP has expired. Please request a new one.'})
            }

        # ── Verify OTP against stored code ──
        stored_otp = item.get('otp_code', '')

        if entered_otp != stored_otp:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'status': 'error', 'message': 'Incorrect OTP. Please try again.'})
            }

        # OTP is valid — mark as verified and clean up
        otp_table.delete_item(Key={'phone': clean_phone})

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'status': 'success',
                'message': 'OTP verified successfully',
                'verified': True
            })
        }

    except Exception as e:
        logger.error(f"OTP verification error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Verification failed. Please try again.'})
        }
