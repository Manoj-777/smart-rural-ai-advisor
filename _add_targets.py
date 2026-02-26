"""Add remaining Lambda targets to the existing Gateway."""
import boto3, json, time

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
GATEWAY_ID = "smartruralai-gateway-xuba3s0e4i"

TARGETS = {
    "smart-rural-ai-crop-advisory": {
        "lambda_name": "smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY",
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
    "smart-rural-ai-weather": {
        "lambda_name": "smart-rural-ai-WeatherFunction-dilSoHSLlXGN",
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
    "smart-rural-ai-govt-schemes": {
        "lambda_name": "smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv",
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
    "smart-rural-ai-farmer-profile": {
        "lambda_name": "smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt",
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

client = boto3.client("bedrock-agentcore-control", region_name=REGION)

# Check existing targets
existing = set()
try:
    resp = client.list_gateway_targets(gatewayIdentifier=GATEWAY_ID, maxResults=50)
    for t in resp.get("items", resp.get("targets", [])):
        existing.add(t.get("name"))
        print(f"  Existing target: {t['name']} ({t['targetId']}) - {t.get('status', '?')}")
except Exception as e:
    print(f"  Could not list targets: {e}")

for target_name, cfg in TARGETS.items():
    if target_name in existing:
        print(f"\n✓ {target_name} already exists, skipping")
        continue

    lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{cfg['lambda_name']}"
    print(f"\n▸ Creating target: {target_name} ({len(cfg['tools'])} tools)")

    try:
        resp = client.create_gateway_target(
            gatewayIdentifier=GATEWAY_ID,
            name=target_name,
            description=f"Lambda tools for {target_name}",
            targetConfiguration={
                "mcp": {
                    "lambda": {
                        "lambdaArn": lambda_arn,
                        "toolSchema": {
                            "inlinePayload": cfg["tools"],
                        },
                    }
                }
            },
            credentialProviderConfigurations=[
                {"credentialProviderType": "GATEWAY_IAM_ROLE"}
            ],
        )
        print(f"  ✓ Created: {resp.get('targetId', 'ok')}")
    except Exception as e:
        if "already exists" in str(e).lower() or "Conflict" in str(e):
            print(f"  ✓ Already exists")
        else:
            print(f"  ✗ Error: {e}")

    time.sleep(3)

# Verify all targets
print("\n\n=== Final target list ===")
resp = client.list_gateway_targets(gatewayIdentifier=GATEWAY_ID, maxResults=50)
for t in resp.get("items", resp.get("targets", [])):
    print(f"  {t['name']} ({t['targetId']}) - {t.get('status', '?')}")

# Save invoke role
print("\nCreating invoke role...")
iam = boto3.client("iam", region_name=REGION)
role_name = "smart-rural-ai-AgentCoreInvokeRole"
trust = {
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Allow", "Principal": {"Service": "bedrock-agentcore.amazonaws.com"}, "Action": "sts:AssumeRole"},
        {"Effect": "Allow", "Principal": {"AWS": f"arn:aws:iam::{ACCOUNT_ID}:user/manoj.rs"}, "Action": "sts:AssumeRole"},
    ],
}
perms = {
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Allow", "Action": "bedrock-agentcore:InvokeGateway", "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{ACCOUNT_ID}:gateway/{GATEWAY_ID}"},
    ],
}
try:
    iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust), Description="Invoke Gateway role")
    print(f"  ✓ Created {role_name}")
except:
    print(f"  ✓ {role_name} exists")
    iam.update_assume_role_policy(RoleName=role_name, PolicyDocument=json.dumps(trust))

iam.put_role_policy(RoleName=role_name, PolicyName="InvokeGatewayPolicy", PolicyDocument=json.dumps(perms))
print("  ✓ Policy attached")
print("\nDone!")
