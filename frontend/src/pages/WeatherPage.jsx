// src/pages/WeatherPage.jsx

import { useState, useEffect } from 'react';
import config from '../config';

function WeatherPage() {
    const [location, setLocation] = useState('Chennai');
    const [weather, setWeather] = useState(null);
    const [loading, setLoading] = useState(false);

    const fetchWeather = async (loc) => {
        setLoading(true);
        try {
            const res = await fetch(
                `${config.API_URL}/weather/${encodeURIComponent(loc)}`
            );
            const data = await res.json();
            setWeather(data.data || data);
        } catch {
            setWeather(null);
        }
        setLoading(false);
    };

    useEffect(() => { fetchWeather(location); }, []);

    return (
        <div>
            <h2>🌤️ Weather Dashboard</h2>
            <div style={{ display: 'flex', gap: '12px', margin: '16px 0' }}>
                <input 
                    type="text" 
                    value={location} 
                    onChange={(e) => setLocation(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && fetchWeather(location)}
                    placeholder="Enter city or district..."
                    style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '2px solid var(--border)' }}
                />
                <button onClick={() => fetchWeather(location)} className="send-btn">
                    Search
                </button>
            </div>

            {loading && <p>Loading weather...</p>}

            {weather?.current && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                    <div className="card" style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '48px' }}>🌡️</div>
                        <h3>{weather.current.temp_celsius}°C</h3>
                        <p style={{ color: 'var(--text-light)' }}>Temperature</p>
                    </div>
                    <div className="card" style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '48px' }}>💧</div>
                        <h3>{weather.current.humidity}%</h3>
                        <p style={{ color: 'var(--text-light)' }}>Humidity</p>
                    </div>
                    <div className="card" style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '48px' }}>🌧️</div>
                        <h3>{weather.current.rain_mm || '0'} mm</h3>
                        <p style={{ color: 'var(--text-light)' }}>Rainfall</p>
                    </div>
                    <div className="card" style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '48px' }}>💨</div>
                        <h3>{weather.current.wind_speed_kmh} km/h</h3>
                        <p style={{ color: 'var(--text-light)' }}>Wind Speed</p>
                    </div>
                </div>
            )}

            {weather?.current?.description && (
                <p style={{ marginTop: '12px', color: 'var(--text-light)' }}>
                    <strong>Condition:</strong> {weather.current.description}
                </p>
            )}

            {weather?.farming_advisory && (
                <div className="card" style={{ marginTop: '16px' }}>
                    <h3>🌾 Farming Advisory</h3>
                    <p>{weather.farming_advisory}</p>
                </div>
            )}

            {weather?.forecast?.length > 0 && (
                <div style={{ marginTop: '16px' }}>
                    <h3>📅 5-Day Forecast</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px' }}>
                        {weather.forecast.map((day, i) => (
                            <div key={i} className="card" style={{ textAlign: 'center', padding: '12px' }}>
                                <strong>{day.date}</strong>
                                <p>🌡️ {day.temp_min}–{day.temp_max}°C</p>
                                <p>☁️ {day.description}</p>
                                <p>🌧️ {day.rain_probability}% rain</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default WeatherPage;
