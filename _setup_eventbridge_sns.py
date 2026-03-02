"""
EventBridge + SNS — Daily Weather Alert System
Creates:
  • SNS Topic for weather alerts (email/SMS delivery)
  • Lambda function that fetches weather for all registered farmers
  • EventBridge rule to trigger daily at 6 AM IST (00:30 UTC)
  • IAM role with least-privilege permissions

Fully standalone — does NOT modify existing infrastructure.
Idempotent — safe to run multiple times.
"""

import boto3
import json
import zipfile
import io
import time
import os

REGION = 'ap-south-1'
ACCOUNT = '948809294205'
PROJECT = 'smart-rural-ai'

# Resource names
SNS_TOPIC_NAME = f'{PROJECT}-weather-alerts'
LAMBDA_NAME = f'{PROJECT}-DailyWeatherAlert'
RULE_NAME = f'{PROJECT}-DailyWeatherRule'
ROLE_NAME = f'{PROJECT}-DailyWeatherAlertRole'

# Existing resources this reads from
DYNAMODB_PROFILES_TABLE = 'farmer_profiles'
S3_BUCKET = f'smart-rural-ai-{ACCOUNT}'

# ── Clients ──
iam = boto3.client('iam')
sns = boto3.client('sns', region_name=REGION)
lam = boto3.client('lambda', region_name=REGION)
events = boto3.client('events', region_name=REGION)
sts = boto3.client('sts')


# ══════════════════════════════════════════════════════════════
#  Step 1: SNS Topic
# ══════════════════════════════════════════════════════════════
def create_sns_topic():
    print('\n[1/5] Creating SNS Topic...')
    resp = sns.create_topic(
        Name=SNS_TOPIC_NAME,
        Tags=[
            {'Key': 'Project', 'Value': PROJECT},
            {'Key': 'Purpose', 'Value': 'Daily weather alerts for farmers'},
        ]
    )
    topic_arn = resp['TopicArn']
    print(f'  Topic ARN: {topic_arn}')
    return topic_arn


# ══════════════════════════════════════════════════════════════
#  Step 2: IAM Role for the Lambda
# ══════════════════════════════════════════════════════════════
def create_iam_role(topic_arn):
    print('\n[2/5] Creating IAM Role...')

    trust_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'Service': 'lambda.amazonaws.com'},
            'Action': 'sts:AssumeRole',
        }]
    }

    # Least-privilege inline policy
    inline_policy = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'CloudWatchLogs',
                'Effect': 'Allow',
                'Action': [
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents',
                ],
                'Resource': f'arn:aws:logs:{REGION}:{ACCOUNT}:log-group:/aws/lambda/{LAMBDA_NAME}:*',
            },
            {
                'Sid': 'DynamoDBReadProfiles',
                'Effect': 'Allow',
                'Action': [
                    'dynamodb:Scan',
                    'dynamodb:GetItem',
                ],
                'Resource': f'arn:aws:dynamodb:{REGION}:{ACCOUNT}:table/{DYNAMODB_PROFILES_TABLE}',
            },
            {
                'Sid': 'SNSPublish',
                'Effect': 'Allow',
                'Action': 'sns:Publish',
                'Resource': topic_arn,
            },
        ]
    }

    try:
        resp = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Smart Rural AI daily weather alert Lambda',
            Tags=[{'Key': 'Project', 'Value': PROJECT}],
        )
        role_arn = resp['Role']['Arn']
        print(f'  Created role: {ROLE_NAME}')
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f'arn:aws:iam::{ACCOUNT}:role/{ROLE_NAME}'
        # Update trust policy in case it changed
        iam.update_assume_role_policy(
            RoleName=ROLE_NAME,
            PolicyDocument=json.dumps(trust_policy),
        )
        print(f'  Role exists, updated: {ROLE_NAME}')

    # Put inline policy (always overwrite for idempotency)
    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName='DailyWeatherAlertPolicy',
        PolicyDocument=json.dumps(inline_policy),
    )
    print(f'  Role ARN: {role_arn}')

    # Wait for IAM propagation
    print('  Waiting for IAM propagation (10s)...')
    time.sleep(10)
    return role_arn


# ══════════════════════════════════════════════════════════════
#  Step 3: Lambda Function
# ══════════════════════════════════════════════════════════════
LAMBDA_CODE = '''\
"""
Daily Weather Alert Lambda
Triggered by EventBridge at 6 AM IST daily.
- Scans farmer_profiles for registered farmers
- Fetches weather for each unique location via OpenWeatherMap
- Publishes alert summary to SNS topic
"""
import json
import boto3
import os
import logging
import urllib.request
import urllib.parse
from collections import defaultdict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

PROFILES_TABLE = os.environ.get('DYNAMODB_PROFILES_TABLE', 'farmer_profiles')
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')


def get_weather(location, state=''):
    """Fetch weather from OpenWeatherMap."""
    if not OPENWEATHER_API_KEY:
        return None
    query = f"{location},{state},IN" if state else f"{location},IN"
    url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"q={urllib.parse.quote(query)}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning(f"Weather fetch failed for {query}: {e}")
        return None


def lambda_handler(event, context):
    logger.info(f"Daily Weather Alert triggered: {json.dumps(event)[:200]}")

    # Scan all farmer profiles
    table = dynamodb.Table(PROFILES_TABLE)
    farmers = []
    scan_kwargs = {'ProjectionExpression': 'farmer_id, #n, district, #s, crops',
                   'ExpressionAttributeNames': {'#n': 'name', '#s': 'state'}}
    while True:
        resp = table.scan(**scan_kwargs)
        farmers.extend(resp.get('Items', []))
        if 'LastEvaluatedKey' not in resp:
            break
        scan_kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

    if not farmers:
        logger.info("No farmers registered. Skipping alerts.")
        return {'statusCode': 200, 'body': 'No farmers to alert'}

    logger.info(f"Found {len(farmers)} registered farmers")

    # Group farmers by location to minimize API calls
    location_groups = defaultdict(list)
    for f in farmers:
        loc = f.get('district') or f.get('state') or 'India'
        state = f.get('state', '')
        location_groups[(loc, state)].append(f)

    # Fetch weather for each unique location
    alerts = []
    for (loc, state), group in location_groups.items():
        weather = get_weather(loc, state)
        if not weather:
            continue

        main = weather.get('main', {})
        w = weather.get('weather', [{}])[0]
        temp = main.get('temp', 'N/A')
        humidity = main.get('humidity', 'N/A')
        description = w.get('description', 'N/A')
        rain_1h = weather.get('rain', {}).get('1h', 0)

        farmer_names = [f.get('name', f.get('farmer_id', 'Farmer')) for f in group]

        alert_line = (
            f"📍 {loc}, {state}\\n"
            f"   🌡️ Temp: {temp}°C | 💧 Humidity: {humidity}%\\n"
            f"   ☁️ {description.title()}"
        )
        if rain_1h > 0:
            alert_line += f" | 🌧️ Rain: {rain_1h}mm/hr"

        # Add farming-specific warnings
        if isinstance(temp, (int, float)):
            if temp > 40:
                alert_line += "\\n   ⚠️ HEAT WARNING: Irrigate crops, provide shade for livestock"
            elif temp < 10:
                alert_line += "\\n   ⚠️ COLD WARNING: Protect seedlings, cover nursery beds"
        if isinstance(humidity, (int, float)) and humidity > 85:
            alert_line += "\\n   ⚠️ HIGH HUMIDITY: Watch for fungal diseases"
        if rain_1h > 20:
            alert_line += "\\n   ⚠️ HEAVY RAIN: Ensure field drainage, delay spraying"

        alert_line += f"\\n   👨‍🌾 Farmers: {', '.join(farmer_names)}"
        alerts.append(alert_line)

    if not alerts:
        logger.info("No weather data available. Skipping alerts.")
        return {'statusCode': 200, 'body': 'No weather data'}

    # Build and publish SNS message
    message = (
        "🌾 Smart Rural AI Advisor — Daily Weather Alert\\n"
        f"📅 Date: {context.function_name}\\n"
        "=" * 50 + "\\n\\n"
        + "\\n\\n".join(alerts)
        + "\\n\\n---\\n"
        "💡 Open the Smart Rural AI Advisor app for personalized crop advice."
    )

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject='🌾 Daily Weather Alert — Smart Rural AI Advisor',
        Message=message,
    )

    logger.info(f"Published alert with {len(alerts)} location(s), {len(farmers)} farmer(s)")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'locations': len(alerts),
            'farmers': len(farmers),
            'message': 'Alerts published to SNS',
        })
    }
'''


def create_lambda(role_arn, topic_arn, openweather_key):
    print('\n[3/5] Creating Lambda Function...')

    # Package code into zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('handler.py', LAMBDA_CODE)
    buf.seek(0)

    env_vars = {
        'DYNAMODB_PROFILES_TABLE': DYNAMODB_PROFILES_TABLE,
        'SNS_TOPIC_ARN': topic_arn,
        'OPENWEATHER_API_KEY': openweather_key,
    }

    try:
        lam.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime='python3.13',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': buf.read()},
            Description='Daily weather alerts for registered farmers',
            Timeout=120,
            MemorySize=256,
            Environment={'Variables': env_vars},
            Tags={'Project': PROJECT},
        )
        print(f'  Created: {LAMBDA_NAME}')
    except lam.exceptions.ResourceConflictException:
        buf.seek(0)
        lam.update_function_code(
            FunctionName=LAMBDA_NAME,
            ZipFile=buf.read(),
        )
        # Wait for update to complete
        time.sleep(3)
        lam.update_function_configuration(
            FunctionName=LAMBDA_NAME,
            Runtime='python3.13',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Description='Daily weather alerts for registered farmers',
            Timeout=120,
            MemorySize=256,
            Environment={'Variables': env_vars},
        )
        print(f'  Updated existing: {LAMBDA_NAME}')

    func_arn = f'arn:aws:lambda:{REGION}:{ACCOUNT}:function:{LAMBDA_NAME}'
    print(f'  ARN: {func_arn}')
    return func_arn


# ══════════════════════════════════════════════════════════════
#  Step 4: EventBridge Rule (daily at 6 AM IST = 00:30 UTC)
# ══════════════════════════════════════════════════════════════
def create_eventbridge_rule(lambda_arn):
    print('\n[4/5] Creating EventBridge Rule...')

    # 6:00 AM IST = 00:30 UTC
    resp = events.put_rule(
        Name=RULE_NAME,
        ScheduleExpression='cron(30 0 * * ? *)',
        State='ENABLED',
        Description='Daily 6 AM IST trigger for weather alerts to farmers',
        Tags=[{'Key': 'Project', 'Value': PROJECT}],
    )
    rule_arn = resp['RuleArn']
    print(f'  Rule: {RULE_NAME} (daily 6:00 AM IST / 00:30 UTC)')

    # Add Lambda as target
    events.put_targets(
        Rule=RULE_NAME,
        Targets=[{
            'Id': 'DailyWeatherAlertLambda',
            'Arn': lambda_arn,
            'Input': json.dumps({'source': 'eventbridge', 'type': 'daily-weather-alert'}),
        }]
    )
    print(f'  Target: {LAMBDA_NAME}')

    # Grant EventBridge permission to invoke Lambda
    try:
        lam.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId='EventBridgeDailyInvoke',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=rule_arn,
        )
        print('  Permission: EventBridge → Lambda ✓')
    except lam.exceptions.ResourceConflictException:
        print('  Permission already exists ✓')

    return rule_arn


# ══════════════════════════════════════════════════════════════
#  Step 5: Verify
# ══════════════════════════════════════════════════════════════
def verify(topic_arn, lambda_arn, rule_arn):
    print('\n[5/5] Verification...')

    # Check SNS topic
    attrs = sns.get_topic_attributes(TopicArn=topic_arn)
    print(f'  ✅ SNS Topic: {topic_arn}')

    # Check Lambda
    func = lam.get_function(FunctionName=LAMBDA_NAME)
    state = func['Configuration']['State']
    print(f'  ✅ Lambda: {LAMBDA_NAME} (state={state})')

    # Check EventBridge
    rule = events.describe_rule(Name=RULE_NAME)
    print(f'  ✅ EventBridge: {RULE_NAME} (state={rule["State"]})')
    print(f'     Schedule: {rule["ScheduleExpression"]}')

    # Check subscriptions
    subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
    sub_count = len(subs.get('Subscriptions', []))
    print(f'  📧 SNS Subscriptions: {sub_count}')
    if sub_count == 0:
        print(f'\n  ⚠️  No subscribers yet! To add an email subscriber:')
        print(f'     aws sns subscribe --topic-arn {topic_arn} \\')
        print(f'       --protocol email --notification-endpoint YOUR_EMAIL')


def main():
    print('=' * 60)
    print('  EventBridge + SNS — Daily Weather Alert System')
    print('=' * 60)

    # Get the OpenWeather API key from the existing orchestrator Lambda
    print('\nFetching OpenWeather API key from existing Lambda...')
    try:
        config = lam.get_function_configuration(
            FunctionName='smart-rural-ai-WeatherFunction-dilSoHSLlXGN'
        )
        openweather_key = config['Environment']['Variables'].get('OPENWEATHER_API_KEY', '')
        if openweather_key:
            print(f'  Found API key: {openweather_key[:6]}...')
        else:
            print('  ⚠️  No OpenWeather API key found — alerts will skip weather data')
    except Exception as e:
        print(f'  ⚠️  Could not read API key: {e}')
        openweather_key = ''

    topic_arn = create_sns_topic()
    role_arn = create_iam_role(topic_arn)
    lambda_arn = create_lambda(role_arn, topic_arn, openweather_key)
    rule_arn = create_eventbridge_rule(lambda_arn)
    verify(topic_arn, lambda_arn, rule_arn)

    print(f'\n{"=" * 60}')
    print(f'  ✅ ALL DONE — Weather Alerts Active')
    print(f'  SNS Topic: {topic_arn}')
    print(f'  Schedule:  Daily 6:00 AM IST')
    print(f'{"=" * 60}\n')


if __name__ == '__main__':
    main()
