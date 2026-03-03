"""
Fix location translation in Sidebar and DashboardPage.
When language changes, the location badge should show the translated district/city name.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent

# ────────────────────────────────────────────────────────────
# 1. Fix Sidebar.jsx — translate resolvedLocation display
# ────────────────────────────────────────────────────────────
sidebar = ROOT / 'frontend' / 'src' / 'components' / 'Sidebar.jsx'
src = sidebar.read_text(encoding='utf-8')
changes = 0

# Add import for getDistrictName
old_import = "import config from '../config';"
new_import = "import config from '../config';\nimport { getDistrictName } from '../i18n/districtTranslations';"
if 'getDistrictName' not in src and old_import in src:
    src = src.replace(old_import, new_import, 1)
    changes += 1
    print('[Sidebar] Added getDistrictName import')

# Fix the navbar location name display — translate it
old_loc = '<span className="navbar-loc-name">{resolvedLocation}</span>'
new_loc = '<span className="navbar-loc-name">{getDistrictName(resolvedLocation, language)}</span>'
if old_loc in src:
    src = src.replace(old_loc, new_loc, 1)
    changes += 1
    print('[Sidebar] Translated navbar-loc-name display')

# Fix the title attributes to also translate
old_title1 = "title={gpsStatus === 'granted' ? `GPS: ${resolvedLocation}` : `Profile: ${resolvedLocation}`}"
new_title1 = "title={gpsStatus === 'granted' ? `GPS: ${getDistrictName(resolvedLocation, language)}` : `${getDistrictName(resolvedLocation, language)}`}"
if old_title1 in src:
    src = src.replace(old_title1, new_title1, 1)
    changes += 1
    print('[Sidebar] Translated location tooltip')

# Fix hardcoded "Enable GPS location" title
old_title2 = 'title="Enable GPS location"'
new_title2 = "title={t('enableLocation') || 'Enable GPS location'}"
if old_title2 in src:
    src = src.replace(old_title2, new_title2, 1)
    changes += 1
    print('[Sidebar] Translated Enable GPS tooltip')

# Sidebar needs `language` from useLanguage — check if it destructures it
# Already has: const { t, language, setLanguage } = useLanguage(); ✅

if changes > 0:
    sidebar.write_text(src, encoding='utf-8')
    print(f'  → Wrote {changes} Sidebar fixes')

# ────────────────────────────────────────────────────────────
# 2. Fix DashboardPage.jsx — translate resolvedLocation display
# ────────────────────────────────────────────────────────────
dashboard = ROOT / 'frontend' / 'src' / 'pages' / 'DashboardPage.jsx'
src = dashboard.read_text(encoding='utf-8')
changes = 0

# Add import for getDistrictName
old_import_d = "import config from '../config';"
new_import_d = "import config from '../config';\nimport { getDistrictName } from '../i18n/districtTranslations';"
if 'getDistrictName' not in src and old_import_d in src:
    src = src.replace(old_import_d, new_import_d, 1)
    changes += 1
    print('[Dashboard] Added getDistrictName import')

# Check what useLanguage destructures
# Need to ensure `language` is available
if "const { t }" in src and "language" not in src.split("useLanguage")[0]:
    # Need to add language to the destructuring
    src = src.replace("const { t }", "const { t, language }", 1)
    changes += 1
    print('[Dashboard] Added language to useLanguage destructuring')
elif "const { t, language" in src:
    print('[Dashboard] language already in useLanguage destructuring')
elif "const { t } = useLanguage" in src:
    src = src.replace("const { t } = useLanguage", "const { t, language } = useLanguage", 1)
    changes += 1
    print('[Dashboard] Added language to useLanguage destructuring')

# Fix the location display
old_dash_loc = "{gpsStatus === 'granted' ? '📍' : '📌'} {resolvedLocation}"
new_dash_loc = "{gpsStatus === 'granted' ? '📍' : '📌'} {getDistrictName(resolvedLocation, language)}"
if old_dash_loc in src:
    src = src.replace(old_dash_loc, new_dash_loc, 1)
    changes += 1
    print('[Dashboard] Translated location display')
else:
    # Try with different emoji encoding
    import re
    # Match the pattern with any emoji chars
    pattern = r"\{gpsStatus === 'granted' \? '.' : '..?'\} \{resolvedLocation\}"
    matches = list(re.finditer(pattern, src))
    if matches:
        for m in matches:
            old = m.group()
            # Extract the emoji parts
            new = old.replace('{resolvedLocation}', '{getDistrictName(resolvedLocation, language)}')
            src = src.replace(old, new, 1)
            changes += 1
            print(f'[Dashboard] Translated location display (regex match)')

if changes > 0:
    dashboard.write_text(src, encoding='utf-8')
    print(f'  → Wrote {changes} Dashboard fixes')

# ────────────────────────────────────────────────────────────
# 3. Also check ProfilePage state dropdown — it already uses
#    getDistrictName + STATE_OPTION_OBJECTS ✅
# ────────────────────────────────────────────────────────────
print('\n✅ Done! Location will now be translated when language changes.')
print('Run: cd frontend && npx vite build')
