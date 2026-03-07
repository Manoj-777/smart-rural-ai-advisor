import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.crop_advisory import handler as crop_handler


def test_check_injection_flags_sql_injection_signatures():
    payloads = [
        "SELECT * FROM users",
        "drop table farmer_profiles",
        "union select password from accounts",
        "' OR 1=1 --",
    ]

    for payload in payloads:
        assert crop_handler._check_injection(payload) is True


def test_check_injection_flags_command_injection_signatures():
    payloads = [
        "run this && rm -rf /",
        "cmd.exe /c dir",
        "powershell -enc AAAA",
        "sh -c whoami",
    ]

    for payload in payloads:
        assert crop_handler._check_injection(payload) is True


def test_check_injection_preserves_safe_agri_queries():
    safe_queries = [
        "How to control stem borer in paddy?",
        "How to select best paddy seed variety for kharif season?",
        "Recommend fertilizer schedule for cotton in black soil",
    ]

    for query in safe_queries:
        assert crop_handler._check_injection(query) is False


def test_lambda_handler_blocks_sql_injection_with_400():
    event = {
        'body': json.dumps({'query': 'SELECT * FROM users', 'crop': 'paddy'})
    }

    response = crop_handler.lambda_handler(event, None)

    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['status'] == 'error'
