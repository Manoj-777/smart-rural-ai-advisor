// src/App.jsx

import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { LanguageProvider, useLanguage } from './contexts/LanguageContext';
import config from './config';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import WeatherPage from './pages/WeatherPage';
import SchemesPage from './pages/SchemesPage';
import CropDoctorPage from './pages/CropDoctorPage';
import ProfilePage from './pages/ProfilePage';
import PricePage from './pages/PricePage';
import './App.css';

function ScrollToTop() {
    const { pathname } = useLocation();
    useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
    return null;
}

function TopBar() {
    const { language, setLanguage } = useLanguage();
    return (
        <div className="top-bar">
            <div className="top-bar__right">
                <span className="top-bar__lang-icon">🌐</span>
                <select
                    className="top-bar__lang-select"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                >
                    {Object.entries(config.LANGUAGES).map(([code, lang]) => (
                        <option key={code} value={code}>{lang.name}</option>
                    ))}
                </select>
            </div>
        </div>
    );
}

function MicFab() {
    const { pathname } = useLocation();
    const navigate = useNavigate();
    if (pathname === '/chat') return null;
    return (
        <button
            className="dash-mic-fab"
            onClick={() => navigate('/chat')}
            aria-label="Voice chat"
        >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
        </button>
    );
}

function App() {
    return (
        <BrowserRouter>
            <LanguageProvider>
                <ScrollToTop />
                <Sidebar />
                <div className="app-body">
                    <div className="lang-bar">
                        <TopBar />
                    </div>
                    <main className="main-content">
                        <Routes>
                            <Route path="/" element={<DashboardPage />} />
                            <Route path="/chat" element={<ChatPage />} />
                            <Route path="/weather" element={<WeatherPage />} />
                            <Route path="/schemes" element={<SchemesPage />} />
                            <Route path="/crop-doctor" element={<CropDoctorPage />} />
                            <Route path="/prices" element={<PricePage />} />
                            <Route path="/profile" element={<ProfilePage />} />
                        </Routes>
                    </main>
                </div>
                <MicFab />
            </LanguageProvider>
        </BrowserRouter>
    );
}

export default App;
