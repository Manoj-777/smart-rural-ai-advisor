"""Check CloudWatch logs for AgentCore Runtime errors."""
import boto3

logs = boto3.client('logs', region_name='ap-south-1')

LOG_GROUPS = [
    '/aws/bedrock-agentcore/runtimes/SmartRuralAdvisor-lcQ47nFSPm-DEFAULT',
    '/aws/bedrock-agentcore/runtimes/SmartRuralAdvisor-lcQ47nFSPm-SmartRuralAdvisor_endpoint',
]

for LOG_GROUP in LOG_GROUPS:
    print(f"\n\n{'='*60}")
    print(f"LOG GROUP: {LOG_GROUP.split('/')[-1]}")
    print(f"{'='*60}")
    
    streams = logs.describe_log_streams(
        logGroupName=LOG_GROUP,
        orderBy='LastEventTime',
        descending=True,
        limit=5,
    )['logStreams']
    
    for stream in streams:
        print(f"\n--- Stream: {stream['logStreamName']} ---")
        events = logs.get_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=stream['logStreamName'],
            limit=50,
            startFromHead=False,
        )
        for event in events['events'][-30:]:
            msg = event['message'].strip()
            if msg:
                print(f"  {msg[:300]}")
