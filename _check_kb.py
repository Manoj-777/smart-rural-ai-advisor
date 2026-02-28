import boto3

s3 = boto3.client('s3', region_name='ap-south-1')
bedrock_agent = boto3.client('bedrock-agent', region_name='ap-south-1')

# Get KB details to find S3 bucket
kb_id = '9X1YUTXNOQ'
kb = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
print(f"KB: {kb['knowledgeBase']['name']}")
print(f"Status: {kb['knowledgeBase']['status']}")

# List data sources
ds_list = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
for ds in ds_list['dataSourceSummaries']:
    print(f"\nData source: {ds['name']} (ID: {ds['dataSourceId']})")
    print(f"  Status: {ds['status']}")
    
    # Get full config to find bucket
    ds_detail = bedrock_agent.get_data_source(knowledgeBaseId=kb_id, dataSourceId=ds['dataSourceId'])
    config = ds_detail['dataSource']['dataSourceConfiguration']
    if 's3Configuration' in config:
        bucket = config['s3Configuration']['bucketArn'].split(':')[-1]
        prefix = config['s3Configuration'].get('inclusionPrefixes', [''])
        print(f"  Bucket: {bucket}")
        print(f"  Prefix: {prefix}")
        
        # List objects in bucket
        print(f"\n  Files in S3 bucket:")
        resp = s3.list_objects_v2(Bucket=bucket)
        if 'Contents' in resp:
            for obj in resp['Contents']:
                print(f"    {obj['Key']:50s}  {obj['Size']:>8} bytes  {obj['LastModified']}")
        else:
            print("    (empty)")
