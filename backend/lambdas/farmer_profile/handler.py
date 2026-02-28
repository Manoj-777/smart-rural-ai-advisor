# backend/lambdas/farmer_profile/handler.py
# AgentCore Tool: Farmer profile management (DynamoDB)
# Owner: Manoj RS
# Endpoints: GET /profile/{farmerId}, PUT /profile/{farmerId}
# See: Detailed_Implementation_Guide.md Section 11

import json
import boto3
import os
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
table = dynamodb.Table(os.environ.get('DYNAMODB_PROFILES_TABLE', 'farmer_profiles'))

CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,PUT,OPTIONS'
}


def lambda_handler(event, context):
    """Handle GET /profile/{farmerId} and PUT /profile/{farmerId}"""
    try:
        method = event.get('httpMethod', 'GET')
        farmer_id = event.get('pathParameters', {}).get('farmerId')

        # Handle CORS preflight
        if method == 'OPTIONS':
            return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

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
    """Create or update farmer profile."""
    # Convert land_size_acres to Decimal for DynamoDB (rejects Python float)
    land_size = body.get('land_size_acres', 0)
    if isinstance(land_size, float):
        land_size = Decimal(str(land_size))

    now = datetime.utcnow().isoformat()
    item = {
        'farmer_id': farmer_id,
        'name': body.get('name', ''),
        'state': body.get('state', ''),
        'district': body.get('district', ''),
        'crops': body.get('crops', []),
        'soil_type': body.get('soil_type', ''),
        'land_size_acres': land_size,
        'language': body.get('language', 'ta-IN'),
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
