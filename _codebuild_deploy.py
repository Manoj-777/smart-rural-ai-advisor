"""
Create and run an AWS CodeBuild project to build ARM64 Linux package
for AgentCore Runtime.

Why CodeBuild? The AgentCore Runtime runs on Linux ARM64 (aarch64).
Building from Windows produces incompatible .pyd/.dll binaries.
CodeBuild ARM64 builds natively correct .so files.
"""
import boto3
import json
import time
import zipfile
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
S3_BUCKET = f"smart-rural-ai-{ACCOUNT_ID}"
PROJECT_NAME = "smart-rural-agentcore-arm64"
SOURCE_KEY = "codebuild-source/agentcore-source.zip"
BASE = os.path.dirname(os.path.abspath(__file__))

# CodeBuild service role
CB_ROLE_NAME = "smart-rural-ai-CodeBuildRole"


def ensure_codebuild_role():
    """Create IAM role for CodeBuild if it doesn't exist."""
    iam = boto3.client("iam", region_name=REGION)

    trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "codebuild.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    try:
        resp = iam.get_role(RoleName=CB_ROLE_NAME)
        role_arn = resp["Role"]["Arn"]
        print(f"  Role exists: {role_arn}")
    except iam.exceptions.NoSuchEntityException:
        print(f"  Creating role {CB_ROLE_NAME}...")
        resp = iam.create_role(
            RoleName=CB_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description="CodeBuild role for Smart Rural AI AgentCore ARM64 build",
        )
        role_arn = resp["Role"]["Arn"]
        print(f"  Created: {role_arn}")

        # Wait for propagation
        time.sleep(5)

    # Attach policies
    policies = [
        "arn:aws:iam::aws:policy/AmazonS3FullAccess",
        "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
    ]
    for p in policies:
        try:
            iam.attach_role_policy(RoleName=CB_ROLE_NAME, PolicyArn=p)
        except Exception:
            pass

    # Inline policy for bedrock-agentcore
    agentcore_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:*",
                "bedrock:*",
            ],
            "Resource": "*"
        }]
    }
    try:
        iam.put_role_policy(
            RoleName=CB_ROLE_NAME,
            PolicyName="AgentCoreAccess",
            PolicyDocument=json.dumps(agentcore_policy),
        )
    except Exception as e:
        print(f"  Warning: {e}")

    return role_arn


def upload_source():
    """Upload agent source code to S3 for CodeBuild."""
    print("[2/5] Packaging source code...")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # buildspec
        zf.write(os.path.join(BASE, "buildspec_agentcore.yml"), "buildspec.yml")

        # agentcore files
        agent_dir = os.path.join(BASE, "agentcore")
        for f in os.listdir(agent_dir):
            fp = os.path.join(agent_dir, f)
            if os.path.isfile(fp) and not f.endswith(".pyc"):
                zf.write(fp, f"agentcore/{f}")

    zip_bytes = buf.getvalue()
    mb = len(zip_bytes) / 1024 / 1024
    print(f"  Source zip: {mb:.2f} MB")

    s3 = boto3.client("s3", region_name=REGION)
    s3.put_object(Bucket=S3_BUCKET, Key=SOURCE_KEY, Body=zip_bytes)
    print(f"  Uploaded to s3://{S3_BUCKET}/{SOURCE_KEY}")


def create_or_update_project(role_arn):
    """Create or update CodeBuild project with ARM64 compute."""
    print("[3/5] Setting up CodeBuild project...")
    cb = boto3.client("codebuild", region_name=REGION)

    project_config = dict(
        name=PROJECT_NAME,
        description="Build ARM64 Linux package for AgentCore Runtime",
        source={
            "type": "S3",
            "location": f"{S3_BUCKET}/{SOURCE_KEY}",
            "buildspec": "buildspec.yml",
        },
        artifacts={"type": "NO_ARTIFACTS"},
        environment={
            "type": "ARM_CONTAINER",
            "computeType": "BUILD_GENERAL1_SMALL",
            "image": "aws/codebuild/amazonlinux-aarch64-standard:3.0",
            "privilegedMode": False,
        },
        serviceRole=role_arn,
        timeoutInMinutes=15,
        logsConfig={
            "cloudWatchLogs": {
                "status": "ENABLED",
                "groupName": f"/codebuild/{PROJECT_NAME}",
            }
        },
    )

    try:
        cb.create_project(**project_config)
        print(f"  Created project: {PROJECT_NAME}")
    except cb.exceptions.ResourceAlreadyExistsException:
        cb.update_project(**project_config)
        print(f"  Updated project: {PROJECT_NAME}")
    except Exception as e:
        if "already exists" in str(e):
            cb.update_project(**project_config)
            print(f"  Updated project: {PROJECT_NAME}")
        else:
            raise


def start_build():
    """Start the CodeBuild build and wait for completion."""
    print("[4/5] Starting ARM64 build...")
    cb = boto3.client("codebuild", region_name=REGION)

    resp = cb.start_build(projectName=PROJECT_NAME)
    build_id = resp["build"]["id"]
    print(f"  Build ID: {build_id}")
    print(f"  Console: https://{REGION}.console.aws.amazon.com/codesuite/codebuild/{ACCOUNT_ID}/projects/{PROJECT_NAME}/build/{build_id.replace(':', '%3A')}")

    # Poll for completion
    print("  Waiting for build to complete...")
    for i in range(90):  # 15 min max
        time.sleep(10)
        detail = cb.batch_get_builds(ids=[build_id])
        build = detail["builds"][0]
        phase = build.get("currentPhase", "?")
        status = build.get("buildStatus", "IN_PROGRESS")

        if i % 3 == 0:  # Print every 30s
            elapsed = (i + 1) * 10
            print(f"  [{elapsed}s] Phase: {phase}, Status: {status}")

        if status != "IN_PROGRESS":
            print(f"\n  Build finished: {status}")
            # Print phase details
            for p in build.get("phases", []):
                pname = p.get("phaseType", "?")
                pstatus = p.get("phaseStatus", "?")
                dur = p.get("durationInSeconds", 0)
                print(f"    {pname}: {pstatus} ({dur}s)")
                for ctx in p.get("contexts", []):
                    if ctx.get("message"):
                        print(f"      {ctx['message'][:200]}")

            return status == "SUCCEEDED", build_id

    print("  Build timed out after 15 min")
    return False, build_id


def print_build_logs(build_id):
    """Print the last build logs."""
    logs = boto3.client("logs", region_name=REGION)
    log_group = f"/codebuild/{PROJECT_NAME}"

    try:
        streams = logs.describe_log_streams(
            logGroupName=log_group, orderBy="LastEventTime",
            descending=True, limit=1,
        )
        if streams.get("logStreams"):
            stream = streams["logStreams"][0]["logStreamName"]
            events = logs.get_log_events(
                logGroupName=log_group, logStreamName=stream,
                limit=100,
            )
            print("\n=== Build Logs (last 100 events) ===")
            for e in events.get("events", []):
                print(f"  {e['message'].rstrip()}")
    except Exception as e:
        print(f"  Could not fetch logs: {e}")


def main():
    print("=" * 60)
    print("  CodeBuild ARM64 Agent Deployment")
    print("=" * 60)

    print("\n[1/5] Ensuring IAM role...")
    role_arn = ensure_codebuild_role()

    upload_source()

    # Small delay for role propagation
    time.sleep(3)

    create_or_update_project(role_arn)

    succeeded, build_id = start_build()

    if succeeded:
        print("\n[5/5] Verifying runtime status...")
        ac = boto3.client("bedrock-agentcore-control", region_name=REGION)
        detail = ac.get_agent_runtime(agentRuntimeId="SmartRuralAdvisor-lcQ47nFSPm")
        status = detail.get("status", "?")
        print(f"  Runtime status: {status}")
        if "FAILED" in (status or ""):
            reason = detail.get("failureReason", "?")
            print(f"  Failure reason: {reason}")
        print("\n=== DONE - SUCCESS ===")
    else:
        print("\n  Build failed. Fetching logs...")
        print_build_logs(build_id)
        print("\n=== DONE - FAILED ===")


if __name__ == "__main__":
    main()
