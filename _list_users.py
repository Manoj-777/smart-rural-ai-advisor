import json, sys
data = json.load(sys.stdin)
for u in data['Users']:
    attrs = {a['Name']: a['Value'] for a in u['Attributes']}
    phone = attrs.get('phone_number', '?')
    email = attrs.get('email', 'NONE')
    ev = attrs.get('email_verified', 'N/A')
    print(f"{phone}  email={email}  email_verified={ev}")
