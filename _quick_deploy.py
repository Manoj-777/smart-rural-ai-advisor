"""Quick deploy: orchestrator only, includes gTTS from previous build."""
import boto3, io, zipfile, os

lambda_client = boto3.client('lambda', region_name='ap-south-1')

buf = io.BytesIO()
src = 'backend/lambdas/agent_orchestrator'

with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src):
        for f in files:
            full = os.path.join(root, f)
            arc = os.path.relpath(full, src)
            if '__pycache__' not in arc:
                zf.write(full, arc)
    # shared utils
    for root, dirs, files in os.walk('backend/utils'):
        for f in files:
            full = os.path.join(root, f)
            arc = os.path.relpath(full, 'backend')
            if '__pycache__' not in arc:
                zf.write(full, arc)

buf.seek(0)
zb = buf.read()
print(f'Zip: {len(zb)//1024} KB')

resp = lambda_client.update_function_code(
    FunctionName='smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM',
    ZipFile=zb
)
print('Deployed:', resp['LastModified'])
