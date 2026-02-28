import boto3

s3 = boto3.client('s3', region_name='ap-south-1')
bedrock_agent = boto3.client('bedrock-agent', region_name='ap-south-1')

bucket = 'smart-rural-ai-948809294205'
kb_id = '9X1YUTXNOQ'
ds_id = 'XAES6NZN0V'

# Upload crop_prices.md to S3
print("Uploading crop_prices.md to S3...")
s3.upload_file('data/knowledge_base/crop_prices.md', bucket, 'knowledge_base/crop_prices.md')
print("  Uploaded!")

# Verify
obj = s3.head_object(Bucket=bucket, Key='knowledge_base/crop_prices.md')
print(f"  Size: {obj['ContentLength']} bytes")

# Trigger KB ingestion sync
print("\nStarting Knowledge Base ingestion sync...")
resp = bedrock_agent.start_ingestion_job(
    knowledgeBaseId=kb_id,
    dataSourceId=ds_id
)
job_id = resp['ingestionJob']['ingestionJobId']
status = resp['ingestionJob']['status']
print(f"  Ingestion job ID: {job_id}")
print(f"  Status: {status}")
print("\nDone! KB will re-index all documents including crop_prices.md")
