import boto3, json

s3 = boto3.client('s3', region_name='ap-south-1')
bucket = 'smart-rural-ai-frontend-948809294205'

# 1. Check if bucket exists and list files
print("=== S3 Bucket Contents ===")
try:
    resp = s3.list_objects_v2(Bucket=bucket, MaxKeys=30)
    if 'Contents' in resp:
        for obj in resp['Contents']:
            print(f"  {obj['Key']:50s} {obj['Size']:>8} bytes")
        print(f"\n  Total: {resp['KeyCount']} files")
    else:
        print("  EMPTY — no files uploaded!")
except s3.exceptions.NoSuchBucket:
    print("  BUCKET DOES NOT EXIST!")
except Exception as e:
    print(f"  Error: {e}")

# 2. Check website configuration
print("\n=== Website Config ===")
try:
    ws = s3.get_bucket_website(Bucket=bucket)
    print(f"  Index: {ws.get('IndexDocument', {}).get('Suffix', 'NOT SET')}")
    print(f"  Error: {ws.get('ErrorDocument', {}).get('Key', 'NOT SET')}")
except Exception as e:
    print(f"  {e}")

# 3. Check bucket policy (public access)
print("\n=== Bucket Policy ===")
try:
    pol = s3.get_bucket_policy(Bucket=bucket)
    policy = json.loads(pol['Policy'])
    for stmt in policy.get('Statement', []):
        print(f"  Effect: {stmt.get('Effect')}, Principal: {stmt.get('Principal')}, Action: {stmt.get('Action')}")
except Exception as e:
    print(f"  {e}")

# 4. Check public access block
print("\n=== Public Access Block ===")
try:
    pab = s3.get_public_access_block(Bucket=bucket)
    cfg = pab['PublicAccessBlockConfiguration']
    for k, v in cfg.items():
        print(f"  {k}: {v}")
except Exception as e:
    print(f"  {e}")

# 5. Check if index.html exists and its content type
print("\n=== index.html ===")
try:
    head = s3.head_object(Bucket=bucket, Key='index.html')
    print(f"  Size: {head['ContentLength']} bytes")
    print(f"  Content-Type: {head['ContentType']}")
except Exception as e:
    print(f"  {e}")
