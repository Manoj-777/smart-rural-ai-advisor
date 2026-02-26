import boto3
from datetime import datetime, timezone, timedelta
cf = boto3.client('cloudformation', region_name='ap-south-1')
events = cf.describe_stack_events(StackName='smart-rural-ai')['StackEvents']
now = datetime.now(timezone.utc)
for e in events[:10]:
    age = now - e['Timestamp']
    if age < timedelta(minutes=30):
        print(f"  {e['Timestamp'].strftime('%H:%M:%S')} {e['LogicalResourceId']}: {e['ResourceStatus']}")
