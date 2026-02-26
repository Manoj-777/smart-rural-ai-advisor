import boto3, json

ba = boto3.client('bedrock-agent', region_name='ap-south-1')
sv = boto3.client('s3vectors', region_name='ap-south-1')
ctrl = boto3.client('bedrock-agentcore-control', region_name='ap-south-1')

# Check index
try:
    idx = sv.get_index(vectorBucketName='smart-rural-ai-kb-vectors', indexName='smart-rural-kb-index')
    print(f"Index: {idx['index']['indexName']} (dim={idx['index']['dimension']})")
    meta = idx['index'].get('metadataConfiguration', {})
    print(f"  Metadata config: {json.dumps(meta)}")
except Exception as e:
    print(f"Index: NOT FOUND - {e}")

# Check KB
kbs = ba.list_knowledge_bases(maxResults=10)
for kb in kbs.get('knowledgeBaseSummaries', []):
    print(f"KB: {kb['name']} ({kb['knowledgeBaseId']}) - {kb['status']}")
if not kbs.get('knowledgeBaseSummaries'):
    print('No KBs')

# Check Gateways
gws = ctrl.list_gateways(maxResults=10)
for g in gws.get('items', gws.get('gateways', [])):
    gid = g['gatewayId']
    detail = ctrl.get_gateway(gatewayIdentifier=gid)
    print(f"Gateway: {g['name']} ({gid}) - {detail['status']} - {detail.get('gatewayUrl', 'N/A')}")
    # List targets
    targets = ctrl.list_gateway_targets(gatewayIdentifier=gid)
    for t in targets.get('items', targets.get('targets', [])):
        print(f"  Target: {t['name']} ({t.get('targetId', 'N/A')}) - {t.get('status', 'N/A')}")
if not gws.get('items', gws.get('gateways', [])):
    print('No Gateways')

# Check Agent Runtimes
rts = ctrl.list_agent_runtimes(maxResults=10)
for r in rts.get('agentRuntimes', rts.get('items', [])):
    print(f"Runtime: {r.get('agentRuntimeName', 'N/A')} ({r.get('agentRuntimeId', 'N/A')}) - {r.get('status', 'N/A')}")
if not rts.get('agentRuntimes', rts.get('items', [])):
    print('No Agent Runtimes')
