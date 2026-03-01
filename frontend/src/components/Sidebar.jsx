// src/components/Sidebar.jsx

import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import config from '../config';

function Sidebar() {
    const { t, language, setLanguage } = useLanguage();
    const { farmerName, farmerPhone, logout } = useFarmer();
    const [mobileOpen, setMobileOpen] = useState(false);
    const navigate = useNavigate();

    const closeMobile = () => setMobileOpen(false);

    return (
        <>
            {/* Mobile hamburger */}
            <button className="mobile-menu-btn" onClick={() => setMobileOpen(true)} aria-label={t('appName')}>
                ☰
            </button>

            {/* Overlay */}
            {mobileOpen && <div className="sidebar-overlay" onClick={closeMobile} />}

            <nav className={`top-navbar ${mobileOpen ? 'open' : ''}`}>
                <div className="navbar-brand">
                    <span className="brand-icon">🌾</span>
                    <span className="brand-text">{t('appName')}</span>
                    {mobileOpen && (
                        <button className="mobile-close-btn" onClick={closeMobile} aria-label={t('loginBack')}>✕</button>
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
                    <NavLink to="/crop-recommend" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">🌱</span> <span className="nav-label">{t('navCropRec')}</span>
                    </NavLink>
                    <NavLink to="/farm-calendar" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">📅</span> <span className="nav-label">{t('navFarmCal')}</span>
                    </NavLink>
                    <NavLink to="/soil-analysis" className={({isActive}) => isActive ? 'active' : ''} onClick={closeMobile}>
                        <span className="nav-icon">🧪</span> <span className="nav-label">{t('navSoilAnalysis')}</span>
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

                {/* User info + logout — inline in navbar */}
                <div className="navbar-user">
                    {farmerName && (
                        <button className="navbar-user-name-btn" onClick={() => { closeMobile(); navigate('/profile'); }}
                            title={t('navProfile')}>
                            <span className="navbar-user-avatar">👤</span>
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
        </>
    );
}

export default Sidebar;
