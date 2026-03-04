"""
Deploy the agent_orchestrator Lambda with all fixes:
  1. Empty input crash guard
  2. Expanded off-topic keyword list (250+ terms)
  3. System prompt: no "only rice and wheat" + crop reference table
"""
import boto3, zipfile, os, io

REGION = 'ap-south-1'
FUNCTION_NAME = 'smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM'

lambda_client = boto3.client('lambda', region_name=REGION)

def deploy():
    source_dir = os.path.join('backend', 'lambdas', 'agent_orchestrator')
    utils_dir = os.path.join('backend', 'utils')

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add all files from agent_orchestrator/
        for root, dirs, files in os.walk(source_dir):
            for f in files:
                if f.endswith(('.py', '.json', '.txt')):
                    fp = os.path.join(root, f)
                    arcname = os.path.relpath(fp, source_dir)
                    zf.write(fp, arcname)
                    print(f'  + {arcname}')

        # Add shared utils/
        if os.path.isdir(utils_dir):
            for f in os.listdir(utils_dir):
                if f.endswith('.py'):
                    zf.write(os.path.join(utils_dir, f), f'utils/{f}')
                    print(f'  + utils/{f}')

    zip_bytes = buf.getvalue()
    print(f'\nZip size: {len(zip_bytes)/1024:.1f} KB')

    print(f'Deploying to {FUNCTION_NAME}...')
    resp = lambda_client.update_function_code(
        FunctionName=FUNCTION_NAME,
        ZipFile=zip_bytes
    )
    print(f'Done! Last modified: {resp["LastModified"]}')
    print(f'Code SHA256: {resp["CodeSha256"][:16]}...')

if __name__ == '__main__':
    deploy()
