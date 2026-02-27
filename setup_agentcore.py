#!/usr/bin/env python3
"""
Smart Rural AI Advisor — AgentCore Setup & Deployment Script

This script automates the complete setup of Amazon Bedrock AgentCore:
  1. Creates an AgentCore Gateway with IAM auth
  2. Adds Lambda functions as Gateway targets (MCP tools)
  3. Creates IAM roles for Gateway execution and invocation
  4. Configures and deploys the agent to AgentCore Runtime
  5. Sets up AgentCore Memory (STM + LTM)
  6. Updates SAM template with AgentCore ARN

Prerequisites:
  - AWS CLI configured with ap-south-1
  - pip install bedrock-agentcore strands-agents bedrock-agentcore-starter-toolkit boto3
  - Existing SAM-deployed Lambda functions

Usage:
    python setup_agentcore.py                  # Full setup
    python setup_agentcore.py --gateway-only   # Only create Gateway + targets
    python setup_agentcore.py --deploy-only    # Only deploy agent (Gateway already exists)
    python setup_agentcore.py --status         # Check deployment status
    python setup_agentcore.py --cleanup        # Delete all AgentCore resources
"""

import json
import sys
import time
import os
import argparse
import subprocess

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("ERROR: boto3 is required. Install with:  pip install boto3")
    sys.exit(1)


# ━━━━━━━━━━━━━━━━━━━━━━ Configuration ━━━━━━━━━━━━━━━━━━━━━━

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
PROJECT_NAME = "smart-rural-ai"
GATEWAY_NAME = "SmartRuralAI-Gateway"
AGENT_NAME = "smart-rural-ai-advisor"

# Existing Lambda functions (from deployed SAM stack)
LAMBDA_FUNCTIONS = {
    "crop_advisory": {
        "name": "smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY",
        "tools": [
            {
                "name": "get_crop_advisory",
                "description": "Get crop advisory guidance for Indian agriculture including crop selection, growing conditions, varieties, and best practices based on region, soil type, and season.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "crop": {"type": "string", "description": "Crop name (e.g., Rice, Wheat, Cotton)"},
                        "state": {"type": "string", "description": "Indian state (e.g., Tamil Nadu)"},
                        "season": {"type": "string", "description": "Growing season (Kharif, Rabi, Summer)"},
                        "soil_type": {"type": "string", "description": "Soil type (Clay loam, Sandy, Red soil)"},
                        "query": {"type": "string", "description": "Free-text farming question"},
                    },
                },
            },
            {
                "name": "get_pest_alert",
                "description": "Identify crop pests and diseases with treatment recommendations. Provides both organic and chemical treatments.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "crop": {"type": "string", "description": "Name of affected crop"},
                        "symptoms": {"type": "string", "description": "Symptom description (yellow leaves, brown spots)"},
                        "state": {"type": "string", "description": "Indian state for regional pest patterns"},
                        "season": {"type": "string", "description": "Current season"},
                    },
                },
            },
            {
                "name": "get_irrigation_advice",
                "description": "Get irrigation recommendations including scheduling, water needs, and methods (drip, sprinkler, flood) for specific crops.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "crop": {"type": "string", "description": "Crop name"},
                        "location": {"type": "string", "description": "Location for weather-based advice"},
                        "soil_type": {"type": "string", "description": "Soil type"},
                        "query": {"type": "string", "description": "Irrigation-specific question"},
                    },
                },
            },
        ],
    },
    "weather": {
        "name": "smart-rural-ai-WeatherFunction-dilSoHSLlXGN",
        "tools": [
            {
                "name": "get_weather",
                "description": "Get real-time weather data with farming advisory for any Indian location. Returns current conditions, 5-day forecast, and farming recommendations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City or district in India (e.g., Chennai, Guntur)"},
                    },
                    "required": ["location"],
                },
            },
        ],
    },
    "govt_schemes": {
        "name": "smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv",
        "tools": [
            {
                "name": "search_schemes",
                "description": "Search Indian government agricultural schemes, subsidies, insurance, and loan programs with eligibility and application steps.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "Search term (insurance, subsidy, drip, loan)"},
                        "category": {"type": "string", "description": "Category filter (insurance, credit, irrigation)"},
                    },
                },
            },
        ],
    },
    "farmer_profile": {
        "name": "smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt",
        "tools": [
            {
                "name": "get_farmer_profile",
                "description": "Look up a farmer's saved profile including location, crops, soil type, and farming details for personalized advice.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "farmer_id": {"type": "string", "description": "Unique farmer identifier"},
                    },
                    "required": ["farmer_id"],
                },
            },
        ],
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━ Helper Functions ━━━━━━━━━━━━━━━━━━━━━━

def wait_with_spinner(seconds, message="Waiting"):
    """Show a spinner while waiting."""
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    for i in range(seconds * 2):
        print(f"\r  {spinner[i % len(spinner)]} {message}... ({i // 2 + 1}s)", end="", flush=True)
        time.sleep(0.5)
    print(f"\r  ✓ {message} — done ({seconds}s)")


def run_command(cmd, check=True):
    """Run a shell command and return output."""
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  ✗ Command failed: {result.stderr}")
        return None
    return result.stdout.strip()


# ━━━━━━━━━━━━━━━━━━━━━━ IAM Setup ━━━━━━━━━━━━━━━━━━━━━━

class IAMSetup:
    """Create IAM roles for AgentCore Gateway and Runtime."""

    def __init__(self):
        self.iam = boto3.client("iam", region_name=REGION)
        self.sts = boto3.client("sts", region_name=REGION)

    def get_current_identity(self):
        """Get the current caller's ARN."""
        return self.sts.get_caller_identity()["Arn"]

    def create_gateway_execution_role(self):
        """
        Create IAM role that Gateway assumes to invoke Lambda targets.
        """
        role_name = f"{PROJECT_NAME}-AgentCoreGatewayRole"
        print(f"\n▸ Creating Gateway execution role: {role_name}")

        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock-agentcore.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        # Permissions to invoke our Lambda functions
        lambda_arns = [
            f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{fn['name']}"
            for fn in LAMBDA_FUNCTIONS.values()
        ]

        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "lambda:InvokeFunction",
                    "Resource": lambda_arns,
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:InvokeGateway",
                        "bedrock-agentcore:GetGateway",
                        "bedrock-agentcore:ListGatewayTargets",
                    ],
                    "Resource": "*",
                },
            ],
        }

        try:
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="AgentCore Gateway execution role for Smart Rural AI",
                Tags=[{"Key": "Project", "Value": PROJECT_NAME}],
            )
            role_arn = response["Role"]["Arn"]
            print(f"  ✓ Created role: {role_arn}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "EntityAlreadyExists":
                role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
                print(f"  ✓ Role exists: {role_arn}")
                # Update trust policy
                self.iam.update_assume_role_policy(
                    RoleName=role_name,
                    PolicyDocument=json.dumps(trust_policy),
                )
            else:
                raise

        # Attach inline policy
        self.iam.put_role_policy(
            RoleName=role_name,
            PolicyName="AgentCoreGatewayPolicy",
            PolicyDocument=json.dumps(permissions_policy),
        )
        print(f"  ✓ Attached inline policy")

        wait_with_spinner(10, "Waiting for IAM propagation")
        return role_arn

    def create_gateway_invoke_role(self, gateway_id):
        """
        Create IAM role for invoking the Gateway (used by agents/orchestrator).
        """
        role_name = f"{PROJECT_NAME}-AgentCoreInvokeRole"
        print(f"\n▸ Creating Gateway invoke role: {role_name}")

        current_arn = self.get_current_identity()
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock-agentcore.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                },
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": current_arn
                    },
                    "Action": "sts:AssumeRole",
                },
            ],
        }

        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "bedrock-agentcore:InvokeGateway",
                    "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{ACCOUNT_ID}:gateway/{gateway_id}",
                }
            ],
        }

        try:
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="AgentCore Gateway invoke role for Smart Rural AI",
                Tags=[{"Key": "Project", "Value": PROJECT_NAME}],
            )
            role_arn = response["Role"]["Arn"]
            print(f"  ✓ Created role: {role_arn}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "EntityAlreadyExists":
                role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
                print(f"  ✓ Role exists: {role_arn}")
                self.iam.update_assume_role_policy(
                    RoleName=role_name,
                    PolicyDocument=json.dumps(trust_policy),
                )
            else:
                raise

        self.iam.put_role_policy(
            RoleName=role_name,
            PolicyName="InvokeGatewayPolicy",
            PolicyDocument=json.dumps(permissions_policy),
        )
        print(f"  ✓ Attached inline policy")

        wait_with_spinner(10, "Waiting for IAM propagation")
        return role_arn

    def create_runtime_execution_role(self):
        """
        Create IAM role for AgentCore Runtime (the agent execution role).
        Needs: Bedrock model invoke, Lambda invoke, S3 access, DynamoDB, etc.
        """
        role_name = f"{PROJECT_NAME}-AgentCoreRuntimeRole"
        print(f"\n▸ Creating Runtime execution role: {role_name}")

        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock-agentcore.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        lambda_arns = [
            f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{fn['name']}"
            for fn in LAMBDA_FUNCTIONS.values()
        ]

        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockModelAccess",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                        "bedrock:Converse",
                        "bedrock:ConverseStream",
                    ],
                    "Resource": [
                        f"arn:aws:bedrock:{REGION}::foundation-model/*",
                        f"arn:aws:bedrock:us-*::foundation-model/*",
                        f"arn:aws:bedrock:*:{ACCOUNT_ID}:inference-profile/*",
                        "arn:aws:bedrock:*::foundation-model/*",
                    ],
                },
                {
                    "Sid": "BedrockKnowledgeBase",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:Retrieve",
                        "bedrock:RetrieveAndGenerate",
                    ],
                    "Resource": [
                        f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:knowledge-base/*",
                    ],
                },
                {
                    "Sid": "LambdaInvoke",
                    "Effect": "Allow",
                    "Action": "lambda:InvokeFunction",
                    "Resource": lambda_arns,
                },
                {
                    "Sid": "AgentCoreAccess",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:*",
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "CloudWatchLogs",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    "Resource": f"arn:aws:logs:{REGION}:{ACCOUNT_ID}:*",
                },
                {
                    "Sid": "S3Access",
                    "Effect": "Allow",
                    "Action": ["s3:GetObject", "s3:PutObject"],
                    "Resource": f"arn:aws:s3:::smart-rural-ai-{ACCOUNT_ID}/*",
                },
                {
                    "Sid": "DynamoDBAccess",
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:Query",
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/farmer_profiles",
                        f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/chat_sessions",
                    ],
                },
                {
                    "Sid": "TranslatePollyAccess",
                    "Effect": "Allow",
                    "Action": [
                        "translate:TranslateText",
                        "comprehend:DetectDominantLanguage",
                        "polly:SynthesizeSpeech",
                    ],
                    "Resource": "*",
                },
            ],
        }

        try:
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="AgentCore Runtime execution role for Smart Rural AI",
                Tags=[{"Key": "Project", "Value": PROJECT_NAME}],
            )
            role_arn = response["Role"]["Arn"]
            print(f"  ✓ Created role: {role_arn}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "EntityAlreadyExists":
                role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
                print(f"  ✓ Role exists: {role_arn}")
                self.iam.update_assume_role_policy(
                    RoleName=role_name,
                    PolicyDocument=json.dumps(trust_policy),
                )
            else:
                raise

        self.iam.put_role_policy(
            RoleName=role_name,
            PolicyName="AgentCoreRuntimePolicy",
            PolicyDocument=json.dumps(permissions_policy),
        )
        print(f"  ✓ Attached inline policy")

        # Also attach managed policies for Bedrock access
        managed_policies = [
            "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
        ]
        for managed_policy in managed_policies:
            try:
                self.iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=managed_policy,
                )
                print(f"  ✓ Attached: {managed_policy.split('/')[-1]}")
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "NoSuchEntity":
                    print(f"  ⚠ Managed policy not found: {managed_policy.split('/')[-1]} — skipping")
                elif error_code == "AccessDeniedException":
                    print(f"  ⚠ No permission to attach: {managed_policy.split('/')[-1]} — inline policy covers essentials")
                else:
                    print(f"  ⚠ Could not attach {managed_policy.split('/')[-1]}: {error_code} — {e}")

        wait_with_spinner(10, "Waiting for IAM propagation")
        return role_arn


# ━━━━━━━━━━━━━━━━━━━━━━ Gateway Setup ━━━━━━━━━━━━━━━━━━━━━━

class GatewaySetup:
    """Create AgentCore Gateway and register Lambda functions as MCP tool targets."""

    def __init__(self):
        self.client = boto3.client("bedrock-agentcore-control", region_name=REGION)
        self.gateway_id = None
        self.gateway_url = None

    def create_gateway(self, role_arn):
        """Create the AgentCore Gateway with IAM auth."""
        print(f"\n▸ Creating AgentCore Gateway: {GATEWAY_NAME}")

        # First check if already exists
        existing = self._find_existing_gateway()
        if existing[0]:
            print(f"  ✓ Gateway already exists: {self.gateway_id}")
            return existing

        try:
            response = self.client.create_gateway(
                name=GATEWAY_NAME,
                roleArn=role_arn,
                protocolType="MCP",
                authorizerType="AWS_IAM",
                description="Smart Rural AI Advisor — Exposes farming tools as MCP-compatible endpoints",
            )
            self.gateway_id = response.get("gatewayId", response.get("id", ""))
            print(f"  ✓ Gateway create initiated: {self.gateway_id}")

            # Wait for ACTIVE
            for i in range(24):
                time.sleep(5)
                gw = self.client.get_gateway(gatewayIdentifier=self.gateway_id)
                status = gw.get("status", "UNKNOWN")
                self.gateway_url = gw.get("gatewayUrl", "")
                print(f"    [{(i+1)*5}s] Status: {status}")
                if status == "ACTIVE":
                    break
                if status in ("FAILED", "DELETE_IN_PROGRESS"):
                    print(f"  ✗ Gateway failed: {gw.get('failureReason', 'unknown')}")
                    return None, None

            print(f"  ✓ Gateway URL: {self.gateway_url}")
            return self.gateway_id, self.gateway_url

        except ClientError as e:
            if "ConflictException" in str(type(e).__name__) or "already exists" in str(e).lower():
                print(f"  ℹ Gateway already exists. Listing...")
                return self._find_existing_gateway()
            raise

    def _find_existing_gateway(self):
        """Find existing gateway by name."""
        try:
            response = self.client.list_gateways(maxResults=50)
            for gw in response.get("items", response.get("gateways", [])):
                if gw.get("name") == GATEWAY_NAME:
                    self.gateway_id = gw["gatewayId"]
                    # Get full details for URL
                    detail = self.client.get_gateway(gatewayIdentifier=self.gateway_id)
                    self.gateway_url = detail.get("gatewayUrl", "")
                    return self.gateway_id, self.gateway_url
        except ClientError:
            pass
        return None, None

    def add_lambda_target(self, function_key, function_config):
        """Add a Lambda function as a Gateway target with tool schema."""
        if not self.gateway_id:
            print("  ✗ No gateway ID — create gateway first")
            return

        function_name = function_config["name"]
        lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{function_name}"
        tools = function_config["tools"]

        target_name = f"{PROJECT_NAME}-{function_key}".replace("_", "-")
        print(f"\n▸ Adding Lambda target: {target_name} ({len(tools)} tools)")

        target_config = {
            "mcp": {
                "lambda": {
                    "lambdaArn": lambda_arn,
                    "toolSchema": {
                        "inlinePayload": tools,
                    },
                }
            }
        }

        credential_config = [
            {"credentialProviderType": "GATEWAY_IAM_ROLE"}
        ]

        try:
            response = self.client.create_gateway_target(
                gatewayIdentifier=self.gateway_id,
                name=target_name,
                description=f"Lambda tools for {function_key}",
                targetConfiguration=target_config,
                credentialProviderConfigurations=credential_config,
            )
            target_id = response.get("targetId", response.get("id", "created"))
            print(f"  ✓ Target created: {target_id}")

            # Wait for target to become ACTIVE
            time.sleep(5)
            return target_id

        except ClientError as e:
            if "ConflictException" in str(e) or "already exists" in str(e).lower():
                print(f"  ℹ Target already exists, skipping")
                return None
            print(f"  ✗ Failed: {e}")
            raise

    def add_all_targets(self):
        """Register all Lambda functions as Gateway targets."""
        print("\n" + "=" * 60)
        print("  ADDING LAMBDA FUNCTIONS AS GATEWAY MCP TARGETS")
        print("=" * 60)

        for key, config in LAMBDA_FUNCTIONS.items():
            self.add_lambda_target(key, config)
            time.sleep(3)  # Avoid throttling

        print(f"\n  ✓ All targets registered. Gateway URL: {self.gateway_url}")


# ━━━━━━━━━━━━━━━━━━━━━━ AgentCore Deploy ━━━━━━━━━━━━━━━━━━━━━━

class AgentCoreDeploy:
    """Deploy the Strands Agent to AgentCore Runtime using the starter toolkit CLI."""

    def __init__(self, runtime_role_arn=None):
        self.runtime_role_arn = runtime_role_arn
        self.agent_dir = os.path.join(os.path.dirname(__file__), "agentcore")

    def configure(self):
        """Run agentcore configure."""
        print("\n" + "=" * 60)
        print("  CONFIGURING AGENTCORE RUNTIME DEPLOYMENT")
        print("=" * 60)

        cmd = f"agentcore configure -e agentcore/agent.py -r {REGION}"
        if self.runtime_role_arn:
            cmd += f" --execution-role {self.runtime_role_arn}"
        cmd += " --disable-memory"  # Start without memory, add later

        print(f"\n  Running: {cmd}")
        print("  (Accept default values when prompted)\n")

        result = subprocess.run(cmd, shell=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            print("\n  ✓ Configuration complete")
        else:
            print("\n  ✗ Configuration failed — you may need to run this interactively")
            print(f"  Try manually:  cd {os.path.dirname(__file__)} && {cmd}")

    def deploy(self):
        """Run agentcore deploy (uses CodeBuild, no Docker needed)."""
        print("\n" + "=" * 60)
        print("  DEPLOYING AGENT TO AGENTCORE RUNTIME")
        print("=" * 60)

        cmd = "agentcore deploy"
        print(f"\n  Running: {cmd}")
        print("  (This builds via AWS CodeBuild and deploys — may take 3-5 minutes)\n")

        result = subprocess.run(cmd, shell=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            print("\n  ✓ Deployment complete!")
            self._print_agent_info()
        else:
            print("\n  ✗ Deployment failed")
            print("  Check CloudWatch logs for details")

    def _print_agent_info(self):
        """Read the .bedrock_agentcore.yaml for agent ARN."""
        yaml_path = os.path.join(os.path.dirname(__file__), ".bedrock_agentcore.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path) as f:
                content = f.read()
            print(f"\n  Agent config saved to: {yaml_path}")
            # Try to extract ARN
            for line in content.split("\n"):
                if "arn" in line.lower():
                    print(f"  {line.strip()}")

    def status(self):
        """Check deployment status."""
        cmd = "agentcore status"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                cwd=os.path.dirname(__file__))
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

    def invoke_test(self, prompt="What crops should I plant in Tamil Nadu during Kharif season?"):
        """Test the deployed agent."""
        payload = json.dumps({
            "prompt": prompt,
            "farmer_id": "test_farmer",
            "session_id": "test_session",
        })
        cmd = f"agentcore invoke '{payload}'"
        print(f"\n▸ Testing agent with: {prompt}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                cwd=os.path.dirname(__file__))
        if result.stdout:
            print(f"  Response: {result.stdout[:500]}")
        if result.stderr:
            print(f"  Error: {result.stderr[:300]}")

    def destroy(self):
        """Clean up AgentCore Runtime resources."""
        cmd = "agentcore destroy"
        print(f"\n▸ Destroying AgentCore Runtime...")
        subprocess.run(cmd, shell=True, cwd=os.path.dirname(__file__))
        print("  ✓ Runtime resources cleaned up")


# ━━━━━━━━━━━━━━━━━━━━━━ Config File Manager ━━━━━━━━━━━━━━━━━━━━━━

class ConfigManager:
    """Manage the AgentCore configuration file."""

    CONFIG_FILE = os.path.join(
        os.path.dirname(__file__), "infrastructure", "agentcore_config.json"
    )

    @classmethod
    def save(cls, gateway_id, gateway_url, agent_arn=None, runtime_role=None):
        """Save AgentCore resource IDs."""
        config = {
            "project": PROJECT_NAME,
            "region": REGION,
            "account_id": ACCOUNT_ID,
            "gateway": {
                "gateway_id": gateway_id,
                "gateway_url": gateway_url,
            },
            "runtime": {
                "agent_arn": agent_arn or "PENDING_DEPLOYMENT",
                "runtime_role": runtime_role or "",
            },
            "lambda_functions": {
                k: v["name"] for k, v in LAMBDA_FUNCTIONS.items()
            },
        }
        os.makedirs(os.path.dirname(cls.CONFIG_FILE), exist_ok=True)
        with open(cls.CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        print(f"\n  ✓ Config saved: {cls.CONFIG_FILE}")
        return config

    @classmethod
    def load(cls):
        """Load saved config."""
        if os.path.exists(cls.CONFIG_FILE):
            with open(cls.CONFIG_FILE) as f:
                return json.load(f)
        return None


# ━━━━━━━━━━━━━━━━━━━━━━ Cleanup ━━━━━━━━━━━━━━━━━━━━━━

def cleanup_all():
    """Delete all AgentCore resources."""
    print("\n" + "=" * 60)
    print("  CLEANING UP AGENTCORE RESOURCES")
    print("=" * 60)

    iam = boto3.client("iam", region_name=REGION)

    # Destroy runtime
    deployer = AgentCoreDeploy()
    deployer.destroy()

    # Delete Gateway
    try:
        gw_client = boto3.client("bedrock-agentcore-control", region_name=REGION)
        response = gw_client.list_gateways(maxResults=50)
        for gw in response.get("items", response.get("gateways", [])):
            if gw.get("name") == GATEWAY_NAME:
                # Delete targets first
                targets = gw_client.list_gateway_targets(gatewayIdentifier=gw["gatewayId"])
                for target in targets.get("items", targets.get("targets", [])):
                    print(f"  Deleting target: {target.get('name')}")
                    gw_client.delete_gateway_target(
                        gatewayIdentifier=gw["gatewayId"],
                        targetIdentifier=target["targetId"],
                    )
                    time.sleep(2)

                print(f"  Deleting gateway: {GATEWAY_NAME}")
                gw_client.delete_gateway(gatewayIdentifier=gw["gatewayId"])
                print(f"  ✓ Gateway deleted")
    except Exception as e:
        print(f"  ℹ Gateway cleanup: {e}")

    # Delete IAM roles
    for role_name in [
        f"{PROJECT_NAME}-AgentCoreGatewayRole",
        f"{PROJECT_NAME}-AgentCoreInvokeRole",
        f"{PROJECT_NAME}-AgentCoreRuntimeRole",
    ]:
        try:
            # Delete inline policies
            policies = iam.list_role_policies(RoleName=role_name)
            for policy in policies.get("PolicyNames", []):
                iam.delete_role_policy(RoleName=role_name, PolicyName=policy)

            # Detach managed policies
            attached = iam.list_attached_role_policies(RoleName=role_name)
            for policy in attached.get("AttachedPolicies", []):
                iam.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

            iam.delete_role(RoleName=role_name)
            print(f"  ✓ Deleted role: {role_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchEntity":
                print(f"  ℹ Role cleanup ({role_name}): {e}")

    print("\n  ✓ Cleanup complete")


# ━━━━━━━━━━━━━━━━━━━━━━ Main ━━━━━━━━━━━━━━━━━━━━━━

def main():
    parser = argparse.ArgumentParser(
        description="Smart Rural AI Advisor — AgentCore Setup & Deployment"
    )
    parser.add_argument(
        "--gateway-only", action="store_true",
        help="Only create Gateway + register Lambda targets"
    )
    parser.add_argument(
        "--deploy-only", action="store_true",
        help="Only deploy agent to AgentCore Runtime (Gateway must exist)"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Check deployment status"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Test the deployed agent"
    )
    parser.add_argument(
        "--cleanup", action="store_true",
        help="Delete all AgentCore resources"
    )
    args = parser.parse_args()

    # ── Handle special modes ──
    if args.cleanup:
        cleanup_all()
        return

    if args.status:
        deployer = AgentCoreDeploy()
        deployer.status()
        return

    if args.test:
        deployer = AgentCoreDeploy()
        deployer.invoke_test()
        return

    # ── Banner ──
    print("=" * 60)
    print("  SMART RURAL AI ADVISOR — AgentCore Setup")
    print("=" * 60)
    print(f"  Region:   {REGION}")
    print(f"  Account:  {ACCOUNT_ID}")
    print(f"  Gateway:  {GATEWAY_NAME}")
    print(f"  Lambdas:  {len(LAMBDA_FUNCTIONS)} functions")
    print("=" * 60)

    iam_setup = IAMSetup()

    if not args.deploy_only:
        # ── Step 1: Create IAM Roles ──
        print("\n" + "─" * 40)
        print("  STEP 1: IAM Roles")
        print("─" * 40)
        gw_role_arn = iam_setup.create_gateway_execution_role()
        runtime_role_arn = iam_setup.create_runtime_execution_role()

        # ── Step 2: Create Gateway ──
        print("\n" + "─" * 40)
        print("  STEP 2: AgentCore Gateway")
        print("─" * 40)
        gateway = GatewaySetup()
        gateway_id, gateway_url = gateway.create_gateway(gw_role_arn)

        if not gateway_id:
            print("\n  ✗ Gateway creation failed. Aborting.")
            sys.exit(1)

        # ── Step 3: Register Lambda targets ──
        print("\n" + "─" * 40)
        print("  STEP 3: Register Lambda Targets")
        print("─" * 40)
        gateway.add_all_targets()

        # ── Step 4: Create invoke role ──
        invoke_role_arn = iam_setup.create_gateway_invoke_role(gateway_id)

        # ── Save config ──
        ConfigManager.save(gateway_id, gateway_url, runtime_role=runtime_role_arn)

        if args.gateway_only:
            print("\n" + "=" * 60)
            print("  GATEWAY SETUP COMPLETE")
            print(f"  Gateway ID:  {gateway_id}")
            print(f"  Gateway URL: {gateway_url}")
            print("=" * 60)
            print("\n  Next: python setup_agentcore.py --deploy-only")
            return
    else:
        # Load saved config
        config = ConfigManager.load()
        if config:
            runtime_role_arn = config["runtime"].get("runtime_role", "")
        else:
            runtime_role_arn = None

    # ── Step 5: Deploy Agent to Runtime ──
    print("\n" + "─" * 40)
    print("  STEP 4: Deploy to AgentCore Runtime")
    print("─" * 40)
    deployer = AgentCoreDeploy(runtime_role_arn)
    deployer.configure()
    deployer.deploy()

    # ── Step 6: Test ──
    print("\n" + "─" * 40)
    print("  STEP 5: Test Deployed Agent")
    print("─" * 40)
    deployer.invoke_test()

    # ── Summary ──
    print("\n" + "=" * 60)
    print("  SETUP COMPLETE!")
    print("=" * 60)
    print(f"""
  AgentCore Resources Created:
    • Gateway: {GATEWAY_NAME}
    • Lambda targets: {len(LAMBDA_FUNCTIONS)} registered as MCP tools
    • Agent: Deployed to AgentCore Runtime

  Commands:
    agentcore status              # Check agent status
    agentcore invoke '{{"prompt": "..."}}'  # Test agent
    python setup_agentcore.py --cleanup  # Remove everything

  Next Steps:
    1. Get the agent ARN from: .bedrock_agentcore.yaml
    2. Update agent_orchestrator Lambda to call invoke_agent_runtime()
    3. Redeploy SAM stack with the agent ARN
""")


if __name__ == "__main__":
    main()
