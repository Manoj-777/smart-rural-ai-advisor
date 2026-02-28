import requests

urls = {
    'S3': 'http://smart-rural-ai-frontend-948809294205.s3-website.ap-south-1.amazonaws.com',
    'CloudFront': 'https://d80ytlzsrax1n.cloudfront.net',
}

for label, base in urls.items():
    print(f"\n{'='*60}")
    print(f"  Testing: {label} ({base})")
    print(f"{'='*60}")
    
    # Root
    try:
        r = requests.get(base + '/', timeout=15)
        has_root = 'id="root"' in r.text
        has_js = 'index-BulfCnxW.js' in r.text
        print(f"  /          -> {r.status_code}  HTML={has_root}  JS-ref={has_js}  size={len(r.text)}")
    except Exception as e:
        print(f"  /          -> ERROR: {e}")
    
    # /chat SPA route
    try:
        r2 = requests.get(base + '/chat', timeout=15)
        has_root2 = 'id="root"' in r2.text
        print(f"  /chat      -> {r2.status_code}  HTML={has_root2}  size={len(r2.text)}")
    except Exception as e:
        print(f"  /chat      -> ERROR: {e}")
    
    # /profile SPA route
    try:
        r3 = requests.get(base + '/profile', timeout=15)
        has_root3 = 'id="root"' in r3.text
        print(f"  /profile   -> {r3.status_code}  HTML={has_root3}  size={len(r3.text)}")
    except Exception as e:
        print(f"  /profile   -> ERROR: {e}")
    
    # JS
    try:
        r4 = requests.get(base + '/assets/index-BulfCnxW.js', timeout=15)
        ct = r4.headers.get('Content-Type', '')
        print(f"  JS bundle  -> {r4.status_code}  type={ct}  size={len(r4.content)}")
    except Exception as e:
        print(f"  JS bundle  -> ERROR: {e}")
    
    # CSS
    try:
        r5 = requests.get(base + '/assets/index-FXDXUc_I.css', timeout=15)
        ct = r5.headers.get('Content-Type', '')
        print(f"  CSS bundle -> {r5.status_code}  type={ct}  size={len(r5.content)}")
    except Exception as e:
        print(f"  CSS bundle -> ERROR: {e}")

print("\n\nDONE")
