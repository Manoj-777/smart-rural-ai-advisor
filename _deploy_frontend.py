import boto3, os, json, mimetypes

s3 = boto3.client('s3', region_name='ap-south-1')
bucket_name = 'smart-rural-ai-frontend-948809294205'
dist_dir = 'frontend/dist'

# Step 1: Create bucket
print("Step 1: Creating S3 bucket...")
try:
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'ap-south-1'}
    )
    print(f"  Created bucket: {bucket_name}")
except s3.exceptions.BucketAlreadyOwnedByYou:
    print(f"  Bucket already exists: {bucket_name}")
except Exception as e:
    if 'BucketAlreadyOwnedByYou' in str(e):
        print(f"  Bucket already exists: {bucket_name}")
    else:
        raise

# Step 2: Disable block public access
print("Step 2: Allowing public access...")
s3.put_public_access_block(
    Bucket=bucket_name,
    PublicAccessBlockConfiguration={
        'BlockPublicAcls': False,
        'IgnorePublicAcls': False,
        'BlockPublicPolicy': False,
        'RestrictPublicBuckets': False
    }
)

# Step 3: Set bucket policy for public read
print("Step 3: Setting public read policy...")
policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "PublicReadGetObject",
        "Effect": "Allow",
        "Principal": "*",
        "Action": "s3:GetObject",
        "Resource": f"arn:aws:s3:::{bucket_name}/*"
    }]
}
s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))

# Step 4: Enable static website hosting
print("Step 4: Enabling static website hosting...")
s3.put_bucket_website(
    Bucket=bucket_name,
    WebsiteConfiguration={
        'IndexDocument': {'Suffix': 'index.html'},
        'ErrorDocument': {'Key': 'index.html'}  # SPA: route all 404s to index.html
    }
)

# Step 5: Clean old assets from S3 (remove stale hashed bundles)
print("Step 5: Cleaning old assets...")
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=bucket_name, Prefix='assets/'):
    for obj in page.get('Contents', []):
        s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
print("  Old assets removed")

# Step 6: Upload dist/ files
print("Step 6: Uploading files...")
uploaded = 0
for root, dirs, files in os.walk(dist_dir):
    for f in files:
        local_path = os.path.join(root, f)
        s3_key = os.path.relpath(local_path, dist_dir).replace('\\', '/')
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(local_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Set cache headers - assets have content hashes (long cache), index.html must always revalidate
        cache = 'max-age=31536000, public' if '/assets/' in s3_key else 'no-cache, no-store, must-revalidate'
        
        s3.upload_file(
            local_path, bucket_name, s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': cache
            }
        )
        uploaded += 1
        print(f"  {s3_key} ({content_type})")

url = f"http://{bucket_name}.s3-website.ap-south-1.amazonaws.com"
print(f"\n{'='*60}")
print(f"  DEPLOYED! {uploaded} files uploaded")
print(f"  URL: {url}")
print(f"{'='*60}")
