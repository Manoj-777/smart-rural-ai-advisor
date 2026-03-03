import json
import boto3

lam = boto3.client('lambda', region_name='ap-south-1')

for loc in ['Viluppuram', 'Villupuram']:
    event = {'pathParameters': {'location': loc}}
    resp = lam.invoke(
        FunctionName='smart-rural-ai-WeatherFunction-dilSoHSLlXGN',
        InvocationType='RequestResponse',
        Payload=json.dumps(event).encode('utf-8')
    )
    raw = resp['Payload'].read().decode('utf-8')
    print('\n===', loc, '===')
    print('raw:', raw[:800])
    try:
        payload = json.loads(raw)
        print('keys:', list(payload.keys()))
    except Exception:
        pass
