import boto3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
cb = boto3.client("codebuild", region_name="ap-south-1")
builds = cb.list_builds_for_project(projectName="smart-rural-agentcore-arm64", sortOrder="DESCENDING")
bid = builds["ids"][0]
d = cb.batch_get_builds(ids=[bid])["builds"][0]
print(f"Build: {bid}")
print(f"Status: {d['buildStatus']}")
print(f"Phase: {d.get('currentPhase', '?')}")
for p in d.get("phases", []):
    pn = p.get("phaseType", "?")
    ps = p.get("phaseStatus", "?")
    dur = p.get("durationInSeconds", 0)
    print(f"  {pn}: {ps} ({dur}s)")
    for ctx in p.get("contexts", []):
        msg = ctx.get("message", "")
        if msg:
            print(f"    {msg[:200]}")

if d["buildStatus"] == "SUCCEEDED":
    ac = boto3.client("bedrock-agentcore-control", region_name="ap-south-1")
    rt = ac.get_agent_runtime(agentRuntimeId="SmartRuralAdvisor-lcQ47nFSPm")
    print(f"\nRuntime status: {rt.get('status')}")
    if rt.get("failureReason"):
        print(f"  Reason: {rt['failureReason']}")
        val = val[:4] + '****' if val else 'EMPTY'
    print(f"  {p['ParameterKey']}: {val}")
