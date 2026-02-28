import boto3, requests

cf = boto3.client('cloudfront', region_name='us-east-1')

# Find our distribution
print("=== CloudFront Distribution Status ===")
found = False
dists = cf.list_distributions()
for d in dists['DistributionList'].get('Items', []):
    origins = [o['DomainName'] for o in d['Origins']['Items']]
    if any('smart-rural-ai-frontend' in o for o in origins):
        found = True
        dist_id = d['Id']
        domain = d['DomainName']
        status = d['Status']
        print(f"  ID: {dist_id}")
        print(f"  Domain: https://{domain}")
        print(f"  Status: {status}")
        
        if status == 'Deployed':
            print("\n=== Testing CloudFront ===")
            
            # Root
            print("\n[1] GET / (root)")
            r = requests.get(f"https://{domain}/", timeout=15)
            print(f"    Status: {r.status_code}")
            print(f"    Has HTML: {'<html' in r.text.lower()}")
            print(f"    Has root div: {'id=' in r.text and 'root' in r.text}")
            print(f"    Size: {len(r.text)} bytes")
            
            # SPA route
            print("\n[2] GET /chat (SPA route)")
            r2 = requests.get(f"https://{domain}/chat", timeout=15)
            print(f"    Status: {r2.status_code}")
            print(f"    Has HTML: {'<html' in r2.text.lower()}")
            print(f"    Size: {len(r2.text)} bytes")
            
            # JS
            print("\n[3] GET /assets/index-BulfCnxW.js")
            r3 = requests.get(f"https://{domain}/assets/index-BulfCnxW.js", timeout=15)
            print(f"    Status: {r3.status_code}")
            print(f"    Content-Type: {r3.headers.get('Content-Type', 'N/A')}")
            print(f"    Size: {len(r3.content)} bytes")
            
            # CSS
            print("\n[4] GET /assets/index-FXDXUc_I.css")
            r4 = requests.get(f"https://{domain}/assets/index-FXDXUc_I.css", timeout=15)
            print(f"    Status: {r4.status_code}")
            print(f"    Content-Type: {r4.headers.get('Content-Type', 'N/A')}")
            print(f"    Size: {len(r4.content)} bytes")
            
            # Summary
            all_pass = all(x.status_code == 200 for x in [r, r2, r3, r4])
            print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
            print(f"LIVE URL: https://{domain}")
        else:
            print(f"\nDistribution still deploying ({status}). Wait a few minutes.")
        break

if not found:
    print("No CloudFront distribution found for smart-rural-ai-frontend.")
    print("\nFalling back to S3 website test...")
    s3_url = "http://smart-rural-ai-frontend-948809294205.s3-website.ap-south-1.amazonaws.com"
    r = requests.get(s3_url, timeout=10)
    print(f"  S3 root: {r.status_code}, size={len(r.text)}")
