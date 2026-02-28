import boto3, json, time

cf = boto3.client('cloudfront', region_name='us-east-1')  # CloudFront is global
s3_bucket = 'smart-rural-ai-frontend-948809294205'
s3_origin = f'{s3_bucket}.s3-website.ap-south-1.amazonaws.com'

# Check if distribution already exists for this origin
print("Checking for existing CloudFront distribution...")
existing = cf.list_distributions()
dist_id = None
dist_domain = None

if 'DistributionList' in existing and 'Items' in existing['DistributionList']:
    for dist in existing['DistributionList']['Items']:
        for origin in dist['Origins']['Items']:
            if s3_bucket in origin.get('DomainName', ''):
                dist_id = dist['Id']
                dist_domain = dist['DomainName']
                print(f"  Found existing: {dist_id} -> {dist_domain}")
                break

if not dist_id:
    print("Creating new CloudFront distribution...")
    
    caller_ref = f'smart-rural-frontend-{int(time.time())}'
    
    config = {
        'CallerReference': caller_ref,
        'Comment': 'Smart Rural AI Advisor Frontend',
        'DefaultCacheBehavior': {
            'TargetOriginId': 's3-website',
            'ViewerProtocolPolicy': 'redirect-to-https',
            'AllowedMethods': {
                'Quantity': 2,
                'Items': ['GET', 'HEAD'],
                'CachedMethods': {
                    'Quantity': 2,
                    'Items': ['GET', 'HEAD']
                }
            },
            'ForwardedValues': {
                'QueryString': False,
                'Cookies': {'Forward': 'none'}
            },
            'MinTTL': 0,
            'DefaultTTL': 86400,
            'MaxTTL': 31536000,
            'Compress': True,
        },
        'Origins': {
            'Quantity': 1,
            'Items': [{
                'Id': 's3-website',
                'DomainName': s3_origin,
                'CustomOriginConfig': {
                    'HTTPPort': 80,
                    'HTTPSPort': 443,
                    'OriginProtocolPolicy': 'http-only'  # S3 website only serves HTTP
                }
            }]
        },
        'Enabled': True,
        'DefaultRootObject': 'index.html',
        # SPA routing: return index.html for 403/404 errors with 200 status
        'CustomErrorResponses': {
            'Quantity': 2,
            'Items': [
                {
                    'ErrorCode': 404,
                    'ResponsePagePath': '/index.html',
                    'ResponseCode': '200',
                    'ErrorCachingMinTTL': 0
                },
                {
                    'ErrorCode': 403,
                    'ResponsePagePath': '/index.html',
                    'ResponseCode': '200',
                    'ErrorCachingMinTTL': 0
                }
            ]
        },
        'PriceClass': 'PriceClass_200',  # Use only NA, EU, Asia (cheaper)
    }
    
    resp = cf.create_distribution(DistributionConfig=config)
    dist_id = resp['Distribution']['Id']
    dist_domain = resp['Distribution']['DomainName']
    status = resp['Distribution']['Status']
    print(f"  Created: {dist_id}")
    print(f"  Domain: {dist_domain}")
    print(f"  Status: {status} (takes ~5-10 min to deploy)")
else:
    # Update existing distribution to add custom error responses
    print(f"\nUpdating existing distribution {dist_id} with SPA error handling...")
    dist_config_resp = cf.get_distribution_config(Id=dist_id)
    etag = dist_config_resp['ETag']
    config = dist_config_resp['DistributionConfig']
    
    config['CustomErrorResponses'] = {
        'Quantity': 2,
        'Items': [
            {
                'ErrorCode': 404,
                'ResponsePagePath': '/index.html',
                'ResponseCode': '200',
                'ErrorCachingMinTTL': 0
            },
            {
                'ErrorCode': 403,
                'ResponsePagePath': '/index.html',
                'ResponseCode': '200',
                'ErrorCachingMinTTL': 0
            }
        ]
    }
    
    resp = cf.update_distribution(Id=dist_id, DistributionConfig=config, IfMatch=etag)
    dist_domain = resp['Distribution']['DomainName']
    print(f"  Updated!")

print(f"\n{'='*60}")
print(f"CloudFront Distribution ID: {dist_id}")
print(f"CloudFront URL: https://{dist_domain}")
print(f"{'='*60}")
print(f"\nThis URL will handle SPA routing correctly (all routes -> index.html with 200)")
print(f"Note: CloudFront takes ~5-10 minutes to fully deploy.")
