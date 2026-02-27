// src/pages/WeatherPage.jsx

import { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import config from '../config';
import { useLanguage } from '../contexts/LanguageContext';
import { WeatherSkeleton } from '../components/SkeletonLoader';

// Fix Leaflet default marker icon issue with bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Major Indian cities for quick selection
const INDIA_CITIES = [
    { name: 'Delhi', lat: 28.6139, lng: 77.2090 },
    { name: 'Mumbai', lat: 19.0760, lng: 72.8777 },
    { name: 'Chennai', lat: 13.0827, lng: 80.2707 },
    { name: 'Kolkata', lat: 22.5726, lng: 88.3639 },
    { name: 'Bangalore', lat: 12.9716, lng: 77.5946 },
    { name: 'Hyderabad', lat: 17.3850, lng: 78.4867 },
    { name: 'Ahmedabad', lat: 23.0225, lng: 72.5714 },
    { name: 'Pune', lat: 18.5204, lng: 73.8567 },
    { name: 'Jaipur', lat: 26.9124, lng: 75.7873 },
    { name: 'Lucknow', lat: 26.8467, lng: 80.9462 },
    { name: 'Chandigarh', lat: 30.7333, lng: 76.7794 },
    { name: 'Bhopal', lat: 23.2599, lng: 77.4126 },
    { name: 'Patna', lat: 25.6093, lng: 85.1376 },
    { name: 'Thiruvananthapuram', lat: 8.5241, lng: 76.9366 },
    { name: 'Guwahati', lat: 26.1445, lng: 91.7362 },
    { name: 'Bhubaneswar', lat: 20.2961, lng: 85.8245 },
    { name: 'Raipur', lat: 21.2514, lng: 81.6296 },
    { name: 'Ranchi', lat: 23.3441, lng: 85.3096 },
    { name: 'Coimbatore', lat: 11.0168, lng: 76.9558 },
    { name: 'Visakhapatnam', lat: 17.6868, lng: 83.2185 },
    { name: 'Salem', lat: 11.6643, lng: 78.1460 },
    { name: 'Madurai', lat: 9.9252, lng: 78.1198 },
    { name: 'Trichy', lat: 10.7905, lng: 78.7047 },
];

/* Map click handler component */
function MapClickHandler({ onMapClick }) {
    useMapEvents({
        click(e) {
            onMapClick(e.latlng.lat, e.latlng.lng);
        },
    });
    return null;
}

// OpenWeatherMap condition translations
const CONDITION_MAP = {
    'en-IN': {},
    'ta-IN': { 'clear sky':'தெளிவான வானம்','few clouds':'சில மேகங்கள்','scattered clouds':'சிதறிய மேகங்கள்','broken clouds':'உடைந்த மேகங்கள்','overcast clouds':'மூடிய மேகங்கள்','light rain':'லேசான மழை','moderate rain':'மிதமான மழை','heavy intensity rain':'கனமழை','very heavy rain':'மிகக் கனமழை','extreme rain':'தீவிர மழை','light intensity drizzle':'லேசான தூறல்','drizzle':'தூறல்','thunderstorm':'இடியுடன் கூடிய மழை','thunderstorm with light rain':'லேசான மழையுடன் இடி','thunderstorm with rain':'மழையுடன் இடி','thunderstorm with heavy rain':'கனமழையுடன் இடி','mist':'மூடுபனி','haze':'புகைமூட்டம்','fog':'அடர் பனி','smoke':'புகை','dust':'தூசு','sand':'மணல்','tornado':'சூறாவளி','squalls':'புயல்காற்று','snow':'பனி','light snow':'லேசான பனி' },
    'hi-IN': { 'clear sky':'साफ़ आसमान','few clouds':'कुछ बादल','scattered clouds':'बिखरे बादल','broken clouds':'टूटे बादल','overcast clouds':'घने बादल','light rain':'हल्की बारिश','moderate rain':'मध्यम बारिश','heavy intensity rain':'भारी बारिश','very heavy rain':'बहुत भारी बारिश','extreme rain':'अत्यधिक बारिश','light intensity drizzle':'हल्की बूंदाबांदी','drizzle':'बूंदाबांदी','thunderstorm':'आंधी-तूफान','thunderstorm with light rain':'हल्की बारिश के साथ तूफान','thunderstorm with rain':'बारिश के साथ तूफान','thunderstorm with heavy rain':'भारी बारिश के साथ तूफान','mist':'धुंध','haze':'कुहासा','fog':'कोहरा','smoke':'धुआं','dust':'धूल','sand':'रेत','tornado':'बवंडर','squalls':'तेज़ हवाएं','snow':'बर्फ','light snow':'हल्की बर्फ' },
    'te-IN': { 'clear sky':'నిర్మలమైన ఆకాశం','few clouds':'కొన్ని మేఘాలు','scattered clouds':'చెదురుమదురు మేఘాలు','broken clouds':'విరిగిన మేఘాలు','overcast clouds':'మేఘావృతం','light rain':'తేలిక వర్షం','moderate rain':'మోస్తరు వర్షం','heavy intensity rain':'భారీ వర్షం','very heavy rain':'చాలా భారీ వర్షం','light intensity drizzle':'తేలిక జల్లు','drizzle':'జల్లు','thunderstorm':'ఉరుములతో తుఫాను','mist':'పొగమంచు','haze':'మసక','fog':'దట్టమైన పొగమంచు','smoke':'పొగ','dust':'ధూళి' },
    'kn-IN': { 'clear sky':'ನಿರ್ಮಲ ಆಕಾಶ','few clouds':'ಕೆಲವು ಮೋಡಗಳು','scattered clouds':'ಚದುರಿದ ಮೋಡಗಳು','broken clouds':'ಒಡೆದ ಮೋಡಗಳು','overcast clouds':'ಮೋಡ ಕವಿದ','light rain':'ಹಗುರ ಮಳೆ','moderate rain':'ಮಧ್ಯಮ ಮಳೆ','heavy intensity rain':'ಭಾರೀ ಮಳೆ','drizzle':'ತುಂತುರು','thunderstorm':'ಗುಡುಗು ಮಳೆ','mist':'ಮಂಜು','haze':'ಮಬ್ಬು','fog':'ದಟ್ಟ ಮಂಜು','smoke':'ಹೊಗೆ','dust':'ಧೂಳು' },
    'ml-IN': { 'clear sky':'തെളിഞ്ഞ ആകാശം','few clouds':'ചില മേഘങ്ങൾ','scattered clouds':'ചിതറിയ മേഘങ്ങൾ','broken clouds':'ഭാഗിക മേഘാവൃതം','overcast clouds':'മേഘാവൃതം','light rain':'നേരിയ മഴ','moderate rain':'മിതമായ മഴ','heavy intensity rain':'കനത്ത മഴ','drizzle':'ചാറ്റൽ മഴ','thunderstorm':'ഇടിമഴ','mist':'മൂടൽമഞ്ഞ്','haze':'മങ്ങൽ','fog':'കടുത്ത മൂടൽമഞ്ഞ്','smoke':'പുക','dust':'പൊടി' },
    'bn-IN': { 'clear sky':'পরিষ্কার আকাশ','few clouds':'কিছু মেঘ','scattered clouds':'বিক্ষিপ্ত মেঘ','broken clouds':'ভাঙা মেঘ','overcast clouds':'মেঘাচ্ছন্ন','light rain':'হালকা বৃষ্টি','moderate rain':'মাঝারি বৃষ্টি','heavy intensity rain':'ভারী বৃষ্টি','drizzle':'গুঁড়ি গুঁড়ি বৃষ্টি','thunderstorm':'বজ্রঝড়','mist':'কুয়াশা','haze':'ধোঁয়াশা','fog':'ঘন কুয়াশা','smoke':'ধোঁয়া','dust':'ধুলো' },
    'mr-IN': { 'clear sky':'स्वच्छ आकाश','few clouds':'थोडे ढग','scattered clouds':'विखुरलेले ढग','broken clouds':'तुटलेले ढग','overcast clouds':'ढगाळ','light rain':'हलका पाऊस','moderate rain':'मध्यम पाऊस','heavy intensity rain':'जोरदार पाऊस','drizzle':'रिमझिम','thunderstorm':'वादळी पाऊस','mist':'धुके','haze':'कुहरा','fog':'दाट धुके','smoke':'धूर','dust':'धूळ' },
    'gu-IN': { 'clear sky':'સ્વચ્છ આકાશ','few clouds':'થોડા વાદળો','scattered clouds':'વિખરાયેલા વાદળો','broken clouds':'તૂટેલા વાદળો','overcast clouds':'વાદળછાયું','light rain':'હળવો વરસાદ','moderate rain':'મધ્યમ વરસાદ','heavy intensity rain':'ભારે વરસાદ','drizzle':'ઝરમર','thunderstorm':'વીજળી સાથે વરસાદ','mist':'ઝાકળ','haze':'ધૂંધ','fog':'ગાઢ ધુમ્મસ','smoke':'ધુમાડો','dust':'ધૂળ' },
    'pa-IN': { 'clear sky':'ਸਾਫ਼ ਅਸਮਾਨ','few clouds':'ਕੁਝ ਬੱਦਲ','scattered clouds':'ਖਿੱਲਰੇ ਬੱਦਲ','broken clouds':'ਟੁੱਟੇ ਬੱਦਲ','overcast clouds':'ਬੱਦਲਵਾਈ','light rain':'ਹਲਕੀ ਬਾਰਿਸ਼','moderate rain':'ਦਰਮਿਆਨੀ ਬਾਰਿਸ਼','heavy intensity rain':'ਭਾਰੀ ਬਾਰਿਸ਼','drizzle':'ਫੁਹਾਰ','thunderstorm':'ਗਰਜ ਨਾਲ ਮੀਂਹ','mist':'ਧੁੰਦ','haze':'ਕੋਹਰਾ','fog':'ਸੰਘਣੀ ਧੁੰਦ','smoke':'ਧੂੰਆਂ','dust':'ਧੂੜ' },
    'or-IN': { 'clear sky':'ସ୍ୱଚ୍ଛ ଆକାଶ','few clouds':'କିଛି ମେଘ','scattered clouds':'ବିଖଣ୍ଡିତ ମେଘ','broken clouds':'ଭଗ୍ନ ମେଘ','overcast clouds':'ମେଘାଚ୍ଛନ୍ନ','light rain':'ହାଲକା ବର୍ଷା','moderate rain':'ମଧ୍ୟମ ବର୍ଷା','heavy intensity rain':'ଭାରି ବର୍ଷା','drizzle':'ଝିରିଝିରି','thunderstorm':'ବଜ୍ରପାତ ସହ ବର୍ଷା','mist':'କୁହୁଡ଼ି','haze':'ଧୂଆଁ','fog':'ଘନ କୁହୁଡ଼ି','smoke':'ଧୂଆଁ','dust':'ଧୂଳି' },
    'as-IN': { 'clear sky':'পৰিষ্কাৰ আকাশ','few clouds':'কিছু ডাৱৰ','scattered clouds':'সিঁচৰতি ডাৱৰ','broken clouds':'ভঙা ডাৱৰ','overcast clouds':'ডাৱৰীয়া','light rain':'লঘু বৰষুণ','moderate rain':'মধ্যমীয়া বৰষুণ','heavy intensity rain':'ভাৰী বৰষুণ','drizzle':'টোপালটোপাল','thunderstorm':'ঢেৰেকনি','mist':'কুঁৱলী','haze':'ধোঁৱা-কুঁৱলী','fog':'ডাঠ কুঁৱলী','smoke':'ধোঁৱা','dust':'ধূলি' },
    'ur-IN': { 'clear sky':'صاف آسمان','few clouds':'کچھ بادل','scattered clouds':'بکھرے بادل','broken clouds':'ٹوٹے بادل','overcast clouds':'ابر آلود','light rain':'ہلکی بارش','moderate rain':'معتدل بارش','heavy intensity rain':'بھاری بارش','drizzle':'بوندا باندی','thunderstorm':'آندھی طوفان','mist':'دھند','haze':'کہر','fog':'گہری دھند','smoke':'دھواں','dust':'گرد' },
};

function translateCondition(desc, lang) {
    if (!desc) return '';
    const map = CONDITION_MAP[lang];
    if (!map) return desc;
    const lower = desc.toLowerCase();
    return map[lower] || desc;
}

function WeatherPage() {
    const { language, t } = useLanguage();
    const [location, setLocation] = useState('Chennai');
    const [weather, setWeather] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [markerPos, setMarkerPos] = useState({ lat: 13.0827, lng: 80.2707 });
    const [clickedPlace, setClickedPlace] = useState('Chennai');

    const fetchWeather = async (loc) => {
        if (!loc || loc === 'Loading...') return;
        setLoading(true);
        setError(null);
        setWeather(null);
        try {
            const res = await fetch(`${config.API_URL}/weather/${encodeURIComponent(loc)}`);
            if (!res.ok) throw new Error(`API returned ${res.status}`);
            const data = await res.json();
            if (data.status === 'success' && data.data) {
                setWeather(data.data);
            } else if (data.current) {
                setWeather(data);
            } else {
                setError(t('weatherNoData'));
            }
        } catch (err) {
            console.error('Weather fetch error:', err);
            setError(t('weatherFetchError'));
            setWeather(null);
        }
        setLoading(false);
    };

    // Reverse geocode lat/lng to place name using Nominatim
    const reverseGeocode = useCallback(async (lat, lng) => {
        try {
            const res = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10&addressdetails=1`,
                { headers: { 'Accept-Language': 'en' } }
            );
            const data = await res.json();
            const addr = data.address;
            return addr.city || addr.town || addr.village || addr.county || addr.state_district || addr.state || 'Unknown';
        } catch {
            return `${lat.toFixed(2)},${lng.toFixed(2)}`;
        }
    }, []);

    const handleMapClick = useCallback(async (lat, lng) => {
        setMarkerPos({ lat, lng });
        setClickedPlace('Loading...');
        const placeName = await reverseGeocode(lat, lng);
        setClickedPlace(placeName);
        setLocation(placeName);
        fetchWeather(placeName);
    }, [reverseGeocode]);

    const handleCityClick = useCallback((city) => {
        setMarkerPos({ lat: city.lat, lng: city.lng });
        setClickedPlace(city.name);
        setLocation(city.name);
        fetchWeather(city.name);
    }, []);

    const handleSearch = () => {
        if (!location.trim()) return;
        setClickedPlace(location.trim());
        fetchWeather(location.trim());
    };

    useEffect(() => { fetchWeather(location); }, []);

    return (
        <div className="weather-page">
            <div className="page-header">
                <h2>🌤️ {t('weatherTitle')}</h2>
                <p>{t('weatherSubtitle')}</p>
            </div>

            <div className="weather-page-scroll">

            {/* Map + Search Section */}
            <div className="weather-map-section">
                {/* Interactive Map */}
                <div className="weather-map-container">
                    <MapContainer
                        center={[22.5, 82.0]}
                        zoom={5}
                        className="weather-map"
                        scrollWheelZoom={true}
                    >
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                        <MapClickHandler onMapClick={handleMapClick} />
                        <Marker position={[markerPos.lat, markerPos.lng]}>
                            <Popup>
                                <strong>📍 {clickedPlace}</strong>
                            </Popup>
                        </Marker>
                    </MapContainer>
                    <p className="map-hint">👆 {t('weatherMapHint')}</p>
                </div>

                {/* Quick Cities + Search */}
                <div className="weather-sidebar">
                    {/* Search */}
                    <div className="weather-search-box">
                        <div className="search-bar" style={{ flex: 1 }}>
                            <span className="search-icon">🔍</span>
                            <input
                                type="text"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                placeholder={t('weatherSearch')}
                            />
                        </div>
                        <button type="button" onClick={handleSearch} className="send-btn" style={{ borderRadius: '12px', padding: '0 20px', height: 'auto', alignSelf: 'stretch' }}>
                            {t('search')}
                        </button>
                    </div>

                    {/* Quick city buttons */}
                    <h4 className="weather-cities-title">📍 {t('weatherQuickSelect')}</h4>
                    <div className="weather-cities-grid">
                        {INDIA_CITIES.map((city) => (
                            <button
                                key={city.name}
                                className={`weather-city-btn ${clickedPlace === city.name ? 'active' : ''}`}
                                onClick={() => handleCityClick(city)}
                            >
                                {city.name}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Selected location */}
            {clickedPlace && !loading && (
                <div className="weather-location-badge">
                    📍 {t('weatherShowingFor')}: <strong>{clickedPlace}</strong>
                </div>
            )}

            {loading && <WeatherSkeleton />}

            {error && !loading && (
                <div className="alert" style={{ marginBottom: '18px', background: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca', borderRadius: '12px', padding: '14px 18px' }}>
                    ⚠️ {error}
                </div>
            )}

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
                    ☁️ <strong>{t('weatherCondition')}:</strong>&nbsp;{translateCondition(weather.current.description, language)}
                </div>
            )}

            {/* Farming Advisory */}
            {weather?.current && !loading && (() => {
                const temp = weather.current.temp_celsius || 0;
                const humidity = weather.current.humidity || 0;
                const rain = weather.current.rain_mm || 0;
                const parts = [];
                if (humidity > 80) parts.push(t('advHighHumidity'));
                if (temp > 38) parts.push(t('advExtremeHeat'));
                if (rain > 10) parts.push(t('advHeavyRain'));
                if (parts.length === 0) parts.push(t('advNormal'));
                return (
                    <div className="card" style={{ marginTop: '18px', borderLeft: '4px solid var(--primary)' }}>
                        <h3>🌾 {t('weatherAdvisory')}</h3>
                        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7 }}>{parts.join(' ')}</p>
                    </div>
                );
            })()}

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
                                <p>☁️ {translateCondition(day.description, language)}</p>
                                <p>🌧️ {day.rain_probability}% {t('weatherRainChance')}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
            </div>{/* end weather-page-scroll */}
        </div>
    );
}

export default WeatherPage;
