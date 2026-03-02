"""
CloudWatch Dashboard — Smart Rural AI Advisor
Creates a comprehensive monitoring dashboard covering:
  • API Gateway (requests, errors, latency)
  • Lambda (invocations, errors, duration, throttles) for all 8 functions
  • DynamoDB (read/write, throttles) for all 4 tables
  • S3 (requests, bytes) for main bucket
  • CloudFront (requests, error rate)

Fully standalone — reads existing resources, no changes to infrastructure.
Idempotent — safe to run multiple times (updates existing dashboard).
"""

import boto3
import json

REGION = 'ap-south-1'
ACCOUNT = '948809294205'
DASHBOARD_NAME = 'SmartRuralAI-Operations'

# ── Resources ──────────────────────────────────────────────
API_GW_NAME = 'smart-rural-ai'
API_GW_ID = 'zuadk9l1nc'
API_GW_STAGE = 'Prod'

LAMBDA_FUNCTIONS = [
    'smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM',
    'smart-rural-ai-WeatherFunction-dilSoHSLlXGN',
    'smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY',
    'smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv',
    'smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt',
    'smart-rural-ai-ImageAnalysisFunction-wY2rBz7uHgKV',
    'smart-rural-ai-TranscribeSpeechFunction-rF4EDECy1VaO',
    'smart-rural-ai-HealthCheckFunction-FQB8TfJ91HKs',
]

# Short names for display
LAMBDA_SHORT = {f: f.split('-')[-1][:12] for f in LAMBDA_FUNCTIONS}
# Better short names
LAMBDA_SHORT = {
    'smart-rural-ai-AgentOrchestratorFunction-9L6obTRaxJHM': 'Orchestrator',
    'smart-rural-ai-WeatherFunction-dilSoHSLlXGN': 'Weather',
    'smart-rural-ai-CropAdvisoryFunction-Z8jAKbsH7mkY': 'CropAdvisory',
    'smart-rural-ai-GovtSchemesFunction-BgTy36y4fgGv': 'GovtSchemes',
    'smart-rural-ai-FarmerProfileFunction-mEzTIZOAvxKt': 'FarmerProfile',
    'smart-rural-ai-ImageAnalysisFunction-wY2rBz7uHgKV': 'ImageAnalysis',
    'smart-rural-ai-TranscribeSpeechFunction-rF4EDECy1VaO': 'Transcribe',
    'smart-rural-ai-HealthCheckFunction-FQB8TfJ91HKs': 'HealthCheck',
}

DYNAMODB_TABLES = ['farmer_profiles', 'chat_sessions', 'otp_codes', 'rate_limits']
S3_BUCKET = f'smart-rural-ai-{ACCOUNT}'
CLOUDFRONT_DIST = 'E2HUWT1BUYIIRG'


def _lambda_metric(metric, stat, fns, title, period=300, y_label='Count'):
    """Build a Lambda metric widget with one line per function."""
    metrics = []
    for fn in fns:
        metrics.append([
            'AWS/Lambda', metric, 'FunctionName', fn,
            {'label': LAMBDA_SHORT[fn], 'stat': stat, 'period': period}
        ])
    return {
        'type': 'metric',
        'width': 12,
        'height': 6,
        'properties': {
            'title': title,
            'region': REGION,
            'metrics': metrics,
            'view': 'timeSeries',
            'stacked': False,
            'yAxis': {'left': {'label': y_label, 'min': 0}},
            'period': period,
        }
    }


def _api_gw_widget():
    """API Gateway overview — requests, 4XX, 5XX, latency."""
    dims = ['ApiName', API_GW_NAME, 'Stage', API_GW_STAGE]
    return {
        'type': 'metric',
        'width': 24,
        'height': 6,
        'properties': {
            'title': 'API Gateway — Requests & Errors',
            'region': REGION,
            'metrics': [
                ['AWS/ApiGateway', 'Count', *dims, {'stat': 'Sum', 'label': 'Total Requests', 'color': '#2ca02c'}],
                ['AWS/ApiGateway', '4XXError', *dims, {'stat': 'Sum', 'label': '4XX Errors', 'color': '#ff7f0e'}],
                ['AWS/ApiGateway', '5XXError', *dims, {'stat': 'Sum', 'label': '5XX Errors', 'color': '#d62728'}],
            ],
            'view': 'timeSeries',
            'stacked': False,
            'period': 300,
            'yAxis': {'left': {'label': 'Count', 'min': 0}},
        }
    }


def _api_latency_widget():
    """API Gateway latency — p50, p90, p99."""
    dims = ['ApiName', API_GW_NAME, 'Stage', API_GW_STAGE]
    return {
        'type': 'metric',
        'width': 12,
        'height': 6,
        'properties': {
            'title': 'API Gateway — Latency (ms)',
            'region': REGION,
            'metrics': [
                ['AWS/ApiGateway', 'Latency', *dims, {'stat': 'p50', 'label': 'p50'}],
                ['AWS/ApiGateway', 'Latency', *dims, {'stat': 'p90', 'label': 'p90', 'color': '#ff7f0e'}],
                ['AWS/ApiGateway', 'Latency', *dims, {'stat': 'p99', 'label': 'p99', 'color': '#d62728'}],
                ['AWS/ApiGateway', 'IntegrationLatency', *dims, {'stat': 'p90', 'label': 'Integration p90', 'color': '#9467bd'}],
            ],
            'view': 'timeSeries',
            'stacked': False,
            'period': 300,
            'yAxis': {'left': {'label': 'ms', 'min': 0}},
        }
    }


def _dynamodb_widget():
    """DynamoDB — consumed RCU/WCU for all tables."""
    metrics = []
    colors = ['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728']
    for i, table in enumerate(DYNAMODB_TABLES):
        metrics.append([
            'AWS/DynamoDB', 'ConsumedReadCapacityUnits', 'TableName', table,
            {'stat': 'Sum', 'label': f'{table} (Read)', 'color': colors[i % len(colors)]}
        ])
    for i, table in enumerate(DYNAMODB_TABLES):
        metrics.append([
            'AWS/DynamoDB', 'ConsumedWriteCapacityUnits', 'TableName', table,
            {'stat': 'Sum', 'label': f'{table} (Write)', 'color': colors[i % len(colors)], 'yAxis': 'right'}
        ])
    return {
        'type': 'metric',
        'width': 12,
        'height': 6,
        'properties': {
            'title': 'DynamoDB — Read/Write Capacity',
            'region': REGION,
            'metrics': metrics,
            'view': 'timeSeries',
            'stacked': False,
            'period': 300,
            'yAxis': {
                'left': {'label': 'Read CU', 'min': 0},
                'right': {'label': 'Write CU', 'min': 0},
            },
        }
    }


def _dynamodb_errors_widget():
    """DynamoDB throttles and errors."""
    metrics = []
    for table in DYNAMODB_TABLES:
        metrics.append([
            'AWS/DynamoDB', 'ThrottledRequests', 'TableName', table,
            {'stat': 'Sum', 'label': f'{table} Throttles'}
        ])
        metrics.append([
            'AWS/DynamoDB', 'SystemErrors', 'TableName', table,
            {'stat': 'Sum', 'label': f'{table} Errors'}
        ])
    return {
        'type': 'metric',
        'width': 12,
        'height': 6,
        'properties': {
            'title': 'DynamoDB — Throttles & Errors',
            'region': REGION,
            'metrics': metrics,
            'view': 'timeSeries',
            'stacked': True,
            'period': 300,
            'yAxis': {'left': {'label': 'Count', 'min': 0}},
        }
    }


def _cloudfront_widget():
    """CloudFront — requests and error rate."""
    return {
        'type': 'metric',
        'width': 12,
        'height': 6,
        'properties': {
            'title': 'CloudFront CDN — Frontend',
            'region': 'us-east-1',  # CloudFront metrics are always us-east-1
            'metrics': [
                ['AWS/CloudFront', 'Requests', 'DistributionId', CLOUDFRONT_DIST, 'Region', 'Global',
                 {'stat': 'Sum', 'label': 'Requests', 'color': '#2ca02c'}],
                ['AWS/CloudFront', 'TotalErrorRate', 'DistributionId', CLOUDFRONT_DIST, 'Region', 'Global',
                 {'stat': 'Average', 'label': 'Error Rate %', 'color': '#d62728', 'yAxis': 'right'}],
                ['AWS/CloudFront', 'BytesDownloaded', 'DistributionId', CLOUDFRONT_DIST, 'Region', 'Global',
                 {'stat': 'Sum', 'label': 'Bytes Downloaded', 'color': '#1f77b4'}],
            ],
            'view': 'timeSeries',
            'stacked': False,
            'period': 300,
            'yAxis': {
                'left': {'label': 'Requests / Bytes', 'min': 0},
                'right': {'label': 'Error Rate %', 'min': 0, 'max': 100},
            },
        }
    }


def _header_widget(text, width=24):
    """Section header text widget."""
    return {
        'type': 'text',
        'width': width,
        'height': 1,
        'properties': {'markdown': f'## {text}'}
    }


def build_dashboard_body():
    """Build the full dashboard JSON."""
    widgets = [
        # ── Overview Header ──
        _header_widget('🚀 Smart Rural AI Advisor — Operations Dashboard'),

        # ── API Gateway Row ──
        _header_widget('📡 API Gateway'),
        _api_gw_widget(),
        _api_latency_widget(),
        _cloudfront_widget(),

        # ── Lambda Row ──
        _header_widget('⚡ Lambda Functions'),
        _lambda_metric('Invocations', 'Sum', LAMBDA_FUNCTIONS,
                        'Lambda — Invocations'),
        _lambda_metric('Errors', 'Sum', LAMBDA_FUNCTIONS,
                        'Lambda — Errors'),
        _lambda_metric('Duration', 'Average', LAMBDA_FUNCTIONS,
                        'Lambda — Avg Duration', y_label='ms'),
        _lambda_metric('Throttles', 'Sum', LAMBDA_FUNCTIONS,
                        'Lambda — Throttles'),

        # ── Lambda Memory & Concurrency ──
        _lambda_metric('ConcurrentExecutions', 'Maximum', LAMBDA_FUNCTIONS,
                        'Lambda — Concurrent Executions'),
        _lambda_metric('Duration', 'p99', LAMBDA_FUNCTIONS,
                        'Lambda — p99 Duration', y_label='ms'),

        # ── DynamoDB Row ──
        _header_widget('🗄️ DynamoDB'),
        _dynamodb_widget(),
        _dynamodb_errors_widget(),
    ]
    return {'widgets': widgets}


def main():
    print('=' * 60)
    print('  CloudWatch Dashboard — Smart Rural AI Advisor')
    print('=' * 60)

    cw = boto3.client('cloudwatch', region_name=REGION)

    body = build_dashboard_body()
    body_json = json.dumps(body)

    print(f'\nCreating dashboard: {DASHBOARD_NAME}')
    print(f'  Widgets: {len(body["widgets"])}')
    print(f'  Lambda functions: {len(LAMBDA_FUNCTIONS)}')
    print(f'  DynamoDB tables: {len(DYNAMODB_TABLES)}')

    cw.put_dashboard(
        DashboardName=DASHBOARD_NAME,
        DashboardBody=body_json,
    )

    console_url = (
        f'https://{REGION}.console.aws.amazon.com/cloudwatch/home'
        f'?region={REGION}#dashboards/dashboard/{DASHBOARD_NAME}'
    )
    print(f'\n✅ Dashboard created successfully!')
    print(f'\n  Open in console:\n  {console_url}')
    print()


if __name__ == '__main__':
    main()
