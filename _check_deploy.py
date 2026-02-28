import boto3
client = boto3.client('lambda', region_name='ap-south-1')
funcs = [
    'AgentOrchestratorFunction-9L6obTRaxJHM',
    'WeatherFunction-dilSoHSLlXGN',
    'CropAdvisoryFunction-Z8jAKbsH7mkY',
    'GovtSchemesFunction-BgTy36y4fgGv',
    'FarmerProfileFunction-mEzTIZOAvxKt',
    'ImageAnalysisFunction-wY2rBz7uHgKV',
    'TranscribeSpeechFunction-rF4EDECy1VaO',
    'HealthCheckFunction-FQB8TfJ91HKs',
]
for f in funcs:
    name = 'smart-rural-ai-' + f
    r = client.get_function_configuration(FunctionName=name)
    short = f.split('-')[0]
    ts = r['LastModified']
    print(f"{short:35s} Last deployed: {ts}")
