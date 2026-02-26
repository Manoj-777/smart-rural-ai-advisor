"""
Smart Rural AI Advisor — Bedrock Agent Setup Script
Run AFTER creating the Knowledge Base in the Bedrock Console.

Usage:
    python setup_bedrock_agent.py <knowledge_base_id>

Example:
    python setup_bedrock_agent.py ABCDE12345
"""

import json
import sys
import time
import subprocess

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
AGENT_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/BedrockAgentRole"

# Lambda function names (from deployed stack)
LAMBDA_FUNCTIONS = {
    "crop_advisory": "smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY",
    "weather": "smart-rural-ai-WeatherFunction-dilSoHSLlXGN",
    "govt_schemes": "smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv",
    "farmer_profile": "smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt",
}

AGENT_INSTRUCTION = """You are the Smart Rural AI Advisor — a trusted, knowledgeable farming assistant for Indian farmers.

PERSONALITY:
- You speak like a friendly, experienced agricultural officer
- You are respectful, patient, and encouraging
- You use simple language (avoid jargon unless explaining it)
- You always explain WHY you recommend something

CAPABILITIES:
- Recommend the best crops based on soil, season, region, and climate
- Provide irrigation schedules based on crop stage and weather
- Alert about pest and disease risks with organic + chemical treatments
- Explain government schemes (PM-KISAN, PMFBY, KCC) with exact eligibility and application steps
- Share weather forecasts and climate-related farming advice
- Integrate traditional Indian farming wisdom (Panchagavya, crop rotation, companion planting)

RESPONSE FORMAT:
- Always start with a direct answer to the farmer's question
- Follow with a brief explanation of WHY
- Include specific, actionable steps the farmer can take
- If relevant, mention applicable government schemes or subsidies
- End with a follow-up question or helpful tip

RULES:
- NEVER make up data — if you don't know, say so and suggest consulting a local Krishi Vigyan Kendra (KVK)
- Always consider the farmer's specific state/region when giving advice
- Prefer organic/traditional solutions first, then chemical options
- Include cost estimates in Indian Rupees when possible
- If the farmer seems to be in a crisis (crop failure, pest outbreak), be empathetic and urgent
- Reference government helpline numbers when relevant: Kisan Call Centre (1800-180-1551)

TOOLS:
- Use get_crop_advisory for crop-related questions
- Use get_weather_data for weather and climate questions
- Use get_govt_schemes for scheme/loan/insurance questions
- Use get_pest_alert for pest and disease questions
- Use get_irrigation_advice for water and irrigation questions
- You can use multiple tools in a single response if needed"""

# --- OpenAPI Schemas for Action Groups ---

CROP_ADVISORY_SCHEMA = {
    "openapi": "3.0.0",
    "info": {"title": "Crop Advisory API", "version": "1.0"},
    "paths": {
        "/get_crop_advisory": {
            "post": {
                "summary": "Get crop planning and advisory information for Indian farming",
                "description": "Returns crop recommendations based on soil type, season, region, and climate conditions.",
                "operationId": "getCropAdvisory",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "The farmer's crop-related question in English"},
                                    "state": {"type": "string", "description": "Indian state name, e.g. Tamil Nadu, Punjab"},
                                    "crop": {"type": "string", "description": "Crop name if mentioned, e.g. rice, wheat, cotton"},
                                    "season": {"type": "string", "enum": ["kharif", "rabi", "zaid", "unknown"], "description": "Farming season"}
                                },
                                "required": ["query"]
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Crop advisory information"}}
            }
        },
        "/get_pest_alert": {
            "post": {
                "summary": "Get pest and disease alerts for crops",
                "description": "Returns pest/disease identification, symptoms, organic and chemical treatments, prevention methods.",
                "operationId": "getPestAlert",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "The farmer's pest/disease question in English"},
                                    "crop": {"type": "string", "description": "Affected crop name"},
                                    "symptoms": {"type": "string", "description": "Described symptoms like yellow leaves, spots, wilting"}
                                },
                                "required": ["query"]
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Pest alert information"}}
            }
        },
        "/get_irrigation_advice": {
            "post": {
                "summary": "Get irrigation and water management advice",
                "description": "Returns irrigation schedules, water requirements, drip/sprinkler recommendations.",
                "operationId": "getIrrigationAdvice",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "The farmer's irrigation question in English"},
                                    "crop": {"type": "string", "description": "Crop name"},
                                    "location": {"type": "string", "description": "District or city name for weather context"}
                                },
                                "required": ["query"]
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Irrigation advice"}}
            }
        }
    }
}

WEATHER_SCHEMA = {
    "openapi": "3.0.0",
    "info": {"title": "Weather API", "version": "1.0"},
    "paths": {
        "/get_weather_data": {
            "post": {
                "summary": "Get current weather and forecast for an Indian location",
                "description": "Returns real-time temperature, humidity, rainfall, wind speed, and 5-day forecast.",
                "operationId": "getWeatherData",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "location": {"type": "string", "description": "Indian city or district name, e.g. Thanjavur, Chennai, Pune"}
                                },
                                "required": ["location"]
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Weather data"}}
            }
        }
    }
}

SCHEMES_SCHEMA = {
    "openapi": "3.0.0",
    "info": {"title": "Government Schemes API", "version": "1.0"},
    "paths": {
        "/get_govt_schemes": {
            "post": {
                "summary": "Get Indian government agricultural scheme information",
                "description": "Returns eligibility criteria, application process, benefits, and helpline numbers for government schemes.",
                "operationId": "getGovtSchemes",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "The farmer's scheme question in English"},
                                    "scheme_name": {"type": "string", "description": "Specific scheme name if mentioned, e.g. PM-KISAN, PMFBY, KCC"}
                                },
                                "required": ["query"]
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Scheme information"}}
            }
        }
    }
}


def run_aws(cmd, parse_json=True):
    """Run AWS CLI command and return parsed output."""
    full_cmd = f"aws {cmd} --region {REGION} --output json"
    print(f"  > {full_cmd[:120]}...")
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        return None
    if parse_json and result.stdout.strip():
        return json.loads(result.stdout)
    return result.stdout.strip()


def add_lambda_permission(function_name, agent_id):
    """Allow Bedrock Agent to invoke the Lambda function."""
    stmt_id = f"AllowBedrockAgent-{agent_id}"
    cmd = (
        f"lambda add-permission --function-name {function_name} "
        f"--statement-id {stmt_id} "
        f"--action lambda:InvokeFunction "
        f"--principal bedrock.amazonaws.com "
        f"--source-arn arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent/{agent_id}"
    )
    result = run_aws(cmd)
    if result is None:
        print(f"  (Permission may already exist for {function_name})")


def create_agent():
    """Create the Bedrock Agent."""
    print("\n[1/6] Creating Bedrock Agent...")
    
    # Write instruction to temp file to avoid shell escaping issues
    with open("agent-instruction.txt", "w", encoding="utf-8") as f:
        f.write(AGENT_INSTRUCTION)
    
    cmd = (
        f'bedrock-agent create-agent '
        f'--agent-name smart-rural-advisor '
        f'--agent-resource-role-arn {AGENT_ROLE_ARN} '
        f'--foundation-model "anthropic.claude-sonnet-4-5-20250929-v1:0" '
        f'--idle-session-ttl-in-seconds 1800 '
        f'--instruction file://agent-instruction.txt '
        f'--description "AI farming advisor for Indian farmers. Provides crop, weather, pest, and scheme advice in Tamil, English, Telugu, and Hindi."'
    )
    
    result = run_aws(cmd)
    if result is None:
        sys.exit(1)
    
    agent_id = result["agent"]["agentId"]
    print(f"  Agent created: {agent_id}")
    
    # Wait for agent to be ready
    print("  Waiting for agent to be ready...")
    for i in range(30):
        time.sleep(5)
        status = run_aws(f"bedrock-agent get-agent --agent-id {agent_id}")
        if status and status["agent"]["agentStatus"] in ["NOT_PREPARED", "PREPARED"]:
            print(f"  Agent status: {status['agent']['agentStatus']}")
            break
        if status:
            print(f"  Agent status: {status['agent']['agentStatus']} (waiting...)")
    
    return agent_id


def add_action_groups(agent_id):
    """Add all action groups to the agent."""
    print("\n[2/6] Adding action groups...")
    
    groups = [
        {
            "name": "crop_advisory_tools",
            "description": "Tools for crop advisory, pest alerts, and irrigation advice",
            "lambda_key": "crop_advisory",
            "schema": CROP_ADVISORY_SCHEMA,
        },
        {
            "name": "weather_tools",
            "description": "Tools for weather data and forecasts",
            "lambda_key": "weather",
            "schema": WEATHER_SCHEMA,
        },
        {
            "name": "scheme_tools",
            "description": "Tools for government agricultural schemes",
            "lambda_key": "govt_schemes",
            "schema": SCHEMES_SCHEMA,
        },
    ]
    
    for group in groups:
        lambda_name = LAMBDA_FUNCTIONS[group["lambda_key"]]
        lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{lambda_name}"
        
        # Write schema to temp file
        schema_file = f"schema-{group['name']}.json"
        with open(schema_file, "w") as f:
            json.dump(group["schema"], f)
        
        cmd = (
            f'bedrock-agent create-agent-action-group '
            f'--agent-id {agent_id} '
            f'--agent-version DRAFT '
            f'--action-group-name {group["name"]} '
            f'--description "{group["description"]}" '
            f'--action-group-executor lambdaArn={lambda_arn} '
            f'--api-schema \'{{\"payload\": {json.dumps(json.dumps(group["schema"]))}}}\''
        )
        
        # Simpler approach: use file-based schema
        api_schema_str = json.dumps({"payload": json.dumps(group["schema"])})
        schema_config_file = f"schema-config-{group['name']}.json"
        with open(schema_config_file, "w") as f:
            f.write(api_schema_str)
        
        cmd = (
            f'bedrock-agent create-agent-action-group '
            f'--agent-id {agent_id} '
            f'--agent-version DRAFT '
            f'--action-group-name {group["name"]} '
            f'--description "{group["description"]}" '
            f'--action-group-executor lambdaArn={lambda_arn} '
            f'--api-schema file://{schema_config_file}'
        )
        
        result = run_aws(cmd)
        if result:
            print(f"  Added action group: {group['name']}")
        
        # Add Lambda invoke permission for the agent
        add_lambda_permission(lambda_name, agent_id)


def associate_knowledge_base(agent_id, kb_id):
    """Associate the Knowledge Base with the agent."""
    print("\n[3/6] Associating Knowledge Base...")
    
    cmd = (
        f'bedrock-agent associate-agent-knowledge-base '
        f'--agent-id {agent_id} '
        f'--agent-version DRAFT '
        f'--knowledge-base-id {kb_id} '
        f'--description "Indian farming knowledge base with crop guides, pest data, irrigation, govt schemes, and traditional practices"'
    )
    
    result = run_aws(cmd)
    if result:
        print(f"  Knowledge Base {kb_id} associated with agent {agent_id}")


def prepare_agent(agent_id):
    """Prepare the agent for use."""
    print("\n[4/6] Preparing agent...")
    
    result = run_aws(f"bedrock-agent prepare-agent --agent-id {agent_id}")
    if result:
        print(f"  Agent preparation initiated")
    
    # Wait for preparation
    for i in range(30):
        time.sleep(5)
        status = run_aws(f"bedrock-agent get-agent --agent-id {agent_id}")
        if status and status["agent"]["agentStatus"] == "PREPARED":
            print(f"  Agent is PREPARED")
            return True
        if status:
            print(f"  Status: {status['agent']['agentStatus']} (waiting...)")
    
    print("  WARNING: Agent preparation timed out. Check console.")
    return False


def create_alias(agent_id):
    """Create a production alias for the agent."""
    print("\n[5/6] Creating agent alias...")
    
    cmd = (
        f'bedrock-agent create-agent-alias '
        f'--agent-id {agent_id} '
        f'--agent-alias-name prod '
        f'--description "Production alias for Smart Rural AI Advisor"'
    )
    
    result = run_aws(cmd)
    if result is None:
        return None
    
    alias_id = result["agentAlias"]["agentAliasId"]
    print(f"  Alias created: {alias_id}")
    return alias_id


def update_stack(agent_id, alias_id, kb_id):
    """Redeploy the SAM stack with real Bedrock IDs."""
    print("\n[6/6] Redeploying stack with Bedrock IDs...")
    
    deploy_cmd = (
        f"..\\.venv313\\Scripts\\sam.exe deploy "
        f"--stack-name smart-rural-ai --region {REGION} "
        f"--s3-bucket smart-rural-ai-{ACCOUNT_ID} --s3-prefix sam-artifacts "
        f"--capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset "
        f'--parameter-overrides '
        f'"OpenWeatherApiKey={os.environ.get("OPENWEATHER_API_KEY", "PLACEHOLDER")} '
        f"BedrockAgentId={agent_id} "
        f"BedrockAgentAliasId={alias_id} "
        f'BedrockKBId={kb_id}"'
    )
    
    print(f"  Running: {deploy_cmd[:100]}...")
    result = subprocess.run(deploy_cmd, shell=True, cwd=".", capture_output=False)
    return result.returncode == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python setup_bedrock_agent.py <knowledge_base_id>")
        print("Example: python setup_bedrock_agent.py ABCDE12345")
        print("\nFirst create the KB in the Bedrock Console:")
        print("  1. Go to: https://ap-south-1.console.aws.amazon.com/bedrock/home?region=ap-south-1#/knowledge-bases")
        print("  2. Click 'Create knowledge base'")
        print("  3. Name: smart-rural-farming-kb")
        print("  4. IAM role: Select existing 'BedrockKBRole'")
        print("  5. Data source: S3 → s3://smart-rural-ai-948809294205/knowledge_base/")
        print("  6. Chunking: Fixed-size, 300 tokens, 20% overlap")
        print("  7. Embeddings: Amazon Titan Text Embeddings V2")
        print("  8. Vector store: Quick create new")
        print("  9. After creation, click 'Sync' on the data source")
        print(" 10. Copy the KB ID and run this script with it")
        sys.exit(0)
    
    kb_id = sys.argv[1].strip()
    print(f"=" * 60)
    print(f"  Smart Rural AI Advisor — Bedrock Agent Setup")
    print(f"  Knowledge Base ID: {kb_id}")
    print(f"=" * 60)
    
    # Step 1: Create agent
    agent_id = create_agent()
    
    # Step 2: Add action groups
    add_action_groups(agent_id)
    
    # Step 3: Associate KB
    associate_knowledge_base(agent_id, kb_id)
    
    # Step 4: Prepare agent
    prepare_agent(agent_id)
    
    # Step 5: Create alias
    alias_id = create_alias(agent_id)
    
    if not alias_id:
        print("\nERROR: Failed to create alias. Check the Bedrock Console.")
        sys.exit(1)
    
    # Step 6: Update & redeploy stack
    print(f"\n{'=' * 60}")
    print(f"  BEDROCK IDS:")
    print(f"  Agent ID:    {agent_id}")
    print(f"  Alias ID:    {alias_id}")
    print(f"  KB ID:       {kb_id}")
    print(f"{'=' * 60}")
    
    # Update .env file
    env_updates = {
        "BEDROCK_AGENT_ID": agent_id,
        "BEDROCK_AGENT_ALIAS_ID": alias_id,
        "BEDROCK_KB_ID": kb_id,
    }
    
    try:
        with open(".env", "r") as f:
            env_content = f.read()
        for key, value in env_updates.items():
            if f"{key}=" in env_content:
                lines = env_content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}"
                env_content = "\n".join(lines)
        with open(".env", "w") as f:
            f.write(env_content)
        print("\n  .env updated with Bedrock IDs")
    except FileNotFoundError:
        print("\n  WARNING: .env file not found")
    
    # Update bedrock_agentcore_config.json
    try:
        with open("infrastructure/bedrock_agentcore_config.json", "r") as f:
            config = json.load(f)
        config["agent"]["agent_id"] = agent_id
        config["agent"]["agent_alias_id"] = alias_id
        config["knowledge_base"]["kb_id"] = kb_id
        with open("infrastructure/bedrock_agentcore_config.json", "w") as f:
            json.dump(config, f, indent=4)
        print("  bedrock_agentcore_config.json updated")
    except Exception as e:
        print(f"  WARNING: Could not update config: {e}")
    
    # Redeploy
    print("\n  Redeploying stack with real Bedrock IDs...")
    update_stack(agent_id, alias_id, kb_id)
    
    print(f"\n{'=' * 60}")
    print(f"  SETUP COMPLETE!")
    print(f"  API: https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/")
    print(f"  Test: POST /chat with {{\"message\": \"What crop for Tamil Nadu?\"}}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
