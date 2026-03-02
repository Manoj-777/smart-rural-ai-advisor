import boto3, zipfile, os, io, subprocess, tempfile, shutil

lambda_client = boto3.client('lambda', region_name='ap-south-1')

# Pip dependencies to bundle in the orchestrator Lambda
# gTTS needs: requests, click, charset_normalizer, idna, certifi, urllib3
# Lambda runtime has boto3/botocore but NOT requests or its deps.
ORCHESTRATOR_DEPS = ['gTTS']

# Packages already in Lambda runtime — exclude from zip to save space
LAMBDA_RUNTIME_PKGS = {
    'boto3', 'botocore', 's3transfer', 'jmespath', 'python_dateutil',
    'dateutil', 'six', 'pip', 'setuptools',
}

def deploy_lambda(name, source_dir, function_name, pip_deps=None):
    print(f'Packaging {name}...')
    buf = io.BytesIO()

    # Install pip deps into a temp dir for bundling
    deps_dir = None
    if pip_deps:
        deps_dir = tempfile.mkdtemp(prefix='lambda_deps_')
        print(f'  Installing pip deps: {", ".join(pip_deps)}')
        subprocess.check_call([
            'pip', 'install', '--target', deps_dir, '--no-user',
            '--quiet',
            *pip_deps
        ])

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        added = set()
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for f in files:
                fp = os.path.join(root, f)
                arcname = os.path.relpath(fp, source_dir)
                zf.write(fp, arcname)
                added.add(arcname.replace('\\', '/'))
        # Add shared utils (skip if already in source tree)
        utils_dir = 'backend/utils'
        for f in os.listdir(utils_dir):
            arcname = f'utils/{f}'
            if f.endswith('.py') and arcname not in added:
                zf.write(os.path.join(utils_dir, f), arcname)
                added.add(arcname)
        # Add pip dependencies (skip runtime pkgs and already-present files)
        if deps_dir:
            for root, dirs, files in os.walk(deps_dir):
                rel_root = os.path.relpath(root, deps_dir).replace('\\', '/')
                top_pkg = rel_root.split('/')[0] if rel_root != '.' else ''
                # Skip dist-info, __pycache__, and Lambda runtime packages
                dirs[:] = [d for d in dirs
                           if not d.endswith('.dist-info')
                           and d != '__pycache__'
                           and d.split('-')[0].lower() not in LAMBDA_RUNTIME_PKGS]
                if top_pkg and top_pkg.split('-')[0].lower() in LAMBDA_RUNTIME_PKGS:
                    continue
                for f in files:
                    fp = os.path.join(root, f)
                    arcname = os.path.relpath(fp, deps_dir).replace('\\', '/')
                    if arcname not in added:
                        zf.write(fp, arcname)
                        added.add(arcname)

    if deps_dir:
        shutil.rmtree(deps_dir, ignore_errors=True)

    buf.seek(0)
    zip_bytes = buf.read()
    print(f'  Zip size: {len(zip_bytes) / 1024:.0f} KB')
    resp = lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_bytes
    )
    print(f'  -> Deployed: {resp["LastModified"]}')

deploy_lambda('agent_orchestrator',
              'backend/lambdas/agent_orchestrator',
              'smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM',
              pip_deps=ORCHESTRATOR_DEPS)

deploy_lambda('farmer_profile',
              'backend/lambdas/farmer_profile',
              'smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt')

print('All done!')
