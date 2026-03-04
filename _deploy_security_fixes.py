"""
Deploy security + cleanup fixes to all affected Lambdas:
  1. Orchestrator — safe error messages (no str(e) leak)
  2. Weather — removed dead Bedrock Agent paths
  3. Crop Advisory — removed dead Bedrock Agent paths + renamed client
  4. Govt Schemes — removed dead Bedrock Agent paths
  5. Transcribe — safe error messages
  6. Farmer Profile — OTP gated behind STAGE, safe delete error messages
"""
import boto3, zipfile, os, io, sys

REGION = 'ap-south-1'
lambda_client = boto3.client('lambda', region_name=REGION)

LAMBDAS = {
    'orchestrator': {
        'function_name': 'smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM',
        'source_dir': os.path.join('backend', 'lambdas', 'agent_orchestrator'),
        'deps_dir': os.path.join('.aws-sam', 'build', 'AgentOrchestratorFunction'),
    },
    'weather': {
        'function_name': 'smart-rural-ai-WeatherFunction-dilSoHSLlXGN',
        'source_dir': os.path.join('backend', 'lambdas', 'weather_lookup'),
        'deps_dir': os.path.join('.aws-sam', 'build', 'WeatherFunction'),
    },
    'crop': {
        'function_name': 'smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY',
        'source_dir': os.path.join('backend', 'lambdas', 'crop_advisory'),
    },
    'schemes': {
        'function_name': 'smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv',
        'source_dir': os.path.join('backend', 'lambdas', 'govt_schemes'),
    },
    'transcribe': {
        'function_name': 'smart-rural-ai-TranscribeSpeechFunction-rF4EDECy1VaO',
        'source_dir': os.path.join('backend', 'lambdas', 'transcribe_speech'),
    },
    'profile': {
        'function_name': 'smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt',
        'source_dir': os.path.join('backend', 'lambdas', 'farmer_profile'),
    },
}


def build_zip(source_dir, extra_deps_dir=None):
    """Build deployment zip from source directory + shared utils overlay.
    If extra_deps_dir is set, also include all files from that directory
    (used for Lambdas that need bundled pip packages like 'requests').
    """
    shared_utils = os.path.join('backend', 'utils')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add bundled pip dependencies first (if any)
        if extra_deps_dir and os.path.isdir(extra_deps_dir):
            for root, dirs, files in os.walk(extra_deps_dir):
                for f in files:
                    if f.endswith(('.py', '.pem', '.txt', '.typed')):
                        fp = os.path.join(root, f)
                        arcname = os.path.relpath(fp, extra_deps_dir)
                        zf.write(fp, arcname)

        # Add Lambda source code (overwrites any same-named files from deps)
        for root, dirs, files in os.walk(source_dir):
            for f in files:
                if f.endswith(('.py', '.json', '.txt')):
                    fp = os.path.join(root, f)
                    arcname = os.path.relpath(fp, source_dir)
                    zf.write(fp, arcname)

        # Overlay shared utils (backend/utils/) — these may have newer
        # versions of helpers than the Lambda-local copies
        if os.path.isdir(shared_utils):
            for f in os.listdir(shared_utils):
                if f.endswith('.py'):
                    zf.write(os.path.join(shared_utils, f), f'utils/{f}')
    return buf.getvalue()


def deploy_lambda(name, config):
    """Deploy a single Lambda function."""
    print(f'\n{"="*50}')
    print(f'Deploying: {name} -> {config["function_name"]}')
    print(f'{"="*50}')

    zip_bytes = build_zip(config['source_dir'], config.get('deps_dir'))
    print(f'  Zip size: {len(zip_bytes)/1024:.1f} KB')

    resp = lambda_client.update_function_code(
        FunctionName=config['function_name'],
        ZipFile=zip_bytes
    )
    print(f'  Done! Last modified: {resp["LastModified"]}')
    print(f'  Code SHA256: {resp["CodeSha256"][:16]}...')
    return True


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(LAMBDAS.keys())

    print(f'Deploying {len(targets)} Lambda(s): {", ".join(targets)}')
    results = {}

    for name in targets:
        if name not in LAMBDAS:
            print(f'\nUnknown Lambda: {name}. Available: {", ".join(LAMBDAS.keys())}')
            continue
        try:
            deploy_lambda(name, LAMBDAS[name])
            results[name] = 'OK'
        except Exception as e:
            print(f'  FAILED: {str(e)}')
            results[name] = f'FAILED: {str(e)}'

    print(f'\n{"="*50}')
    print('DEPLOY SUMMARY')
    print(f'{"="*50}')
    for name, status in results.items():
        print(f'  {name}: {status}')


if __name__ == '__main__':
    main()
