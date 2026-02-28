import boto3, os, mimetypes

s3 = boto3.client('s3', region_name='ap-south-1')
bucket = 'smart-rural-ai-frontend-948809294205'
base = os.path.dirname(os.path.abspath(__file__))
dist_dir = os.path.join(base, 'frontend', 'dist')

# 1. Delete all existing files in the bucket first (clean deploy)
print("=== Cleaning bucket ===")
resp = s3.list_objects_v2(Bucket=bucket)
if 'Contents' in resp:
    for obj in resp['Contents']:
        key = obj['Key']
        if key.startswith('audio/') or key.startswith('knowledge_base/') or key.startswith('agentcore-code/'):
            continue  # Don't delete non-frontend files
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"  Deleted: {key}")

# 2. Upload all dist files with correct content types
print("\n=== Uploading fresh build ===")
mime_map = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
}

uploaded = 0
for root, dirs, files in os.walk(dist_dir):
    for fname in files:
        filepath = os.path.join(root, fname)
        key = os.path.relpath(filepath, dist_dir).replace('\\', '/')
        
        ext = os.path.splitext(fname)[1].lower()
        content_type = mime_map.get(ext, mimetypes.guess_type(fname)[0] or 'application/octet-stream')
        
        # Add cache headers - assets are hashed so can be cached forever, html should not
        cache = 'max-age=31536000' if '/assets/' in key else 'no-cache, no-store, must-revalidate'
        
        s3.upload_file(
            filepath, bucket, key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': cache
            }
        )
        size = os.path.getsize(filepath)
        print(f"  {key:50s} {size:>8} bytes  ({content_type})")
        uploaded += 1

print(f"\n  Uploaded {uploaded} files")

# 3. Verify website config
ws = s3.get_bucket_website(Bucket=bucket)
print(f"\nWebsite: index={ws['IndexDocument']['Suffix']}, error={ws['ErrorDocument']['Key']}")
print(f"\nS3 URL: http://{bucket}.s3-website.ap-south-1.amazonaws.com")

# 4. CloudFront status + invalidation
cf = boto3.client('cloudfront', region_name='us-east-1')
dists = cf.list_distributions()
for d in dists['DistributionList'].get('Items', []):
    origins = [o['DomainName'] for o in d['Origins']['Items']]
    if any('smart-rural-ai-frontend' in o for o in origins):
        print(f"\nCloudFront: {d['Id']} ({d['Status']})")
        print(f"CloudFront URL: https://{d['DomainName']}")
        if d['Status'] == 'Deployed':
            import time
            inv = cf.create_invalidation(
                DistributionId=d['Id'],
                InvalidationBatch={
                    'Paths': {'Quantity': 1, 'Items': ['/*']},
                    'CallerReference': str(int(time.time()))
                }
            )
            print(f"Cache invalidation: {inv['Invalidation']['Status']}")
        break
