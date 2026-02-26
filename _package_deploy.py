"""Create a properly packaged zip with all dependencies for AgentCore Runtime."""
import subprocess
import sys
import os
import io
import zipfile
import shutil
import boto3
import json
import time

REGION = "ap-south-1"
S3_BUCKET = "smart-rural-ai-948809294205"
S3_KEY = "agentcore-code/SmartRuralAdvisor.zip"
RT_ID = "SmartRuralAdvisor-lcQ47nFSPm"
AGENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agentcore")
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pkg_temp")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_deploy_output.log")


def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")


def package():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    req_file = os.path.join(AGENT_DIR, "requirements.txt")
    log(f"[1/4] Installing deps from {req_file}")
    subprocess.run(
        [sys.executable, "-m", "pip", "install",
         "-r", req_file, "-t", TEMP_DIR, "--upgrade", "--quiet"],
        check=True,
    )
    log("[1/4] Deps installed OK")

    log("[2/4] Creating zip...")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(AGENT_DIR):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                if f.endswith('.pyc'):
                    continue
                fp = os.path.join(root, f)
                arc = os.path.relpath(fp, os.path.dirname(AGENT_DIR))
                zf.write(fp, arc)

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
    log(f"[2/4] Zip: {len(zip_bytes) / 1024 / 1024:.1f} MB, {dep_count} dep files")
    shutil.rmtree(TEMP_DIR)
    return zip_bytes


def upload_and_update(zip_bytes):
    s3 = boto3.client("s3", region_name=REGION)
    ac = boto3.client("bedrock-agentcore-control", region_name=REGION)

    if zip_bytes:
        log("[3/4] Uploading to S3...")
        s3.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=zip_bytes)
        log("[3/4] Uploaded OK")

    log(f"[4/4] Updating runtime {RT_ID}...")
    try:
        resp = ac.update_agent_runtime(
            agentRuntimeId=RT_ID,
            agentRuntimeArtifact={
                "codeConfiguration": {
                    "code": {"s3": {"bucket": S3_BUCKET, "prefix": S3_KEY}},
                    "runtime": "PYTHON_3_13",
                    "entryPoint": ["agentcore/agent.py"],
                }
            },
            roleArn="arn:aws:iam::948809294205:role/smart-rural-ai-AgentCoreRuntimeRole",
            networkConfiguration={"networkMode": "PUBLIC"},
        )
        log(f"[4/4] Update initiated: {resp.get('status', '?')}")
    except Exception as e:
        log(f"[4/4] FAILED: {e}")
        return False

    for i in range(60):
        time.sleep(10)
        detail = ac.get_agent_runtime(agentRuntimeId=RT_ID)
        status = detail.get("status", "UNKNOWN")
        log(f"  [{(i+1)*10}s] {status}")
        if status in ("ACTIVE", "READY"):
            log(f"DONE - Runtime is {status}")
            return True
        if status == "FAILED":
            log(f"FAILED: {detail.get('statusReason', '?')}")
            return False
    return False


if __name__ == "__main__":
    with open(LOG_FILE, "w") as f:
        f.write("")
    log("=== UPDATE RUNTIME (zip already in S3) ===")
    # Skip packaging - already uploaded 37.7 MB zip
    ok = upload_and_update(None)
    log(f"Result: {'SUCCESS' if ok else 'FAILED'}")
