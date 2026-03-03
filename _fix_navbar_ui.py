"""
Enhance navbar UI:
- Desktop/tablet: compact nav links, no need to scroll
- Phone (<600px): bottom tab bar with 5-column grid (2 rows)
- All features visible without dragging/scrolling
Uses line-based approach to handle encoding issues.
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent
CSS  = ROOT / 'frontend' / 'src' / 'App.css'
SIDEBAR = ROOT / 'frontend' / 'src' / 'components' / 'Sidebar.jsx'

# ────────────────────────────────────────────────────────────
# 1. Rewrite Sidebar.jsx with bottom nav for phones
# ────────────────────────────────────────────────────────────
NEW_SIDEBAR = r'''// src/components/Sidebar.jsx

import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import config from '../config';
import { getDistrictName } from '../i18n/districtTranslations';

function Sidebar() {
    const { t, language, setLanguage } = useLanguage();
    const { farmerName, farmerPhone, logout, resolvedLocation, gpsStatus, requestGps } = useFarmer();
    const navigate = useNavigate();

    const navItems = [
        { to: '/', end: true, icon: '\u{1F3E0}', labelKey: 'navDashboard' },
        { to: '/chat', icon: '\u{1F4AC}', labelKey: 'navChat' },
        { to: '/weather', icon: '\u{1F324}\uFE0F', labelKey: 'navWeather', prefetch: '../pages/WeatherPage' },
        { to: '/schemes', icon: '\u{1F4CB}', labelKey: 'navSchemes', prefetch: '../pages/SchemesPage' },
        { to: '/crop-doctor', icon: '\u{1F4F8}', labelKey: 'navCropDoctor', prefetch: '../pages/CropDoctorPage' },
        { to: '/prices', icon: '\u{1F4B0}', labelKey: 'navPrices', prefetch: '../pages/PricePage' },
        { to: '/crop-recommend', icon: '\u{1F331}', labelKey: 'navCropRec', prefetch: '../pages/CropRecommendPage' },
        { to: '/farm-calendar', icon: '\u{1F4C5}', labelKey: 'navFarmCal', prefetch: '../pages/FarmCalendarPage' },
        { to: '/soil-analysis', icon: '\u{1F9EA}', labelKey: 'navSoilAnalysis', prefetch: '../pages/SoilAnalysisPage' },
    ];

    return (
        <>
            {/* ── Top navbar: brand + desktop links + location + lang + user ── */}
            <nav className="top-navbar">
                <div className="navbar-brand">
                    <span className="brand-icon">{'\u{1F33E}'}</span>
                    <span className="brand-text">{t('appName')}</span>
                </div>

                {/* Desktop/tablet nav links (hidden on phones via CSS) */}
                <div className="navbar-links navbar-links-desktop">
                    {navItems.map(item => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.end || false}
                            className={({isActive}) => isActive ? 'active' : ''}
                            onMouseEnter={item.prefetch ? () => import(item.prefetch) : undefined}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            <span className="nav-label">{t(item.labelKey)}</span>
                        </NavLink>
                    ))}
                </div>

                {/* Location indicator */}
                {resolvedLocation && (
                    <button
                        className="navbar-location-badge"
                        onClick={() => { if (gpsStatus !== 'granted') requestGps(); }}
                        title={gpsStatus === 'granted' ? `GPS: ${getDistrictName(resolvedLocation, language)}` : getDistrictName(resolvedLocation, language)}
                    >
                        <span className="navbar-loc-icon">{gpsStatus === 'granted' ? '\u{1F4CD}' : '\u{1F4CC}'}</span>
                        <span className="navbar-loc-name">{getDistrictName(resolvedLocation, language)}</span>
                    </button>
                )}
                {!resolvedLocation && gpsStatus !== 'denied' && (
                    <button
                        className="navbar-location-badge navbar-location-badge--request"
                        onClick={requestGps}
                        title={t('enableLocation') || 'Enable GPS location'}
                    >
                        <span className="navbar-loc-icon">{'\u{1F4CD}'}</span>
                        <span className="navbar-loc-name">{t('enableLocation') || 'Set location'}</span>
                    </button>
                )}

                <div className="navbar-lang">
                    <span className="navbar-lang-icon">{'\u{1F310}'}</span>
                    <select
                        className="navbar-lang-select"
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                    >
                        {Object.entries(config.LANGUAGES).map(([code, lang]) => (
                            <option key={code} value={code}>{lang.name}</option>
                        ))}
                    </select>
                </div>

                {/* User info + logout */}
                <div className="navbar-user">
                    {farmerName && (
                        <button className="navbar-user-name-btn" onClick={() => navigate('/profile')}
                            title={t('navProfile')}>
                            <span className="navbar-user-avatar">{'\u{1F464}'}</span>
                            <span className="navbar-user-name">{farmerName}</span>
                        </button>
                    )}
                    <button className="navbar-logout-btn" onClick={logout} title={t('loginLogout')}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                            <polyline points="16 17 21 12 16 7"/>
                            <line x1="21" y1="12" x2="9" y2="12"/>
                        </svg>
                    </button>
                </div>
            </nav>

            {/* ── Bottom tab bar: only visible on phones (<600px) ── */}
            <nav className="bottom-nav">
                {navItems.map(item => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        end={item.end || false}
                        className={({isActive}) => `bottom-nav-item${isActive ? ' active' : ''}`}
                    >
                        <span className="bottom-nav-icon">{item.icon}</span>
                        <span className="bottom-nav-label">{t(item.labelKey)}</span>
                    </NavLink>
                ))}
            </nav>
        </>
    );
}

export default Sidebar;
'''

SIDEBAR.write_text(NEW_SIDEBAR.lstrip('\n'), encoding='utf-8')
print('[OK] Sidebar.jsx rewritten with bottom-nav')

# ────────────────────────────────────────────────────────────
# 2. Update App.css using line-based approach
# ────────────────────────────────────────────────────────────
lines = CSS.read_text(encoding='utf-8').splitlines(keepends=True)

# Helper: find line index containing a pattern
def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return -1

changes = 0

# ── 2a. Fix 600px: replace wrapping navbar with clean top bar ──
idx_600 = find_line('@media (max-width: 600px)')
if idx_600 >= 0:
    # Find the closing brace of this media query
    brace = 0
    end_600 = idx_600
    for i in range(idx_600, len(lines)):
        brace += lines[i].count('{') - lines[i].count('}')
        if brace == 0:
            end_600 = i
            break
    new_600 = """@media (max-width: 600px) {
    .top-navbar {
        height: 48px;
        padding: 0 10px;
        gap: 6px;
    }
    /* Hide desktop nav links on phones \u2014 bottom nav replaces them */
    .navbar-links-desktop {
        display: none !important;
    }
    .navbar-user {
        margin-left: auto;
    }
    .navbar-user-name {
        display: none;
    }
    .lang-bar {
        padding: 8px 16px 0;
    }
}
"""
    lines[idx_600:end_600+1] = [new_600]
    print(f'[OK] Replaced 600px breakpoint (was lines {idx_600+1}-{end_600+1})')
    changes += 1

# ── 2b. Fix 480px navbar section ──
idx_480_nav = find_line('Top Navbar')
if idx_480_nav >= 0 and idx_480_nav > 3000:  # make sure it's in the 480px breakpoint
    # Find the end: it's the line before "Dashboard" comment or next section
    idx_dash = find_line('Dashboard', idx_480_nav + 1)
    if idx_dash < 0:
        idx_dash = find_line('.dashboard', idx_480_nav + 1)
    
    new_480_nav = """    /* Top Navbar \u2013 compact for phones (nav in bottom bar) */
    .top-navbar {
        height: 44px;
        padding: 0 10px;
        flex-wrap: nowrap;
        gap: 6px;
    }
    .navbar-links-desktop {
        display: none !important;
    }
    .navbar-brand {
        margin-right: auto;
    }
    .navbar-brand .brand-icon {
        font-size: 20px;
    }
    .navbar-brand .brand-text {
        font-size: 13px;
        font-weight: 700;
    }
    .navbar-lang-select {
        max-width: none;
        font-size: 11px;
        padding: 3px 6px;
    }
    .navbar-user {
        margin-left: 0;
        gap: 4px;
    }
    .navbar-user-name {
        display: none;
    }
    .navbar-user-name-btn {
        padding: 4px 8px;
    }
    .navbar-logout-btn {
        width: 28px;
        height: 28px;
    }
    .navbar-location-badge {
        max-width: 110px;
        padding: 3px 6px;
        font-size: 11px;
    }
    .navbar-location-badge--request .navbar-loc-name {
        display: none;
    }
    .navbar-location-badge--request .navbar-loc-icon {
        font-size: 14px;
    }

"""
    lines[idx_480_nav:idx_dash] = [new_480_nav]
    print(f'[OK] Replaced 480px navbar section (was lines {idx_480_nav+1}-{idx_dash})')
    changes += 1

# ── 2c. Fix 360px: remove .navbar-links label hide ──
idx_360_label = find_line('.navbar-links a .nav-label', find_line('360px'))
if idx_360_label >= 0:
    # Replace this rule (3 lines: selector { prop } close)
    end_rule = find_line('}', idx_360_label)
    lines[idx_360_label:end_rule+1] = ['    /* nav labels handled by bottom-nav */\n']
    print(f'[OK] Replaced 360px nav-label rule')
    changes += 1

# ── 2d. Fix touch targets ──
idx_touch = find_line('.navbar-links a', find_line('hover: none'))
if idx_touch >= 0:
    end_touch = find_line('}', idx_touch)
    lines[idx_touch:end_touch+1] = ['    .bottom-nav-item {\n', '        min-height: 44px;\n', '    }\n']
    print(f'[OK] Updated touch targets for bottom-nav')
    changes += 1

# ── 2e. Add bottom nav CSS before prefers-reduced-motion ──
BOTTOM_NAV_CSS = """
/* ── Bottom Navigation Bar (phone only) ──────────────────── */
.bottom-nav {
    display: none; /* hidden on desktop */
}

@media (max-width: 600px) {
    .bottom-nav {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 200;
        background: linear-gradient(135deg, #166534 0%, #14532d 100%);
        box-shadow: 0 -2px 12px rgba(0,0,0,0.25);
        padding: 4px 2px 6px;
        gap: 0;
        padding-bottom: max(6px, env(safe-area-inset-bottom));
    }
    .bottom-nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        color: rgba(255,255,255,0.55);
        font-size: 10px;
        padding: 4px 2px 2px;
        border-radius: 8px;
        transition: all 0.15s ease;
        gap: 1px;
        min-width: 0;
    }
    .bottom-nav-icon {
        font-size: 20px;
        line-height: 1;
    }
    .bottom-nav-label {
        font-size: 9px;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
        text-align: center;
        line-height: 1.1;
    }
    .bottom-nav-item.active {
        color: #4ade80;
        background: rgba(74,222,128,0.12);
    }
    .bottom-nav-item.active .bottom-nav-icon {
        transform: scale(1.1);
    }
    .bottom-nav-item:active {
        transform: scale(0.92);
    }

    /* Ensure content is not hidden behind bottom nav */
    .main-content {
        padding-bottom: 90px !important;
    }
    .chat-page {
        height: calc(100vh - 48px - 90px) !important;
    }
    .weather-page {
        height: calc(100vh - 48px - 90px) !important;
    }
}

@media (max-width: 360px) {
    .bottom-nav {
        padding: 3px 1px 4px;
        padding-bottom: max(4px, env(safe-area-inset-bottom));
    }
    .bottom-nav-icon {
        font-size: 18px;
    }
    .bottom-nav-label {
        font-size: 8px;
    }
}

"""

idx_reduced = find_line('prefers-reduced-motion')
if idx_reduced >= 0:
    # Check not already inserted
    if find_line('.bottom-nav {') < 0:
        lines.insert(idx_reduced, BOTTOM_NAV_CSS)
        print(f'[OK] Inserted bottom-nav CSS before prefers-reduced-motion')
        changes += 1

CSS.write_text(''.join(lines), encoding='utf-8')
print(f'\n\u2705 Done! {changes} CSS changes applied.')
print('Next: cd frontend && npx vite build')
