import boto3, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

logs = boto3.client('logs', region_name='ap-south-1')

# Check multiple possible log groups
groups_to_check = [
    "/aws/bedrock-agentcore/runtimes/SmartRuralAdvisor-lcQ47nFSPm-DEFAULT",
    "/aws/bedrock-agentcore/runtimes/SmartRuralAdvisor-lcQ47nFSPm",
    "/codebuild/smart-rural-agentcore-arm64",
]

for log_group in groups_to_check:
    print(f"\n{'='*60}")
    print(f"Log group: {log_group}")
    try:
        streams = logs.describe_log_streams(
            logGroupName=log_group, orderBy='LastEventTime',
            descending=True, limit=5,
        )
        for s in streams.get('logStreams', []):
            name = s['logStreamName']
            print(f"\n--- Stream: {name} ---")
            events = logs.get_log_events(
                logGroupName=log_group, logStreamName=name, limit=80,
            )
            msgs = events.get('events', [])
            if not msgs:
                print("  (empty)")
            for e in msgs:
                msg = e.get('message', '')
                print(f"  {msg[:500]}")
    except Exception as ex:
        print(f"  Error: {ex}")
