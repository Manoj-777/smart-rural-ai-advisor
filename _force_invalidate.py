import boto3

cf = boto3.client("cloudfront")
resp = cf.create_invalidation(
    DistributionId="E2HUWT1BUYIIRG",
    InvalidationBatch={
        "Paths": {"Quantity": 1, "Items": ["/*"]},
        "CallerReference": "force-invalidate-mock-fix-003",
    },
)
inv_id = resp["Invalidation"]["Id"]
status = resp["Invalidation"]["Status"]
print(f"Invalidation {inv_id}: {status}")

s3 = boto3.client("s3")
objs = s3.list_objects_v2(Bucket="smart-rural-ai-frontend-948809294205")
for o in objs.get("Contents", []):
    key = o["Key"]
    size = o["Size"]
    print(f"  {key:50s} {size:>10} bytes")
