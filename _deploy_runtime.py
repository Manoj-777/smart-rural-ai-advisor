"""Upload updated source and trigger CodeBuild for ARM64 agent build."""
import boto3, io, zipfile, os, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
S3_BUCKET = f"smart-rural-ai-{ACCOUNT_ID}"
SOURCE_KEY = "codebuild-source/agentcore-source.zip"
BASE = os.path.dirname(os.path.abspath(__file__))

# Upload source
print("Uploading updated source...")
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(os.path.join(BASE, "buildspec_agentcore.yml"), "buildspec.yml")
    agent_dir = os.path.join(BASE, "agentcore")
    for f in os.listdir(agent_dir):
        fp = os.path.join(agent_dir, f)
        if os.path.isfile(fp) and not f.endswith(".pyc"):
            zf.write(fp, f"agentcore/{f}")

s3 = boto3.client("s3", region_name=REGION)
s3.put_object(Bucket=S3_BUCKET, Key=SOURCE_KEY, Body=buf.getvalue())
print(f"  Uploaded ({len(buf.getvalue())/1024:.1f} KB)")

# Start build
cb = boto3.client("codebuild", region_name=REGION)
resp = cb.start_build(projectName="smart-rural-agentcore-arm64")
build_id = resp["build"]["id"]
print(f"Build: {build_id}")
print("Polling...")

for i in range(60):
    time.sleep(10)
    detail = cb.batch_get_builds(ids=[build_id])
    build = detail["builds"][0]
    phase = build.get("currentPhase", "?")
    status = build.get("buildStatus", "IN_PROGRESS")

    if i % 3 == 0:
        print(f"  [{(i+1)*10}s] {phase} / {status}")

    if status != "IN_PROGRESS":
        print(f"\nDone: {status}")
        for p in build.get("phases", []):
            pn = p.get("phaseType", "?")
            ps = p.get("phaseStatus", "?")
            dur = p.get("durationInSeconds", 0)
            ctx_msg = ""
            for ctx in p.get("contexts", []):
                if ctx.get("message"):
                    ctx_msg = f" - {ctx['message'][:150]}"
            print(f"  {pn}: {ps} ({dur}s){ctx_msg}")

        if status == "SUCCEEDED":
            ac = boto3.client("bedrock-agentcore-control", region_name=REGION)
            rt = ac.get_agent_runtime(agentRuntimeId="SmartRuralAdvisor-lcQ47nFSPm")
            print(f"\nRuntime: {rt.get('status')}")
            if rt.get("failureReason"):
                print(f"  Reason: {rt['failureReason']}")
        break
import zipfile
import time

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
AGENT_NAME = "SmartRuralAdvisor"
S3_BUCKET = f"smart-rural-ai-{ACCOUNT_ID}"
S3_PREFIX = "agentcore-code"
RUNTIME_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/smart-rural-ai-AgentCoreRuntimeRole"
AGENT_DIR = os.path.join(os.path.dirname(__file__), "agentcore")

s3 = boto3.client("s3", region_name=REGION)
ac = boto3.client("bedrock-agentcore-control", region_name=REGION)


def create_code_zip():
    """Create a zip of the agentcore/ directory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(AGENT_DIR):
            # Skip __pycache__
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                filepath = os.path.join(root, f)
                arcname = os.path.relpath(filepath, os.path.dirname(AGENT_DIR))
                zf.writestr(arcname, open(filepath, "rb").read())
                print(f"  Added: {arcname}")
    return buf.getvalue()


def upload_to_s3(zip_bytes):
    """Upload code zip to S3."""
    key = f"{S3_PREFIX}/{AGENT_NAME}.zip"
    print(f"\n▸ Uploading to s3://{S3_BUCKET}/{key} ({len(zip_bytes)} bytes)")
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=zip_bytes)
    print(f"  ✓ Uploaded")
    return key


def find_existing_runtime():
    """Check if agent runtime already exists."""
    try:
        resp = ac.list_agent_runtimes(maxResults=50)
        for rt in resp.get("agentRuntimeSummaries", resp.get("items", [])):
            if rt.get("agentRuntimeName") == AGENT_NAME:
                rt_id = rt["agentRuntimeId"]
                detail = ac.get_agent_runtime(agentRuntimeId=rt_id)
                print(f"  Found existing runtime: {rt_id} - {detail.get('status')}")
                return rt_id, detail.get("agentRuntimeArn"), detail.get("status")
    except Exception as e:
        print(f"  list_agent_runtimes error: {e}")
    return None, None, None


def create_runtime(s3_key):
    """Create AgentCore Runtime with code configuration."""
    print(f"\n▸ Creating AgentCore Runtime: {AGENT_NAME}")

    # Check if already exists
    rt_id, rt_arn, status = find_existing_runtime()
    if rt_id:
        if status in ("ACTIVE", "READY"):
            print(f"  ✓ Runtime already exists and is {status}: {rt_arn}")
            return rt_id, rt_arn
        elif status in ("CREATING", "UPDATING"):
            print(f"  Runtime is {status}, waiting...")
        else:
            print(f"  Runtime is {status}, will try to update or recreate")

    if not rt_id:
        try:
            resp = ac.create_agent_runtime(
                agentRuntimeName=AGENT_NAME,
                description="Smart Rural AI Advisor - Indian agriculture assistant",
                agentRuntimeArtifact={
                    "codeConfiguration": {
                        "code": {
                            "s3": {
                                "bucket": S3_BUCKET,
                                "prefix": s3_key,
                            }
                        },
                        "runtime": "PYTHON_3_13",
                        "entryPoint": ["agentcore/agent.py"],
                    }
                },
                roleArn=RUNTIME_ROLE_ARN,
                networkConfiguration={
                    "networkMode": "PUBLIC",
                },
            )
            rt_id = resp.get("agentRuntimeId")
            rt_arn = resp.get("agentRuntimeArn")
            print(f"  ✓ Runtime created: {rt_id}")
            print(f"  ✓ ARN: {rt_arn}")
        except Exception as e:
            print(f"  ✗ create_agent_runtime failed: {e}")
            raise

    # Wait for READY
    print(f"\n  Waiting for runtime to become READY...")
    for i in range(60):
        time.sleep(10)
        detail = ac.get_agent_runtime(agentRuntimeId=rt_id)
        status = detail.get("status", "UNKNOWN")
        rt_arn = detail.get("agentRuntimeArn", rt_arn)
        print(f"    [{(i+1)*10}s] Status: {status}")
        if status in ("ACTIVE", "READY"):
            print(f"  ✓ Runtime is {status}")
            return rt_id, rt_arn
        if status == "FAILED":
            reason = detail.get("statusReason", "unknown")
            print(f"  ✗ Runtime FAILED: {reason}")
            return rt_id, rt_arn

    print(f"  ⚠ Timeout waiting for runtime (last status: {status})")
    return rt_id, rt_arn


def create_endpoint(rt_id):
    """Create a runtime endpoint."""
    print(f"\n▸ Creating Runtime Endpoint for {rt_id}")

    # Check existing endpoints
    try:
        resp = ac.list_agent_runtime_endpoints(agentRuntimeId=rt_id, maxResults=10)
        for ep in resp.get("agentRuntimeEndpointSummaries", resp.get("items", [])):
            ep_id = ep.get("agentRuntimeEndpointId", ep.get("endpointId"))
            detail = ac.get_agent_runtime_endpoint(
                agentRuntimeId=rt_id,
                agentRuntimeEndpointId=ep_id,
            )
            status = detail.get("status", "UNKNOWN")
            arn = detail.get("agentRuntimeEndpointArn", "")
            print(f"  Found existing endpoint: {ep_id} - {status}")
            if status in ("ACTIVE", "READY"):
                print(f"  ✓ Endpoint ARN: {arn}")
                return ep_id, arn
    except Exception as e:
        print(f"  list endpoints error: {e}")

    try:
        resp = ac.create_agent_runtime_endpoint(
            agentRuntimeId=rt_id,
            name=f"{AGENT_NAME}-endpoint",
            description="Default endpoint for Smart Rural AI Advisor",
        )
        ep_id = resp.get("agentRuntimeEndpointId", resp.get("endpointId"))
        ep_arn = resp.get("agentRuntimeEndpointArn", "")
        print(f"  ✓ Endpoint created: {ep_id}")
    except Exception as e:
        if "already exists" in str(e).lower() or "Conflict" in str(e):
            print(f"  Endpoint already exists")
            return None, None
        print(f"  ✗ create_endpoint failed: {e}")
        raise

    # Wait for READY
    print(f"\n  Waiting for endpoint to become READY...")
    for i in range(60):
        time.sleep(10)
        detail = ac.get_agent_runtime_endpoint(
            agentRuntimeId=rt_id,
            agentRuntimeEndpointId=ep_id,
        )
        status = detail.get("status", "UNKNOWN")
        ep_arn = detail.get("agentRuntimeEndpointArn", ep_arn)
        print(f"    [{(i+1)*10}s] Status: {status}")
        if status in ("ACTIVE", "READY"):
            print(f"  ✓ Endpoint is {status}")
            print(f"  ✓ Endpoint ARN: {ep_arn}")
            return ep_id, ep_arn
        if status == "FAILED":
            reason = detail.get("statusReason", "unknown")
            print(f"  ✗ Endpoint FAILED: {reason}")
            return ep_id, ep_arn

    print(f"  ⚠ Timeout (last status: {status})")
    return ep_id, ep_arn


def main():
    print("=" * 60)
    print("  DEPLOY AGENT TO AGENTCORE RUNTIME")
    print("=" * 60)

    # Step 1: Create zip
    print("\n▸ Creating code package...")
    zip_bytes = create_code_zip()

    # Step 2: Upload to S3
    s3_key = upload_to_s3(zip_bytes)

    # Step 3: Create runtime
    rt_id, rt_arn = create_runtime(s3_key)
    if not rt_id:
        print("  ✗ Failed to create runtime")
        return

    # Step 4: Create endpoint
    ep_id, ep_arn = create_endpoint(rt_id)

    # Save config
    config = {
        "agent_runtime_id": rt_id,
        "agent_runtime_arn": rt_arn,
        "endpoint_id": ep_id,
        "endpoint_arn": ep_arn,
        "gateway_id": "smartruralai-gateway-xuba3s0e4i",
        "kb_id": "9X1YUTXNOQ",
    }
    with open("infrastructure/agentcore_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  DEPLOYMENT SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Runtime ID:      {rt_id}")
    print(f"  Runtime ARN:     {rt_arn}")
    print(f"  Endpoint ID:     {ep_id}")
    print(f"  Endpoint ARN:    {ep_arn}")
    print(f"  Gateway ID:      smartruralai-gateway-xuba3s0e4i")
    print(f"  KB ID:           9X1YUTXNOQ")
    print(f"  Config saved to: infrastructure/agentcore_config.json")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
