"""Create KB with S3 Vectors (index already created with non-filterable metadata)"""
import boto3, json, time, sys

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
KB_SOURCE_BUCKET = f"smart-rural-ai-{ACCOUNT_ID}"
KB_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/BedrockKBRole"
VECTOR_BUCKET_ARN = "arn:aws:s3vectors:ap-south-1:948809294205:bucket/smart-rural-ai-kb-vectors"
INDEX_NAME = "smart-rural-kb-index"

ba = boto3.client("bedrock-agent", region_name=REGION)

# Step 1: Create KB
print("Creating KB...")
sys.stdout.flush()

kbs = ba.list_knowledge_bases(maxResults=10)
kb_id = None
for k in kbs.get("knowledgeBaseSummaries", []):
    if k["name"] == "smart-rural-farming-kb":
        kb_id = k["knowledgeBaseId"]
        print(f"  Already exists: {kb_id} ({k['status']})")
        break

if not kb_id:
    resp = ba.create_knowledge_base(
        name="smart-rural-farming-kb",
        description="Knowledge base for Indian farming advice including crop guides, pest patterns, irrigation, government schemes, and regional advisories",
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
                "indexName": INDEX_NAME
            }
        }
    )
    kb_id = resp["knowledgeBase"]["knowledgeBaseId"]
    status = resp["knowledgeBase"]["status"]
    print(f"  Created: {kb_id} ({status})")

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
    if state in ("FAILED", "DELETE_IN_PROGRESS"):
        reasons = st["knowledgeBase"].get("failureReasons", ["unknown"])
        print(f"  FAILED: {reasons}")
        sys.exit(1)

# Step 2: Create data source
print("Creating data source...")
sys.stdout.flush()
ds_id = None
try:
    dss = ba.list_data_sources(knowledgeBaseId=kb_id, maxResults=10)
    for d in dss.get("dataSourceSummaries", []):
        if d["name"] == "farming-knowledge-docs":
            ds_id = d["dataSourceId"]
            print(f"  Already exists: {ds_id}")
            break
except:
    pass

if not ds_id:
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
    print(f"  Created: {ds_id}")

sys.stdout.flush()

# Step 3: Sync
print("Starting sync...")
sys.stdout.flush()
sync_resp = ba.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
job_id = sync_resp["ingestionJob"]["ingestionJobId"]
print(f"  Job: {job_id}")
sys.stdout.flush()

for i in range(90):
    time.sleep(10)
    jr = ba.get_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id, ingestionJobId=job_id)
    job = jr["ingestionJob"]
    state = job["status"]
    stats = job.get("statistics", {})
    scanned = stats.get("numberOfDocumentsScanned", "?")
    indexed = stats.get("numberOfNewDocumentsIndexed", 0) + stats.get("numberOfModifiedDocumentsIndexed", 0)
    failed = stats.get("numberOfDocumentsFailed", 0)
    print(f"  [{(i+1)*10}s] {state} | scanned={scanned} indexed={indexed} failed={failed}")
    sys.stdout.flush()
    if state == "COMPLETE":
        print(f"\nDONE!")
        if failed > 0:
            reasons = job.get("failureReasons", ["unknown"])
            print(f"  Failure reasons: {reasons}")
        break
    if state == "FAILED":
        reasons = job.get("failureReasons", ["unknown"])
        print(f"\nFAILED: {reasons}")
        break

print(f"\nKB_ID = {kb_id}")
sys.stdout.flush()
