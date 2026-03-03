"""
Fix duplicate location + UI enhancements:
1. Remove location from dashboard hero (already in navbar)
2. Polish bottom nav with glass morphism effect
3. Improve dashboard hero & action cards
4. Better visual hierarchy & modern feel
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
CSS  = ROOT / 'frontend' / 'src' / 'App.css'
DASH = ROOT / 'frontend' / 'src' / 'pages' / 'DashboardPage.jsx'

# ────────────────────────────────────────────────────────────
# 1. Remove duplicate location from DashboardPage.jsx
# ────────────────────────────────────────────────────────────
dash_src = DASH.read_text(encoding='utf-8')

# Remove the getDistrictName import (no longer needed)
dash_src = dash_src.replace(
    "import { getDistrictName } from '../i18n/districtTranslations';\n", '', 1)

# Remove resolvedLocation and gpsStatus from useFarmer destructuring
dash_src = dash_src.replace(
    "const { farmerName, resolvedLocation, gpsStatus, requestGps } = useFarmer();",
    "const { farmerName } = useFarmer();", 1)

# Remove the location block from the hero section
# Find and remove the resolvedLocation block + the GPS request block
# Remove the location display blocks from dashboard using line-based approach
dlines = dash_src.splitlines(keepends=True)
new_dlines = []
skip_depth = 0
in_location_block = False
removed = 0
for line in dlines:
    stripped = line.strip()
    if not in_location_block and ('resolvedLocation &&' in line or ('!resolvedLocation' in line and 'gpsStatus' in line)):
        in_location_block = True
        skip_depth = line.count('{') - line.count('}')
        removed += 1
        continue
    if in_location_block:
        skip_depth += line.count('{') - line.count('}')
        removed += 1
        if skip_depth <= 0:
            in_location_block = False
        continue
    new_dlines.append(line)

if removed > 0:
    dash_src = ''.join(new_dlines)
    print(f'[OK] Removed location block ({removed} lines)')
else:
    print('[WARN] Could not find location block to remove')

DASH.write_text(dash_src, encoding='utf-8')
print('[OK] DashboardPage.jsx updated - no duplicate location')

# ────────────────────────────────────────────────────────────
# 2. CSS Enhancements
# ────────────────────────────────────────────────────────────
lines = CSS.read_text(encoding='utf-8').splitlines(keepends=True)

def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return -1

def find_closing_brace(start):
    brace = 0
    for i in range(start, len(lines)):
        brace += lines[i].count('{') - lines[i].count('}')
        if brace == 0:
            return i
    return -1

changes = 0

# ── 2a. Enhance the top navbar with better glass effect ──
idx_topnav = find_line('.top-navbar {')
if idx_topnav >= 0 and idx_topnav < 310:
    end_topnav = find_closing_brace(idx_topnav)
    new_topnav = """.top-navbar {
    background: linear-gradient(135deg, #166534 0%, #0f4a28 50%, #14532d 100%);
    color: white;
    display: flex;
    align-items: center;
    padding: 0 16px;
    height: 54px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 20px rgba(0,0,0,0.18);
    gap: 6px;
    backdrop-filter: blur(10px);
}
"""
    lines[idx_topnav:end_topnav+1] = [new_topnav]
    print(f'[OK] Enhanced top-navbar style')
    changes += 1

# ── 2b. Upgrade dashboard hero with gradient animation ──
idx_hero = find_line('.dash-hero {')
if idx_hero >= 0:
    end_hero = find_closing_brace(idx_hero)
    # Read current content to preserve most, just enhance
    new_hero = """.dash-hero {
    background: linear-gradient(135deg, #166534 0%, #15803d 40%, #22c55e 100%);
    color: white;
    border-radius: 20px;
    padding: 28px 28px 24px;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(22,101,52,0.25);
    animation: heroGlow 4s ease-in-out infinite alternate;
}
@keyframes heroGlow {
    0% { box-shadow: 0 8px 32px rgba(22,101,52,0.25); }
    100% { box-shadow: 0 12px 40px rgba(34,197,94,0.3); }
}
"""
    lines[idx_hero:end_hero+1] = [new_hero]
    print(f'[OK] Enhanced dash-hero gradient')
    changes += 1

# ── 2c. Upgrade action cards with better hover effects ──
idx_card = find_line('.dash-action-card {')
if idx_card >= 0:
    end_card = find_closing_brace(idx_card)
    new_card = """.dash-action-card {
    background: var(--card-bg);
    border: 2px solid var(--border-light);
    border-radius: 16px;
    padding: 18px 16px;
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    text-align: left;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    position: relative;
    overflow: hidden;
}
"""
    lines[idx_card:end_card+1] = [new_card]
    print(f'[OK] Enhanced action cards')
    changes += 1

# ── 2d. Better card hover effect ──
idx_hover = find_line('.dash-action-card:hover {')
if idx_hover >= 0:
    end_hover = find_closing_brace(idx_hover)
    new_hover = """.dash-action-card:hover {
    border-color: var(--action-color, var(--primary));
    transform: translateY(-6px) scale(1.02);
    box-shadow: 0 12px 28px rgba(0,0,0,0.12);
}
"""
    lines[idx_hover:end_hover+1] = [new_hover]
    print(f'[OK] Enhanced card hover effect')
    changes += 1

# ── 2e. Upgrade the bottom nav with glass morphism ──
idx_bottom = find_line('.bottom-nav {', find_line('@media (max-width: 600px)', find_line('Bottom Navigation')))
if idx_bottom >= 0:
    end_bottom = find_closing_brace(idx_bottom)
    new_bottom = """    .bottom-nav {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 200;
        background: linear-gradient(135deg, rgba(22,101,52,0.95) 0%, rgba(20,83,45,0.97) 100%);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        box-shadow: 0 -4px 20px rgba(0,0,0,0.2);
        padding: 6px 4px 8px;
        gap: 2px;
        padding-bottom: max(8px, env(safe-area-inset-bottom));
        border-top: 1px solid rgba(255,255,255,0.08);
    }
"""
    lines[idx_bottom:end_bottom+1] = [new_bottom]
    print(f'[OK] Enhanced bottom-nav glass effect')
    changes += 1

# ── 2f. Better bottom nav items ──
idx_bni = find_line('.bottom-nav-item {', find_line('Bottom Navigation'))
if idx_bni >= 0:
    end_bni = find_closing_brace(idx_bni)
    new_bni = """    .bottom-nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        color: rgba(255,255,255,0.5);
        font-size: 10px;
        padding: 5px 2px 3px;
        border-radius: 10px;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        gap: 2px;
        min-width: 0;
    }
"""
    lines[idx_bni:end_bni+1] = [new_bni]
    print(f'[OK] Enhanced bottom-nav-item')
    changes += 1

# ── 2g. Better active state for bottom nav ──
idx_active = find_line('.bottom-nav-item.active {', find_line('Bottom Navigation'))
if idx_active >= 0:
    end_active = find_closing_brace(idx_active)
    new_active = """    .bottom-nav-item.active {
        color: #4ade80;
        background: rgba(74,222,128,0.15);
        box-shadow: 0 0 12px rgba(74,222,128,0.15);
    }
"""
    lines[idx_active:end_active+1] = [new_active]
    print(f'[OK] Enhanced bottom-nav active state')
    changes += 1

# ── 2h. Better bottom nav icon sizing ──
idx_bicon = find_line('.bottom-nav-icon {', find_line('Bottom Navigation'))
if idx_bicon >= 0:
    end_bicon = find_closing_brace(idx_bicon)
    new_bicon = """    .bottom-nav-icon {
        font-size: 22px;
        line-height: 1;
        transition: transform 0.2s ease;
    }
"""
    lines[idx_bicon:end_bicon+1] = [new_bicon]
    print(f'[OK] Enhanced bottom-nav icon')
    changes += 1

# ── 2i. Better bottom nav label ──
idx_blabel = find_line('.bottom-nav-label {', find_line('Bottom Navigation'))
if idx_blabel >= 0:
    end_blabel = find_closing_brace(idx_blabel)
    new_blabel = """    .bottom-nav-label {
        font-size: 9.5px;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
        text-align: center;
        line-height: 1.2;
        letter-spacing: 0.01em;
    }
"""
    lines[idx_blabel:end_blabel+1] = [new_blabel]
    print(f'[OK] Enhanced bottom-nav label')
    changes += 1

# ── 2j. Improve the daily tip card ──
idx_tip = find_line('.dash-tip-card {')
if idx_tip >= 0 and idx_tip < 2500:
    end_tip = find_closing_brace(idx_tip)
    new_tip = """.dash-tip-card {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    background: linear-gradient(135deg, #fef9c3 0%, #fde68a 50%, #fef3c7 100%);
    border: 1px solid #fbbf24;
    border-radius: 16px;
    padding: 16px 20px;
    flex-shrink: 0;
    box-shadow: 0 4px 16px rgba(251,191,36,0.15);
    transition: transform 0.2s ease;
}
.dash-tip-card:hover {
    transform: translateY(-2px);
}
"""
    lines[idx_tip:end_tip+1] = [new_tip]
    print(f'[OK] Enhanced daily tip card')
    changes += 1

# ── 2k. Add smooth scroll and better main content area ──
idx_main = find_line('.main-content {')
if idx_main >= 0 and idx_main < 300:
    end_main = find_closing_brace(idx_main)
    old_main_css = ''.join(lines[idx_main:end_main+1])
    # Only enhance if it doesn't already have scroll-behavior
    if 'scroll-behavior' not in old_main_css:
        new_main = """.main-content {
    flex: 1;
    padding: 20px 24px 24px;
    overflow-y: auto;
    background: var(--bg);
    scroll-behavior: smooth;
}
"""
        lines[idx_main:end_main+1] = [new_main]
        print(f'[OK] Enhanced main-content with smooth scroll')
        changes += 1

# ── 2l. Enhance the navbar brand text ──
idx_brand_text = find_line('.navbar-brand .brand-text {')
if idx_brand_text >= 0 and idx_brand_text < 330:
    end_bt = find_closing_brace(idx_brand_text)
    new_bt = """.navbar-brand .brand-text {
    font-size: 15px;
    font-weight: 800;
    white-space: nowrap;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #fff, #bbf7d0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
"""
    lines[idx_brand_text:end_bt+1] = [new_bt]
    print(f'[OK] Enhanced brand text gradient')
    changes += 1

# Write all changes
CSS.write_text(''.join(lines), encoding='utf-8')
print(f'\n\u2705 Done! {changes} enhancements applied.')
print('Next: cd frontend && npx vite build')
