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

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
        logger.error(f"Profile error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Internal server error'})
        }


def get_profile(farmer_id):
    """Get farmer profile by ID. Returns empty profile if not found."""
    result = table.get_item(Key={'farmer_id': farmer_id})

    if 'Item' in result:
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'status': 'success',
                'data': result['Item'],
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
    item = {
        'farmer_id': farmer_id,
        'name': body.get('name', ''),
        'state': body.get('state', ''),
        'district': body.get('district', ''),
        'crops': body.get('crops', []),
        'soil_type': body.get('soil_type', ''),
        'land_size_acres': body.get('land_size_acres', 0),
        'language': body.get('language', 'ta-IN'),
        'updated_at': datetime.utcnow().isoformat()
    }

    # Only set created_at on first save
    existing = table.get_item(Key={'farmer_id': farmer_id})
    if 'Item' not in existing:
        item['created_at'] = datetime.utcnow().isoformat()
    else:
        item['created_at'] = existing['Item'].get('created_at', datetime.utcnow().isoformat())

    table.put_item(Item=item)

    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'status': 'success',
            'message': 'Profile saved',
            'data': item
        })
    }
