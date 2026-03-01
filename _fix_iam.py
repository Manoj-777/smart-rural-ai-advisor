"""Quick script to add sns:GetSMSAttributes to the FarmerProfile Lambda role."""
import boto3, json

iam = boto3.client('iam')
ROLE = 'smart-rural-ai-FarmerProfileFunctionRole-ro6jRwkT6uPq'
POLICY = 'FarmerProfileFunctionRolePolicy0'

resp = iam.get_role_policy(RoleName=ROLE, PolicyName=POLICY)
doc = resp['PolicyDocument']

for stmt in doc['Statement']:
    actions = stmt.get('Action', [])
    if isinstance(actions, list) and 'sns:Publish' in actions:
        if 'sns:GetSMSAttributes' not in actions:
            actions.append('sns:GetSMSAttributes')
            print("Added sns:GetSMSAttributes")
        else:
            print("sns:GetSMSAttributes already present")
        break

iam.put_role_policy(RoleName=ROLE, PolicyName=POLICY, PolicyDocument=json.dumps(doc))
print("Policy updated successfully")
