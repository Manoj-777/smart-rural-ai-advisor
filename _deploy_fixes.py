"""
Deploy the agent_orchestrator Lambda with all fixes:
  1. Empty input crash guard
  2. Expanded off-topic keyword list (250+ terms)
  3. System prompt: no "only rice and wheat" + crop reference table
"""
import boto3, zipfile, os, io, tempfile, shutil, subprocess, sys

REGION = 'ap-south-1'
FUNCTION_NAME = 'smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM'

lambda_client = boto3.client('lambda', region_name=REGION)


def _collect_zip_entries(source_dir, deps_dir=None, utils_dir=None):
    """Collect files for ZIP with deterministic overwrite precedence.

    Precedence: deps < source < shared utils
    """
    entries = {}

    if deps_dir and os.path.isdir(deps_dir):
        for root, _, files in os.walk(deps_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                arcname = os.path.relpath(file_path, deps_dir).replace('\\', '/')
                entries[arcname] = file_path

    for root, _, files in os.walk(source_dir):
        for file_name in files:
            if file_name.endswith(('.py', '.json', '.txt')):
                file_path = os.path.join(root, file_name)
                arcname = os.path.relpath(file_path, source_dir).replace('\\', '/')
                entries[arcname] = file_path

    if utils_dir and os.path.isdir(utils_dir):
        for file_name in os.listdir(utils_dir):
            if file_name.endswith('.py'):
                file_path = os.path.join(utils_dir, file_name)
                arcname = f'utils/{file_name}'
                entries[arcname] = file_path

    return entries

def deploy():
    source_dir = os.path.join('backend', 'lambdas', 'agent_orchestrator')
    utils_dir = os.path.join('backend', 'utils')
    requirements_file = os.path.join(source_dir, 'requirements.txt')

    build_dir = tempfile.mkdtemp(prefix='orchestrator-build-')
    deps_dir = os.path.join(build_dir, 'deps')
    os.makedirs(deps_dir, exist_ok=True)

    if os.path.isfile(requirements_file):
        print('Installing dependencies...')
        subprocess.check_call([
            sys.executable,
            '-m', 'pip',
            'install',
            '-r', requirements_file,
            '-t', deps_dir,
            '--upgrade',
            '--no-cache-dir',
        ])

    entries = _collect_zip_entries(source_dir, deps_dir=deps_dir, utils_dir=utils_dir)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for arcname in sorted(entries.keys()):
            zf.write(entries[arcname], arcname)
            if arcname.endswith('.py'):
                print(f'  + {arcname}')

    shutil.rmtree(build_dir, ignore_errors=True)

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
