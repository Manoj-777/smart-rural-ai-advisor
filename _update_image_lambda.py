"""Update image_analysis Lambda with fixed CORS headers."""
import boto3, zipfile, io, os

fn_name = 'smart-rural-ai-ImageAnalysisFunction-wY2rBz7uHgKV'
region = 'ap-south-1'

with open('backend/lambdas/image_analysis/handler.py', encoding='utf-8') as f:
    handler_code = f.read()

utils_dir = 'backend/lambdas/image_analysis/utils'
utils_files = {}
if os.path.isdir(utils_dir):
    for fname in os.listdir(utils_dir):
        if fname.endswith('.py'):
            with open(os.path.join(utils_dir, fname), encoding='utf-8') as f:
                utils_files[fname] = f.read()

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('handler.py', handler_code)
    for fname, code in utils_files.items():
        zf.writestr('utils/' + fname, code)
buf.seek(0)

lam = boto3.client('lambda', region_name=region)
resp = lam.update_function_code(FunctionName=fn_name, ZipFile=buf.read())
print('Updated', fn_name, '— size', resp['CodeSize'], 'bytes')
