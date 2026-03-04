"""Test child Lambdas directly after dead code removal."""
import boto3, json
from botocore.config import Config

c = boto3.client('lambda', region_name='ap-south-1', config=Config(read_timeout=30))

# Test weather Lambda directly
print('=== Weather Lambda ===')
r = c.invoke(FunctionName='smart-rural-ai-WeatherFunction-dilSoHSLlXGN',
             Payload=json.dumps({'pathParameters': {'location': 'Chennai'}, 'httpMethod': 'GET'}))
b = json.loads(r['Payload'].read())
d = json.loads(b.get('body', '{}'))
loc = d.get('data', {}).get('location', '')
temp = d.get('data', {}).get('current', {}).get('temp_celsius', '')
print(f'  Status: {b.get("statusCode")}  Location: {loc}  Temp: {temp}C')

# Test schemes Lambda directly
print('=== Schemes Lambda ===')
r = c.invoke(FunctionName='smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv',
             Payload=json.dumps({'httpMethod': 'GET', 'queryStringParameters': {'name': 'pm_kisan'}}))
b = json.loads(r['Payload'].read())
d = json.loads(b.get('body', '{}'))
schemes = d.get('data', {}).get('schemes', {})
state_schemes = d.get('data', {}).get('state_schemes', {})
print(f'  Status: {b.get("statusCode")}  Central schemes: {len(schemes) if isinstance(schemes, dict) else 1}  States: {len(state_schemes)}')

# Test crop advisory Lambda directly
print('=== Crop Advisory Lambda ===')
r = c.invoke(FunctionName='smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY',
             Payload=json.dumps({'parameters': [
                 {'name': 'query', 'value': 'rice'},
                 {'name': 'crop', 'value': 'rice'},
                 {'name': 'state', 'value': 'Tamil Nadu'}
             ]}))
b = json.loads(r['Payload'].read())
d = json.loads(b.get('body', '{}'))
results = d.get('data', {}).get('advisory_data', [])
print(f'  Status: {b.get("statusCode")}  KB results: {len(results)}')

print('\nAll child Lambdas working!')
