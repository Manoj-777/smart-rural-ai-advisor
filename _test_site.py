import urllib.request, json

base_url = 'http://smart-rural-ai-frontend-948809294205.s3-website.ap-south-1.amazonaws.com'

# Test 1: Fetch index.html
print("=== Test 1: index.html ===")
try:
    req = urllib.request.Request(base_url)
    resp = urllib.request.urlopen(req)
    html = resp.read().decode('utf-8')
    print(f"  Status: {resp.status}")
    print(f"  Size: {len(html)} bytes")
    print(f"  Has <div id='root'>: {'id=\"root\"' in html}")
    print(f"  Has script tag: {'<script' in html}")
    print(f"  Content:\n{html}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: Fetch JS bundle
print("\n=== Test 2: JS bundle ===")
try:
    req = urllib.request.Request(f'{base_url}/assets/index-BulfCnxW.js')
    resp = urllib.request.urlopen(req)
    js_size = len(resp.read())
    print(f"  Status: {resp.status}")
    print(f"  Size: {js_size} bytes")
    print(f"  Content-Type: {resp.headers['Content-Type']}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 3: Fetch CSS
print("\n=== Test 3: CSS ===")
try:
    req = urllib.request.Request(f'{base_url}/assets/index-FXDXUc_I.css')
    resp = urllib.request.urlopen(req)
    css_size = len(resp.read())
    print(f"  Status: {resp.status}")
    print(f"  Size: {css_size} bytes")
    print(f"  Content-Type: {resp.headers['Content-Type']}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 4: SPA route (/chat)
print("\n=== Test 4: /chat route (SPA fallback) ===")
try:
    req = urllib.request.Request(f'{base_url}/chat')
    resp = urllib.request.urlopen(req)
    chat_html = resp.read().decode('utf-8')
    print(f"  Status: {resp.status}")
    print(f"  Returns index.html: {'id=\"root\"' in chat_html}")
except urllib.error.HTTPError as e:
    print(f"  HTTP Error: {e.code} {e.reason}")
    body = e.read().decode('utf-8')
    print(f"  Body: {body[:500]}")
except Exception as e:
    print(f"  ERROR: {e}")
