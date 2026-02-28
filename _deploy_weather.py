import boto3, zipfile, io, os

lc = boto3.client('lambda', region_name='ap-south-1')
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    src = 'backend/lambdas/weather_lookup'
    for root, dirs, files in os.walk(src):
        for f in files:
            fp = os.path.join(root, f)
            zf.write(fp, os.path.relpath(fp, src))
    for f in os.listdir('backend/utils'):
        if f.endswith('.py'):
            zf.write(os.path.join('backend/utils', f), 'utils/' + f)
buf.seek(0)
resp = lc.update_function_code(
    FunctionName='smart-rural-ai-WeatherFunction-dilSoHSLlXGN',
    ZipFile=buf.read()
)
print('Weather Lambda deployed:', resp['LastModified'])
