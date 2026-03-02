# _setup_guardrails.py
# Creates AWS Bedrock Guardrail + DynamoDB rate_limits table
# Run once to set up enterprise guardrail infrastructure
# Owner: Manoj RS

import boto3
import json
import time

REGION = 'ap-south-1'
bedrock = boto3.client('bedrock', region_name=REGION)
dynamodb = boto3.client('dynamodb', region_name=REGION)


def create_bedrock_guardrail():
    """Create a Bedrock Guardrail with content filters, topic policies, PII filters."""
    print("=== Creating Bedrock Guardrail ===")

    try:
        response = bedrock.create_guardrail(
            name='smart-rural-ai-guardrail',
            description='Enterprise guardrail for Smart Rural AI Advisor — content filtering, PII protection, topic enforcement',

            # Topic policy: deny off-topic queries
            topicPolicyConfig={
                'topicsConfig': [
                    {
                        'name': 'NonAgriculturalTopics',
                        'definition': 'Any topic not related to agriculture, farming, crops, weather, pests, irrigation, livestock, government agricultural schemes, rural livelihood, soil, fertilizers, or market prices',
                        'examples': [
                            'Write me a poem about love',
                            'Help me hack a website',
                            'Tell me about cryptocurrency trading',
                            'Write Python code for a web scraper',
                            'Who will win the election',
                        ],
                        'type': 'DENY',
                    },
                    {
                        'name': 'HarmfulAgricultureContent',
                        'definition': 'Requests to cause deliberate harm using agricultural knowledge, including poisoning water/soil, sabotaging crops, harming livestock, or using banned pesticides to harm people',
                        'examples': [
                            'How to poison my neighbor\'s crops',
                            'How to contaminate the village water supply',
                            'How to use pesticide to harm someone',
                        ],
                        'type': 'DENY',
                    },
                ],
            },

            # Content filters: block hate, insults, sexual, violence, misconduct
            contentPolicyConfig={
                'filtersConfig': [
                    {'type': 'HATE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                    {'type': 'INSULTS', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                    {'type': 'SEXUAL', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                    {'type': 'VIOLENCE', 'inputStrength': 'MEDIUM', 'outputStrength': 'HIGH'},
                    {'type': 'MISCONDUCT', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                    {'type': 'PROMPT_ATTACK', 'inputStrength': 'HIGH', 'outputStrength': 'NONE'},
                ],
            },

            # PII filters: mask sensitive data in input and output
            sensitiveInformationPolicyConfig={
                'piiEntitiesConfig': [
                    {'type': 'EMAIL', 'action': 'ANONYMIZE'},
                    {'type': 'PHONE', 'action': 'ANONYMIZE'},
                    {'type': 'NAME', 'action': 'ANONYMIZE'},
                    {'type': 'US_SOCIAL_SECURITY_NUMBER', 'action': 'BLOCK'},  # catches numeric IDs
                    {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'BLOCK'},
                    {'type': 'PIN', 'action': 'BLOCK'},
                    {'type': 'PASSWORD', 'action': 'BLOCK'},
                    {'type': 'AWS_ACCESS_KEY', 'action': 'BLOCK'},
                    {'type': 'AWS_SECRET_KEY', 'action': 'BLOCK'},
                    {'type': 'IP_ADDRESS', 'action': 'ANONYMIZE'},
                ],
                'regexesConfig': [
                    {
                        'name': 'AadhaarNumber',
                        'description': 'Indian Aadhaar number (12 digits)',
                        'pattern': r'\b[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}\b',
                        'action': 'ANONYMIZE',
                    },
                    {
                        'name': 'PANNumber',
                        'description': 'Indian PAN card number',
                        'pattern': r'\b[A-Z]{5}\d{4}[A-Z]\b',
                        'action': 'ANONYMIZE',
                    },
                    {
                        'name': 'IFSCCode',
                        'description': 'Indian bank IFSC code',
                        'pattern': r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
                        'action': 'ANONYMIZE',
                    },
                    {
                        'name': 'IndianBankAccount',
                        'description': 'Indian bank account number',
                        'pattern': r'\b\d{9,18}\b',
                        'action': 'ANONYMIZE',
                    },
                ],
            },

            # Word policy: block known banned pesticides and harmful terms
            wordPolicyConfig={
                'wordsConfig': [
                    {'text': 'endosulfan'},
                    {'text': 'monocrotophos'},
                    {'text': 'methyl parathion'},
                    {'text': 'phorate'},
                    {'text': 'triazophos'},
                ],
                'managedWordListsConfig': [
                    {'type': 'PROFANITY'},
                ],
            },

            blockedInputMessaging=(
                "I can only help with agriculture and farming topics. "
                "Please ask about crops, weather, pests, schemes, irrigation, or market prices."
            ),
            blockedOutputsMessaging=(
                "I cannot provide that information. Please ask a farming-related question "
                "and I'll do my best to help."
            ),
        )

        guardrail_id = response['guardrailId']
        version = response['version']
        print(f"Guardrail created: ID={guardrail_id}, Version={version}")

        # Create a version for production use
        print("Creating guardrail version...")
        ver_resp = bedrock.create_guardrail_version(
            guardrailIdentifier=guardrail_id,
            description='v1 - Initial enterprise guardrail with content + PII + topic filters',
        )
        prod_version = ver_resp['version']
        print(f"Production version created: {prod_version}")

        return guardrail_id, prod_version

    except bedrock.exceptions.ConflictException:
        # Guardrail already exists — find it
        print("Guardrail may already exist, listing...")
        resp = bedrock.list_guardrails(maxResults=50)
        for g in resp.get('guardrails', []):
            if g['name'] == 'smart-rural-ai-guardrail':
                gid = g['id']
                gver = g['version']
                print(f"Found existing guardrail: ID={gid}, Version={gver}")
                return gid, gver
        raise
    except Exception as e:
        print(f"Error creating guardrail: {e}")
        raise


def create_rate_limits_table():
    """Create DynamoDB table for rate limiting with TTL."""
    print("\n=== Creating rate_limits DynamoDB table ===")

    try:
        dynamodb.create_table(
            TableName='rate_limits',
            KeySchema=[
                {'AttributeName': 'rate_key', 'KeyType': 'HASH'},
                {'AttributeName': 'window', 'KeyType': 'RANGE'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'rate_key', 'AttributeType': 'S'},
                {'AttributeName': 'window', 'AttributeType': 'S'},
            ],
            BillingMode='PAY_PER_REQUEST',
        )
        print("Table 'rate_limits' creating...")

        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName='rate_limits', WaiterConfig={'Delay': 2, 'MaxAttempts': 30})
        print("Table 'rate_limits' is ACTIVE")

        # Enable TTL for automatic cleanup
        dynamodb.update_time_to_live(
            TableName='rate_limits',
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'ttl_epoch',
            },
        )
        print("TTL enabled on 'ttl_epoch' attribute")

    except dynamodb.exceptions.ResourceInUseException:
        print("Table 'rate_limits' already exists — skipping")
    except Exception as e:
        print(f"Error creating table: {e}")
        raise


if __name__ == '__main__':
    # Step 1: Create DynamoDB rate_limits table
    create_rate_limits_table()

    # Step 2: Create Bedrock Guardrail
    guardrail_id, guardrail_version = create_bedrock_guardrail()

    print(f"\n{'='*60}")
    print("SETUP COMPLETE — Add these to your Lambda environment variables:")
    print(f"  BEDROCK_GUARDRAIL_ID = {guardrail_id}")
    print(f"  BEDROCK_GUARDRAIL_VERSION = {guardrail_version}")
    print(f"  ENABLE_RATE_LIMITING = true")
    print(f"{'='*60}")
