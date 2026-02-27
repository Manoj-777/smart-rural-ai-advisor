# AgentCore Deployment Guide

## Quick Deploy
```bash
# Deploy all agents
bedrock-agentcore deploy --all

# Or deploy specific agents
bedrock-agentcore deploy SmartRuralAdvisor
bedrock-agentcore deploy SmartRuralWeather
bedrock-agentcore deploy SmartRuralCrop
bedrock-agentcore deploy SmartRuralSchemes
bedrock-agentcore deploy SmartRuralProfile
bedrock-agentcore deploy SmartRuralPest
```

## Test Invocations

### Test Master Agent
```bash
bedrock-agentcore invoke SmartRuralAdvisor --payload '{
  "prompt": "What crops grow well in Tamil Nadu during Kharif season?",
  "context": {"state": "Tamil Nadu"},
  "farmer_id": "test123"
}'
```

### Test Weather Agent
```bash
bedrock-agentcore invoke SmartRuralWeather --payload '{
  "prompt": "Get weather for Chennai",
  "context": {"location": "Chennai"}
}'
```

### Test Crop Agent
```bash
bedrock-agentcore invoke SmartRuralCrop --payload '{
  "prompt": "Paddy cultivation advice",
  "context": {"crop": "Paddy", "state": "Tamil Nadu"}
}'
```

## Monitoring Cold Start

Check CloudWatch Logs for initialization timing:
```
Module loaded: role=master (all initialization deferred to first invocation)
Invoke [master]: farmer=test123, prompt=What crops grow well...
Initializing Strands Agent: model=anthropic.claude-sonnet-4-5-20250929-v1:0, tools=6
Strands Agent ready: role=master
```

Expected timing:
- Module import: <1 second
- First invocation (cold): 3-5 seconds
- Subsequent invocations (warm): <1 second

## Troubleshooting

### Still timing out?
Check if dependencies are properly installed:
```bash
cd agentcore
pip install -r requirements.txt
```

### Import errors?
Verify Python version (3.13 required):
```bash
python --version
```

### Lambda timeout?
Increase timeout in `.bedrock_agentcore.yaml` if needed (default is usually 30s for init, 300s for execution).
