"""Fix CodeBuild IAM role permissions and re-run build."""
import boto3, json, time

REGION = "ap-south-1"
ROLE = "smart-rural-ai-CodeBuildRole"

iam = boto3.client("iam", region_name=REGION)

# List current
attached = iam.list_attached_role_policies(RoleName=ROLE)["AttachedPolicies"]
print("Currently attached:")
for p in attached:
    print(f"  {p['PolicyName']}")

# Attach required policies
for arn in [
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
    "arn:aws:iam::aws:policy/AWSCodeBuildAdminAccess",
]:
    iam.attach_role_policy(RoleName=ROLE, PolicyArn=arn)
    print(f"Attached: {arn.split('/')[-1]}")

# Inline policy for bedrock-agentcore
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Allow", "Action": ["bedrock-agentcore:*", "bedrock:*"], "Resource": "*"},
        {"Effect": "Allow", "Action": ["iam:PassRole"], "Resource": "*"},
    ]
}
iam.put_role_policy(RoleName=ROLE, PolicyName="AgentCoreAccess", PolicyDocument=json.dumps(policy))
print("Inline policy: AgentCoreAccess")

print("\nWaiting 10s for IAM propagation...")
time.sleep(10)

# Re-run build
cb = boto3.client("codebuild", region_name=REGION)
resp = cb.start_build(projectName="smart-rural-agentcore-arm64")
build_id = resp["build"]["id"]
print(f"\nBuild started: {build_id}")
print("Polling...")

for i in range(90):
    time.sleep(10)
    detail = cb.batch_get_builds(ids=[build_id])
    build = detail["builds"][0]
    phase = build.get("currentPhase", "?")
    status = build.get("buildStatus", "IN_PROGRESS")

    if i % 3 == 0:
        print(f"  [{(i+1)*10}s] Phase: {phase}, Status: {status}")

    if status != "IN_PROGRESS":
        print(f"\nBuild finished: {status}")
        for p in build.get("phases", []):
            pname = p.get("phaseType", "?")
            pstatus = p.get("phaseStatus", "?")
            dur = p.get("durationInSeconds", 0)
            print(f"  {pname}: {pstatus} ({dur}s)")
            for ctx in p.get("contexts", []):
                if ctx.get("message"):
                    print(f"    {ctx['message'][:300]}")

        if status == "SUCCEEDED":
            # Check runtime
            ac = boto3.client("bedrock-agentcore-control", region_name=REGION)
            rt = ac.get_agent_runtime(agentRuntimeId="SmartRuralAdvisor-lcQ47nFSPm")
            print(f"\nRuntime status: {rt.get('status')}")
            if rt.get("failureReason"):
                print(f"Failure reason: {rt['failureReason']}")
        break
else:
    print("Timed out")
