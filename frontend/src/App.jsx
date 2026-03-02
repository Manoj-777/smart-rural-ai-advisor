// src/App.jsx

import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { useEffect, lazy, Suspense } from 'react';
import { LanguageProvider, useLanguage } from './contexts/LanguageContext';
import { FarmerProvider, useFarmer } from './contexts/FarmerContext';
import config from './config';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import LoginPage from './pages/LoginPage';
import './App.css';

// Lazy-load heavy pages (Leaflet map ~150KB, etc.) — only fetched when navigated to
const WeatherPage = lazy(() => import('./pages/WeatherPage'));
const SchemesPage = lazy(() => import('./pages/SchemesPage'));
const CropDoctorPage = lazy(() => import('./pages/CropDoctorPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const PricePage = lazy(() => import('./pages/PricePage'));
const CropRecommendPage = lazy(() => import('./pages/CropRecommendPage'));
const FarmCalendarPage = lazy(() => import('./pages/FarmCalendarPage'));
const SoilAnalysisPage = lazy(() => import('./pages/SoilAnalysisPage'));

// Lightweight loading fallback for lazy pages
const PageLoader = () => (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '40vh', opacity: 0.6 }}>
        <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🌾</div>
            <div style={{ color: 'var(--text-secondary, #666)' }}>Loading...</div>
        </div>
    </div>
);

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
    const { t } = useLanguage();
    if (pathname === '/chat') return null;
    return (
        <div className="mic-fab-wrapper">
            <span className="mic-fab-tooltip">{t('micFabTooltip')}</span>
            <button
                className="dash-mic-fab"
                onClick={() => navigate('/chat')}
                aria-label={t('micFabTooltip')}
            >
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="23"/>
                    <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
            </button>
        </div>
    );
}

function AppContent() {
    const { isLoggedIn } = useFarmer();

    // Prefetch ALL lazy-loaded chunks during idle time
    // → navigation becomes instant because JS is already cached
    useEffect(() => {
        if (!isLoggedIn) return;
        const prefetch = () => {
            import('./pages/WeatherPage');
            import('./pages/SchemesPage');
            import('./pages/CropDoctorPage');
            import('./pages/ProfilePage');
            import('./pages/PricePage');
            import('./pages/CropRecommendPage');
            import('./pages/FarmCalendarPage');
            import('./pages/SoilAnalysisPage');
        };
        // Use requestIdleCallback (fires during browser idle) with 3s hard deadline
        if ('requestIdleCallback' in window) {
            const id = requestIdleCallback(prefetch, { timeout: 3000 });
            return () => cancelIdleCallback(id);
        } else {
            const id = setTimeout(prefetch, 2000);
            return () => clearTimeout(id);
        }
    }, [isLoggedIn]);

    if (!isLoggedIn) {
        return <LoginPage />;
    }

    return (
        <>
            <ScrollToTop />
            <Sidebar />
            <div className="app-body">
                <main className="main-content">
                    <Routes>
                        <Route path="/" element={<DashboardPage />} />
                        <Route path="/chat" element={<ChatPage />} />
                        <Route path="/weather" element={<Suspense fallback={<PageLoader />}><WeatherPage /></Suspense>} />
                        <Route path="/schemes" element={<Suspense fallback={<PageLoader />}><SchemesPage /></Suspense>} />
                        <Route path="/crop-doctor" element={<Suspense fallback={<PageLoader />}><CropDoctorPage /></Suspense>} />
                        <Route path="/prices" element={<Suspense fallback={<PageLoader />}><PricePage /></Suspense>} />
                        <Route path="/crop-recommend" element={<Suspense fallback={<PageLoader />}><CropRecommendPage /></Suspense>} />
                        <Route path="/farm-calendar" element={<Suspense fallback={<PageLoader />}><FarmCalendarPage /></Suspense>} />
                        <Route path="/soil-analysis" element={<Suspense fallback={<PageLoader />}><SoilAnalysisPage /></Suspense>} />
                        <Route path="/profile" element={<Suspense fallback={<PageLoader />}><ProfilePage /></Suspense>} />
                    </Routes>
                </main>
            </div>
            <MicFab />
        </>
    );
}

function App() {
    return (
        <BrowserRouter>
            <LanguageProvider>
                <FarmerProvider>
                    <AppContent />
                </FarmerProvider>
            </LanguageProvider>
        </BrowserRouter>
    );
}

export default App;
