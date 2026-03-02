path = r'c:\Users\MSanjay1\OneDrive - Unisys\Documents\AI Workshop AWS\Rural AI workshop\smart-rural-ai-advisor\backend\lambdas\agent_orchestrator\handler.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

checks = [
    ('import time as _time', 'time import'),
    ('FAST_PATH_PREFIXES', 'constants'),
    ('_is_feature_page', 'feature page detection'),
    ('FAST PATH for feature page', 'fast-path routing'),
    ('Feature page - skipping TTS', 'TTS skip'),
    ('Total handler time', 'timing log'),
]
for text, label in checks:
    ok = text in content
    status = 'OK' if ok else 'MISSING'
    print(f'  {label}: {status}')

lines = content.split('\n')
print(f'Total lines: {len(lines)}')

import ast
ast.parse(content)
print('Syntax: OK')
