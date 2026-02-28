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
    # Bundle requests + dependencies
    deps_dir = 'build_weather_deps'
    for dep_folder in ['requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna']:
        dep_path = os.path.join(deps_dir, dep_folder)
        if os.path.isdir(dep_path):
            for root, dirs, files in os.walk(dep_path):
                for f in files:
                    fp = os.path.join(root, f)
                    arcname = os.path.relpath(fp, deps_dir)
                    zf.write(fp, arcname)
buf.seek(0)
print(f'Package size: {buf.getbuffer().nbytes / 1024:.0f} KB')
resp = lc.update_function_code(
    FunctionName='smart-rural-ai-WeatherFunction-dilSoHSLlXGN',
    ZipFile=buf.read()
)
print('Weather Lambda deployed:', resp['LastModified'])
