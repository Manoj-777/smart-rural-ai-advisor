"""Repackage agent code with FLAT structure and update AgentCore Runtime.

Fix: agent code (agent.py, tools.py) at ZIP ROOT alongside dependencies.
Entry point: ["agent.py"] (not ["agentcore/agent.py"]).
"""
import subprocess, sys, os, io, zipfile, shutil, boto3, time

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
S3_BUCKET = f"smart-rural-ai-{ACCOUNT_ID}"
S3_KEY = "agentcore-code/SmartRuralAdvisor.zip"
RT_ID = "SmartRuralAdvisor-lcQ47nFSPm"
ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/smart-rural-ai-AgentCoreRuntimeRole"
BASE = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(BASE, "agentcore")
TEMP_DIR = os.path.join(BASE, "_pkg_temp2")
LOG_FILE = os.path.join(BASE, "_repackage.log")

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()

def main():
    with open(LOG_FILE, "w") as f:
        f.write("")

    log("=== REPACKAGE + UPDATE RUNTIME (flat zip) ===")

    # 1) Install deps
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    req_file = os.path.join(AGENT_DIR, "requirements.txt")
    log(f"[1/4] Installing deps from {req_file}")
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install",
         "-r", req_file, "-t", TEMP_DIR, "--upgrade", "--quiet",
         "--platform", "manylinux2014_x86_64",
         "--only-binary=:all:",
         "--python-version", "3.13",
         "--no-deps"],
        capture_output=True, text=True
    )
    # --no-deps won't install transitive deps, so install them separately
    # First install everything normally then prune
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install",
         "-r", req_file, "-t", TEMP_DIR, "--upgrade", "--quiet"],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        log(f"[1/4] FAILED: {r.stderr[:500]}")
        return None
    
    # Remove packages already available in AgentCore runtime or not needed on Linux
    prune_dirs = [
        'botocore', 'boto3', 's3transfer',  # available in runtime
        'pythonwin', 'win32', 'win32com', 'win32comext',  # Windows only
        'pywin32_system32', 'isapi',  # Windows only
        'dateutil',  # available in runtime
        'jmespath',  # available in runtime (boto3 dep)
        'urllib3',   # available in runtime (boto3 dep)
    ]
    import glob
    for pattern in prune_dirs:
        for d in glob.glob(os.path.join(TEMP_DIR, pattern)):
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
                log(f"  Pruned: {os.path.basename(d)}/")
        for d in glob.glob(os.path.join(TEMP_DIR, f"{pattern}-*")):
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
        for d in glob.glob(os.path.join(TEMP_DIR, f"{pattern}*.dist-info")):
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
    # Remove .exe and .dll files (Windows binaries)
    for f in glob.glob(os.path.join(TEMP_DIR, "**/*.exe"), recursive=True):
        os.remove(f)
    for f in glob.glob(os.path.join(TEMP_DIR, "**/*.dll"), recursive=True):
        os.remove(f)
    for f in glob.glob(os.path.join(TEMP_DIR, "bin/*")):
        if os.path.isfile(f):
            os.remove(f)
    
    log("[1/4] Deps installed + pruned OK")

    # 2) Create flat zip
    log("[2/4] Creating FLAT zip (agent code at root)...")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        agent_files = 0
        for f in os.listdir(AGENT_DIR):
            fp = os.path.join(AGENT_DIR, f)
            if os.path.isfile(fp) and not f.endswith('.pyc'):
                zf.write(fp, f)
                log(f"  Agent: {f}")
                agent_files += 1

        dep_count = 0
        skip_dirs = {'__pycache__', 'tests', 'test', 'docs', 'examples', 'benchmarks'}
        skip_suffixes = ('.pyc', '.pyo', '.pyi', '.typed', '.rst', '.md', '.txt')
        for root, dirs, files in os.walk(TEMP_DIR):
            # Also skip dist-info dirs to save space
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.endswith('.dist-info')]
            for f in files:
                if any(f.endswith(s) for s in skip_suffixes):
                    continue
                fp = os.path.join(root, f)
                arc = os.path.relpath(fp, TEMP_DIR)
                zf.write(fp, arc)
                dep_count += 1

    zip_bytes = buf.getvalue()
    mb = len(zip_bytes) / 1024 / 1024
    log(f"[2/4] Zip: {mb:.1f} MB, {agent_files} agent files, {dep_count} dep files")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    # 3) Upload to S3
    s3 = boto3.client("s3", region_name=REGION)
    ac = boto3.client("bedrock-agentcore-control", region_name=REGION)

    log(f"[3/4] Uploading {mb:.1f} MB to s3://{S3_BUCKET}/{S3_KEY}")
    s3.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=zip_bytes)
    log("[3/4] Uploaded OK")

    # 4) Update runtime
    log(f"[4/4] Updating runtime {RT_ID} with entryPoint=['agent.py']")
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

    # Wait for READY
    for i in range(60):
        time.sleep(10)
        detail = ac.get_agent_runtime(agentRuntimeId=RT_ID)
        status = detail.get("status", "UNKNOWN")
        log(f"  [{(i+1)*10}s] {status}")
        if status in ("ACTIVE", "READY"):
            log(f"DONE - Runtime is {status}")
            log("Result: SUCCESS")
            return
        if status == "FAILED":
            reason = detail.get("statusReason", "?")
            log(f"FAILED: {reason}")
            log("Result: FAILED")
            return
    log("TIMEOUT waiting for runtime")
    log("Result: FAILED")

if __name__ == "__main__":
    main()
