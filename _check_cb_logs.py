"""Fetch full CodeBuild logs (BUILD phase) to see .so architecture."""
import boto3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logs = boto3.client("logs", region_name="ap-south-1")
log_group = "/codebuild/smart-rural-agentcore-arm64"

# Get latest build stream
streams = logs.describe_log_streams(
    logGroupName=log_group, orderBy="LastEventTime",
    descending=True, limit=1,
)
stream = streams["logStreams"][0]["logStreamName"]
print(f"Stream: {stream}\n")

# Get all events
token = None
all_events = []
for _ in range(10):
    kwargs = dict(logGroupName=log_group, logStreamName=stream, startFromHead=True, limit=200)
    if token:
        kwargs["nextToken"] = token
    resp = logs.get_log_events(**kwargs)
    events = resp.get("events", [])
    if not events:
        break
    all_events.extend(events)
    new_token = resp.get("nextForwardToken")
    if new_token == token:
        break
    token = new_token

print(f"Total events: {len(all_events)}\n")
for e in all_events:
    print(e["message"].rstrip())
