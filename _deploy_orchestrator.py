#!/usr/bin/env python3
"""Quick-deploy the AgentOrchestrator Lambda directly (bypasses SAM).
Installs gTTS into the package for free Indic TTS support."""
import zipfile, io, os, subprocess, sys, tempfile, shutil, boto3

REGION = "ap-south-1"
BASE = os.path.dirname(os.path.abspath(__file__))
LAMBDA_DIR = os.path.join(BASE, "backend", "lambdas", "agent_orchestrator")

# --- Install gTTS into a temp dir for bundling ---
deps_dir = tempfile.mkdtemp(prefix="orch_deps_")
try:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "gTTS>=2.5.0",
        "--target", deps_dir,
        "--no-user",
        "--quiet",
    ])
except Exception as e:
    print(f"WARNING: pip install gTTS failed: {e}  (will deploy without gTTS)")
    deps_dir = None

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
    # 1) Lambda source .py files
    for root, dirs, files in os.walk(LAMBDA_DIR):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                fpath = os.path.join(root, f)
                arcname = os.path.relpath(fpath, LAMBDA_DIR)
                zf.write(fpath, arcname)

    # 2) Bundled pip dependencies (gTTS + its deps)
    if deps_dir:
        for root, dirs, files in os.walk(deps_dir):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "pip", "setuptools")]
            for f in files:
                fpath = os.path.join(root, f)
                arcname = os.path.relpath(fpath, deps_dir)
                # skip dist-info, .pyc, tests
                if ".dist-info" in arcname or f.endswith(".pyc"):
                    continue
                zf.write(fpath, arcname)
        shutil.rmtree(deps_dir, ignore_errors=True)

buf.seek(0)
zip_bytes = buf.getvalue()
print(f"Package size: {len(zip_bytes)} bytes ({len(zip_bytes)/1024/1024:.1f} MB)")

client = boto3.client("lambda", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)
funcs = client.list_functions(MaxItems=50)
orch_name = None
for fn in funcs["Functions"]:
    if "AgentOrchestrator" in fn["FunctionName"]:
        orch_name = fn["FunctionName"]
        break

if not orch_name:
    print("ERROR: AgentOrchestrator function not found!")
    for fn in funcs["Functions"]:
        print(f"  - {fn['FunctionName']}")
    exit(1)

resp = client.update_function_code(FunctionName=orch_name, ZipFile=zip_bytes)
print(f"Updated: {orch_name}")
print(f"Last modified: {resp['LastModified']}")
