import boto3

s3 = boto3.client('s3', region_name='ap-south-1')
bucket = 'smart-rural-ai-frontend-948809294205'

# Check content types of all files
resp = s3.list_objects_v2(Bucket=bucket)
for obj in resp.get('Contents', []):
    key = obj['Key']
    head = s3.head_object(Bucket=bucket, Key=key)
    ct = head.get('ContentType', 'unknown')
    print(f"  {key:50s}  ContentType: {ct}")

# Get the bucket region/website URL  
loc = s3.get_bucket_location(Bucket=bucket)
region = loc['LocationConstraint'] or 'us-east-1'
url = f"http://{bucket}.s3-website.{region}.amazonaws.com"
print(f"\nWebsite URL: {url}")
