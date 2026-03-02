"""
AWS Step Functions — Cognitive Pipeline State Machine
Creates a Step Functions state machine that mirrors the 4-agent
cognitive pipeline (Understanding → Reasoning → Fact-Check → Communication)
as a visual, observable workflow.

Architecture:
  EventBridge/API → Step Functions → 4× Lambda (one per agent)
  Each step is a separate Lambda that calls Bedrock converse().

Creates:
  • 4 agent Lambda functions (understanding, reasoning, factcheck, communication)
  • IAM execution role for the state machine
  • Step Functions state machine with error handling & retries
  • Optional /chat-v2 API Gateway route (parallel to existing /chat)

Fully standalone — does NOT modify existing orchestrator Lambda.
Idempotent — safe to run multiple times.
"""

import boto3
import json
import zipfile
import io
import time

REGION = 'ap-south-1'
ACCOUNT = '948809294205'
PROJECT = 'smart-rural-ai'

# State machine name
STATE_MACHINE_NAME = f'{PROJECT}-cognitive-pipeline'
SFN_ROLE_NAME = f'{PROJECT}-StepFunctionsRole'

# Agent Lambda names
AGENT_LAMBDAS = {
    'understanding': f'{PROJECT}-SFN-UnderstandingAgent',
    'reasoning':     f'{PROJECT}-SFN-ReasoningAgent',
    'factcheck':     f'{PROJECT}-SFN-FactCheckAgent',
    'communication': f'{PROJECT}-SFN-CommunicationAgent',
}
AGENT_ROLE_NAME = f'{PROJECT}-SFN-AgentLambdaRole'

# Existing resources
FOUNDATION_MODEL = 'apac.amazon.nova-pro-v1:0'
S3_BUCKET = f'smart-rural-ai-{ACCOUNT}'

# Clients
iam = boto3.client('iam')
lam = boto3.client('lambda', region_name=REGION)
sfn = boto3.client('stepfunctions', region_name=REGION)


# ══════════════════════════════════════════════════════════════
#  AGENT LAMBDA CODE  (one Lambda per cognitive agent)
# ══════════════════════════════════════════════════════════════

UNDERSTANDING_CODE = '''\
"""Step Functions Agent 1: Understanding Agent"""
import json, boto3, os, logging, re
logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
MODEL = os.environ.get("FOUNDATION_MODEL", "apac.amazon.nova-pro-v1:0")

SYSTEM_PROMPT = """You are the Understanding Agent. Analyze the farmer query and output STRICT JSON:
{
  "intents": ["weather","crop","pest","schemes","profile","irrigation","general"],
  "entities": {"location":null,"crop":null,"season":null,"state":null,"pest_symptom":null},
  "tools_needed": ["get_weather","get_crop_advisory","get_pest_alert","search_schemes","get_farmer_profile"],
  "urgency": "high/medium/low",
  "summary": "one-line summary"
}
Use farmer context to fill null entities. Output ONLY valid JSON."""

def lambda_handler(event, context):
    query = event.get("query", "")
    farmer_context = event.get("farmer_context", {})
    prompt = f"Farmer query: {query}"
    if farmer_context:
        prompt += f"\\nFarmer context: {json.dumps(farmer_context)}"

    resp = bedrock.converse(
        modelId=MODEL,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        system=[{"text": SYSTEM_PROMPT}],
        inferenceConfig={"maxTokens": 512, "temperature": 0.1},
    )
    text = resp["output"]["message"]["content"][0]["text"]
    # Parse JSON
    cleaned = re.sub(r"^```(?:json)?\\s*", "", text.strip())
    cleaned = re.sub(r"\\s*```$", "", cleaned.strip())
    try:
        analysis = json.loads(cleaned)
    except json.JSONDecodeError:
        analysis = {"intents": ["general"], "entities": {}, "tools_needed": [], "urgency": "medium", "summary": query}

    return {**event, "understanding": analysis, "agent_trace": ["understanding"]}
'''

REASONING_CODE = '''\
"""Step Functions Agent 2: Reasoning Agent (tool calling)"""
import json, boto3, os, logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
lam_client = boto3.client("lambda", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
MODEL = os.environ.get("FOUNDATION_MODEL", "apac.amazon.nova-pro-v1:0")

SYSTEM_PROMPT = """You are the Reasoning Agent for Indian farmers. Use the provided tool results
to synthesize a comprehensive advisory. Ground ALL claims in tool data.
Include specific numbers (temperatures, kg/hectare, dates).
If data is missing, say so. Do NOT hallucinate."""

TOOL_LAMBDA_MAP = {
    "get_weather": os.environ.get("WEATHER_LAMBDA", "smart-rural-ai-WeatherFunction-dilSoHSLlXGN"),
    "get_crop_advisory": os.environ.get("CROP_LAMBDA", "smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY"),
    "search_schemes": os.environ.get("SCHEMES_LAMBDA", "smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv"),
    "get_farmer_profile": os.environ.get("PROFILE_LAMBDA", "smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt"),
}

def invoke_tool(tool_name, params):
    fn = TOOL_LAMBDA_MAP.get(tool_name)
    if not fn:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        resp = lam_client.invoke(FunctionName=fn, Payload=json.dumps({"queryStringParameters": params}).encode())
        payload = json.loads(resp["Payload"].read())
        body = json.loads(payload.get("body", "{}"))
        return body.get("data", body)
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return {"error": str(e)}

def lambda_handler(event, context):
    query = event.get("query", "")
    understanding = event.get("understanding", {})
    farmer_ctx = event.get("farmer_context", {})
    tools_needed = understanding.get("tools_needed", [])
    entities = understanding.get("entities", {})

    # Call tools
    tool_results = {}
    for tool in tools_needed:
        params = {}
        if tool == "get_weather":
            params["location"] = entities.get("location") or farmer_ctx.get("district") or farmer_ctx.get("state", "")
        elif tool == "get_crop_advisory":
            params["crop"] = entities.get("crop") or ""
            params["state"] = entities.get("state") or farmer_ctx.get("state", "")
        elif tool == "search_schemes":
            params["query"] = query
            params["state"] = entities.get("state") or farmer_ctx.get("state", "")
        elif tool == "get_farmer_profile":
            params["farmer_id"] = farmer_ctx.get("farmer_id", "")
        tool_results[tool] = invoke_tool(tool, params)

    # Synthesize with Bedrock
    prompt = f"Farmer query: {query}\\nTool results: {json.dumps(tool_results, default=str)[:3000]}"
    if farmer_ctx:
        prompt += f"\\nFarmer context: {json.dumps(farmer_ctx)}"

    resp = bedrock.converse(
        modelId=MODEL,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        system=[{"text": SYSTEM_PROMPT}],
        inferenceConfig={"maxTokens": 1500, "temperature": 0.3},
    )
    advisory = resp["output"]["message"]["content"][0]["text"]
    trace = event.get("agent_trace", []) + ["reasoning"]
    return {**event, "draft_advisory": advisory, "tool_results": tool_results, "tools_used": list(tool_results.keys()), "agent_trace": trace}
'''

FACTCHECK_CODE = '''\
"""Step Functions Agent 3: Fact-Check Agent"""
import json, boto3, os, logging, re
logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
MODEL = os.environ.get("FOUNDATION_MODEL", "apac.amazon.nova-pro-v1:0")

SYSTEM_PROMPT = """You are the Fact-Checking Agent. Validate the advisory against tool data.
Output STRICT JSON:
{"validated":true/false,"corrected_advisory":"...","confidence":0.0-1.0,"corrections":[],"warnings":[],"hallucinations_found":[]}
Check numbers, scheme names, and crop advice. Be strict."""

def lambda_handler(event, context):
    draft = event.get("draft_advisory", "")
    tool_results = event.get("tool_results", {})
    prompt = f"Advisory to check:\\n{draft}\\n\\nTool data:\\n{json.dumps(tool_results, default=str)[:3000]}"

    resp = bedrock.converse(
        modelId=MODEL,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        system=[{"text": SYSTEM_PROMPT}],
        inferenceConfig={"maxTokens": 1500, "temperature": 0.1},
    )
    text = resp["output"]["message"]["content"][0]["text"]
    cleaned = re.sub(r"^```(?:json)?\\s*", "", text.strip())
    cleaned = re.sub(r"\\s*```$", "", cleaned.strip())
    try:
        result = json.loads(cleaned)
        fact_checked = result.get("corrected_advisory", draft)
        confidence = result.get("confidence", 0.5)
    except json.JSONDecodeError:
        fact_checked = draft
        confidence = 0.5
        result = {}

    trace = event.get("agent_trace", []) + ["factcheck"]
    return {**event, "fact_checked_advisory": fact_checked, "fact_check_meta": result, "confidence": confidence, "agent_trace": trace}
'''

COMMUNICATION_CODE = '''\
"""Step Functions Agent 4: Communication Agent"""
import json, boto3, os, logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
MODEL = os.environ.get("FOUNDATION_MODEL", "apac.amazon.nova-pro-v1:0")

SYSTEM_PROMPT = """You are the Communication Agent. Rewrite the advisory in a warm,
conversational tone for an Indian farmer. Use simple words, short sentences.
Sound like a helpful neighbor, not a textbook. Keep ALL factual data exact.
Under 200 words for simple queries, up to 300 for complex. Write in English only.
Do NOT add information not in the original advisory."""

def lambda_handler(event, context):
    advisory = event.get("fact_checked_advisory", event.get("draft_advisory", ""))
    farmer_ctx = event.get("farmer_context", {})
    prompt = f"Rewrite for a farmer:\\n{advisory}"
    if farmer_ctx:
        prompt += f"\\nFarmer: {json.dumps(farmer_ctx)}"

    resp = bedrock.converse(
        modelId=MODEL,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        system=[{"text": SYSTEM_PROMPT}],
        inferenceConfig={"maxTokens": 1500, "temperature": 0.6},
    )
    final = resp["output"]["message"]["content"][0]["text"]
    trace = event.get("agent_trace", []) + ["communication"]

    return {
        "response": final,
        "tools_used": event.get("tools_used", []),
        "agent_trace": trace,
        "confidence": event.get("confidence", 0.5),
        "pipeline": "step-functions",
    }
'''

AGENT_CODE = {
    'understanding': UNDERSTANDING_CODE,
    'reasoning': REASONING_CODE,
    'factcheck': FACTCHECK_CODE,
    'communication': COMMUNICATION_CODE,
}


# ══════════════════════════════════════════════════════════════
#  Step 1: IAM Roles
# ══════════════════════════════════════════════════════════════
def create_agent_lambda_role():
    print('\n[1/4] Creating IAM Role for Agent Lambdas...')

    trust = {
        'Version': '2012-10-17',
        'Statement': [{'Effect': 'Allow', 'Principal': {'Service': 'lambda.amazonaws.com'}, 'Action': 'sts:AssumeRole'}]
    }

    policy = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'Logs',
                'Effect': 'Allow',
                'Action': ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
                'Resource': f'arn:aws:logs:{REGION}:{ACCOUNT}:log-group:/aws/lambda/{PROJECT}-SFN-*:*',
            },
            {
                'Sid': 'BedrockInvoke',
                'Effect': 'Allow',
                'Action': ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
                'Resource': f'arn:aws:bedrock:{REGION}::foundation-model/*',
            },
            {   # Reasoning agent needs to invoke tool Lambdas
                'Sid': 'InvokeToolLambdas',
                'Effect': 'Allow',
                'Action': 'lambda:InvokeFunction',
                'Resource': f'arn:aws:lambda:{REGION}:{ACCOUNT}:function:{PROJECT}-*',
            },
            {
                'Sid': 'DynamoDBRead',
                'Effect': 'Allow',
                'Action': ['dynamodb:GetItem', 'dynamodb:Query'],
                'Resource': f'arn:aws:dynamodb:{REGION}:{ACCOUNT}:table/*',
            },
        ]
    }

    try:
        resp = iam.create_role(RoleName=AGENT_ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust),
                               Description='Role for SFN agent Lambdas', Tags=[{'Key': 'Project', 'Value': PROJECT}])
        role_arn = resp['Role']['Arn']
        print(f'  Created: {AGENT_ROLE_NAME}')
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f'arn:aws:iam::{ACCOUNT}:role/{AGENT_ROLE_NAME}'
        iam.update_assume_role_policy(RoleName=AGENT_ROLE_NAME, PolicyDocument=json.dumps(trust))
        print(f'  Exists, updated: {AGENT_ROLE_NAME}')

    iam.put_role_policy(RoleName=AGENT_ROLE_NAME, PolicyName='SFNAgentPolicy', PolicyDocument=json.dumps(policy))

    # Step Functions execution role
    sfn_trust = {
        'Version': '2012-10-17',
        'Statement': [{'Effect': 'Allow', 'Principal': {'Service': 'states.amazonaws.com'}, 'Action': 'sts:AssumeRole'}]
    }
    sfn_policy = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'InvokeLambda',
                'Effect': 'Allow',
                'Action': ['lambda:InvokeFunction'],
                'Resource': [f'arn:aws:lambda:{REGION}:{ACCOUNT}:function:{PROJECT}-SFN-*'],
            },
            {
                'Sid': 'LogsForXRay',
                'Effect': 'Allow',
                'Action': ['logs:CreateLogDelivery', 'logs:GetLogDelivery', 'logs:UpdateLogDelivery',
                           'logs:DeleteLogDelivery', 'logs:ListLogDeliveries', 'logs:PutResourcePolicy',
                           'logs:DescribeResourcePolicies', 'logs:DescribeLogGroups',
                           'xray:PutTraceSegments', 'xray:PutTelemetryRecords', 'xray:GetSamplingRules',
                           'xray:GetSamplingTargets'],
                'Resource': '*',
            },
        ]
    }

    try:
        resp = iam.create_role(RoleName=SFN_ROLE_NAME, AssumeRolePolicyDocument=json.dumps(sfn_trust),
                               Description='Step Functions execution role', Tags=[{'Key': 'Project', 'Value': PROJECT}])
        sfn_role_arn = resp['Role']['Arn']
        print(f'  Created: {SFN_ROLE_NAME}')
    except iam.exceptions.EntityAlreadyExistsException:
        sfn_role_arn = f'arn:aws:iam::{ACCOUNT}:role/{SFN_ROLE_NAME}'
        iam.update_assume_role_policy(RoleName=SFN_ROLE_NAME, PolicyDocument=json.dumps(sfn_trust))
        print(f'  Exists, updated: {SFN_ROLE_NAME}')

    iam.put_role_policy(RoleName=SFN_ROLE_NAME, PolicyName='SFNExecutionPolicy', PolicyDocument=json.dumps(sfn_policy))

    print('  Waiting for IAM propagation (10s)...')
    time.sleep(10)
    return role_arn, sfn_role_arn


# ══════════════════════════════════════════════════════════════
#  Step 2: Create Agent Lambdas
# ══════════════════════════════════════════════════════════════
def create_agent_lambdas(role_arn):
    print('\n[2/4] Creating Agent Lambda Functions...')
    arns = {}

    for agent, fn_name in AGENT_LAMBDAS.items():
        code = AGENT_CODE[agent]
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('handler.py', code)
        buf.seek(0)
        zip_bytes = buf.read()

        env = {
            'FOUNDATION_MODEL': FOUNDATION_MODEL,
            'WEATHER_LAMBDA': 'smart-rural-ai-WeatherFunction-dilSoHSLlXGN',
            'CROP_LAMBDA': 'smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY',
            'SCHEMES_LAMBDA': 'smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv',
            'PROFILE_LAMBDA': 'smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt',
        }

        try:
            resp = lam.create_function(
                FunctionName=fn_name,
                Runtime='python3.13',
                Role=role_arn,
                Handler='handler.lambda_handler',
                Code={'ZipFile': zip_bytes},
                Description=f'SFN Cognitive Pipeline — {agent.title()} Agent',
                Timeout=90,
                MemorySize=512,
                Environment={'Variables': env},
                Tags={'Project': PROJECT, 'Agent': agent},
            )
            print(f'  Created: {fn_name}')
        except lam.exceptions.ResourceConflictException:
            lam.update_function_code(FunctionName=fn_name, ZipFile=zip_bytes)
            time.sleep(3)
            lam.update_function_configuration(
                FunctionName=fn_name, Runtime='python3.13', Role=role_arn,
                Handler='handler.lambda_handler', Timeout=90, MemorySize=512,
                Environment={'Variables': env},
            )
            print(f'  Updated: {fn_name}')

        arns[agent] = f'arn:aws:lambda:{REGION}:{ACCOUNT}:function:{fn_name}'

    return arns


# ══════════════════════════════════════════════════════════════
#  Step 3: Create State Machine
# ══════════════════════════════════════════════════════════════
def create_state_machine(sfn_role_arn, lambda_arns):
    print('\n[3/4] Creating Step Functions State Machine...')

    definition = {
        'Comment': 'Smart Rural AI Advisor — 4-Agent Cognitive Pipeline',
        'StartAt': 'UnderstandingAgent',
        'States': {
            'UnderstandingAgent': {
                'Type': 'Task',
                'Resource': 'arn:aws:states:::lambda:invoke',
                'Parameters': {
                    'FunctionName': lambda_arns['understanding'],
                    'Payload.$': '$',
                },
                'ResultSelector': {'Payload.$': '$.Payload'},
                'ResultPath': '$',
                'OutputPath': '$.Payload',
                'Retry': [{'ErrorEquals': ['States.TaskFailed', 'Lambda.ServiceException'],
                           'IntervalSeconds': 2, 'MaxAttempts': 2, 'BackoffRate': 2.0}],
                'Catch': [{'ErrorEquals': ['States.ALL'], 'Next': 'FallbackResponse',
                           'ResultPath': '$.error'}],
                'TimeoutSeconds': 30,
                'Next': 'ReasoningAgent',
            },
            'ReasoningAgent': {
                'Type': 'Task',
                'Resource': 'arn:aws:states:::lambda:invoke',
                'Parameters': {
                    'FunctionName': lambda_arns['reasoning'],
                    'Payload.$': '$',
                },
                'ResultSelector': {'Payload.$': '$.Payload'},
                'ResultPath': '$',
                'OutputPath': '$.Payload',
                'Retry': [{'ErrorEquals': ['States.TaskFailed'], 'IntervalSeconds': 3,
                           'MaxAttempts': 1, 'BackoffRate': 2.0}],
                'Catch': [{'ErrorEquals': ['States.ALL'], 'Next': 'FallbackResponse',
                           'ResultPath': '$.error'}],
                'TimeoutSeconds': 60,
                'Next': 'FactCheckAgent',
            },
            'FactCheckAgent': {
                'Type': 'Task',
                'Resource': 'arn:aws:states:::lambda:invoke',
                'Parameters': {
                    'FunctionName': lambda_arns['factcheck'],
                    'Payload.$': '$',
                },
                'ResultSelector': {'Payload.$': '$.Payload'},
                'ResultPath': '$',
                'OutputPath': '$.Payload',
                'Retry': [{'ErrorEquals': ['States.TaskFailed'], 'IntervalSeconds': 2,
                           'MaxAttempts': 1, 'BackoffRate': 2.0}],
                'Catch': [{'ErrorEquals': ['States.ALL'], 'Next': 'CommunicationAgent',
                           'ResultPath': '$.error'}],
                'TimeoutSeconds': 30,
                'Next': 'CommunicationAgent',
            },
            'CommunicationAgent': {
                'Type': 'Task',
                'Resource': 'arn:aws:states:::lambda:invoke',
                'Parameters': {
                    'FunctionName': lambda_arns['communication'],
                    'Payload.$': '$',
                },
                'ResultSelector': {'Payload.$': '$.Payload'},
                'ResultPath': '$',
                'OutputPath': '$.Payload',
                'Retry': [{'ErrorEquals': ['States.TaskFailed'], 'IntervalSeconds': 2,
                           'MaxAttempts': 1, 'BackoffRate': 2.0}],
                'Catch': [{'ErrorEquals': ['States.ALL'], 'Next': 'FallbackResponse',
                           'ResultPath': '$.error'}],
                'TimeoutSeconds': 30,
                'End': True,
            },
            'FallbackResponse': {
                'Type': 'Pass',
                'Result': {
                    'response': 'I apologize, I encountered an issue processing your request. Please try again.',
                    'pipeline': 'step-functions',
                    'agent_trace': ['error-fallback'],
                    'tools_used': [],
                },
                'End': True,
            },
        },
    }

    sm_arn = f'arn:aws:states:{REGION}:{ACCOUNT}:stateMachine:{STATE_MACHINE_NAME}'

    try:
        resp = sfn.create_state_machine(
            name=STATE_MACHINE_NAME,
            definition=json.dumps(definition),
            roleArn=sfn_role_arn,
            type='STANDARD',
            tracingConfiguration={'enabled': True},
            tags=[{'key': 'Project', 'value': PROJECT}],
        )
        sm_arn = resp['stateMachineArn']
        print(f'  Created: {STATE_MACHINE_NAME}')
    except sfn.exceptions.StateMachineAlreadyExists:
        # List and find ARN
        machines = sfn.list_state_machines(maxResults=100)
        for m in machines['stateMachines']:
            if m['name'] == STATE_MACHINE_NAME:
                sm_arn = m['stateMachineArn']
                break
        sfn.update_state_machine(
            stateMachineArn=sm_arn,
            definition=json.dumps(definition),
            roleArn=sfn_role_arn,
            tracingConfiguration={'enabled': True},
        )
        print(f'  Updated: {STATE_MACHINE_NAME}')

    print(f'  ARN: {sm_arn}')
    return sm_arn


# ══════════════════════════════════════════════════════════════
#  Step 4: Verify with test execution
# ══════════════════════════════════════════════════════════════
def verify(sm_arn):
    print('\n[4/4] Verification...')

    # Describe state machine
    desc = sfn.describe_state_machine(stateMachineArn=sm_arn)
    print(f'  ✅ State Machine: {desc["name"]}')
    print(f'     Status: {desc["status"]}')
    print(f'     Type: {desc["type"]}')

    # Count agent Lambdas
    for agent, fn_name in AGENT_LAMBDAS.items():
        try:
            func = lam.get_function(FunctionName=fn_name)
            state = func['Configuration']['State']
            print(f'  ✅ {agent.title()} Agent: {state}')
        except Exception as e:
            print(f'  ❌ {agent.title()} Agent: {e}')

    console_url = (
        f'https://{REGION}.console.aws.amazon.com/states/home?region={REGION}'
        f'#/statemachines/view/{sm_arn}'
    )
    print(f'\n  Console: {console_url}')
    return console_url


def main():
    print('=' * 60)
    print('  Step Functions — Cognitive Pipeline State Machine')
    print('=' * 60)

    role_arn, sfn_role_arn = create_agent_lambda_role()
    lambda_arns = create_agent_lambdas(role_arn)
    sm_arn = create_state_machine(sfn_role_arn, lambda_arns)
    console_url = verify(sm_arn)

    # Save config
    config = {
        'stateMachineArn': sm_arn,
        'agentLambdas': AGENT_LAMBDAS,
        'agentLambdaArns': lambda_arns,
        'consoleUrl': console_url,
    }
    config_path = 'infrastructure/stepfunctions_config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f'\n{"=" * 60}')
    print(f'  ✅ Step Functions Pipeline Created')
    print(f'{"=" * 60}')
    print(f'  State Machine: {sm_arn}')
    print(f'  Agent Lambdas: {len(AGENT_LAMBDAS)}')
    print(f'  Config saved:  {config_path}')
    print(f'\n  To test:')
    print(f'    aws stepfunctions start-execution \\')
    print(f'      --state-machine-arn {sm_arn} \\')
    print(f'      --input \'{{"query":"what is the weather in Viluppuram","farmer_context":{{"name":"Manoj","state":"Tamil Nadu","district":"Viluppuram"}}}}\'')
    print()


if __name__ == '__main__':
    main()
