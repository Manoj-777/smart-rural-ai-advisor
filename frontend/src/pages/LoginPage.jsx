// src/pages/LoginPage.jsx
// Cognito-authenticated login — phone + PIN for rural farmers
// Sign-up: phone + name + profile + PIN → auto-confirmed → JWT tokens
// Sign-in: phone + PIN → JWT tokens

import { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import config from '../config';
import { CROP_KEYS, CROP_VALUES_EN, SOIL_KEYS, SOIL_VALUES_EN, STATE_OPTIONS, DISTRICT_MAP } from '../i18n/translations';

function LoginPage() {
    const { t, language, setLanguage } = useLanguage();
    const { signUpAndLogin, signInWithPin, checkPhoneExists } = useFarmer();
    const [phone, setPhone] = useState('');
    const [pin, setPin] = useState('');
    const [name, setName] = useState('');
    const [mode, setMode] = useState('welcome'); // 'welcome' | 'new' | 'returning'
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Registration form fields
    const [regState, setRegState] = useState('Tamil Nadu');
    const [regDistrict, setRegDistrict] = useState('');
    const [regCrops, setRegCrops] = useState([]);
    const [regSoilType, setRegSoilType] = useState('Alluvial');
    const [regLandSize, setRegLandSize] = useState('');
    const [regLanguage, setRegLanguage] = useState(language);

    const isValidPhone = phone.replace(/\D/g, '').length >= 10;
    const isValidPin = pin.length >= 6;

    const handleCropToggle = (crop) => {
        setRegCrops(prev =>
            prev.includes(crop) ? prev.filter(c => c !== crop) : [...prev, crop]
        );
    };

    // ── Sign up new farmer ──
    const handleNewSignup = async () => {
        if (!isValidPhone) { setError(t('loginInvalidPhone')); return; }
        if (!name.trim()) { setError(t('loginNameRequired')); return; }
        if (!isValidPin) { setError(t('loginPinRequired')); return; }
        if (!regState) { setError(t('loginSelectState')); return; }
        if (!regDistrict) { setError(t('loginSelectDistrict')); return; }
        if (regCrops.length === 0) { setError(t('loginSelectCrop')); return; }
        if (!regLandSize || parseFloat(regLandSize) <= 0) { setError(t('loginEnterLand')); return; }
        setLoading(true);
        setError('');
        try {
            const profileData = {
                name: name.trim(),
                state: regState,
                district: regDistrict.trim(),
                crops: regCrops,
                soil_type: regSoilType,
                land_size_acres: parseFloat(regLandSize) || 0,
                language: regLanguage,
            };
            await signUpAndLogin(phone, pin, name.trim(), profileData);
            if (regLanguage !== language) {
                setLanguage(regLanguage);
            }
        } catch (err) {
            const msg = err?.message || '';
            if (msg.includes('UsernameExistsException') || msg.includes('already exists')) {
                setError(t('loginAlreadyRegistered'));
            } else {
                setError(msg || t('loginError'));
            }
        }
        setLoading(false);
    };

    // ── Sign in returning farmer ──
    const handleSignIn = async () => {
        if (!isValidPhone) { setError(t('loginInvalidPhone')); return; }
        if (!isValidPin) { setError(t('loginPinRequired')); return; }
        setLoading(true);
        setError('');
        try {
            await signInWithPin(phone, pin);
        } catch (err) {
            const msg = err?.message || '';
            if (msg.includes('UserNotFoundException') || msg.includes('does not exist')) {
                setError(t('loginNotRegistered'));
            } else if (msg.includes('NotAuthorizedException') || msg.includes('Incorrect')) {
                setError(t('loginWrongPin'));
            } else {
                setError(msg || t('loginError'));
            }
        }
        setLoading(false);
    };

    return (
        <div className="login-page">
            <div className="login-container">
                {/* Language selector - only show on welcome screen */}
                {mode === 'welcome' && (
                    <div className="login-lang">
                        <span>🌐</span>
                        <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                            {Object.entries(config.LANGUAGES).map(([code, lang]) => (
                                <option key={code} value={code}>{lang.name}</option>
                            ))}
                        </select>
                    </div>
                )}

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
                            <label>{t('loginPhoneLabel')} <span className="required-star">*</span></label>
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
                            <label>{t('profileName')} <span className="required-star">*</span></label>
                            <input
                                type="text"
                                className="form-input"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder={t('profileNamePlaceholder')}
                            />
                        </div>

                        {/* PIN */}
                        <div className="login-form-group">
                            <label>{t('loginPinLabel')} <span className="required-star">*</span></label>
                            <input
                                type="password"
                                className="form-input"
                                maxLength={20}
                                value={pin}
                                onChange={(e) => setPin(e.target.value)}
                                placeholder={t('loginPinPlaceholder')}
                            />
                            <span className="login-form-hint-small">{t('loginPinHint')}</span>
                        </div>

                        {/* State & District */}
                        <div className="login-form-row">
                            <div className="login-form-group">
                                <label>{t('profileState')} <span className="required-star">*</span></label>
                                <select className="form-input" value={regState}
                                    onChange={(e) => { setRegState(e.target.value); setRegDistrict(''); }}>
                                    {STATE_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                                </select>
                            </div>
                            <div className="login-form-group">
                                <label>{t('profileDistrict')} <span className="required-star">*</span></label>
                                <select className="form-input" value={regDistrict}
                                    onChange={(e) => setRegDistrict(e.target.value)}>
                                    <option value="" disabled>{t('loginSelectDistrict')}</option>
                                    {(DISTRICT_MAP[regState] || []).map(d =>
                                        <option key={d} value={d}>{d}</option>
                                    )}
                                </select>
                            </div>
                        </div>

                        {/* Crops */}
                        <div className="login-form-group">
                            <label>{t('profileCrops')} <span className="required-star">*</span></label>
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
                                <label>{t('profileSoilType')} <span className="required-star">*</span></label>
                                <select className="form-input" value={regSoilType}
                                    onChange={(e) => setRegSoilType(e.target.value)}>
                                    {SOIL_KEYS.map((key, i) =>
                                        <option key={key} value={SOIL_VALUES_EN[i]}>{t(key)}</option>
                                    )}
                                </select>
                            </div>
                            <div className="login-form-group">
                                <label>{t('profileLandSize')} <span className="required-star">*</span></label>
                                <input className="form-input" type="number" value={regLandSize}
                                    min="0" step="0.5"
                                    onChange={(e) => setRegLandSize(e.target.value)}
                                    placeholder="0" />
                            </div>
                            <div className="login-form-group">
                                <label>{t('profileLanguage')} <span className="required-star">*</span></label>
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
                            disabled={loading || !isValidPhone || !name.trim() || !isValidPin || !regDistrict || regCrops.length === 0 || !regLandSize}
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
                        <p className="login-form-hint">{t('loginEnterPhonePin')}</p>
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
                            <label>{t('loginPinLabel')}</label>
                            <input
                                type="password"
                                className="form-input"
                                maxLength={20}
                                value={pin}
                                onChange={(e) => setPin(e.target.value)}
                                placeholder={t('loginPinPlaceholder')}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && isValidPhone && isValidPin && !loading) {
                                        handleSignIn();
                                    }
                                }}
                            />
                        </div>
                        {error && (
                            <div className="login-error">
                                {error}
                                {error === t('loginNotRegistered') && (
                                    <button
                                        className="login-error-link"
                                        onClick={() => { setMode('new'); setError(''); }}
                                    >
                                        → {t('loginNewFarmer')}
                                    </button>
                                )}
                            </div>
                        )}
                        <button
                            className="login-btn login-btn-primary"
                            onClick={handleSignIn}
                            disabled={loading || !isValidPhone || !isValidPin}
                        >
                            {loading ? '⏳ ...' : `🔓 ${t('loginSignIn')}`}
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
