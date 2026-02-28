// src/pages/LoginPage.jsx
// Simple phone-number based identity for rural farmers
// No password — phone number IS the identity (common in rural India apps)

import { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import config from '../config';
import { CROP_KEYS, CROP_VALUES_EN, SOIL_KEYS, SOIL_VALUES_EN, STATE_OPTIONS, DISTRICT_MAP } from '../i18n/translations';

function LoginPage() {
    const { t, language, setLanguage } = useLanguage();
    const { loginWithPhone, checkPhoneExists } = useFarmer();
    const [phone, setPhone] = useState('');
    const [name, setName] = useState('');
    const [mode, setMode] = useState('welcome'); // 'welcome' | 'new' | 'returning'
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [returnedProfile, setReturnedProfile] = useState(null);

    // Registration form fields
    const [regState, setRegState] = useState('Tamil Nadu');
    const [regDistrict, setRegDistrict] = useState('');
    const [regCrops, setRegCrops] = useState([]);
    const [regSoilType, setRegSoilType] = useState('Alluvial');
    const [regLandSize, setRegLandSize] = useState('');
    const [regLanguage, setRegLanguage] = useState(language);

    const isValidPhone = phone.replace(/\D/g, '').length >= 10;

    const handleCropToggle = (crop) => {
        setRegCrops(prev =>
            prev.includes(crop) ? prev.filter(c => c !== crop) : [...prev, crop]
        );
    };

    const handleReturningLogin = async () => {
        if (!isValidPhone) { setError(t('loginInvalidPhone')); return; }
        setLoading(true);
        setError('');
        try {
            const existing = await checkPhoneExists(phone);
            if (!existing) {
                setError(t('loginNotRegistered'));
                setLoading(false);
                return;
            }
            // Phone is registered — proceed with login
            const profile = await loginWithPhone(phone);
            if (profile) {
                setReturnedProfile(profile);
                // Auto-switch to the farmer's saved language preference
                if (profile.language && profile.language !== language) {
                    setLanguage(profile.language);
                }
            }
        } catch {
            setError(t('loginError'));
        }
        setLoading(false);
    };

    const handleNewSignup = async () => {
        if (!isValidPhone) { setError(t('loginInvalidPhone')); return; }
        if (!name.trim()) { setError(t('loginNameRequired')); return; }
        setLoading(true);
        setError('');
        try {
            // Check if already registered
            const existing = await checkPhoneExists(phone);
            if (existing) {
                setError(t('loginAlreadyRegistered'));
                setLoading(false);
                return;
            }
            // Build full profile
            const profileData = {
                name: name.trim(),
                state: regState,
                district: regDistrict.trim(),
                crops: regCrops,
                soil_type: regSoilType,
                land_size_acres: parseFloat(regLandSize) || 0,
                language: regLanguage,
            };
            await loginWithPhone(phone, name.trim(), profileData);
            // Auto-switch the app language to the farmer's chosen preference
            if (regLanguage !== language) {
                setLanguage(regLanguage);
            }
        } catch {
            setError(t('loginError'));
        }
        setLoading(false);
    };

    return (
        <div className="login-page">
            <div className="login-container">
                {/* Language selector at top */}
                <div className="login-lang">
                    <span>🌐</span>
                    <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                        {Object.entries(config.LANGUAGES).map(([code, lang]) => (
                            <option key={code} value={code}>{lang.name}</option>
                        ))}
                    </select>
                </div>

                {/* Logo */}
                <div className="login-logo">
                    <span className="login-logo-icon">🌾</span>
                    <h1>{t('appName')}</h1>
                    <p className="login-tagline">{t('tagline')}</p>
                </div>

                {mode === 'welcome' && (
                    <div className="login-welcome">
                        <div className="login-welcome-art">
                            <div className="login-feature">🌤️ {t('loginFeatureWeather')}</div>
                            <div className="login-feature">🌱 {t('loginFeatureCrop')}</div>
                            <div className="login-feature">📋 {t('loginFeatureSchemes')}</div>
                            <div className="login-feature">🎤 {t('loginFeatureVoice')}</div>
                        </div>
                        <button className="login-btn login-btn-primary" onClick={() => setMode('new')}>
                            🚀 {t('loginNewFarmer')}
                        </button>
                        <button className="login-btn login-btn-secondary" onClick={() => setMode('returning')}>
                            🔄 {t('loginReturningFarmer')}
                        </button>
                    </div>
                )}

                {mode === 'new' && (
                    <div className="login-form login-form-register">
                        <h2>{t('loginCreateProfile')}</h2>

                        {/* Phone */}
                        <div className="login-form-group">
                            <label>{t('loginPhoneLabel')}</label>
                            <div className="login-phone-input">
                                <span className="login-phone-prefix">+91</span>
                                <input
                                    type="tel"
                                    maxLength={10}
                                    value={phone}
                                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                                    placeholder={t('loginPhonePlaceholder')}
                                    autoFocus
                                />
                            </div>
                        </div>

                        {/* Name */}
                        <div className="login-form-group">
                            <label>{t('profileName')} *</label>
                            <input
                                type="text"
                                className="form-input"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder={t('profileNamePlaceholder')}
                            />
                        </div>

                        {/* State & District */}
                        <div className="login-form-row">
                            <div className="login-form-group">
                                <label>{t('profileState')}</label>
                                <select className="form-input" value={regState}
                                    onChange={(e) => { setRegState(e.target.value); setRegDistrict(''); }}>
                                    {STATE_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                                </select>
                            </div>
                            <div className="login-form-group">
                                <label>{t('profileDistrict')}</label>
                                <select className="form-input" value={regDistrict}
                                    onChange={(e) => setRegDistrict(e.target.value)}>
                                    <option value="">{t('profileDistrictPlaceholder')}</option>
                                    {(DISTRICT_MAP[regState] || []).map(d =>
                                        <option key={d} value={d}>{d}</option>
                                    )}
                                </select>
                            </div>
                        </div>

                        {/* Crops */}
                        <div className="login-form-group">
                            <label>{t('profileCrops')}</label>
                            <div className="crop-chips crop-chips-compact">
                                {CROP_KEYS.map((key, i) => (
                                    <button
                                        key={key}
                                        type="button"
                                        className={`crop-chip ${regCrops.includes(CROP_VALUES_EN[i]) ? 'selected' : ''}`}
                                        onClick={() => handleCropToggle(CROP_VALUES_EN[i])}
                                    >
                                        {t(key)}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Soil Type, Land Size, Language */}
                        <div className="login-form-row login-form-row-3">
                            <div className="login-form-group">
                                <label>{t('profileSoilType')}</label>
                                <select className="form-input" value={regSoilType}
                                    onChange={(e) => setRegSoilType(e.target.value)}>
                                    {SOIL_KEYS.map((key, i) =>
                                        <option key={key} value={SOIL_VALUES_EN[i]}>{t(key)}</option>
                                    )}
                                </select>
                            </div>
                            <div className="login-form-group">
                                <label>{t('profileLandSize')}</label>
                                <input className="form-input" type="number" value={regLandSize}
                                    min="0" step="0.5"
                                    onChange={(e) => setRegLandSize(e.target.value)}
                                    placeholder="0" />
                            </div>
                            <div className="login-form-group">
                                <label>{t('profileLanguage')}</label>
                                <select className="form-input" value={regLanguage}
                                    onChange={(e) => setRegLanguage(e.target.value)}>
                                    {Object.entries(config.LANGUAGES).map(([code, lang]) =>
                                        <option key={code} value={code}>{lang.name}</option>
                                    )}
                                </select>
                            </div>
                        </div>

                        {error && <div className="login-error">{error}</div>}
                        <button
                            className="login-btn login-btn-primary"
                            onClick={handleNewSignup}
                            disabled={loading || !isValidPhone || !name.trim()}
                        >
                            {loading ? '⏳ ...' : `✅ ${t('loginStart')}`}
                        </button>
                        <button className="login-btn login-btn-back" onClick={() => { setMode('welcome'); setError(''); }}>
                            ← {t('loginBack')}
                        </button>
                    </div>
                )}

                {mode === 'returning' && (
                    <div className="login-form">
                        <h2>{t('loginWelcomeBack')}</h2>
                        <p className="login-form-hint">{t('loginEnterPhone')}</p>
                        <div className="login-form-group">
                            <label>{t('loginPhoneLabel')}</label>
                            <div className="login-phone-input">
                                <span className="login-phone-prefix">+91</span>
                                <input
                                    type="tel"
                                    maxLength={10}
                                    value={phone}
                                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                                    placeholder={t('loginPhonePlaceholder')}
                                    autoFocus
                                />
                            </div>
                        </div>
                        {error && <div className="login-error">{error}</div>}
                        <button
                            className="login-btn login-btn-primary"
                            onClick={handleReturningLogin}
                            disabled={loading || !isValidPhone}
                        >
                            {loading ? '⏳ ...' : `🔓 ${t('loginContinue')}`}
                        </button>
                        <button className="login-btn login-btn-back" onClick={() => { setMode('welcome'); setError(''); }}>
                            ← {t('loginBack')}
                        </button>
                    </div>
                )}

                <div className="login-footer">
                    <p>📞 {t('helpline')}</p>
                </div>
            </div>
        </div>
    );
}

export default LoginPage;
