#!/usr/bin/env python3
"""
Fix AgentCore IAM Policies — Apply corrected permissions to existing roles.

Run this ONCE to update the runtime/gateway roles with the missing permissions
that were causing AgentCore invocations to fail.

Usage:
    python fix_agentcore_policies.py          # Apply all fixes
    python fix_agentcore_policies.py --check  # Dry-run: show what would change
"""

import json
import sys
import argparse

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("ERROR: boto3 required → pip install boto3")
    sys.exit(1)

# ── Config (must match setup_agentcore.py) ──
REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
PROJECT_NAME = "smart-rural-ai"

LAMBDA_ARNS = [
    f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY",
    f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:smart-rural-ai-WeatherFunction-dilSoHSLlXGN",
    f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv",
    f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt",
]


def get_corrected_runtime_policy():
    """The complete, corrected runtime role inline policy."""
    return {
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
                "Resource": LAMBDA_ARNS,
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


def get_corrected_gateway_policy():
    """The complete, corrected gateway execution role inline policy."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "lambda:InvokeFunction",
                "Resource": LAMBDA_ARNS,
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


def get_corrected_runtime_trust():
    """Trust policy for the runtime role."""
    return {
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


def check_role(iam, role_name):
    """Check if a role exists and return its current inline policy."""
    try:
        iam.get_role(RoleName=role_name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            return False
        raise


def diff_policy(iam, role_name, policy_name, new_policy):
    """Compare current vs new policy."""
    try:
        current = iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        current_doc = current["PolicyDocument"]
        # Normalize for comparison
        current_str = json.dumps(current_doc, sort_keys=True, indent=2)
        new_str = json.dumps(new_policy, sort_keys=True, indent=2)
        if current_str == new_str:
            return False, "No changes needed"
        return True, f"Policy differs — will update"
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            return True, "Policy does not exist — will create"
        raise


def apply_fixes(dry_run=False):
    iam = boto3.client("iam", region_name=REGION)

    roles_to_fix = [
        {
            "role_name": f"{PROJECT_NAME}-AgentCoreRuntimeRole",
            "policy_name": "AgentCoreRuntimePolicy",
            "new_policy": get_corrected_runtime_policy(),
            "trust_policy": get_corrected_runtime_trust(),
            "managed_policies": ["arn:aws:iam::aws:policy/AmazonBedrockFullAccess"],
        },
        {
            "role_name": f"{PROJECT_NAME}-AgentCoreGatewayRole",
            "policy_name": "AgentCoreGatewayPolicy",
            "new_policy": get_corrected_gateway_policy(),
            "trust_policy": None,
            "managed_policies": [],
        },
    ]

    print("=" * 60)
    print("  AGENTCORE POLICY FIX" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)

    all_ok = True

    for role_info in roles_to_fix:
        role_name = role_info["role_name"]
        policy_name = role_info["policy_name"]
        new_policy = role_info["new_policy"]

        print(f"\n▸ Role: {role_name}")

        exists = check_role(iam, role_name)
        if not exists:
            print(f"  ✗ Role does NOT exist — run setup_agentcore.py first")
            all_ok = False
            continue

        print(f"  ✓ Role exists")

        # Check inline policy
        needs_update, reason = diff_policy(iam, role_name, policy_name, new_policy)
        print(f"  Inline policy '{policy_name}': {reason}")

        if needs_update and not dry_run:
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(new_policy),
            )
            print(f"  ✓ Updated inline policy")

        # Check trust policy
        if role_info.get("trust_policy"):
            if not dry_run:
                iam.update_assume_role_policy(
                    RoleName=role_name,
                    PolicyDocument=json.dumps(role_info["trust_policy"]),
                )
                print(f"  ✓ Updated trust policy")
            else:
                print(f"  Trust policy: will update")

        # Check managed policies
        for managed_arn in role_info.get("managed_policies", []):
            try:
                attached = iam.list_attached_role_policies(RoleName=role_name)
                already_attached = any(
                    p["PolicyArn"] == managed_arn
                    for p in attached.get("AttachedPolicies", [])
                )
                if already_attached:
                    print(f"  ✓ Managed policy already attached: {managed_arn.split('/')[-1]}")
                elif not dry_run:
                    iam.attach_role_policy(RoleName=role_name, PolicyArn=managed_arn)
                    print(f"  ✓ Attached managed policy: {managed_arn.split('/')[-1]}")
                else:
                    print(f"  Managed policy: will attach {managed_arn.split('/')[-1]}")
            except ClientError as e:
                print(f"  ⚠ Could not handle managed policy {managed_arn.split('/')[-1]}: {e}")

    # ── Summary of what was fixed ──
    print("\n" + "=" * 60)
    print("  PERMISSIONS ADDED/FIXED:")
    print("=" * 60)
    print("""
  Runtime Role:
    + bedrock:Converse, bedrock:ConverseStream     (was missing — agent uses converse API)
    + arn:aws:bedrock:*:ACCOUNT:inference-profile/* (cross-region inference models)
    + arn:aws:bedrock:*::foundation-model/*         (all-region foundation models)
    + bedrock:Retrieve, bedrock:RetrieveAndGenerate (Knowledge Base access)
    + translate:TranslateText                       (multilingual support)
    + comprehend:DetectDominantLanguage              (language detection)
    + polly:SynthesizeSpeech                         (voice output)

  Gateway Role:
    + bedrock-agentcore:ListGatewayTargets          (target enumeration)
""")

    if dry_run:
        print("  → Re-run without --check to apply these changes.\n")
    else:
        if all_ok:
            print("  ✓ All policies updated successfully!")
            print("  → Redeploy the agent:  agentcore deploy")
            print("  → Redeploy SAM stack:  sam deploy\n")
        else:
            print("  ⚠ Some roles missing — run setup_agentcore.py first.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix AgentCore IAM policies")
    parser.add_argument("--check", action="store_true", help="Dry run — show what would change")
    args = parser.parse_args()
    apply_fixes(dry_run=args.check)
