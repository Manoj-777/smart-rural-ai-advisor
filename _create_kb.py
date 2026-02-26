"""
Create Bedrock Knowledge Base using S3 Vectors (no OpenSearch Serverless needed).

S3 Vectors uses S3 Tables as the vector store backend - fully managed by AWS,
no subscription required, no OpenSearch provisioning.

Flow:
  1. Create S3 Tables bucket (for vector storage)
  2. Update IAM role with S3 Tables permissions
  3. Create Bedrock KB with S3_VECTORS storage type
  4. Add S3 data source (our existing knowledge_base/ docs)
  5. Sync the data source (embed + index)
"""
import boto3
import json
import time
import sys

REGION = "ap-south-1"
ACCOUNT_ID = "948809294205"
KB_SOURCE_BUCKET = f"smart-rural-ai-{ACCOUNT_ID}"
KB_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/BedrockKBRole"
VECTOR_BUCKET_NAME = "smart-rural-ai-vectors"

bedrock_agent = boto3.client("bedrock-agent", region_name=REGION)
s3tables = boto3.client("s3tables", region_name=REGION)
iam = boto3.client("iam")


def update_kb_role_for_s3_vectors(vector_bucket_arn):
    """Add S3 Tables/Vectors permissions to BedrockKBRole."""
    policy_name = "BedrockKBVectorsPolicy"
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3tables:*"
                ],
                "Resource": [
                    vector_bucket_arn,
                    f"{vector_bucket_arn}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetBucketLocation",
                    "s3:ListBucket",
                    "s3:GetObject"
                ],
                "Resource": [
                    f"arn:aws:s3:::{KB_SOURCE_BUCKET}",
                    f"arn:aws:s3:::{KB_SOURCE_BUCKET}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel"
                ],
                "Resource": [
                    f"arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v2:0"
                ]
            }
        ]
    }
    try:
        iam.put_role_policy(
            RoleName="BedrockKBRole",
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_doc)
        )
        print(f"  Updated BedrockKBRole with S3 Tables permissions")
    except Exception as e:
        print(f"  IAM update warning: {e}")


def create_vector_bucket():
    """Create S3 Tables bucket for vector storage."""
    print("\n[1/5] Creating S3 Tables bucket for vectors...")

    # Check if already exists
    existing = s3tables.list_table_buckets(maxBuckets=100)
    for tb in existing.get("tableBuckets", []):
        if tb["name"] == VECTOR_BUCKET_NAME:
            print(f"  Already exists: {tb['arn']}")
            return tb["arn"]

    resp = s3tables.create_table_bucket(name=VECTOR_BUCKET_NAME)
    arn = resp["arn"]
    print(f"  Created: {arn}")
    return arn


def create_knowledge_base(vector_bucket_arn):
    """Create Bedrock KB with S3 Vectors storage."""
    print("\n[3/5] Creating Bedrock Knowledge Base...")

    # Check if already exists
    existing = bedrock_agent.list_knowledge_bases(maxResults=10)
    for kb in existing.get("knowledgeBaseSummaries", []):
        if kb["name"] == "smart-rural-farming-kb":
            print(f"  Already exists: {kb['knowledgeBaseId']} ({kb['status']})")
            return kb["knowledgeBaseId"]

    resp = bedrock_agent.create_knowledge_base(
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
                "vectorBucketArn": vector_bucket_arn
            }
        }
    )

    kb = resp["knowledgeBase"]
    kb_id = kb["knowledgeBaseId"]
    print(f"  Created KB: {kb_id} (status: {kb['status']})")

    # Wait for ACTIVE
    for i in range(18):
        time.sleep(5)
        status = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
        state = status["knowledgeBase"]["status"]
        if state == "ACTIVE":
            print(f"  KB is ACTIVE!")
            return kb_id
        print(f"    [{(i+1)*5}s] Status: {state}")

    print(f"  WARNING: KB still not ACTIVE after 90s. Continuing anyway...")
    return kb_id


def add_data_source(kb_id):
    """Add S3 data source to the KB."""
    print("\n[4/5] Adding S3 data source...")

    # Check if already exists
    existing = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id, maxResults=10)
    for ds in existing.get("dataSourceSummaries", []):
        if ds["name"] == "farming-knowledge-docs":
            print(f"  Already exists: {ds['dataSourceId']} ({ds['status']})")
            return ds["dataSourceId"]

    resp = bedrock_agent.create_data_source(
        knowledgeBaseId=kb_id,
        name="farming-knowledge-docs",
        description="Indian farming knowledge documents - crop guides, pest patterns, irrigation, government schemes, regional advisories",
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

    ds_id = resp["dataSource"]["dataSourceId"]
    print(f"  Created data source: {ds_id}")
    return ds_id


def sync_data_source(kb_id, ds_id):
    """Trigger data source sync (embed + index documents)."""
    print("\n[5/5] Syncing data source (embedding + indexing)...")

    resp = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=ds_id
    )

    job_id = resp["ingestionJob"]["ingestionJobId"]
    print(f"  Ingestion job started: {job_id}")

    # Wait for completion
    for i in range(60):
        time.sleep(10)
        status = bedrock_agent.get_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
            ingestionJobId=job_id
        )
        job = status["ingestionJob"]
        state = job["status"]
        stats = job.get("statistics", {})

        if state == "COMPLETE":
            print(f"\n  Sync COMPLETE!")
            print(f"    Documents scanned:  {stats.get('numberOfDocumentsScanned', '?')}")
            print(f"    Documents indexed:   {stats.get('numberOfNewDocumentsIndexed', 0) + stats.get('numberOfModifiedDocumentsIndexed', 0)}")
            print(f"    Documents failed:    {stats.get('numberOfDocumentsFailed', 0)}")
            return True
        elif state == "FAILED":
            print(f"\n  Sync FAILED!")
            print(f"    Failure reasons: {job.get('failureReasons', 'unknown')}")
            return False

        print(f"    [{(i+1)*10}s] Status: {state} | Scanned: {stats.get('numberOfDocumentsScanned', '?')}")

    print("  TIMEOUT - sync taking too long. Check Console.")
    return False


def main():
    print("=" * 60)
    print("Smart Rural AI - Bedrock Knowledge Base Setup")
    print("Using S3 Vectors (no OpenSearch needed)")
    print("=" * 60)

    # Step 1: Create vector bucket
    vector_bucket_arn = create_vector_bucket()

    # Step 2: Update IAM role
    print("\n[2/5] Updating IAM role...")
    update_kb_role_for_s3_vectors(vector_bucket_arn)
    print("  Waiting 10s for IAM propagation...")
    time.sleep(10)

    # Step 3: Create KB
    kb_id = create_knowledge_base(vector_bucket_arn)

    # Step 4: Add data source
    ds_id = add_data_source(kb_id)

    # Step 5: Sync
    success = sync_data_source(kb_id, ds_id)

    print()
    print("=" * 60)
    if success:
        print(f"  Knowledge Base ID:  {kb_id}")
        print(f"  STATUS: READY")
        print()
        print(f"  Next: python setup_agentcore.py")
    else:
        print(f"  KB ID: {kb_id} (sync may still be running)")
    print("=" * 60)

    return kb_id


if __name__ == "__main__":
    kb_id = main()
