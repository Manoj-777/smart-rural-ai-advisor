import boto3

db = boto3.resource('dynamodb', region_name='ap-south-1')
t = db.Table('farmer_profiles')
r = t.get_item(Key={'farmer_id': 'ph_6382593381'})
item = r.get('Item')
if item:
    print(f"FOUND in DynamoDB: name={item.get('name')}, state={item.get('state')}")
else:
    print("NOT FOUND in DynamoDB")

c = boto3.client('cognito-idp', region_name='ap-south-1')
try:
    u = c.admin_get_user(UserPoolId='ap-south-1_X58lNMEcn', Username='+916382593381')
    print(f"COGNITO USER EXISTS: {u['Username']}")
    for a in u['UserAttributes']:
        print(f"  {a['Name']}: {a['Value']}")
except c.exceptions.UserNotFoundException:
    print("NOT FOUND in Cognito")
