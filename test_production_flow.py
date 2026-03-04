#!/usr/bin/env python3
"""
Test the complete production flow: Frontend → API Gateway → Orchestrator → AgentCore Runtimes
This script simulates what the frontend does and checks each step of the pipeline.
"""

import json
import boto3
import requests
import time
from datetime import datetime

# Configuration
API_URL = "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod"
REGION = "ap-south-1"

# Initialize AWS clients
bedrock_agentcore = boto3.client('bedrock-agentcore', region_name=REGION)
logs_client = boto3.client('logs', region_name=REGION)

# Runtime ARNs (from environment or config)
RUNTIMES = {
    "SmartRuralAdvisor": "arn:aws:bedrock:ap-south-1:471112971854:agentcore-runtime/SmartRuralAdvisor",
    "SmartRuralWeather": "arn:aws:bedrock:ap-south-1:471112971854:agentcore-runtime/SmartRuralWeather",
    "SmartRuralSchemes": "arn:aws:bedrock:ap-south-1:471112971854:agentcore-runtime/SmartRuralSchemes",
    "SmartRuralCrop": "arn:aws:bedrock:ap-south-1:471112971854:agentcore-runtime/SmartRuralCrop",
    "SmartRuralProfile": "arn:aws:bedrock:ap-south-1:471112971854:agentcore-runtime/SmartRuralProfile",
    "SmartRuralPest": "arn:aws:bedrock:ap-south-1:471112971854:agentcore-runtime/SmartRuralPest",
}

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def check_runtime_status():
    """Check the status of all AgentCore runtimes"""
    print_section("1. Checking AgentCore Runtime Status")
    
    for name, arn in RUNTIMES.items():
        try:
            # Try to invoke with a simple test to check if runtime is responsive
            test_payload = {"prompt": "test", "session_id": "status-check"}
            response = bedrock_agentcore.invoke_agent_runtime(
                agentRuntimeArn=arn,
                runtimeSessionId="status-check-" + str(int(time.time())),
                payload=json.dumps(test_payload).encode('utf-8'),
                qualifier='DEFAULT'
            )
            print(f"✓ {name}: Runtime is responsive")
        except Exception as e:
            error_msg = str(e)
            if 'RuntimeClientError' in error_msg or 'timeout' in error_msg.lower():
                print(f"✗ {name}: Runtime timeout (cold start issue)")
            else:
                print(f"✗ {name}: {error_msg[:100]}")
        print()

def test_api_gateway():
    """Test the API Gateway /chat endpoint"""
    print_section("2. Testing API Gateway /chat Endpoint")
    
    test_message = "What is the weather in Chennai?"
    payload = {
        "message": test_message,
        "session_id": f"test-{int(time.time())}",
        "farmer_id": "test-farmer",
        "language": "en"
    }
    
    print(f"Sending test message: {test_message}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        elapsed = time.time() - start_time
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {elapsed:.2f}s")
        print(f"Response Headers: {dict(response.headers)}\n")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success!")
            print(f"Response Data:")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"✗ Request timed out after 60 seconds")
        return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def test_direct_runtime_invocation():
    """Test direct invocation of the master runtime"""
    print_section("3. Testing Direct Runtime Invocation")
    
    runtime_arn = RUNTIMES["SmartRuralAdvisor"]
    session_id = f"direct-test-{int(time.time())}"
    
    payload = {
        "prompt": "What crops are suitable for Tamil Nadu?",
        "session_id": session_id,
        "farmer_id": "test-farmer",
        "context": {
            "state": "Tamil Nadu",
            "district": "Coimbatore"
        }
    }
    
    print(f"Invoking runtime: {runtime_arn}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        start_time = time.time()
        response = bedrock_agentcore.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            runtimeSessionId=session_id,
            payload=json.dumps(payload).encode('utf-8'),
            qualifier='DEFAULT'
        )
        elapsed = time.time() - start_time
        
        print(f"✓ Invocation successful!")
        print(f"Response Time: {elapsed:.2f}s")
        
        # Parse response
        response_payload = response.get('response', response.get('payload', ''))
        if isinstance(response_payload, bytes):
            response_payload = response_payload.decode('utf-8')
        elif hasattr(response_payload, 'read'):
            response_payload = response_payload.read().decode('utf-8')
        
        print(f"Response:")
        print(response_payload)
        
        return response_payload
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def check_cloudwatch_logs():
    """Check recent CloudWatch logs for the orchestrator Lambda"""
    print_section("4. Checking CloudWatch Logs")
    
    log_group = "/aws/lambda/smart-rural-ai-AgentOrchestratorFunction"
    
    try:
        # Get recent log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        print(f"Recent log streams for {log_group}:\n")
        
        for stream in response.get('logStreams', []):
            stream_name = stream['logStreamName']
            last_event = datetime.fromtimestamp(stream['lastEventTime'] / 1000)
            
            print(f"Stream: {stream_name}")
            print(f"Last Event: {last_event}")
            
            # Get recent log events
            events_response = logs_client.get_log_events(
                logGroupName=log_group,
                logStreamName=stream_name,
                limit=20,
                startFromHead=False
            )
            
            print("Recent events:")
            for event in events_response.get('events', []):
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                print(f"  [{timestamp}] {message}")
            print()
            
    except Exception as e:
        print(f"✗ Error reading logs: {str(e)}")

def main():
    print(f"\n{'#'*80}")
    print(f"  Smart Rural AI - Production Flow Test")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    # Step 1: Check runtime status
    check_runtime_status()
    
    # Step 2: Test API Gateway
    api_response = test_api_gateway()
    
    # Step 3: Test direct runtime invocation
    runtime_response = test_direct_runtime_invocation()
    
    # Step 4: Check CloudWatch logs
    check_cloudwatch_logs()
    
    print_section("Test Summary")
    print(f"API Gateway: {'✓ Working' if api_response else '✗ Failed'}")
    print(f"Direct Runtime: {'✓ Working' if runtime_response else '✗ Failed'}")
    print()
    
    if not api_response and not runtime_response:
        print("⚠️  Both API Gateway and direct runtime invocation failed.")
        print("   This suggests the AgentCore runtimes are still timing out.")
        print("   Possible causes:")
        print("   1. The fixed agent.py was not deployed correctly")
        print("   2. The strands-agents dependency is still causing slow initialization")
        print("   3. The runtime needs more memory or different configuration")
        print()
        print("Next steps:")
        print("   1. Verify the deployed package contains the fixed agent.py")
        print("   2. Consider removing strands-agents entirely and using direct boto3")
        print("   3. Check if AGENT_ROLE environment variables are set correctly")

if __name__ == "__main__":
    main()
