#!/usr/bin/env python3
"""
Twilio SMS Test Script
Tests sending SMS messages using Twilio API
"""

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Load credentials from environment variables (more secure)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')  # Your Twilio number
TO_PHONE_NUMBER = os.environ.get('TO_PHONE_NUMBER', '')  # Recipient number


def send_sms(to_number, message_body, from_number=None):
    """
    Send an SMS message using Twilio.
    
    Args:
        to_number (str): Recipient phone number in E.164 format (e.g., +916382593381)
        message_body (str): Message content to send
        from_number (str, optional): Twilio phone number to send from
        
    Returns:
        dict: Message details including SID, status, and error if any
    """
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Prepare message parameters
        message_params = {
            'to': to_number,
            'body': message_body
        }
        
        # Add from number if provided, otherwise use messaging service
        if from_number:
            message_params['from_'] = from_number
        else:
            # If you have a Messaging Service SID, use it instead
            messaging_service_sid = os.environ.get('TWILIO_MESSAGING_SERVICE_SID')
            if messaging_service_sid:
                message_params['messaging_service_sid'] = messaging_service_sid
            else:
                print("⚠️  Warning: No 'from' number or messaging service SID provided")
                print("    You need to either:")
                print("    1. Set TWILIO_PHONE_NUMBER environment variable")
                print("    2. Set TWILIO_MESSAGING_SERVICE_SID environment variable")
                print("    3. Pass from_number parameter to send_sms()")
                return {
                    'success': False,
                    'error': 'No sender number or messaging service configured'
                }
        
        # Send the message
        message = client.messages.create(**message_params)
        
        return {
            'success': True,
            'sid': message.sid,
            'status': message.status,
            'to': message.to,
            'from': message.from_,
            'body': message.body,
            'date_created': str(message.date_created),
            'price': message.price,
            'price_unit': message.price_unit
        }
        
    except TwilioRestException as e:
        return {
            'success': False,
            'error': str(e),
            'error_code': e.code,
            'error_message': e.msg
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def check_account_balance():
    """Check Twilio account balance."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        balance = client.api.v2010.balance.fetch()
        return {
            'success': True,
            'balance': balance.balance,
            'currency': balance.currency
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def list_phone_numbers():
    """List all phone numbers in your Twilio account."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        numbers = client.incoming_phone_numbers.list()
        return {
            'success': True,
            'numbers': [
                {
                    'phone_number': num.phone_number,
                    'friendly_name': num.friendly_name,
                    'capabilities': {
                        'sms': num.capabilities.get('sms', False),
                        'voice': num.capabilities.get('voice', False)
                    }
                }
                for num in numbers
            ]
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def check_trial_status():
    """Check if account is in trial mode."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        return {
            'success': True,
            'status': account.status,
            'is_trial': account.status == 'active' and account.type == 'Trial'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def list_verified_numbers():
    """List verified phone numbers (for trial accounts)."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        validated_numbers = client.validation_requests.list()
        return {
            'success': True,
            'verified_numbers': [num.phone_number for num in validated_numbers]
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main test function."""
    print("=" * 60)
    print("Twilio SMS Test Script")
    print("=" * 60)
    print()
    
    # Check trial status
    print("🔍 Checking account status...")
    trial_status = check_trial_status()
    if trial_status['success']:
        if trial_status.get('is_trial'):
            print("⚠️  TRIAL ACCOUNT DETECTED")
            print("   Limitations:")
            print("   • Can only send to 5 verified phone numbers")
            print("   • Messages include 'Sent from your Twilio trial account' prefix")
            print("   • To upgrade: https://console.twilio.com/billing")
            print()
            
            # List verified numbers
            verified = list_verified_numbers()
            if verified['success'] and verified['verified_numbers']:
                print(f"   ✅ Verified numbers ({len(verified['verified_numbers'])}/5):")
                for num in verified['verified_numbers']:
                    print(f"      • {num}")
            else:
                print("   ⚠️  No verified numbers found")
                print("   To verify numbers: https://console.twilio.com/phone-numbers/verified")
            print()
        else:
            print(f"✅ Account Status: {trial_status['status']}")
    else:
        print(f"❌ Error checking status: {trial_status['error']}")
    print()
    
    # Check account balance
    print("📊 Checking account balance...")
    balance_result = check_account_balance()
    if balance_result['success']:
        print(f"✅ Balance: {balance_result['balance']} {balance_result['currency']}")
    else:
        print(f"❌ Error: {balance_result['error']}")
    print()
    
    # List phone numbers
    print("📱 Listing phone numbers...")
    numbers_result = list_phone_numbers()
    if numbers_result['success']:
        if numbers_result['numbers']:
            print(f"✅ Found {len(numbers_result['numbers'])} phone number(s):")
            for num in numbers_result['numbers']:
                print(f"   • {num['phone_number']} - {num['friendly_name']}")
                print(f"     SMS: {num['capabilities']['sms']}, Voice: {num['capabilities']['voice']}")
        else:
            print("⚠️  No phone numbers found in account")
            print("   You may need to purchase a phone number or use a Messaging Service")
    else:
        print(f"❌ Error: {numbers_result['error']}")
    print()
    
    # Send test SMS
    print("📤 Sending test SMS...")
    test_message = "Hello from Twilio! This is a test message from your Smart Rural AI Advisor system. 🌾"
    
    # Try to get a from number
    from_number = TWILIO_PHONE_NUMBER
    if not from_number and numbers_result['success'] and numbers_result['numbers']:
        from_number = numbers_result['numbers'][0]['phone_number']
        print(f"   Using phone number: {from_number}")
    
    result = send_sms(
        to_number=TO_PHONE_NUMBER,
        message_body=test_message,
        from_number=from_number if from_number else None
    )
    
    if result['success']:
        print("✅ Message sent successfully!")
        print(f"   Message SID: {result['sid']}")
        print(f"   Status: {result['status']}")
        print(f"   To: {result['to']}")
        print(f"   From: {result['from']}")
        print(f"   Body: {result['body'][:50]}...")
        if result['price']:
            print(f"   Cost: {result['price']} {result['price_unit']}")
    else:
        print("❌ Failed to send message!")
        print(f"   Error: {result['error']}")
        if 'error_code' in result:
            print(f"   Error Code: {result['error_code']}")
            print(f"   Error Message: {result['error_message']}")
    print()
    
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
