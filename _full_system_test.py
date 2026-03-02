"""
COMPREHENSIVE SYSTEM TEST — Smart Rural AI Advisor
Tests ALL AWS resources — optimized for speed (avoids long Lambda invokes).
"""
import boto3, json, time, sys

REGION = 'ap-south-1'
ACCOUNT = '948809294205'
API_ID = 'zuadk9l1nc'
CF_DIST_ID = 'E2HUWT1BUYIIRG'
CF_DOMAIN = 'd80ytlzsrax1n.cloudfront.net'
SM_ARN = f'arn:aws:states:{REGION}:{ACCOUNT}:stateMachine:smart-rural-ai-cognitive-pipeline'

lam = boto3.client('lambda', region_name=REGION)
ddb = boto3.client('dynamodb', region_name=REGION)
cw = boto3.client('cloudwatch', region_name=REGION)
events = boto3.client('events', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)
cog = boto3.client('cognito-idp', region_name=REGION)
sfn = boto3.client('stepfunctions', region_name=REGION)
cf = boto3.client('cloudfront')
s3 = boto3.client('s3', region_name=REGION)
apigw = boto3.client('apigateway', region_name=REGION)

passed = []
failed = []
warnings = []

def test(name, fn):
    try:
        r = fn()
        if r == 'WARN':
            warnings.append(name)
            print(f'  WARN  {name}')
        else:
            passed.append(name)
            print(f'  PASS  {name}')
    except Exception as e:
        failed.append((name, str(e)[:200]))
        print(f'  FAIL  {name}: {e}')


print('=' * 70)
print('  COMPREHENSIVE SYSTEM TEST')
print('=' * 70)

# ═══ 1. ALL 13 LAMBDA FUNCTIONS ═══
print('\n[1/9] Lambda Functions (13)')
ALL_FNS = [
    'smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM',
    'smart-rural-ai-WeatherFunction-dilSoHSLlXGN',
    'smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY',
    'smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv',
    'smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt',
    'smart-rural-ai-ImageAnalysisFunction-wY2rBz7uHgKV',
    'smart-rural-ai-TranscribeSpeechFunction-rF4EDECy1VaO',
    'smart-rural-ai-HealthCheckFunction-FQB8TfJ91HKs',
    'smart-rural-ai-DailyWeatherAlert',
    'smart-rural-ai-SFN-UnderstandingAgent',
    'smart-rural-ai-SFN-ReasoningAgent',
    'smart-rural-ai-SFN-FactCheckAgent',
    'smart-rural-ai-SFN-CommunicationAgent',
]
for fn in ALL_FNS:
    short = fn.replace('smart-rural-ai-', '')
    def ck(f=fn):
        r = lam.get_function(FunctionName=f)
        c = r['Configuration']
        if c.get('State') != 'Active':
            raise Exception(f'State={c.get("State")}, LastUpdate={c.get("LastUpdateStatus")}')
    test(f'Lambda: {short}', ck)

# Quick invocations (fast Lambdas only)
print('\n  --- Quick Lambda Invocations ---')

def ck_health():
    r = lam.invoke(FunctionName='smart-rural-ai-HealthCheckFunction-FQB8TfJ91HKs', Payload=b'{}')
    p = json.loads(r['Payload'].read())
    if p.get('statusCode') != 200: raise Exception(f'Status {p.get("statusCode")}')
test('Invoke: HealthCheck', ck_health)

def ck_crop():
    r = lam.invoke(FunctionName='smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY',
                   Payload=json.dumps({'queryStringParameters':{'crop':'rice','state':'Tamil Nadu'}}).encode())
    p = json.loads(r['Payload'].read())
    b = json.loads(p['body'])
    if 'data' not in b: raise Exception(f'No data: {list(b.keys())}')
test('Invoke: CropAdvisory (rice)', ck_crop)

def ck_schemes():
    r = lam.invoke(FunctionName='smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv',
                   Payload=json.dumps({'queryStringParameters':{'query':'irrigation','state':'Tamil Nadu'}}).encode())
    p = json.loads(r['Payload'].read())
    b = json.loads(p['body'])
    if 'data' not in b: raise Exception(f'No data: {list(b.keys())}')
test('Invoke: GovtSchemes (irrigation)', ck_schemes)

def ck_weather():
    r = lam.invoke(FunctionName='smart-rural-ai-WeatherFunction-dilSoHSLlXGN',
                   Payload=json.dumps({'queryStringParameters':{'location':'Chennai'}}).encode())
    p = json.loads(r['Payload'].read())
    b = json.loads(p['body'])
    if 'data' not in b: raise Exception(f'No data: {list(b.keys())}')
    temp = b['data'].get('current',{}).get('temperature')
    print(f'         Chennai: {temp}C', end='')
test('Invoke: Weather (Chennai)', ck_weather)

# ═══ 2. API GATEWAY ═══
print('\n[2/9] API Gateway')

def ck_api_routes():
    res = apigw.get_resources(restApiId=API_ID)
    paths = sorted([r['path'] for r in res['items']])
    expected = ['/chat', '/health', '/schemes', '/weather', '/voice', '/transcribe', '/image-analyze']
    missing = [p for p in expected if p not in paths]
    if missing: raise Exception(f'Missing routes: {missing}')
    print(f'         Routes: {len(paths)} ({", ".join(paths[:8])}...)', end='')
test('API GW: All routes exist', ck_api_routes)

def ck_api_stage():
    stage = apigw.get_stage(restApiId=API_ID, stageName='Prod')
    print(f'         Stage: Prod, Deployed: {str(stage.get("lastUpdatedDate","?"))[:19]}', end='')
test('API GW: Prod stage', ck_api_stage)

# Quick HTTP tests
try:
    import requests
    requests.packages.urllib3.disable_warnings()
    API_URL = f'https://{API_ID}.execute-api.{REGION}.amazonaws.com/Prod'

    def ck_http_health():
        r = requests.get(f'{API_URL}/health', timeout=10)
        if r.status_code != 200: raise Exception(f'HTTP {r.status_code}')
    test('HTTP: GET /health', ck_http_health)

    def ck_http_weather():
        r = requests.get(f'{API_URL}/weather/Chennai', timeout=15)
        if r.status_code != 200: raise Exception(f'HTTP {r.status_code}: {r.text[:80]}')
    test('HTTP: GET /weather/Chennai', ck_http_weather)

    def ck_http_schemes():
        r = requests.get(f'{API_URL}/schemes?query=irrigation', timeout=15)
        if r.status_code != 200: raise Exception(f'HTTP {r.status_code}')
    test('HTTP: GET /schemes', ck_http_schemes)

    def ck_cors():
        r = requests.options(f'{API_URL}/chat', timeout=10)
        h = r.headers.get('Access-Control-Allow-Origin', '')
        if not h: raise Exception('No CORS headers')
        print(f'         Origin: {h}', end='')
    test('HTTP: CORS /chat', ck_cors)

    def ck_http_frontend():
        r = requests.get(f'https://{CF_DOMAIN}/', timeout=15)
        if r.status_code != 200: raise Exception(f'HTTP {r.status_code}')
        if '<div id="root">' not in r.text: raise Exception('No React root')
        print(f'         Size: {len(r.text)} bytes', end='')
    test('HTTP: CloudFront frontend', ck_http_frontend)

except ImportError:
    print('  SKIP  HTTP tests (requests not installed)')

# ═══ 3. DYNAMODB ═══
print('\n[3/9] DynamoDB Tables')
for t in ['farmer_profiles', 'chat_sessions', 'otp_codes', 'rate_limits']:
    def ck_ddb(t=t):
        r = ddb.describe_table(TableName=t)
        if r['Table']['TableStatus'] != 'ACTIVE': raise Exception(r['Table']['TableStatus'])
        print(f'         Items: {r["Table"]["ItemCount"]}', end='')
    test(f'DynamoDB: {t}', ck_ddb)

# ═══ 4. CLOUDWATCH DASHBOARD ═══
print('\n[4/9] CloudWatch Dashboard')
def ck_cw():
    r = cw.get_dashboard(DashboardName='SmartRuralAI-Operations')
    body = json.loads(r['DashboardBody'])
    n = len(body['widgets'])
    if n < 10: raise Exception(f'Only {n} widgets')
    print(f'         Widgets: {n}', end='')
test('CloudWatch: Dashboard', ck_cw)

# ═══ 5. EVENTBRIDGE + SNS ═══
print('\n[5/9] EventBridge + SNS')
def ck_eb():
    r = events.describe_rule(Name='smart-rural-ai-DailyWeatherRule')
    if r['State'] != 'ENABLED': raise Exception(f'State: {r["State"]}')
    print(f'         Schedule: {r["ScheduleExpression"]}', end='')
test('EventBridge: Rule ENABLED', ck_eb)

def ck_eb_targets():
    r = events.list_targets_by_rule(Rule='smart-rural-ai-DailyWeatherRule')
    if len(r['Targets']) == 0: raise Exception('No targets')
test('EventBridge: Has targets', ck_eb_targets)

def ck_sns():
    arn = f'arn:aws:sns:{REGION}:{ACCOUNT}:smart-rural-ai-weather-alerts'
    r = sns.get_topic_attributes(TopicArn=arn)
    print(f'         Subs: {r["Attributes"].get("SubscriptionsConfirmed","0")}', end='')
test('SNS: Topic exists', ck_sns)

def ck_eb_lambda():
    r = lam.get_function(FunctionName='smart-rural-ai-DailyWeatherAlert')
    c = r['Configuration']
    if c['State'] != 'Active': raise Exception(f'State: {c["State"]}')
    print(f'         Runtime: {c["Runtime"]}, Timeout: {c["Timeout"]}s', end='')
test('EventBridge Lambda: Active', ck_eb_lambda)

# ═══ 6. COGNITO ═══
print('\n[6/9] Cognito')
pool_id = None
def ck_pool():
    global pool_id
    pools = cog.list_user_pools(MaxResults=10)
    p = next((x for x in pools['UserPools'] if 'smart-rural' in x['Name']), None)
    if not p: raise Exception('Pool not found')
    pool_id = p['Id']
    desc = cog.describe_user_pool(UserPoolId=pool_id)['UserPool']
    print(f'         ID: {pool_id}, Protection: {desc.get("DeletionProtection")}', end='')
test('Cognito: User Pool', ck_pool)

def ck_client():
    if not pool_id: raise Exception('No pool')
    cs = cog.list_user_pool_clients(UserPoolId=pool_id, MaxResults=5)
    if not cs['UserPoolClients']: raise Exception('No clients')
    c = cs['UserPoolClients'][0]
    cd = cog.describe_user_pool_client(UserPoolId=pool_id, ClientId=c['ClientId'])['UserPoolClient']
    print(f'         Client: {c["ClientId"]}, Flows: {len(cd.get("ExplicitAuthFlows",[]))}', end='')
test('Cognito: App Client', ck_client)

def ck_domain():
    r = cog.describe_user_pool_domain(Domain='smart-rural-ai-auth')
    s = r.get('DomainDescription',{}).get('Status','NOT_FOUND')
    if s not in ('ACTIVE','CREATING'): raise Exception(f'Status: {s}')
    print(f'         Status: {s}', end='')
test('Cognito: Domain', ck_domain)

def ck_auth():
    auths = apigw.get_authorizers(restApiId=API_ID)
    a = [x for x in auths['items'] if 'cognito' in x.get('name','').lower()]
    if not a: raise Exception('No authorizer')
    print(f'         ID: {a[0]["id"]}', end='')
test('Cognito: API GW Authorizer', ck_auth)

# ═══ 7. STEP FUNCTIONS ═══
print('\n[7/9] Step Functions')
def ck_sm():
    d = sfn.describe_state_machine(stateMachineArn=SM_ARN)
    if d['status'] != 'ACTIVE': raise Exception(d['status'])
    print(f'         Type: {d["type"]}, XRay: {d.get("tracingConfiguration",{}).get("enabled")}', end='')
test('SFN: State Machine ACTIVE', ck_sm)

def ck_sm_def():
    d = sfn.describe_state_machine(stateMachineArn=SM_ARN)
    defn = json.loads(d['definition'])
    states = list(defn['States'].keys())
    need = ['UnderstandingAgent','ReasoningAgent','FactCheckAgent','CommunicationAgent','FallbackResponse']
    missing = [s for s in need if s not in states]
    if missing: raise Exception(f'Missing: {missing}')
    print(f'         States: {", ".join(states)}', end='')
test('SFN: All 5 states', ck_sm_def)

def ck_sfn_exec():
    execs = sfn.list_executions(stateMachineArn=SM_ARN, maxResults=5)
    if not execs['executions']: raise Exception('No executions')
    for e in execs['executions']:
        if e['status'] == 'SUCCEEDED':
            desc = sfn.describe_execution(executionArn=e['executionArn'])
            out = json.loads(desc.get('output','{}'))
            trace = out.get('agent_trace',[])
            if len(trace) >= 4 and 'error-fallback' not in trace:
                print(f'         Last success: {e["name"]}, trace={trace}', end='')
                return
    # Check any succeeded
    succeeded = [e for e in execs['executions'] if e['status']=='SUCCEEDED']
    if succeeded:
        print(f'         {len(succeeded)} runs completed (some via fallback)', end='')
        return 'WARN'
    raise Exception('No successful executions')
test('SFN: Past execution OK', ck_sfn_exec)

# ═══ 8. CLOUDFRONT ═══
print('\n[8/9] CloudFront')
def ck_cf():
    d = cf.get_distribution(Id=CF_DIST_ID)
    dist = d['Distribution']
    if not dist['DistributionConfig']['Enabled']: raise Exception('Disabled')
    print(f'         Status: {dist["Status"]}, Domain: {CF_DOMAIN}', end='')
test('CloudFront: Distribution', ck_cf)

def ck_cf_inv():
    inv = cf.list_invalidations(DistributionId=CF_DIST_ID, MaxItems='3')
    items = inv.get('InvalidationList',{}).get('Items',[])
    if items:
        latest = items[0]
        print(f'         Latest: {latest["Id"]} ({latest["Status"]})', end='')
    else:
        print('         No invalidations', end='')
test('CloudFront: Invalidation', ck_cf_inv)

# ═══ 9. S3 ═══
print('\n[9/9] S3 Buckets')
def ck_s3_data():
    r = s3.list_objects_v2(Bucket=f'smart-rural-ai-{ACCOUNT}', MaxKeys=5)
    if r.get('KeyCount',0)==0: raise Exception('Empty')
    print(f'         Objects: {r["KeyCount"]}+', end='')
test('S3: Data bucket', ck_s3_data)

def ck_s3_fe():
    r = s3.list_objects_v2(Bucket=f'smart-rural-ai-frontend-{ACCOUNT}', MaxKeys=20)
    if r.get('KeyCount',0)==0: raise Exception('Empty')
    s3.head_object(Bucket=f'smart-rural-ai-frontend-{ACCOUNT}', Key='index.html')
    print(f'         Objects: {r["KeyCount"]}, index.html: present', end='')
test('S3: Frontend bucket', ck_s3_fe)

# ═══ BEDROCK ═══
print('\n[BONUS] Bedrock')
def ck_bedrock():
    br = boto3.client('bedrock-runtime', region_name=REGION)
    r = br.converse(
        modelId='apac.amazon.nova-pro-v1:0',
        messages=[{'role':'user','content':[{'text':'Say hello in 5 words.'}]}],
        inferenceConfig={'maxTokens':50,'temperature':0.1},
    )
    text = r['output']['message']['content'][0]['text']
    print(f'         Model: apac.nova-pro, Response: "{text[:60]}"', end='')
test('Bedrock: converse() works', ck_bedrock)

# ═══════════════════════════════════════════════════════════════
#  SUMMARY
# ═══════════════════════════════════════════════════════════════
total = len(passed) + len(failed) + len(warnings)
print(f'\n{"=" * 70}')
print(f'  RESULTS: {len(passed)} passed, {len(failed)} failed, {len(warnings)} warnings  (total: {total})')
print(f'{"=" * 70}')

if failed:
    print(f'\n  FAILED ({len(failed)}):')
    for n, e in failed:
        print(f'    X {n}: {e}')

if warnings:
    print(f'\n  WARNINGS ({len(warnings)}):')
    for w in warnings:
        print(f'    ~ {w}')

if not failed:
    print('\n  ALL SYSTEMS OPERATIONAL')

sys.exit(1 if failed else 0)
