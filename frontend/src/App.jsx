// src/App.jsx

import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { LanguageProvider } from './contexts/LanguageContext';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import WeatherPage from './pages/WeatherPage';
import SchemesPage from './pages/SchemesPage';
import CropDoctorPage from './pages/CropDoctorPage';
import ProfilePage from './pages/ProfilePage';
import './App.css';

function ScrollToTop() {
    const { pathname } = useLocation();
    useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
    return null;
}

function App() {
    return (
        <BrowserRouter>
            <LanguageProvider>
                <ScrollToTop />
                <div className="app-container">
                    <Sidebar />
                    <main className="main-content">
                        <Routes>
                            <Route path="/" element={<DashboardPage />} />
                            <Route path="/chat" element={<ChatPage />} />
                            <Route path="/weather" element={<WeatherPage />} />
                            <Route path="/schemes" element={<SchemesPage />} />
                            <Route path="/crop-doctor" element={<CropDoctorPage />} />
                            <Route path="/profile" element={<ProfilePage />} />
                        </Routes>
                    </main>
                </div>
            </LanguageProvider>
        </BrowserRouter>
    );
}

export default App;
