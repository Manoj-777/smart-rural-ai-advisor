import boto3

s3 = boto3.client('s3', region_name='ap-south-1')
bucket = 'smart-rural-ai-frontend-948809294205'

# Download and print index.html
resp = s3.get_object(Bucket=bucket, Key='index.html')
html = resp['Body'].read().decode('utf-8')
print("=== index.html content ===")
print(html)

# Also check the vite config base path
print("\n=== Local dist/index.html ===")
try:
    with open('frontend/dist/index.html', 'r') as f:
        print(f.read())
except FileNotFoundError:
    print("(no local dist)")
