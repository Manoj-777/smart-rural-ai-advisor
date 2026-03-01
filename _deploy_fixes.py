import boto3, zipfile, os, io

lambda_client = boto3.client('lambda', region_name='ap-south-1')

def deploy_lambda(name, source_dir, function_name):
    print(f'Packaging {name}...')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for f in files:
                fp = os.path.join(root, f)
                arcname = os.path.relpath(fp, source_dir)
                zf.write(fp, arcname)
        utils_dir = 'backend/utils'
        for f in os.listdir(utils_dir):
            if f.endswith('.py'):
                zf.write(os.path.join(utils_dir, f), f'utils/{f}')
    buf.seek(0)
    resp = lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=buf.read()
    )
    print(f'  -> Deployed: {resp["LastModified"]}')

deploy_lambda('agent_orchestrator',
              'backend/lambdas/agent_orchestrator',
              'smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM')

deploy_lambda('crop_advisory',
              'backend/lambdas/crop_advisory',
              'smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY')

print('All done!')
