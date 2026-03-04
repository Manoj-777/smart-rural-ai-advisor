"""Quick smoke test: 5 chat paths through the orchestrator Lambda."""
import boto3, json
from botocore.config import Config

config = Config(read_timeout=60, connect_timeout=10, retries={'max_attempts': 0})
client = boto3.client('lambda', region_name='ap-south-1', config=config)
FN = 'smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM'

def invoke(msg):
    resp = client.invoke(
        FunctionName=FN,
        Payload=json.dumps({
            'body': json.dumps({'message': msg, 'language': 'en'}),
            'httpMethod': 'POST'
        })
    )
    body = json.loads(resp['Payload'].read())
    data = json.loads(body.get('body', '{}'))
    status = body.get('statusCode', 0)
    text = data.get('data', {}).get('response', '') or data.get('message', '')
    return status, text

tests = [
    ('Greeting',   'hello'),
    ('Weather',    'weather in Chennai'),
    ('Farming',    'How to grow rice in Tamil Nadu?'),
    ('Off-topic',  'write me python code'),
    ('Schemes',    'Tell me about PM-KISAN scheme'),
]

passed = 0
for name, query in tests:
    print(f'\n=== {name} ===')
    status, text = invoke(query)
    ok = status == 200 and len(text) > 10
    print(f'  Status: {status}  {"PASS" if ok else "FAIL"}')
    print(f'  Response: {text[:150]}...' if len(text) > 150 else f'  Response: {text}')
    if ok:
        passed += 1

print(f'\n{"="*50}')
print(f'Results: {passed}/{len(tests)} passed')
