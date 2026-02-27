// src/components/Sidebar.jsx

import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import config from '../config';

function Sidebar() {
    const { language, setLanguage, t } = useLanguage();
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

            <nav className={`sidebar ${mobileOpen ? 'open' : ''}`}>
                <div className="sidebar-brand">
                    <h1><span className="brand-icon">🌾</span> {t('appName')}</h1>
                    <p>{t('tagline')}</p>
                    {mobileOpen && (
                        <button className="mobile-close-btn" onClick={closeMobile} aria-label="Close menu">✕</button>
                    )}
                </div>

                <div className="sidebar-nav">
                    <NavLink to="/" end className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">🏠</span> {t('navDashboard')}
                    </NavLink>
                    <NavLink to="/chat" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">💬</span> {t('navChat')}
                    </NavLink>
                    <NavLink to="/weather" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">🌤️</span> {t('navWeather')}
                    </NavLink>
                    <NavLink to="/schemes" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">📋</span> {t('navSchemes')}
                    </NavLink>
                    <NavLink to="/crop-doctor" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">📸</span> {t('navCropDoctor')}
                    </NavLink>
                    <NavLink to="/profile" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">👤</span> {t('navProfile')}
                    </NavLink>
                </div>

                <div className="sidebar-lang">
                    <label>{t('sidebarLanguage')}</label>
                    <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                        {Object.entries(config.LANGUAGES).map(([code, lang]) => (
                            <option key={code} value={code}>{lang.name}</option>
                        ))}
                    </select>
                </div>

                <div className="sidebar-footer">
                    📞 {t('helpline')}
                </div>
            </nav>
        </>
    );
}

export default Sidebar;
