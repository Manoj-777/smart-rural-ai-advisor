"""Add apiFetch import and replace raw fetch calls with auth-aware apiFetch across all frontend files."""
import re, os

BASE = r'c:\Users\RSManoj\Downloads\smart-rural-ai-advisor\frontend\src'

# Files and their relative import paths for apiFetch
FILES = {
    'pages/SchemesPage.jsx':        '../utils/apiFetch',
    'pages/CropRecommendPage.jsx':  '../utils/apiFetch',
    'pages/FarmCalendarPage.jsx':   '../utils/apiFetch',
    'pages/CropDoctorPage.jsx':     '../utils/apiFetch',
    'pages/WeatherPage.jsx':        '../utils/apiFetch',
    'pages/SoilAnalysisPage.jsx':   '../utils/apiFetch',
    'pages/PricePage.jsx':          '../utils/apiFetch',
    'pages/ProfilePage.jsx':        '../utils/apiFetch',
    'pages/ChatPage.jsx':           '../utils/apiFetch',
    'utils/asyncTts.js':            './apiFetch',
    'hooks/useSpeechRecognition.js': '../utils/apiFetch',
    'contexts/LanguageContext.jsx':  '../utils/apiFetch',
    'components/ChatMessage.jsx':   '../utils/apiFetch',
}

for rel_path, import_path in FILES.items():
    fp = os.path.join(BASE, rel_path)
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Add import if not already present
    if 'apiFetch' not in content:
        # Add after last import line
        lines = content.split('\n')
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import '):
                last_import_idx = i
        lines.insert(last_import_idx + 1, f"import {{ apiFetch }} from '{import_path}';")
        content = '\n'.join(lines)

    # 2. Replace fetch(`${config.API_URL}/path...`, opts) → apiFetch(`/path...`, opts)
    # Pattern: fetch(`${config.API_URL}/...`)  or  fetch(`${config.API_URL}/...`, {
    content = re.sub(
        r'fetch\(`\$\{config\.API_URL\}(/[^`]*)`\)',
        r'apiFetch(`\1`)',
        content
    )
    content = re.sub(
        r'fetch\(`\$\{config\.API_URL\}(/[^`]*)`\s*,\s*\{',
        r'apiFetch(`\1`, {',
        content
    )

    if content != original:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        changes = content.count('apiFetch') - original.count('apiFetch')
        print(f'  ✓ {rel_path} — {changes} changes')
    else:
        print(f'  - {rel_path} — no changes needed')

print('\nDone — all API calls now use authenticated apiFetch.')
