"""Deploy agent to AgentCore Runtime with ARM64 Linux compatible wheels.

Key findings:
- AgentCore Runtime runs on Linux ARM64 (aarch64)
- Must use --platform manylinux2014_aarch64 for binary packages
- Runtime has boto3/botocore pre-installed (don't include them)
"""
import subprocess, sys, os, io, zipfile, shutil, boto3, time, glob

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
S3_BUCKET = f"smart-rural-ai-{ACCOUNT_ID}"
S3_KEY = "agentcore-code/SmartRuralAdvisor.zip"
RT_ID = "SmartRuralAdvisor-lcQ47nFSPm"
ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/smart-rural-ai-AgentCoreRuntimeRole"
BASE = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(BASE, "agentcore")
TEMP_DIR = os.path.join(BASE, "_pkg_arm64")
LOG = os.path.join(BASE, "_repackage.log")


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()


def install_deps():
    """Install dependencies with ARM64 Linux wheels."""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    req_file = os.path.join(AGENT_DIR, "requirements.txt")
    log(f"[1/4] Installing deps (ARM64 Linux) from {req_file}")

    # Step 1: Download ARM64 binary wheels
    r = subprocess.run(
        [sys.executable, "-m", "pip", "download",
         "-r", req_file, "-d", os.path.join(TEMP_DIR, "_wheels"),
         "--platform", "manylinux2014_aarch64",
         "--only-binary=:all:",
         "--python-version", "3.13",
         "--implementation", "cp"],
        capture_output=True, text=True
    )
    log(f"  pip download rc={r.returncode}")
    if r.returncode != 0:
        log(f"  stderr: {r.stderr[:500]}")
        # Some packages might not have aarch64 wheels; try without platform constraint
        # for pure-python packages
    
    # Step 2: Install from downloaded wheels
    wheels_dir = os.path.join(TEMP_DIR, "_wheels")
    if os.path.exists(wheels_dir):
        r2 = subprocess.run(
            [sys.executable, "-m", "pip", "install",
             "--no-index", "--find-links", wheels_dir,
             "-r", req_file, "-t", TEMP_DIR, "--quiet"],
            capture_output=True, text=True
        )
        log(f"  pip install from wheels rc={r2.returncode}")
        if r2.returncode != 0:
            log(f"  stderr: {r2.stderr[:300]}")
            # Fallback: install pure-python first, then overwrite binaries
            log("  Fallback: two-stage install")
            subprocess.run(
                [sys.executable, "-m", "pip", "install",
                 "-r", req_file, "-t", TEMP_DIR, "--upgrade", "--quiet"],
                capture_output=True, text=True
            )
            # Remove all Windows binary files
            for ext in ("*.pyd", "*.dll", "*.exe"):
                for f in glob.glob(os.path.join(TEMP_DIR, f"**/{ext}"), recursive=True):
                    os.remove(f)
                    log(f"  Removed Windows binary: {os.path.basename(f)}")
            # Install just the binary packages with ARM64
            for pkg in ["pydantic_core", "cryptography"]:
                r3 = subprocess.run(
                    [sys.executable, "-m", "pip", "install",
                     pkg, "-t", TEMP_DIR, "--upgrade", "--quiet",
                     "--platform", "manylinux2014_aarch64",
                     "--only-binary=:all:",
                     "--python-version", "3.13",
                     "--implementation", "cp"],
                    capture_output=True, text=True
                )
                log(f"  ARM64 {pkg}: rc={r3.returncode}")
        shutil.rmtree(wheels_dir, ignore_errors=True)
    else:
        log("  No wheels dir, using fallback two-stage install")
        subprocess.run(
            [sys.executable, "-m", "pip", "install",
             "-r", req_file, "-t", TEMP_DIR, "--upgrade", "--quiet"],
            capture_output=True, text=True
        )
        for ext in ("*.pyd", "*.dll", "*.exe"):
            for f in glob.glob(os.path.join(TEMP_DIR, f"**/{ext}"), recursive=True):
                os.remove(f)
        for pkg in ["pydantic_core"]:
            subprocess.run(
                [sys.executable, "-m", "pip", "install",
                 pkg, "-t", TEMP_DIR, "--upgrade", "--quiet",
                 "--platform", "manylinux2014_aarch64",
                 "--only-binary=:all:",
                 "--python-version", "3.13",
                 "--implementation", "cp"],
                capture_output=True, text=True
            )
            log(f"  ARM64 override for {pkg}")

    # Prune packages already in the runtime or not needed
    prune_dirs = [
        'botocore', 'boto3', 's3transfer',      # available in runtime
        'pythonwin', 'win32', 'win32com',        # Windows only
        'win32comext', 'pywin32_system32',       # Windows only
        'isapi', 'pywin32',                      # Windows only
        'dateutil', 'jmespath', 'urllib3',       # boto3 deps (in runtime)
    ]
    for p in prune_dirs:
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

    # Remove remaining Windows binaries
    for ext in ("*.pyd", "*.dll", "*.exe"):
        for f in glob.glob(os.path.join(TEMP_DIR, f"**/{ext}"), recursive=True):
            os.remove(f)
            log(f"  Removed: {os.path.basename(f)}")

    log("[1/4] Deps installed + pruned OK")


def create_zip():
    """Create zip: agent code at root + deps at root."""
    log("[2/4] Creating zip (agent code at root)...")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Agent code files at root
        agent_files = 0
        for f in os.listdir(AGENT_DIR):
            fp = os.path.join(AGENT_DIR, f)
            if os.path.isfile(fp) and not f.endswith('.pyc'):
                zf.write(fp, f)
                log(f"  Agent: {f}")
                agent_files += 1

        # Dependencies at root
        dep_count = 0
        skip_dirs = {'__pycache__', 'tests', 'test', 'docs', 'examples', 'benchmarks', '_wheels'}
        skip_ext = ('.pyc', '.pyo', '.pyi', '.typed', '.rst', '.md', '.txt')
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
    log(f"[2/4] Zip: {mb:.1f} MB, {agent_files} agent files, {dep_count} dep files")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    return zip_bytes


def upload_and_update(zip_bytes):
    s3 = boto3.client("s3", region_name=REGION)
    ac = boto3.client("bedrock-agentcore-control", region_name=REGION)

    mb = len(zip_bytes) / 1024 / 1024
    log(f"[3/4] Uploading {mb:.1f} MB to S3...")
    s3.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=zip_bytes)
    log("[3/4] Uploaded OK")

    log(f"[4/4] Updating runtime {RT_ID} (entryPoint=['agent.py'])")
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
        return False

    for i in range(60):
        time.sleep(10)
        detail = ac.get_agent_runtime(agentRuntimeId=RT_ID)
        status = detail.get("status", "UNKNOWN")
        log(f"  [{(i+1)*10}s] {status}")
        if status in ("ACTIVE", "READY"):
            log(f"DONE - Runtime is {status}")
            return True
        if "FAILED" in (status or ""):
            reason = detail.get("failureReason", detail.get("statusReason", "?"))
            log(f"FAILED: {reason}")
            return False
    log("TIMEOUT")
    return False


if __name__ == "__main__":
    with open(LOG, "w") as f:
        f.write("")
    log("=== ARM64 REPACKAGE + UPDATE ===")
    install_deps()
    zip_bytes = create_zip()
    ok = upload_and_update(zip_bytes)
    log(f"Result: {'SUCCESS' if ok else 'FAILED'}")
