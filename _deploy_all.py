"""
Deploy all Lambda functions from local code to AWS.
Handles dependency bundling for agent_orchestrator (gTTS) and weather_lookup (requests).
"""
import boto3
import os
import sys
import zipfile
import subprocess
import shutil
import tempfile

REGION = 'ap-south-1'
BASE = os.path.dirname(os.path.abspath(__file__))
LAMBDAS_DIR = os.path.join(BASE, 'backend', 'lambdas')

# Map: logical name -> (physical function name, has external deps)
FUNCTIONS = {
    'agent_orchestrator': ('smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM', True),
    'crop_advisory':      ('smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY', False),
    'farmer_profile':     ('smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt', False),
    'govt_schemes':       ('smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv', False),
    'image_analysis':     ('smart-rural-ai-ImageAnalysisFunction-wY2rBz7uHgKV', False),
    'transcribe_speech':  ('smart-rural-ai-TranscribeSpeechFunction-rF4EDECy1VaO', False),
    'weather_lookup':     ('smart-rural-ai-WeatherFunction-dilSoHSLlXGN', True),
}

lambda_client = boto3.client('lambda', region_name=REGION)


def install_deps(requirements_txt, target_dir):
    """Install pip dependencies into target directory."""
    print(f"    Installing dependencies from {os.path.basename(requirements_txt)}...")
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', requirements_txt,
         '-t', target_dir, '--no-deps-warning', '--quiet', '--platform', 'manylinux2014_x86_64',
         '--only-binary=:all:'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        # Fallback without platform constraint
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', requirements_txt,
             '-t', target_dir, '--quiet'],
            capture_output=True, text=True
        )
    if result.returncode != 0:
        print(f"    WARNING: pip install failed: {result.stderr[:200]}")
        return False
    return True


def zip_lambda(func_dir, func_name, has_deps):
    """Create a zip file for a Lambda function."""
    zip_path = os.path.join(BASE, f'_tmp_{func_name}.zip')

    if has_deps:
        # Create temp dir, install deps, then add source code
        tmp_dir = tempfile.mkdtemp(prefix=f'lambda_{func_name}_')
        try:
            req_file = os.path.join(func_dir, 'requirements.txt')
            if os.path.exists(req_file):
                # Check if requirements actually have packages
                with open(req_file) as f:
                    has_packages = any(
                        line.strip() and not line.strip().startswith('#')
                        for line in f.readlines()
                    )
                if has_packages:
                    # For weather_lookup, use pre-built deps if available
                    if func_name == 'weather_lookup':
                        weather_deps = os.path.join(BASE, 'build_weather_deps')
                        if os.path.exists(weather_deps):
                            print(f"    Using pre-built weather deps from build_weather_deps/")
                            for item in os.listdir(weather_deps):
                                src = os.path.join(weather_deps, item)
                                dst = os.path.join(tmp_dir, item)
                                if os.path.isdir(src):
                                    shutil.copytree(src, dst)
                                else:
                                    shutil.copy2(src, dst)
                        else:
                            install_deps(req_file, tmp_dir)
                    else:
                        install_deps(req_file, tmp_dir)

            # Copy Lambda source code on top
            for item in os.listdir(func_dir):
                if item.endswith('.zip') or item.startswith('_tmp_'):
                    continue
                src = os.path.join(func_dir, item)
                dst = os.path.join(tmp_dir, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

            # Zip everything
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(tmp_dir):
                    # Skip __pycache__ and .dist-info
                    dirs[:] = [d for d in dirs if d != '__pycache__']
                    for f in files:
                        if f.endswith('.pyc'):
                            continue
                        full = os.path.join(root, f)
                        arcname = os.path.relpath(full, tmp_dir)
                        zf.write(full, arcname)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    else:
        # Simple zip - just handler.py + utils/
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(func_dir):
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for f in files:
                    if f.endswith(('.pyc', '.zip')):
                        continue
                    full = os.path.join(root, f)
                    arcname = os.path.relpath(full, func_dir)
                    zf.write(full, arcname)

    size = os.path.getsize(zip_path) / 1024
    return zip_path, size


def deploy_function(func_name, aws_name, zip_path):
    """Deploy a zip to a Lambda function."""
    with open(zip_path, 'rb') as f:
        zip_bytes = f.read()

    # Check size - if > 50MB, need to use S3
    if len(zip_bytes) > 50 * 1024 * 1024:
        print(f"    ERROR: Zip is {len(zip_bytes)/1024/1024:.1f}MB (>50MB limit)")
        return False

    response = lambda_client.update_function_code(
        FunctionName=aws_name,
        ZipFile=zip_bytes,
        Publish=True
    )
    version = response.get('Version', 'N/A')
    state = response.get('State', 'Unknown')
    print(f"    Deployed version {version} ({state})")
    return True


def main():
    print("=" * 60)
    print("  Smart Rural AI Advisor — Deploy All Lambdas")
    print("=" * 60)

    successes = []
    failures = []

    for func_name, (aws_name, has_deps) in FUNCTIONS.items():
        func_dir = os.path.join(LAMBDAS_DIR, func_name)
        if not os.path.exists(func_dir):
            print(f"\n[SKIP] {func_name} — directory not found")
            failures.append(func_name)
            continue

        print(f"\n[{func_name}] → {aws_name}")
        try:
            print(f"  Zipping...")
            zip_path, size_kb = zip_lambda(func_dir, func_name, has_deps)
            print(f"    Zip size: {size_kb:.0f} KB")

            print(f"  Deploying...")
            if deploy_function(func_name, aws_name, zip_path):
                successes.append(func_name)
            else:
                failures.append(func_name)
        except Exception as e:
            print(f"    ERROR: {e}")
            failures.append(func_name)
        finally:
            # Clean up temp zip
            tmp_zip = os.path.join(BASE, f'_tmp_{func_name}.zip')
            if os.path.exists(tmp_zip):
                os.remove(tmp_zip)

    print(f"\n{'=' * 60}")
    print(f"  Results: {len(successes)}/{len(FUNCTIONS)} deployed successfully")
    if failures:
        print(f"  Failed: {', '.join(failures)}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
