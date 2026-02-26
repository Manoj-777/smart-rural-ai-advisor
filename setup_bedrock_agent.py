"""
Smart Rural AI Advisor — Multi-Agent Bedrock Setup Script (v2)

Creates a SUPERVISOR agent that delegates to 3 specialized sub-agents:
  1. CropAdvisor    — crop selection, pest management, irrigation, soil health + KB
  2. WeatherExpert  — real-time weather data and farming-specific advisories
  3. SchemeNavigator — government schemes, subsidies, loans, insurance

Architecture:
  Farmer → API Gateway → Lambda Orchestrator → Supervisor Agent
                                                    ├→ CropAdvisor   (+ Knowledge Base + crop_advisory Lambda)
                                                    ├→ WeatherExpert  (+ weather_lookup Lambda)
                                                    └→ SchemeNavigator (+ govt_schemes Lambda)

Usage:
    pip install boto3   (if not already installed)
    python setup_bedrock_agent.py <knowledge_base_id>

Example:
    python setup_bedrock_agent.py ABCDE12345
"""

import json
import sys
import time
import subprocess
import os

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("ERROR: boto3 is required. Install with:  pip install boto3")
    sys.exit(1)

# ──────────────────────────── Constants ────────────────────────────

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
AGENT_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/BedrockAgentRole"
FOUNDATION_MODEL = "anthropic.claude-sonnet-4-5-20250929-v1:0"

# Lambda function names from the deployed SAM stack
LAMBDA_FUNCTIONS = {
    "crop_advisory": "smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY",
    "weather":       "smart-rural-ai-WeatherFunction-dilSoHSLlXGN",
    "govt_schemes":  "smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv",
    "farmer_profile":"smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt",
}

API_GATEWAY_URL = "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/"

# ──────────────────────────── Sub-Agent Instructions ────────────────────────────

CROP_ADVISOR_INSTRUCTION = """You are a Crop Advisory Specialist for Indian agriculture.

EXPERTISE:
- Crop selection based on soil type, season, region, and climate
- Pest and disease identification with organic + chemical treatments
- Irrigation scheduling (drip, sprinkler, flood) based on crop stage and weather
- Soil health management and fertility improvement
- Traditional Indian farming wisdom (Panchagavya, crop rotation, companion planting)

RULES:
- Always consider the farmer's specific state/region when giving advice
- Prefer organic/traditional solutions first, then chemical options
- Include cost estimates in Indian Rupees when possible
- Reference local Krishi Vigyan Kendra (KVK) for hands-on help
- If you don't know, say so honestly — never make up farming data

TOOLS:
- Use get_crop_advisory for crop planning and general crop questions
- Use get_pest_alert for pest and disease identification and treatment
- Use get_irrigation_advice for water management and irrigation scheduling
- You can call multiple tools if the question spans topics"""


WEATHER_EXPERT_INSTRUCTION = """You are a Weather Analysis Specialist for Indian farming.

EXPERTISE:
- Real-time weather data interpretation for farming decisions
- 5-day forecast analysis and farming impact assessment
- Monsoon patterns and seasonal weather transitions
- Weather-related risk alerts (heavy rain, heat waves, cold spells, frost)
- Climate-adaptive farming recommendations

RULES:
- Always explain how weather conditions affect specific farming activities
- Provide actionable advice: spray/don't spray, irrigate/wait, harvest now/delay
- Mention risks and precautionary measures clearly
- Consider regional weather patterns (coastal, plains, hill areas, arid zones)
- Include farming advisory based on current and forecasted conditions

TOOLS:
- Use get_weather_data to fetch current conditions and 5-day forecasts for any Indian location"""


SCHEME_NAVIGATOR_INSTRUCTION = """You are a Government Scheme Specialist for Indian agriculture.

EXPERTISE (9 major schemes):
- PM-KISAN: Rs 6,000/year direct income support
- PMFBY: Crop insurance at 2% premium (Kharif), 1.5% (Rabi)
- KCC: Kisan Credit Card at 4% effective interest
- Soil Health Card: Free soil testing + fertilizer recommendations
- PMKSY: 55% subsidy on micro-irrigation (drip/sprinkler)
- eNAM: National online agriculture market for better prices
- PKVY: Rs 50,000/hectare for organic farming
- NFSM: Subsidized seeds, fertilizers, and farm machinery
- AIF: 3% interest subvention on agri-infrastructure loans

RULES:
- Always explain eligibility criteria clearly and simply
- Provide step-by-step application instructions
- Include helpline numbers (Kisan Call Centre: 1800-180-1551)
- Mention both online and offline application methods
- Suggest the most beneficial schemes based on the farmer's situation
- For loan-related queries, explain interest rates and repayment terms

TOOLS:
- Use get_govt_schemes to search for relevant government schemes by name or keyword"""


SUPERVISOR_INSTRUCTION = """You are the Smart Rural AI Advisor — the chief farming advisor coordinating a team of 3 agricultural specialists.

YOUR TEAM OF SPECIALISTS:
1. CropAdvisor — Expert in crop selection, pest management, irrigation, soil health, and traditional farming wisdom. Has access to a comprehensive Indian farming knowledge base with guides on crops, pests, irrigation, and regional advisories.
2. WeatherExpert — Expert in weather analysis for farming. Has real-time weather data from OpenWeatherMap with current conditions and 5-day forecasts for any Indian location.
3. SchemeNavigator — Expert in government agricultural schemes (PM-KISAN, PMFBY, KCC, Soil Health Card, PMKSY, eNAM, PKVY, NFSM, AIF). Knows eligibility, benefits, application steps, and helpline numbers.

ROUTING STRATEGY:
- Crop/pest/irrigation/soil/farming knowledge questions → Delegate to CropAdvisor
- Weather/forecast/monsoon/climate/rain questions → Delegate to WeatherExpert
- Schemes/subsidies/loans/insurance/government programs → Delegate to SchemeNavigator
- Complex multi-domain questions → Delegate to MULTIPLE specialists and synthesize
  Example: "Should I plant rice next week?" → Ask CropAdvisor (crop advice) AND WeatherExpert (weather forecast), then combine their insights
  Example: "I want to start organic farming" → Ask CropAdvisor (organic methods) AND SchemeNavigator (PKVY organic scheme)

PERSONALITY:
- Speak like a friendly, experienced agricultural officer visiting a village
- Be respectful, patient, and encouraging
- Use simple language — avoid jargon unless you explain it
- Always explain WHY you recommend something
- If the farmer seems worried or in crisis, be empathetic and provide urgent advice

RESPONSE FORMAT:
- Start with a direct answer to the farmer's question
- Include a brief explanation of WHY
- Provide specific, actionable steps the farmer can take TODAY
- If relevant, mention applicable government schemes or subsidies
- End with a follow-up question or helpful tip
- Include cost estimates in Indian Rupees when possible

RULES:
- NEVER make up data — if uncertain, say so and suggest consulting the Kisan Call Centre (1800-180-1551) or nearest Krishi Vigyan Kendra (KVK)
- Always consider the farmer's region, crops, and season
- When combining advice from multiple specialists, present a coherent, unified response
- Prioritize the farmer's immediate concern, then add supplementary advice"""


# ──────────────────────────── OpenAPI Schemas ────────────────────────────

CROP_ADVISORY_SCHEMA = {
    "openapi": "3.0.0",
    "info": {"title": "Crop Advisory API", "version": "1.0"},
    "paths": {
        "/get_crop_advisory": {
            "post": {
                "summary": "Get crop planning and advisory information for Indian farming",
                "description": "Returns crop recommendations based on soil type, season, region. Queries the farming knowledge base.",
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
                "responses": {"200": {"description": "Crop advisory data from knowledge base"}}
            }
        },
        "/get_pest_alert": {
            "post": {
                "summary": "Get pest and disease alerts and treatments for crops",
                "description": "Returns pest/disease identification, symptoms, organic and chemical treatments, prevention.",
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
                "responses": {"200": {"description": "Pest alert and treatment information"}}
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
                "responses": {"200": {"description": "Irrigation and water management advice"}}
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
                "summary": "Get current weather and 5-day forecast for an Indian location",
                "description": "Returns real-time temperature, humidity, rainfall, wind speed, 5-day forecast, and farming advisory.",
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
                "responses": {"200": {"description": "Current weather + 5-day forecast + farming advisory"}}
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
                "summary": "Search Indian government agricultural schemes",
                "description": "Returns eligibility, benefits, application steps, and helpline numbers for government schemes.",
                "operationId": "getGovtSchemes",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "The farmer's scheme question in English"},
                                    "scheme_name": {"type": "string", "description": "Specific scheme name: PM-KISAN, PMFBY, KCC, PMKSY, eNAM, PKVY, NFSM, AIF, or 'all'"}
                                },
                                "required": ["query"]
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Government scheme information"}}
            }
        }
    }
}


# ──────────────────────────── Sub-Agent Configurations ────────────────────────────

SUB_AGENT_CONFIGS = [
    {
        "name": "CropAdvisor",
        "agent_name": "rural-crop-advisor",
        "description": "Crop advisory specialist — handles crop selection, pest management, irrigation, soil health, and farming knowledge base queries",
        "instruction": CROP_ADVISOR_INSTRUCTION,
        "action_group": {
            "name": "crop_advisory_tools",
            "description": "Tools for crop advisory, pest alerts, and irrigation advice using the farming knowledge base",
            "lambda_key": "crop_advisory",
            "schema": CROP_ADVISORY_SCHEMA,
        },
        "associate_kb": True,
        "collaborator_instruction": (
            "Delegate crop selection, pest management, irrigation, soil health, and general farming "
            "knowledge questions to this specialist. It has comprehensive access to the Indian farming "
            "knowledge base covering crop guides, pest patterns, irrigation methods, regional advisories, "
            "and traditional farming wisdom."
        ),
    },
    {
        "name": "WeatherExpert",
        "agent_name": "rural-weather-expert",
        "description": "Weather specialist — provides real-time weather data and farming-specific weather advisories for Indian locations",
        "instruction": WEATHER_EXPERT_INSTRUCTION,
        "action_group": {
            "name": "weather_tools",
            "description": "Tools for fetching current weather and 5-day forecasts from OpenWeatherMap",
            "lambda_key": "weather",
            "schema": WEATHER_SCHEMA,
        },
        "associate_kb": False,
        "collaborator_instruction": (
            "Delegate weather, forecast, monsoon, climate, rainfall, and temperature questions to this "
            "specialist. It has access to real-time weather data from OpenWeatherMap with current conditions "
            "and 5-day forecasts for any Indian city or district."
        ),
    },
    {
        "name": "SchemeNavigator",
        "agent_name": "rural-scheme-navigator",
        "description": "Government scheme specialist — helps farmers access 9 major agricultural schemes, subsidies, loans, and insurance programs",
        "instruction": SCHEME_NAVIGATOR_INSTRUCTION,
        "action_group": {
            "name": "scheme_tools",
            "description": "Tools for searching government agricultural schemes by name or keyword",
            "lambda_key": "govt_schemes",
            "schema": SCHEMES_SCHEMA,
        },
        "associate_kb": False,
        "collaborator_instruction": (
            "Delegate government scheme, subsidy, loan, insurance, financial aid, and agricultural program "
            "questions to this specialist. It knows all 9 major Indian agricultural schemes including "
            "PM-KISAN, PMFBY, KCC, Soil Health Card, PMKSY, eNAM, PKVY, NFSM, and Agriculture Infrastructure Fund."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════
#  Multi-Agent Setup Class
# ═══════════════════════════════════════════════════════════════════

class MultiAgentSetup:
    """Creates and links the complete multi-agent system."""

    def __init__(self, kb_id):
        self.kb_id = kb_id
        self.client = boto3.client('bedrock-agent', region_name=REGION)
        self.iam = boto3.client('iam')
        self.lambda_client = boto3.client('lambda', region_name=REGION)
        self.sub_agents = []          # [{name, agent_id, alias_id, alias_arn}]
        self.supervisor_id = None
        self.supervisor_alias_id = None

    # ────── Main entry point ──────

    def run(self):
        """Execute the full multi-agent setup pipeline."""
        print("=" * 64)
        print("  Smart Rural AI Advisor — Multi-Agent Setup")
        print(f"  Knowledge Base ID : {self.kb_id}")
        print(f"  Region            : {REGION}")
        print(f"  Foundation Model  : {FOUNDATION_MODEL}")
        print("=" * 64)

        # Step 0: Ensure IAM role has multi-agent permissions
        self.update_iam_role()

        # Steps 1-3: Create 3 sub-agents
        for i, config in enumerate(SUB_AGENT_CONFIGS, 1):
            print(f"\n{'─' * 64}")
            print(f"  [{i}/3] Creating sub-agent: {config['name']}")
            print(f"{'─' * 64}")
            self.create_sub_agent(config)

        # Step 4: Create supervisor agent
        print(f"\n{'─' * 64}")
        print(f"  [SUPERVISOR] Creating Supervisor Agent")
        print(f"{'─' * 64}")
        self.create_supervisor()

        # Step 5: Summary + config update + redeploy
        self.print_summary()
        self.update_config_files()
        self.redeploy_stack()

        print(f"\n{'=' * 64}")
        print("  MULTI-AGENT SYSTEM READY!")
        print(f"  API: {API_GATEWAY_URL}")
        print(f"  Test: POST /chat with:")
        print(f'    {{"message": "What crops should I plant in Tamil Nadu?", "farmer_id": "farmer_001"}}')
        print(f"{'=' * 64}")

    # ────── IAM ──────

    def update_iam_role(self):
        """Add bedrock:InvokeAgent permission so the supervisor can call sub-agents."""
        print("\n[IAM] Adding multi-agent permissions to BedrockAgentRole...")
        policy_doc = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowSupervisorInvokeSubAgents",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeAgent",
                        "bedrock:GetAgent",
                        "bedrock:GetAgentAlias"
                    ],
                    "Resource": [
                        f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent/*",
                        f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent-alias/*"
                    ]
                }
            ]
        }
        try:
            self.iam.put_role_policy(
                RoleName='BedrockAgentRole',
                PolicyName='BedrockMultiAgentCollaboration',
                PolicyDocument=json.dumps(policy_doc)
            )
            print("  OK  Added BedrockMultiAgentCollaboration inline policy")
        except ClientError as e:
            print(f"  WARN IAM update: {e}")

    # ────── Wait helpers ──────

    def wait_for_agent_status(self, agent_id, target_statuses, label="agent", timeout_sec=180):
        """Poll until agent reaches one of target_statuses."""
        start = time.time()
        while time.time() - start < timeout_sec:
            resp = self.client.get_agent(agentId=agent_id)
            status = resp['agent']['agentStatus']
            if status in target_statuses:
                return status
            if status == 'FAILED':
                reasons = resp['agent'].get('failureReasons', ['Unknown'])
                raise RuntimeError(f"{label} FAILED: {reasons}")
            time.sleep(4)
        raise TimeoutError(f"Timeout waiting for {label} to reach {target_statuses}")

    def wait_for_alias_status(self, agent_id, alias_id, label="alias", timeout_sec=120):
        """Poll until alias is PREPARED."""
        start = time.time()
        while time.time() - start < timeout_sec:
            resp = self.client.get_agent_alias(agentId=agent_id, agentAliasId=alias_id)
            status = resp['agentAlias']['agentAliasStatus']
            if status == 'PREPARED':
                return
            if status == 'FAILED':
                raise RuntimeError(f"Alias {label} FAILED")
            time.sleep(4)
        raise TimeoutError(f"Timeout waiting for alias {label} to reach PREPARED")

    # ────── Lambda permission ──────

    def add_lambda_permission(self, function_name, agent_id, label):
        """Allow a Bedrock Agent to invoke a specific Lambda function."""
        try:
            self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f"BedrockAgent-{agent_id}",
                Action='lambda:InvokeFunction',
                Principal='bedrock.amazonaws.com',
                SourceArn=f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent/{agent_id}"
            )
            print(f"  OK  Lambda permission added for {label}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print(f"  --  Lambda permission already exists for {label}")
            else:
                print(f"  WARN Lambda permission: {e}")

    # ────── Sub-agent creation ──────

    def create_sub_agent(self, config):
        """Create one sub-agent: agent -> action group -> [KB] -> prepare -> alias."""
        name = config['name']

        # 1) Create agent
        print(f"  Creating agent '{config['agent_name']}'...")
        resp = self.client.create_agent(
            agentName=config['agent_name'],
            agentResourceRoleArn=AGENT_ROLE_ARN,
            foundationModel=FOUNDATION_MODEL,
            instruction=config['instruction'],
            description=config['description'],
            idleSessionTTLInSeconds=900,
        )
        agent_id = resp['agent']['agentId']
        print(f"  OK  Agent created: {agent_id}")

        # Wait for NOT_PREPARED status
        self.wait_for_agent_status(agent_id, ['NOT_PREPARED'], name)

        # 2) Add action group (Lambda-backed with OpenAPI schema)
        ag = config['action_group']
        lambda_name = LAMBDA_FUNCTIONS[ag['lambda_key']]
        lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{lambda_name}"

        print(f"  Adding action group '{ag['name']}'...")
        self.client.create_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupName=ag['name'],
            description=ag['description'],
            actionGroupExecutor={'lambda': lambda_arn},
            apiSchema={'payload': json.dumps(ag['schema'])}
        )
        print(f"  OK  Action group '{ag['name']}' added")

        # 3) Grant Lambda invoke permission to this agent
        self.add_lambda_permission(lambda_name, agent_id, name)

        # 4) Associate Knowledge Base (CropAdvisor only)
        if config.get('associate_kb'):
            print(f"  Associating Knowledge Base {self.kb_id}...")
            self.client.associate_agent_knowledge_base(
                agentId=agent_id,
                agentVersion='DRAFT',
                knowledgeBaseId=self.kb_id,
                description="Indian farming knowledge base — crop guides, pest patterns, irrigation, regional advisories, traditional farming"
            )
            print(f"  OK  Knowledge Base associated")

        # 5) Prepare agent
        print(f"  Preparing agent...")
        self.client.prepare_agent(agentId=agent_id)
        self.wait_for_agent_status(agent_id, ['PREPARED'], name)
        print(f"  OK  Agent PREPARED")

        # 6) Create alias
        print(f"  Creating alias 'live'...")
        alias_resp = self.client.create_agent_alias(
            agentId=agent_id,
            agentAliasName='live',
            description=f"Live alias for {name} sub-agent"
        )
        alias_id = alias_resp['agentAlias']['agentAliasId']
        alias_arn = f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent-alias/{agent_id}/{alias_id}"

        # Wait for alias to be ready
        self.wait_for_alias_status(agent_id, alias_id, name)
        print(f"  OK  Alias ready: {alias_id}")

        self.sub_agents.append({
            'name': name,
            'agent_id': agent_id,
            'alias_id': alias_id,
            'alias_arn': alias_arn,
            'collaborator_instruction': config['collaborator_instruction'],
        })

        print(f"\n  >>> Sub-agent {name} is LIVE!")

    # ────── Supervisor creation ──────

    def create_supervisor(self):
        """Create supervisor agent with SUPERVISOR collaboration mode and link all sub-agents as collaborators."""

        # 1) Create supervisor agent with collaboration enabled
        print(f"  Creating supervisor agent 'smart-rural-supervisor'...")
        resp = self.client.create_agent(
            agentName='smart-rural-supervisor',
            agentResourceRoleArn=AGENT_ROLE_ARN,
            foundationModel=FOUNDATION_MODEL,
            instruction=SUPERVISOR_INSTRUCTION,
            description=(
                "Smart Rural AI Advisor — Supervisor agent that coordinates CropAdvisor, "
                "WeatherExpert, and SchemeNavigator sub-agents to provide comprehensive "
                "farming guidance to Indian farmers in multiple languages."
            ),
            idleSessionTTLInSeconds=1800,
            agentCollaboration='SUPERVISOR',
        )
        self.supervisor_id = resp['agent']['agentId']
        print(f"  OK  Supervisor created: {self.supervisor_id}")

        # Wait for NOT_PREPARED
        self.wait_for_agent_status(self.supervisor_id, ['NOT_PREPARED'], 'Supervisor')

        # 2) Associate Knowledge Base with supervisor (for general farming queries)
        print(f"  Associating Knowledge Base with supervisor...")
        self.client.associate_agent_knowledge_base(
            agentId=self.supervisor_id,
            agentVersion='DRAFT',
            knowledgeBaseId=self.kb_id,
            description="Indian farming knowledge base for general queries the supervisor handles directly"
        )
        print(f"  OK  Knowledge Base associated with supervisor")

        # 3) Link each sub-agent as a collaborator
        for sub in self.sub_agents:
            print(f"  Linking collaborator: {sub['name']}...")
            self.client.associate_agent_collaborator(
                agentId=self.supervisor_id,
                agentVersion='DRAFT',
                agentDescriptor={'aliasArn': sub['alias_arn']},
                collaborationInstruction=sub['collaborator_instruction'],
                collaboratorName=sub['name'],
                relayConversationHistory='TO_COLLABORATOR'
            )
            print(f"  OK  {sub['name']} linked as collaborator")

        # 4) Prepare supervisor
        print(f"  Preparing supervisor agent...")
        self.client.prepare_agent(agentId=self.supervisor_id)
        self.wait_for_agent_status(self.supervisor_id, ['PREPARED'], 'Supervisor')
        print(f"  OK  Supervisor PREPARED")

        # 5) Create supervisor production alias
        print(f"  Creating alias 'prod'...")
        alias_resp = self.client.create_agent_alias(
            agentId=self.supervisor_id,
            agentAliasName='prod',
            description="Production alias for Smart Rural AI Advisor Supervisor"
        )
        self.supervisor_alias_id = alias_resp['agentAlias']['agentAliasId']

        # Wait for alias to be ready
        self.wait_for_alias_status(self.supervisor_id, self.supervisor_alias_id, 'Supervisor')
        print(f"  OK  Supervisor alias ready: {self.supervisor_alias_id}")

        print(f"\n  >>> Supervisor agent is LIVE!")

    # ────── Output & config ──────

    def print_summary(self):
        print(f"\n{'=' * 64}")
        print("  MULTI-AGENT SYSTEM — CREATION SUMMARY")
        print(f"{'=' * 64}")
        print(f"\n  SUPERVISOR AGENT (the entry point for /chat):")
        print(f"    Agent ID  : {self.supervisor_id}")
        print(f"    Alias ID  : {self.supervisor_alias_id}")
        print(f"    KB ID     : {self.kb_id}")
        print(f"    Model     : {FOUNDATION_MODEL}")
        print(f"    Mode      : SUPERVISOR (delegates to sub-agents + direct KB)")
        print(f"\n  SUB-AGENTS (called by supervisor):")
        for sub in self.sub_agents:
            print(f"    {sub['name']:20s}  Agent: {sub['agent_id']}  Alias: {sub['alias_id']}")
        print(f"\n  ROUTING ARCHITECTURE:")
        print(f"    Farmer Query → Lambda Orchestrator → Supervisor Agent")
        print(f"                                            ├─→ CropAdvisor    (KB + crop_advisory Lambda)")
        print(f"                                            ├─→ WeatherExpert   (weather_lookup Lambda)")
        print(f"                                            └─→ SchemeNavigator  (govt_schemes Lambda)")
        print()

    def update_config_files(self):
        """Update .env and bedrock_agentcore_config.json with real supervisor IDs."""
        print("[Config] Updating configuration files...")

        script_dir = os.path.dirname(os.path.abspath(__file__))

        # --- .env ---
        env_path = os.path.join(script_dir, '.env')
        env_updates = {
            "BEDROCK_AGENT_ID": self.supervisor_id,
            "BEDROCK_AGENT_ALIAS_ID": self.supervisor_alias_id,
            "BEDROCK_KB_ID": self.kb_id,
        }
        try:
            with open(env_path, "r") as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                replaced = False
                for key, val in env_updates.items():
                    if line.strip().startswith(f"{key}="):
                        new_lines.append(f"{key}={val}\n")
                        replaced = True
                        break
                if not replaced:
                    new_lines.append(line)
            with open(env_path, "w") as f:
                f.writelines(new_lines)
            print("  OK  .env updated with supervisor agent IDs")
        except FileNotFoundError:
            print("  WARN .env not found — skipping")

        # --- bedrock_agentcore_config.json ---
        config_path = os.path.join(script_dir, 'infrastructure', 'bedrock_agentcore_config.json')
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            config['agent']['agent_id'] = self.supervisor_id
            config['agent']['agent_alias_id'] = self.supervisor_alias_id
            config['knowledge_base']['kb_id'] = self.kb_id
            config['multi_agent'] = {
                'architecture': 'SUPERVISOR',
                'description': 'Supervisor delegates to 3 specialized sub-agents',
                'supervisor': {
                    'agent_id': self.supervisor_id,
                    'alias_id': self.supervisor_alias_id,
                    'model': FOUNDATION_MODEL,
                },
                'sub_agents': {
                    sub['name']: {
                        'agent_id': sub['agent_id'],
                        'alias_id': sub['alias_id'],
                        'alias_arn': sub['alias_arn'],
                    } for sub in self.sub_agents
                }
            }
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
            print("  OK  bedrock_agentcore_config.json updated with multi-agent topology")
        except Exception as e:
            print(f"  WARN Config update: {e}")

    def redeploy_stack(self):
        """Rebuild and redeploy SAM stack with real Bedrock supervisor IDs."""
        print("\n[Deploy] Redeploying SAM stack with supervisor agent IDs...")
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Build first
        print("  Building...")
        build_cmd = ".venv313\\Scripts\\sam.exe build --template-file infrastructure/template.yaml"
        build_result = subprocess.run(build_cmd, shell=True, cwd=script_dir)
        if build_result.returncode != 0:
            print("  WARN sam build had issues — trying deploy anyway")

        # Deploy with supervisor IDs
        print("  Deploying with supervisor agent IDs...")
        deploy_cmd = (
            f".venv313\\Scripts\\sam.exe deploy "
            f"--stack-name smart-rural-ai --region {REGION} "
            f"--s3-bucket smart-rural-ai-{ACCOUNT_ID} --s3-prefix sam-artifacts "
            f"--capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset "
            f"--parameter-overrides "
            f'"OpenWeatherApiKey={os.environ.get("OPENWEATHER_API_KEY", "PLACEHOLDER")} '
            f"BedrockAgentId={self.supervisor_id} "
            f"BedrockAgentAliasId={self.supervisor_alias_id} "
            f'BedrockKBId={self.kb_id}"'
        )
        result = subprocess.run(deploy_cmd, shell=True, cwd=script_dir)
        if result.returncode == 0:
            print("  OK  Stack redeployed with supervisor agent IDs")
        else:
            print("  WARN Deploy had issues — check CloudFormation console")
            print(f"  You can manually deploy with:")
            print(f"    BedrockAgentId={self.supervisor_id}")
            print(f"    BedrockAgentAliasId={self.supervisor_alias_id}")
            print(f"    BedrockKBId={self.kb_id}")


# ═══════════════════════════════════════════════════════════════════
#  Cleanup utility
# ═══════════════════════════════════════════════════════════════════

def cleanup_agents():
    """Delete all agents created by this script. Useful before re-running."""
    client = boto3.client('bedrock-agent', region_name=REGION)
    print("\n[Cleanup] Searching for rural agents to delete...")

    resp = client.list_agents(maxResults=50)
    rural_agents = [
        a for a in resp.get('agentSummaries', [])
        if a['agentName'].startswith('rural-') or a['agentName'] == 'smart-rural-supervisor'
    ]

    if not rural_agents:
        print("  No rural agents found. Nothing to clean up.")
        return

    print(f"  Found {len(rural_agents)} agent(s) to delete:")
    for agent in rural_agents:
        print(f"    - {agent['agentName']} ({agent['agentId']})")

    for agent in rural_agents:
        aid = agent['agentId']
        name = agent['agentName']
        try:
            # Delete aliases first (required before deleting agent)
            aliases = client.list_agent_aliases(agentId=aid).get('agentAliasSummaries', [])
            for alias in aliases:
                if alias['agentAliasName'] != 'default':
                    try:
                        client.delete_agent_alias(agentId=aid, agentAliasId=alias['agentAliasId'])
                        print(f"  OK  Deleted alias '{alias['agentAliasName']}' from {name}")
                    except Exception:
                        pass
                    time.sleep(2)

            # Delete the agent
            client.delete_agent(agentId=aid, skipResourceInUseCheck=True)
            print(f"  OK  Deleted agent: {name}")
            time.sleep(2)
        except Exception as e:
            print(f"  WARN Could not delete {name}: {e}")

    print("\n  Cleanup complete. You can now re-run the setup.")


# ═══════════════════════════════════════════════════════════════════
#  CLI Entry Point
# ═══════════════════════════════════════════════════════════════════

USAGE = """
Smart Rural AI Advisor — Multi-Agent Setup (v2)
================================================

Creates a SUPERVISOR agent coordinating 3 specialized sub-agents:
  - CropAdvisor (crop/pest/irrigation + Knowledge Base)
  - WeatherExpert (real-time weather via OpenWeatherMap)
  - SchemeNavigator (9 government agricultural schemes)

Usage:
    python setup_bedrock_agent.py <knowledge_base_id>     Create multi-agent system
    python setup_bedrock_agent.py --cleanup               Delete all rural agents (for re-run)

Prerequisites:
  1. pip install boto3
  2. AWS CLI configured (aws configure)
  3. Create the Knowledge Base in the Bedrock Console:
     https://ap-south-1.console.aws.amazon.com/bedrock/home?region=ap-south-1#/knowledge-bases
     - Name: smart-rural-farming-kb
     - IAM role: Select existing 'BedrockKBRole'
     - Data source: S3 -> s3://smart-rural-ai-948809294205/knowledge_base/
     - Chunking: Fixed-size, 300 tokens, 20% overlap
     - Embeddings: Titan Text Embeddings V2
     - Vector store: Quick create
     - Sync the data source
  4. Copy the KB ID and run: python setup_bedrock_agent.py <KB_ID>
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(0)

    if sys.argv[1] == '--cleanup':
        cleanup_agents()
        sys.exit(0)

    kb_id = sys.argv[1].strip()
    if len(kb_id) < 5:
        print(f"ERROR: '{kb_id}' doesn't look like a valid Knowledge Base ID.")
        print(USAGE)
        sys.exit(1)

    setup = MultiAgentSetup(kb_id)
    try:
        setup.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted! Some agents may have been partially created.")
        print("To clean up:  python setup_bedrock_agent.py --cleanup")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\nSome agents may have been created. To clean up and retry:")
        print("  python setup_bedrock_agent.py --cleanup")
        print(f"  python setup_bedrock_agent.py {kb_id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
