// src/components/Sidebar.jsx

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
