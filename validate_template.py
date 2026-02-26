import yaml

# Register CloudFormation intrinsic functions
for tag in ['!Ref','!Sub','!GetAtt','!Join','!Select','!Split','!If','!Equals','!Not','!And','!Or']:
    yaml.add_constructor(tag, lambda loader, node: str(node.value), yaml.UnsafeLoader)

with open('infrastructure/template.yaml') as f:
    data = yaml.load(f, Loader=yaml.UnsafeLoader)

resources = data.get('Resources', {})
print(f'YAML syntax: VALID')
print(f'Resources: {len(resources)}')
for name, res in resources.items():
    t = res.get('Type', '?')
    print(f'  {name}: {t}')

params = data.get('Parameters', {})
print(f'Parameters: {list(params.keys())}')

outputs = data.get('Outputs', {})
print(f'Outputs: {list(outputs.keys())}')
