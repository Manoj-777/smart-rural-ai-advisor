import boto3
import random
import string

c = boto3.client('cognito-idp', region_name='ap-south-1')
client_id = '4c3c6he88im15hmv5rdkv3m6h0'
pool = 'ap-south-1_X58lNMEcn'

phone = '9' + ''.join(random.choice('0123456789') for _ in range(9))
username = '+91' + phone
password = 'Demo@' + ''.join(random.choice(string.digits) for _ in range(6))
email = f'test{phone}@example.com'

resp = c.sign_up(
    ClientId=client_id,
    Username=username,
    Password=password,
    UserAttributes=[
        {'Name': 'phone_number', 'Value': username},
        {'Name': 'name', 'Value': 'Test User'},
        {'Name': 'email', 'Value': email},
    ],
)
print('SIGNUP UserConfirmed:', resp.get('UserConfirmed'))

user = c.admin_get_user(UserPoolId=pool, Username=username)
print('ADMIN UserStatus:', user.get('UserStatus'))

c.admin_delete_user(UserPoolId=pool, Username=username)
print('Cleanup done for', username)
