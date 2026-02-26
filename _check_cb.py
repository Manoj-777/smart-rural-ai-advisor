"""Check CodeBuild builds status."""
import boto3
cb = boto3.client("codebuild", region_name="ap-south-1")
builds = cb.list_builds_for_project(projectName="smart-rural-agentcore-arm64", sortOrder="DESCENDING")
print("Recent builds:")
for bid in builds.get("ids", [])[:5]:
    d = cb.batch_get_builds(ids=[bid])["builds"][0]
    status = d["buildStatus"]
    phase = d.get("currentPhase", "?")
    print(f"\n  {bid}")
    print(f"    Status: {status}, Phase: {phase}")
    for p in d.get("phases", []):
        pn = p.get("phaseType", "?")
        ps = p.get("phaseStatus", "?")
        dur = p.get("durationInSeconds", 0)
        print(f"    {pn}: {ps} ({dur}s)")
        for ctx in p.get("contexts", []):
            msg = ctx.get("message", "")
            if msg:
                print(f"      {msg[:200]}")
