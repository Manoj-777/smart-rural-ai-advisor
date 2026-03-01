# backend/utils/dynamodb_helper.py
# DynamoDB operations for farmer_profiles and chat_sessions tables
# Owner: Manoj RS
# See: Detailed_Implementation_Guide.md Section 12

import boto3
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
PROFILES_TABLE = os.environ.get('DYNAMODB_PROFILES_TABLE', 'farmer_profiles')
SESSIONS_TABLE = os.environ.get('DYNAMODB_SESSIONS_TABLE', 'chat_sessions')

profiles_table = dynamodb.Table(PROFILES_TABLE)
sessions_table = dynamodb.Table(SESSIONS_TABLE)


def get_farmer_profile(farmer_id):
    """Retrieve farmer profile by ID. Returns dict or None."""
    try:
        response = profiles_table.get_item(Key={'farmer_id': farmer_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"DynamoDB get profile error: {e}")
        return None


def put_farmer_profile(farmer_id, profile_data):
    """Create or update farmer profile. Returns True on success."""
    try:
        item = {
            'farmer_id': farmer_id,
            **profile_data,
            'updated_at': datetime.utcnow().isoformat()
        }
        profiles_table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"DynamoDB put profile error: {e}")
        return False


def save_chat_message(session_id, role, message, language='en', farmer_id=None):
    """Save a single chat message to session history."""
    try:
        timestamp = datetime.utcnow().isoformat()
        item = {
            'session_id': session_id,
            'timestamp': timestamp,
            'role': role,  # 'user' or 'assistant'
            'message': message,
            'language': language
        }
        if farmer_id:
            item['farmer_id'] = farmer_id
        sessions_table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"DynamoDB save chat error: {e}")
        return False


def get_chat_history(session_id, limit=10):
    """Retrieve recent chat messages for a session (sorted by timestamp)."""
    try:
        response = sessions_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('session_id').eq(session_id),
            ScanIndexForward=True,  # Oldest first
            Limit=limit
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"DynamoDB get chat history error: {e}")
        return []
