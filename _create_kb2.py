"""Create KB - step by step with progress output"""
import boto3, json, time, sys

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
KB_SOURCE_BUCKET = f"smart-rural-ai-{ACCOUNT_ID}"
KB_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/BedrockKBRole"
VECTOR_BUCKET_ARN = f"arn:aws:s3tables:{REGION}:{ACCOUNT_ID}:bucket/smart-rural-ai-vectors"

ba = boto3.client("bedrock-agent", region_name=REGION)

# Step 1: Create KB
print("Creating KB...")
sys.stdout.flush()
try:
    resp = ba.create_knowledge_base(
        name="smart-rural-farming-kb",
        description="Knowledge base for Indian farming advice",
        roleArn=KB_ROLE_ARN,
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": f"arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v2:0"
            }
        },
        storageConfiguration={
            "type": "S3_VECTORS",
            "s3VectorsConfiguration": {
                "vectorBucketArn": VECTOR_BUCKET_ARN,
                "indexName": "smart-rural-kb-index"
            }
        }
    )
    kb_id = resp["knowledgeBase"]["knowledgeBaseId"]
    print(f"KB created: {kb_id} (status: {resp['knowledgeBase']['status']})")
except Exception as e:
    if "already exists" in str(e).lower() or "ConflictException" in str(type(e).__name__):
        # Find existing
        kbs = ba.list_knowledge_bases(maxResults=10)
        for k in kbs.get("knowledgeBaseSummaries", []):
            if k["name"] == "smart-rural-farming-kb":
                kb_id = k["knowledgeBaseId"]
                print(f"KB already exists: {kb_id}")
                break
    else:
        print(f"ERROR: {e}")
        sys.exit(1)

sys.stdout.flush()

# Wait for ACTIVE
print("Waiting for ACTIVE...")
sys.stdout.flush()
for i in range(30):
    time.sleep(5)
    st = ba.get_knowledge_base(knowledgeBaseId=kb_id)
    state = st["knowledgeBase"]["status"]
    print(f"  [{(i+1)*5}s] {state}")
    sys.stdout.flush()
    if state == "ACTIVE":
        break
    if state == "FAILED":
        print(f"  FAILED: {st['knowledgeBase'].get('failureReasons', 'unknown')}")
        sys.exit(1)

# Step 2: Create data source
print("\nCreating data source...")
sys.stdout.flush()
try:
    ds_resp = ba.create_data_source(
        knowledgeBaseId=kb_id,
        name="farming-knowledge-docs",
        description="Indian farming knowledge documents",
        dataSourceConfiguration={
            "type": "S3",
            "s3Configuration": {
                "bucketArn": f"arn:aws:s3:::{KB_SOURCE_BUCKET}",
                "inclusionPrefixes": ["knowledge_base/"]
            }
        },
        vectorIngestionConfiguration={
            "chunkingConfiguration": {
                "chunkingStrategy": "FIXED_SIZE",
                "fixedSizeChunkingConfiguration": {
                    "maxTokens": 300,
                    "overlapPercentage": 20
                }
            }
        }
    )
    ds_id = ds_resp["dataSource"]["dataSourceId"]
    print(f"Data source created: {ds_id}")
except Exception as e:
    if "already exists" in str(e).lower() or "ConflictException" in str(type(e).__name__):
        dss = ba.list_data_sources(knowledgeBaseId=kb_id, maxResults=10)
        for d in dss.get("dataSourceSummaries", []):
            if d["name"] == "farming-knowledge-docs":
                ds_id = d["dataSourceId"]
                print(f"Data source already exists: {ds_id}")
                break
    else:
        print(f"ERROR: {e}")
        sys.exit(1)

sys.stdout.flush()

# Step 3: Sync
print("\nStarting sync (embed + index)...")
sys.stdout.flush()
sync_resp = ba.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
job_id = sync_resp["ingestionJob"]["ingestionJobId"]
print(f"Job: {job_id}")
sys.stdout.flush()

for i in range(90):
    time.sleep(10)
    jr = ba.get_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id, ingestionJobId=job_id)
    job = jr["ingestionJob"]
    state = job["status"]
    stats = job.get("statistics", {})
    scanned = stats.get("numberOfDocumentsScanned", "?")
    print(f"  [{(i+1)*10}s] {state} | scanned={scanned}")
    sys.stdout.flush()
    if state == "COMPLETE":
        indexed = stats.get("numberOfNewDocumentsIndexed", 0) + stats.get("numberOfModifiedDocumentsIndexed", 0)
        failed = stats.get("numberOfDocumentsFailed", 0)
        print(f"\nDONE! Indexed={indexed}, Failed={failed}")
        break
    if state == "FAILED":
        print(f"\nFAILED: {job.get('failureReasons', 'unknown')}")
        break

print(f"\n>>> KB_ID = {kb_id}")
sys.stdout.flush()
