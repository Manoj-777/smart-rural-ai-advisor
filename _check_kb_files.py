import boto3, os

s3 = boto3.client('s3', region_name='ap-south-1')
bucket = 'smart-rural-ai-948809294205'
prefix = 'knowledge_base/'

# List files under knowledge_base/ prefix in S3
print("=== Files in S3 (knowledge_base/) ===")
s3_files = set()
resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
if 'Contents' in resp:
    for obj in resp['Contents']:
        key = obj['Key']
        fname = key.replace(prefix, '')
        if fname:
            s3_files.add(fname)
            print(f"  {fname:40s} {obj['Size']:>8} bytes  {obj['LastModified']}")
else:
    print("  (no files found under knowledge_base/)")

# List local files
print("\n=== Local files (data/knowledge_base/) ===")
local_dir = 'data/knowledge_base/'
local_files = set()
for f in os.listdir(local_dir):
    if os.path.isfile(os.path.join(local_dir, f)):
        size = os.path.getsize(os.path.join(local_dir, f))
        local_files.add(f)
        print(f"  {f:40s} {size:>8} bytes")

# Compare
print("\n=== MISSING from S3 ===")
missing = local_files - s3_files
if missing:
    for f in sorted(missing):
        print(f"  MISSING: {f}")
else:
    print("  None — all local files are in S3")

print("\n=== EXTRA in S3 (not local) ===")
extra = s3_files - local_files
if extra:
    for f in sorted(extra):
        print(f"  EXTRA: {f}")
else:
    print("  None")
