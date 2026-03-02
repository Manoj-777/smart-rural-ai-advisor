"""Deploy agent_orchestrator with gTTS dependency."""
import tempfile, subprocess, sys, os, zipfile, shutil, boto3

tmp = tempfile.mkdtemp(prefix='gtts_')
func_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'lambdas', 'agent_orchestrator')

# Install gTTS (--no-user overrides any pip.conf user=true setting)
print("Installing gTTS...")
env = os.environ.copy()
env['PIP_USER'] = '0'
subprocess.run([sys.executable, '-m', 'pip', 'install', 'gTTS>=2.5.0', '-t', tmp, '--quiet', '--no-user'], check=False, env=env)
# Fallback: try without --no-user if it's not recognized
if not os.listdir(tmp):
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'gTTS>=2.5.0', '-t', tmp, '--quiet'], check=True, env=env)

# Copy Lambda source on top
print("Copying source code...")
for item in os.listdir(func_dir):
    if item.endswith('.zip'):
        continue
    src = os.path.join(func_dir, item)
    dst = os.path.join(tmp, item)
    if os.path.isdir(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)

# Zip
zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_tmp_orchestrator.zip')
print("Zipping...")
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(tmp):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if f.endswith('.pyc'):
                continue
            full = os.path.join(root, f)
            zf.write(full, os.path.relpath(full, tmp))
shutil.rmtree(tmp, ignore_errors=True)
size = os.path.getsize(zip_path) / 1024
print(f"Zip size: {size:.0f} KB")

# Deploy
print("Deploying...")
client = boto3.client('lambda', region_name='ap-south-1')
with open(zip_path, 'rb') as f:
    resp = client.update_function_code(
        FunctionName='smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM',
        ZipFile=f.read(),
        Publish=True
    )
ver = resp.get('Version', 'N/A')
state = resp.get('State', 'Unknown')
print(f"Deployed version {ver} ({state})")
os.remove(zip_path)
print("Done!")
