// src/components/Sidebar.jsx

import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import config from '../config';

function Sidebar() {
    const { t, language, setLanguage } = useLanguage();
    const [mobileOpen, setMobileOpen] = useState(false);

    const closeMobile = () => setMobileOpen(false);

    return (
        <>
            {/* Mobile hamburger */}
            <button className="mobile-menu-btn" onClick={() => setMobileOpen(true)} aria-label="Open menu">
                ☰
            </button>

            {/* Overlay */}
            {mobileOpen && <div className="sidebar-overlay" onClick={closeMobile} />}

            <nav className={`top-navbar ${mobileOpen ? 'open' : ''}`}>
                <div className="navbar-brand">
                    <span className="brand-icon">🌾</span>
                    <span className="brand-text">{t('appName')}</span>
                    {mobileOpen && (
                        <button className="mobile-close-btn" onClick={closeMobile} aria-label="Close menu">✕</button>
                    )}
                </div>

                <div className="navbar-links">
                    <NavLink to="/" end className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">🏠</span> <span className="nav-label">{t('navDashboard')}</span>
                    </NavLink>
                    <NavLink to="/chat" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">💬</span> <span className="nav-label">{t('navChat')}</span>
                    </NavLink>
                    <NavLink to="/weather" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">🌤️</span> <span className="nav-label">{t('navWeather')}</span>
                    </NavLink>
                    <NavLink to="/schemes" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">📋</span> <span className="nav-label">{t('navSchemes')}</span>
                    </NavLink>
                    <NavLink to="/crop-doctor" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">📸</span> <span className="nav-label">{t('navCropDoctor')}</span>
                    </NavLink>
                    <NavLink to="/prices" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">💰</span> <span className="nav-label">{t('navPrices')}</span>
                    </NavLink>
                    <NavLink to="/profile" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">👤</span> <span className="nav-label">{t('navProfile')}</span>
                    </NavLink>
                </div>

                <div className="navbar-lang">
                    <span className="navbar-lang-icon">🌐</span>
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
            </nav>
        </>
    );
}

export default Sidebar;
