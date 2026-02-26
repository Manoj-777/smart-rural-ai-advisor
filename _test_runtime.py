"""Quick test: invoke the AgentCore Runtime directly via boto3."""
import boto3, json, uuid, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REGION = "ap-south-1"
RT_ID = "SmartRuralAdvisor-lcQ47nFSPm"
LOG = "_test_runtime.log"

def log(msg):
    print(msg, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def main():
    with open(LOG, "w") as f:
        f.write("")

    client = boto3.client("bedrock-agentcore", region_name=REGION)

    session_id = str(uuid.uuid4()) + "-" + str(uuid.uuid4())  # >33 chars
    payload = json.dumps({
        "prompt": "Hello! What crops can I plant in Tamil Nadu?",
        "farmer_id": "test_farmer",
        "session_id": session_id,
    })

    log(f"Invoking runtime {RT_ID}")
    log(f"Session: {session_id}")
    log(f"Payload: {payload[:200]}")

    start = time.time()
    try:
        resp = client.invoke_agent_runtime(
            agentRuntimeArn=f"arn:aws:bedrock-agentcore:{REGION}:948809294205:runtime/{RT_ID}",
            runtimeSessionId=session_id,
            payload=payload.encode("utf-8"),
            qualifier="DEFAULT",
        )
        elapsed = time.time() - start
        log(f"Response received in {elapsed:.1f}s")
        log(f"HTTP status: {resp.get('ResponseMetadata', {}).get('HTTPStatusCode')}")

        raw = resp.get("response", b"")
        if hasattr(raw, "read"):
            raw = raw.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")

        log(f"Response length: {len(raw)} chars")
        log(f"Response: {raw[:1000]}")

    except Exception as e:
        elapsed = time.time() - start
        log(f"ERROR after {elapsed:.1f}s: {type(e).__name__}: {e}")

    log("DONE")

if __name__ == "__main__":
    main()
