// src/App.jsx

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatPage from './pages/ChatPage';
import WeatherPage from './pages/WeatherPage';
import SchemesPage from './pages/SchemesPage';
import CropDoctorPage from './pages/CropDoctorPage';
import ProfilePage from './pages/ProfilePage';
import './App.css';

function App() {
    return (
        <BrowserRouter>
            <div className="app-container">
                <Sidebar />
                <main className="main-content">
                    <Routes>
                        <Route path="/" element={<ChatPage />} />
                        <Route path="/weather" element={<WeatherPage />} />
                        <Route path="/schemes" element={<SchemesPage />} />
                        <Route path="/crop-doctor" element={<CropDoctorPage />} />
                        <Route path="/profile" element={<ProfilePage />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    );
}

export default App;
