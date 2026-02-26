"""Repackage agent code with FLAT structure and update AgentCore Runtime.

Fix: agent code (agent.py, tools.py) at ZIP ROOT alongside dependencies.
Entry point: ["agent.py"] (not ["agentcore/agent.py"]).
"""
import subprocess
import sys
import os
import io
import zipfile
import shutil
import boto3
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
S3_BUCKET = f"smart-rural-ai-{ACCOUNT_ID}"
S3_KEY = "agentcore-code/SmartRuralAdvisor.zip"
RT_ID = "SmartRuralAdvisor-lcQ47nFSPm"
ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/smart-rural-ai-AgentCoreRuntimeRole"
AGENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agentcore")
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pkg_temp")


def package():
    """Create zip with agent code at ROOT (not under agentcore/) + deps at ROOT."""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    req_file = os.path.join(AGENT_DIR, "requirements.txt")
    print(f"[1/4] Installing deps from {req_file}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install",
         "-r", req_file, "-t", TEMP_DIR, "--upgrade", "--quiet"],
        check=True,
    )
    print("[1/4] Deps installed OK")

    print("[2/4] Creating FLAT zip (agent code at root)...")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Agent code files - put at ROOT (not under agentcore/)
        agent_files = 0
        for f in os.listdir(AGENT_DIR):
            fp = os.path.join(AGENT_DIR, f)
            if os.path.isfile(fp) and not f.endswith('.pyc'):
                zf.write(fp, f)  # arcname is just filename = at root
                print(f"  Agent: {f}")
                agent_files += 1

        # Dependencies - also at root
        dep_count = 0
        for root, dirs, files in os.walk(TEMP_DIR):
            dirs[:] = [d for d in dirs if d not in ('__pycache__', 'tests', 'test')]
            for f in files:
                if f.endswith('.pyc'):
                    continue
                fp = os.path.join(root, f)
                arc = os.path.relpath(fp, TEMP_DIR)
                zf.write(fp, arc)
                dep_count += 1

    zip_bytes = buf.getvalue()
    mb = len(zip_bytes) / 1024 / 1024
    print(f"[2/4] Zip: {mb:.1f} MB, {agent_files} agent files, {dep_count} dep files")
    shutil.rmtree(TEMP_DIR)
    return zip_bytes


def upload_and_update(zip_bytes):
    s3 = boto3.client("s3", region_name=REGION)
    ac = boto3.client("bedrock-agentcore-control", region_name=REGION)

    print(f"[3/4] Uploading {len(zip_bytes)/1024/1024:.1f} MB to S3...")
    s3.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=zip_bytes)
    print("[3/4] Uploaded OK")

    print(f"[4/4] Updating runtime {RT_ID} with entry point ['agent.py']...")
    try:
        resp = ac.update_agent_runtime(
            agentRuntimeId=RT_ID,
            agentRuntimeArtifact={
                "codeConfiguration": {
                    "code": {"s3": {"bucket": S3_BUCKET, "prefix": S3_KEY}},
                    "runtime": "PYTHON_3_13",
                    "entryPoint": ["agent.py"],  # FIXED: was agentcore/agent.py
                }
            },
            roleArn=ROLE_ARN,
            networkConfiguration={"networkMode": "PUBLIC"},
        )
        print(f"[4/4] Update initiated: {resp.get('status', '?')}")
    except Exception as e:
        print(f"[4/4] FAILED: {e}")
        return False

    for i in range(60):
        time.sleep(10)
        detail = ac.get_agent_runtime(agentRuntimeId=RT_ID)
        status = detail.get("status", "UNKNOWN")
        print(f"  [{(i+1)*10}s] {status}")
        if status in ("ACTIVE", "READY"):
            print(f"DONE - Runtime is {status}")
            return True
        if status == "FAILED":
            reason = detail.get("statusReason", "?")
            print(f"FAILED: {reason}")
            return False
    return False


LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_repackage.log")

def log(msg):
    print(msg, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

if __name__ == "__main__":
    with open(LOG, "w") as f:
        f.write("")
    log("=== REPACKAGE + UPDATE RUNTIME (flat zip) ===")
    zip_bytes = package()
    ok = upload_and_update(zip_bytes)
    log(f"Result: {'SUCCESS' if ok else 'FAILED'}")
