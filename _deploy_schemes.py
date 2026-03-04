import boto3, zipfile, io, os

zf = io.BytesIO()
with zipfile.ZipFile(zf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write('backend/lambdas/govt_schemes/handler.py', 'handler.py')
    for root, dirs, files in os.walk('backend/utils'):
        for f in files:
            fp = os.path.join(root, f)
            arcname = os.path.join('utils', f)
            z.write(fp, arcname)
zf.seek(0)

client = boto3.client('lambda', region_name='ap-south-1')
resp = client.update_function_code(
    FunctionName='smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv',
    ZipFile=zf.read()
)
print(f"Deployed {resp['FunctionName']} -- {resp['LastModified']}")
