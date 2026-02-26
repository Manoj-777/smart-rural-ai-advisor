import boto3
ac = boto3.client('bedrock-agentcore-control', region_name='ap-south-1')
d = ac.get_agent_runtime(agentRuntimeId='SmartRuralAdvisor-lcQ47nFSPm')
for k,v in d.items():
    if k != 'ResponseMetadata':
        print(f"{k}: {v}")
