import boto3, json
c = boto3.client('bedrock-agentcore', region_name='ap-south-1')
sm = c._service_model
op = sm.operation_model('InvokeAgentRuntime')
print("Input shape members:")
for name, shape in op.input_shape.members.items():
    req = name in op.input_shape.metadata.get('required', op.input_shape.serialization.get('required', []))
    print(f"  {name}: {shape.type_name} {'(required)' if req else ''}")
print(f"\nRequired: {op.input_shape.metadata.get('required', [])}")
print(f"\nOutput shape members:")
for name, shape in op.output_shape.members.items():
    print(f"  {name}: {shape.type_name}")
