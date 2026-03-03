"""
Fix floating logo overlap with language bar on LoginPage,
fix regSoilType default, and audit/fix alignment across UI.
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent
CSS  = ROOT / 'frontend' / 'src' / 'App.css'
LOGIN = ROOT / 'frontend' / 'src' / 'pages' / 'LoginPage.jsx'

# ────────────────────────────────────────────────────────────
# 1. Fix LoginPage.jsx: regSoilType default 'Alluvial' → 'Alluvial Soil'
# ────────────────────────────────────────────────────────────
login_src = LOGIN.read_text(encoding='utf-8')
old_default = "const [regSoilType, setRegSoilType] = useState('Alluvial');"
new_default = "const [regSoilType, setRegSoilType] = useState('Alluvial Soil');"
if old_default in login_src:
    login_src = login_src.replace(old_default, new_default, 1)
    LOGIN.write_text(login_src, encoding='utf-8')
    print('[LoginPage] Fixed regSoilType default: Alluvial → Alluvial Soil')
else:
    print('[LoginPage] regSoilType default already correct or not found')

# ────────────────────────────────────────────────────────────
# 2. Fix App.css: Multiple alignment issues
# ────────────────────────────────────────────────────────────
css = CSS.read_text(encoding='utf-8')
changes = 0

# ── 2a. Login logo: add margin-top so bounce animation doesn't overlap lang bar
# Currently: .login-logo { margin-bottom: 40px; margin-top: 8px; }
# The logo icon is 72px with a bounce of -10px, and lang bar is at top:24px
# Fix: increase margin-top so logo clears the language bar
old_login_logo = """.login-logo {
    margin-bottom: 40px;
    margin-top: 8px;
}"""
new_login_logo = """.login-logo {
    margin-bottom: 32px;
    margin-top: 48px;
}"""
if old_login_logo in css:
    css = css.replace(old_login_logo, new_login_logo, 1)
    changes += 1
    print('[CSS] Fixed .login-logo margin-top: 8px → 48px (clears lang bar)')

# ── 2b. Login lang bar: make it flow in document instead of absolute
# to avoid overlap issues entirely on small screens.
# Actually let's keep it absolute but constrain the bounce so it can't reach it.
# Better: reduce bounce amplitude and ensure sufficient gap.
old_bounce = """@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}"""
new_bounce = """@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}"""
if old_bounce in css:
    css = css.replace(old_bounce, new_bounce, 1)
    changes += 1
    print('[CSS] Reduced bounce amplitude: -10px → -8px')

# ── 2c. Login container padding: ensure enough top padding 
# for the absolute-positioned lang bar not to crowd the logo
old_container = """.login-container {
    width: 100%;
    max-width: 520px;
    text-align: center;
    position: relative;
    z-index: 1;
    background: rgba(255,255,255,0.98);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 48px 40px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.5);
}"""
new_container = """.login-container {
    width: 100%;
    max-width: 520px;
    text-align: center;
    position: relative;
    z-index: 1;
    background: rgba(255,255,255,0.98);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 32px 40px 40px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.5);
}"""
if old_container in css:
    css = css.replace(old_container, new_container, 1)
    changes += 1
    print('[CSS] Adjusted .login-container padding: 48px 40px → 32px 40px 40px')

# ── 2d. Login lang: refine positioning - move it slightly inward for breathing room
old_lang = """.login-lang {
    position: absolute;
    top: 24px;
    right: 24px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    z-index: 10;
    background: var(--primary-50);
    padding: 8px 14px;
    border-radius: 20px;
    border: 2px solid var(--primary-light);
}"""
new_lang = """.login-lang {
    position: absolute;
    top: 16px;
    right: 16px;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    z-index: 10;
    background: var(--primary-50);
    padding: 6px 12px;
    border-radius: 20px;
    border: 2px solid var(--primary-light);
}"""
if old_lang in css:
    css = css.replace(old_lang, new_lang, 1)
    changes += 1
    print('[CSS] Compacted .login-lang: top:24→16, right:24→16, smaller padding')

# ── 2e. Mobile login container (max-width: 500px) - reduce padding
old_mobile_container = """@media (max-width: 500px) {
    .login-form-row, .login-form-row-3 {
        grid-template-columns: 1fr;
    }
    .login-container {
        padding: 32px 24px;
    }
}"""
new_mobile_container = """@media (max-width: 500px) {
    .login-form-row, .login-form-row-3 {
        grid-template-columns: 1fr;
    }
    .login-container {
        padding: 24px 18px 32px;
    }
    .login-lang {
        top: 12px;
        right: 12px;
        padding: 5px 10px;
        font-size: 12px;
    }
    .login-logo {
        margin-top: 40px;
        margin-bottom: 24px;
    }
}"""
if old_mobile_container in css:
    css = css.replace(old_mobile_container, new_mobile_container, 1)
    changes += 1
    print('[CSS] Fixed mobile login: added lang/logo overrides for small screens')

# ── 2f. Phone breakpoint login adjustments (existing at ~3579)
# Already has .login-logo-icon font-size:42px and .login-logo h1 font-size:20px
# Add specific overrides for the logo margin on very small screens
old_phone_login = """    /* Login \u2013 phone optimized */
    .login-page {
        padding: 12px;
    }
    .login-container {
        max-width: 100%;
    }
    .login-logo-icon {
        font-size: 42px;
    }
    .login-logo h1 {
        font-size: 20px;
    }"""

# Check for the actual text on disk (encoding issue with em-dash)
if old_phone_login not in css:
    # Try with different dash characters
    for dash in ['–', '—', '\u2013', '\u2014', '-']:
        test = old_phone_login.replace('\u2013', dash)
        if test in css:
            old_phone_login = test
            break

new_phone_login = old_phone_login.replace(
    """    .login-logo-icon {
        font-size: 42px;
    }
    .login-logo h1 {
        font-size: 20px;
    }""",
    """    .login-logo-icon {
        font-size: 42px;
    }
    .login-logo h1 {
        font-size: 20px;
    }
    .login-logo {
        margin-top: 36px;
        margin-bottom: 20px;
    }
    .login-lang {
        top: 10px;
        right: 10px;
        padding: 4px 8px;
        font-size: 11px;
        gap: 4px;
    }
    .login-lang select {
        padding: 3px 8px;
        font-size: 11px;
    }"""
)

if old_phone_login in css and old_phone_login != new_phone_login:
    css = css.replace(old_phone_login, new_phone_login, 1)
    changes += 1
    print('[CSS] Added phone-optimized login-logo + login-lang overrides at 480px')

# ── 2g. Fix login-logo-icon: ensure it doesn't escape its container  
old_icon = """.login-logo-icon {
    font-size: 72px;
    display: block;
    margin-bottom: 16px;
    animation: bounce 2s ease-in-out infinite;
}"""
new_icon = """.login-logo-icon {
    font-size: 64px;
    display: block;
    margin-bottom: 12px;
    animation: bounce 2s ease-in-out infinite;
    line-height: 1;
}"""
if old_icon in css:
    css = css.replace(old_icon, new_icon, 1)
    changes += 1
    print('[CSS] Adjusted .login-logo-icon: 72px → 64px, added line-height:1')

# ── 2h. Fix main-content padding consistency across breakpoints
# At 768px: padding: 16px 16px 24px (OK)
# At 480px: padding: 12px 10px 20px (OK)  
# At 360px: padding: 8px 6px 16px (OK)
# Base: padding: 24px 40px 40px (wide screens have big side padding)
# These look reasonable, skip.

# ── 2i. Fix the login form register scroll area
# The .login-form-register might not scroll properly on small phones
old_register_hint = """.login-form-register .login-form-group {
    margin-bottom: 18px;
}
.login-form-register h2 {
    margin-bottom: 20px;
}"""
new_register_hint = """.login-form-register {
    max-height: calc(100vh - 200px);
    overflow-y: auto;
}
.login-form-register .login-form-group {
    margin-bottom: 16px;
}
.login-form-register h2 {
    margin-bottom: 16px;
}"""
if old_register_hint in css:
    css = css.replace(old_register_hint, new_register_hint, 1)
    changes += 1
    print('[CSS] Added scroll container for .login-form-register on small screens')

# ── 2j. Ensure page-header alignment is consistent
# page-header has padding: 16px 24px, which is fine
# But let's verify the h2 inside has proper margins
# This is fine from what I see.

# ── 2k. Fix navbar links overflow on tablets - ensure proper alignment
# navbar-links has flex:1 overflow-x:auto - this is fine

# ── 2l. Ensure delete-zone alignment on mobile
old_delete_mobile = """@media (max-width: 480px) {
    .delete-zone-inner {"""
if old_delete_mobile in css:
    # Already handled in earlier script, just verify
    print('[CSS] delete-zone mobile styles already present')

# ── Write CSS changes back ──
if changes > 0:
    CSS.write_text(css, encoding='utf-8')
    print(f'\n✅ Wrote {changes} CSS fixes to App.css')
else:
    print('\n⚠️  No CSS changes applied (blocks not found on disk)')

print('\nDone! Run: cd frontend && npx vite build')
