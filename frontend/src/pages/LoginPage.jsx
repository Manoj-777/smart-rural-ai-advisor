// src/pages/LoginPage.jsx
// Simple phone-number based identity for rural farmers
// No password — phone number IS the identity (common in rural India apps)

import { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import config from '../config';

function LoginPage() {
    const { t, language, setLanguage } = useLanguage();
    const { loginWithPhone } = useFarmer();
    const [phone, setPhone] = useState('');
    const [name, setName] = useState('');
    const [mode, setMode] = useState('welcome'); // 'welcome' | 'new' | 'returning'
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [returnedProfile, setReturnedProfile] = useState(null);

    const isValidPhone = phone.replace(/\D/g, '').length >= 10;

    const handleLogin = async () => {
        if (!isValidPhone) {
            setError(t('loginInvalidPhone'));
            return;
        }
        setLoading(true);
        setError('');
        try {
            const profile = await loginWithPhone(phone, name);
            if (profile) {
                setReturnedProfile(profile);
            }
            // FarmerContext will set isLoggedIn=true, App.jsx will redirect
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
                    <div className="login-form">
                        <h2>{t('loginCreateProfile')}</h2>
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
                        <div className="login-form-group">
                            <label>{t('profileName')}</label>
                            <input
                                type="text"
                                className="form-input"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder={t('profileNamePlaceholder')}
                            />
                        </div>
                        {error && <div className="login-error">{error}</div>}
                        <button
                            className="login-btn login-btn-primary"
                            onClick={handleLogin}
                            disabled={loading || !isValidPhone}
                        >
                            {loading ? '⏳ ...' : `✅ ${t('loginStart')}`}
                        </button>
                        <button className="login-btn login-btn-back" onClick={() => setMode('welcome')}>
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
                            onClick={handleLogin}
                            disabled={loading || !isValidPhone}
                        >
                            {loading ? '⏳ ...' : `🔓 ${t('loginContinue')}`}
                        </button>
                        <button className="login-btn login-btn-back" onClick={() => setMode('welcome')}>
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
