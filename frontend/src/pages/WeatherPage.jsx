// src/pages/WeatherPage.jsx

import { useState, useEffect } from 'react';
import config from '../config';
import { useLanguage } from '../contexts/LanguageContext';
import { WeatherSkeleton } from '../components/SkeletonLoader';

function WeatherPage() {
    const { t } = useLanguage();
    const [location, setLocation] = useState('Chennai');
    const [weather, setWeather] = useState(null);
    const [loading, setLoading] = useState(false);

    const fetchWeather = async (loc) => {
        setLoading(true);
        try {
            const res = await fetch(`${config.API_URL}/weather/${encodeURIComponent(loc)}`);
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
            <div className="page-header">
                <h2>🌤️ {t('weatherTitle')}</h2>
                <p>{t('weatherSubtitle')}</p>
            </div>

            {/* Search */}
            <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
                <div className="search-bar" style={{ flex: 1 }}>
                    <span className="search-icon">🔍</span>
                    <input
                        type="text"
                        value={location}
                        onChange={(e) => setLocation(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && fetchWeather(location)}
                        placeholder={t('weatherSearch')}
                    />
                </div>
                <button onClick={() => fetchWeather(location)} className="send-btn" style={{ borderRadius: '12px', padding: '14px 24px' }}>
                    {t('search')}
                </button>
            </div>

            {loading && <WeatherSkeleton />}

            {/* Stats */}
            {weather?.current && !loading && (
                <div className="stat-grid">
                    <div className="stat-card">
                        <span className="stat-icon">🌡️</span>
                        <div className="stat-value">{weather.current.temp_celsius}°C</div>
                        <div className="stat-label">{t('weatherTemp')}</div>
                    </div>
                    <div className="stat-card">
                        <span className="stat-icon">💧</span>
                        <div className="stat-value">{weather.current.humidity}%</div>
                        <div className="stat-label">{t('weatherHumidity')}</div>
                    </div>
                    <div className="stat-card">
                        <span className="stat-icon">🌧️</span>
                        <div className="stat-value">{weather.current.rain_mm || '0'} mm</div>
                        <div className="stat-label">{t('weatherRainfall')}</div>
                    </div>
                    <div className="stat-card">
                        <span className="stat-icon">💨</span>
                        <div className="stat-value">{weather.current.wind_speed_kmh} km/h</div>
                        <div className="stat-label">{t('weatherWind')}</div>
                    </div>
                </div>
            )}

            {weather?.current?.description && !loading && (
                <div className="alert alert-info" style={{ marginTop: '18px' }}>
                    ☁️ <strong>{t('weatherCondition')}:</strong>&nbsp;{weather.current.description}
                </div>
            )}

            {/* Farming Advisory */}
            {weather?.farming_advisory && !loading && (
                <div className="card" style={{ marginTop: '18px', borderLeft: '4px solid var(--primary)' }}>
                    <h3>🌾 {t('weatherAdvisory')}</h3>
                    <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7 }}>{weather.farming_advisory}</p>
                </div>
            )}

            {/* 5-Day Forecast */}
            {weather?.forecast?.length > 0 && !loading && (
                <div style={{ marginTop: '24px' }}>
                    <h3 style={{ marginBottom: '14px', fontSize: '18px', fontWeight: 600 }}>
                        📅 {t('weatherForecast')}
                    </h3>
                    <div className="forecast-grid">
                        {weather.forecast.map((day, i) => (
                            <div key={i} className="forecast-card">
                                <strong>{day.date}</strong>
                                <p>🌡️ {day.temp_min}–{day.temp_max}°C</p>
                                <p>☁️ {day.description}</p>
                                <p>🌧️ {day.rain_probability}% {t('weatherRainChance')}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default WeatherPage;
