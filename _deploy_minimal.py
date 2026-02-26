"""Ultra-minimal agent for testing AgentCore Runtime initialization."""
import subprocess, sys, os, io, zipfile, boto3, time

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
S3_BUCKET = f"smart-rural-ai-{ACCOUNT_ID}"
S3_KEY = "agentcore-code/SmartRuralAdvisor.zip"
RT_ID = "SmartRuralAdvisor-lcQ47nFSPm"
ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/smart-rural-ai-AgentCoreRuntimeRole"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_repackage.log")

MINIMAL_AGENT = '''
import json
import logging
import sys
import os
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("minimal-agent")
logger.info(f"MINIMAL AGENT LOADING - Python {sys.version}")

from bedrock_agentcore import BedrockAgentCoreApp

logger.info(f"BedrockAgentCoreApp imported OK at {time.time()}")

app = BedrockAgentCoreApp()
logger.info("App created - registering entrypoint")

@app.entrypoint
def invoke(payload: dict) -> dict:
    prompt = payload.get("prompt", "Hello!")
    logger.info(f"Received: {prompt[:100]}")
    return {
        "result": f"Echo: {prompt}. This is a minimal test response from Smart Rural AI Advisor.",
        "tools_used": [],
        "session_id": payload.get("session_id", "test"),
        "farmer_id": payload.get("farmer_id", "anonymous"),
    }

if __name__ == "__main__":
    app.run()
'''

MINIMAL_TOOLS = '''
# placeholder - no tools in minimal mode
'''

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\\n")
        f.flush()

def main():
    with open(LOG, "w") as f:
        f.write("")

    log("=== MINIMAL AGENT DEPLOY ===")

    # Only bedrock-agentcore (no strands, no boto3 since runtime has it)
    TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pkg_min")
    import shutil
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    log("[1/4] Installing bedrock-agentcore only (Linux x86_64 wheels)...")
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install",
         "bedrock-agentcore", "-t", TEMP_DIR, "--upgrade", "--quiet",
         "--platform", "manylinux2014_x86_64",
         "--only-binary=:all:",
         "--python-version", "3.13",
         "--implementation", "cp"],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        log(f"[1/4] binary install issue: {r.stderr[:300]}")
        # Fallback: install pure-python packages normally, then overwrite binaries
        r2 = subprocess.run(
            [sys.executable, "-m", "pip", "install",
             "bedrock-agentcore", "-t", TEMP_DIR, "--upgrade", "--quiet"],
            capture_output=True, text=True
        )
        if r2.returncode != 0:
            log(f"[1/4] FAILED: {r2.stderr[:500]}")
            return
        # Now overwrite just pydantic_core with Linux binary
        r3 = subprocess.run(
            [sys.executable, "-m", "pip", "install",
             "pydantic_core", "-t", TEMP_DIR, "--upgrade", "--quiet",
             "--platform", "manylinux2014_x86_64",
             "--only-binary=:all:",
             "--python-version", "3.13",
             "--implementation", "cp"],
            capture_output=True, text=True
        )
        log(f"[1/4] pydantic_core linux overwrite: rc={r3.returncode}")

    # Prune heavy unnecessary deps
    prune = ['botocore', 'boto3', 's3transfer', 'pythonwin', 'win32',
             'win32com', 'win32comext', 'pywin32_system32', 'isapi',
             'dateutil', 'jmespath', 'urllib3', 'strands', 'cryptography',
             'pywin32']
    import glob
    for p in prune:
        for d in glob.glob(os.path.join(TEMP_DIR, p)):
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
                log(f"  Pruned: {os.path.basename(d)}/")
        for d in glob.glob(os.path.join(TEMP_DIR, f"{p}-*")):
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
        for d in glob.glob(os.path.join(TEMP_DIR, f"{p}*.dist-info")):
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
    for ext in ("*.exe", "*.dll"):
        for f in glob.glob(os.path.join(TEMP_DIR, f"**/{ext}"), recursive=True):
            os.remove(f)
    log("[1/4] Done")

    # Create zip
    log("[2/4] Creating minimal zip...")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("agent.py", MINIMAL_AGENT)
        zf.writestr("tools.py", MINIMAL_TOOLS)

        dep_count = 0
        skip_dirs = {'__pycache__', 'tests', 'test', 'docs', 'examples'}
        skip_ext = ('.pyc', '.pyo', '.pyi', '.rst', '.md', '.txt')
        for root, dirs, files in os.walk(TEMP_DIR):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.endswith('.dist-info')]
            for f in files:
                if any(f.endswith(s) for s in skip_ext):
                    continue
                fp = os.path.join(root, f)
                arc = os.path.relpath(fp, TEMP_DIR)
                zf.write(fp, arc)
                dep_count += 1

    zip_bytes = buf.getvalue()
    mb = len(zip_bytes) / 1024 / 1024
    log(f"[2/4] Zip: {mb:.1f} MB, {dep_count} dep files")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    # Upload + update
    s3 = boto3.client("s3", region_name=REGION)
    ac = boto3.client("bedrock-agentcore-control", region_name=REGION)

    log(f"[3/4] Uploading {mb:.1f} MB to S3...")
    s3.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=zip_bytes)
    log("[3/4] Uploaded OK")

    log(f"[4/4] Updating runtime {RT_ID}")
    try:
        resp = ac.update_agent_runtime(
            agentRuntimeId=RT_ID,
            agentRuntimeArtifact={
                "codeConfiguration": {
                    "code": {"s3": {"bucket": S3_BUCKET, "prefix": S3_KEY}},
                    "runtime": "PYTHON_3_13",
                    "entryPoint": ["agent.py"],
                }
            },
            roleArn=ROLE_ARN,
            networkConfiguration={"networkMode": "PUBLIC"},
        )
        log(f"[4/4] Update initiated: {resp.get('status', '?')}")
    except Exception as e:
        log(f"[4/4] FAILED: {e}")
        return

    for i in range(30):
        time.sleep(10)
        detail = ac.get_agent_runtime(agentRuntimeId=RT_ID)
        status = detail.get("status", "UNKNOWN")
        log(f"  [{(i+1)*10}s] {status}")
        if status in ("ACTIVE", "READY"):
            log(f"DONE - Runtime is {status}")
            log("Result: SUCCESS")
            return
        if status == "FAILED":
            log(f"FAILED: {detail.get('statusReason', '?')}")
            return
    log("TIMEOUT")

if __name__ == "__main__":
    main()
