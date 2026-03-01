// src/pages/LoginPage.jsx
// Simple phone-number based identity for rural farmers
// OTP verification for returning users

import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import config from '../config';
import { CROP_KEYS, CROP_VALUES_EN, SOIL_KEYS, SOIL_VALUES_EN, STATE_OPTIONS, DISTRICT_MAP } from '../i18n/translations';

function LoginPage() {
    const { t, language, setLanguage } = useLanguage();
    const { loginWithPhone, checkPhoneExists } = useFarmer();
    const [phone, setPhone] = useState('');
    const [name, setName] = useState('');
    const [mode, setMode] = useState('welcome'); // 'welcome' | 'new' | 'returning' | 'otp'
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [returnedProfile, setReturnedProfile] = useState(null);

    // OTP state
    const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
    const [otpTimer, setOtpTimer] = useState(0);
    const [demoOtp, setDemoOtp] = useState('');
    const [otpSmsSent, setOtpSmsSent] = useState(false);
    const [maskedPhone, setMaskedPhone] = useState('');
    const otpRefs = useRef([]);

    // Registration form fields
    const [regState, setRegState] = useState('Tamil Nadu');
    const [regDistrict, setRegDistrict] = useState('');
    const [regCrops, setRegCrops] = useState([]);
    const [regSoilType, setRegSoilType] = useState('Alluvial');
    const [regLandSize, setRegLandSize] = useState('');
    const [regLanguage, setRegLanguage] = useState(language);

    const isValidPhone = phone.replace(/\D/g, '').length >= 10;

    // OTP countdown timer
    useEffect(() => {
        if (otpTimer <= 0) return;
        const interval = setInterval(() => {
            setOtpTimer(prev => {
                if (prev <= 1) { clearInterval(interval); return 0; }
                return prev - 1;
            });
        }, 1000);
        return () => clearInterval(interval);
    }, [otpTimer]);

    const handleCropToggle = (crop) => {
        setRegCrops(prev =>
            prev.includes(crop) ? prev.filter(c => c !== crop) : [...prev, crop]
        );
    };

    // ── Send OTP ──
    const handleSendOtp = async () => {
        if (!isValidPhone) { setError(t('loginInvalidPhone')); return; }
        setLoading(true);
        setError('');
        try {
            // First check if user exists
            const existing = await checkPhoneExists(phone);
            if (!existing) {
                setError(t('loginNotRegistered'));
                setLoading(false);
                return;
            }
            setReturnedProfile(existing);

            // Send OTP
            const res = await fetch(`${config.API_URL}/otp/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone.replace(/\D/g, '') })
            });
            const data = await res.json();

            if (data.status === 'success') {
                setMode('otp');
                setOtpDigits(['', '', '', '', '', '']);
                setOtpTimer(300); // 5 minutes
                setOtpSmsSent(data.sms_sent || data.sandbox_verification || false);
                setMaskedPhone(data.phone_masked || `+91 ${phone.slice(0,3)}***${phone.slice(-2)}`);
                if (data.demo_otp) {
                    setDemoOtp(data.demo_otp);
                } else {
                    setDemoOtp('');
                }
                // Focus first OTP input
                setTimeout(() => otpRefs.current[0]?.focus(), 100);
            } else {
                setError(data.error || data.message || t('otpSendFailed'));
            }
        } catch {
            setError(t('loginError'));
        }
        setLoading(false);
    };

    // ── Verify OTP ──
    const handleVerifyOtp = async () => {
        const otpCode = otpDigits.join('');
        if (otpCode.length !== 6) { setError(t('otpIncomplete')); return; }
        setLoading(true);
        setError('');
        try {
            const res = await fetch(`${config.API_URL}/otp/verify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    phone: phone.replace(/\D/g, ''),
                    otp: otpCode
                })
            });
            const data = await res.json();

            if (data.status === 'success' && data.verified) {
                // OTP verified — proceed with login
                // Language stays as the user's current selection (from login page or localStorage)
                await loginWithPhone(phone);
            } else {
                setError(data.message || t('loginError'));
            }
        } catch {
            setError(t('loginError'));
        }
        setLoading(false);
    };

    // ── Resend OTP ──
    const handleResendOtp = async () => {
        if (otpTimer > 240) return; // prevent spam — wait at least 60s
        setLoading(true);
        setError('');
        try {
            const res = await fetch(`${config.API_URL}/otp/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone.replace(/\D/g, '') })
            });
            const data = await res.json();
            if (data.status === 'success') {
                setOtpDigits(['', '', '', '', '', '']);
                setOtpTimer(300);
                setOtpSmsSent(data.sms_sent || data.sandbox_verification || false);
                if (data.demo_otp) setDemoOtp(data.demo_otp);
                setError('');
                setTimeout(() => otpRefs.current[0]?.focus(), 100);
            }
        } catch { /* ignore */ }
        setLoading(false);
    };

    // ── OTP input handling ──
    const handleOtpChange = (index, value) => {
        if (!/^\d*$/.test(value)) return; // digits only
        const newDigits = [...otpDigits];
        newDigits[index] = value.slice(-1); // single digit
        setOtpDigits(newDigits);

        // Auto-advance to next input
        if (value && index < 5) {
            otpRefs.current[index + 1]?.focus();
        }

        // Auto-submit when all 6 entered
        if (value && index === 5 && newDigits.every(d => d !== '')) {
            setTimeout(() => handleVerifyOtp(), 200);
        }
    };

    const handleOtpKeyDown = (index, e) => {
        if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
            otpRefs.current[index - 1]?.focus();
        }
        if (e.key === 'Enter') {
            const otpCode = otpDigits.join('');
            if (otpCode.length === 6) handleVerifyOtp();
        }
    };

    const handleOtpPaste = (e) => {
        e.preventDefault();
        const paste = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
        if (paste.length === 6) {
            const newDigits = paste.split('');
            setOtpDigits(newDigits);
            otpRefs.current[5]?.focus();
            setTimeout(() => handleVerifyOtp(), 200);
        }
    };

    const formatTimer = (seconds) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    const handleNewSignup = async () => {
        if (!isValidPhone) { setError(t('loginInvalidPhone')); return; }
        if (!name.trim()) { setError(t('loginNameRequired')); return; }
        if (!regState) { setError(t('loginSelectState')); return; }
        if (!regDistrict) { setError(t('loginSelectDistrict')); return; }
        if (regCrops.length === 0) { setError(t('loginSelectCrop')); return; }
        if (!regLandSize || parseFloat(regLandSize) <= 0) { setError(t('loginEnterLand')); return; }
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
                                    onKeyDown={(e) => e.key === 'Enter' && handleNewSignup()}
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
                                onKeyDown={(e) => e.key === 'Enter' && handleNewSignup()}
                                placeholder={t('profileNamePlaceholder')}
                            />
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
                                    onKeyDown={(e) => e.key === 'Enter' && handleNewSignup()}
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
                            disabled={loading || !isValidPhone || !name.trim() || !regDistrict || regCrops.length === 0 || !regLandSize}
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
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && isValidPhone && !loading) {
                                            handleSendOtp();
                                        }
                                    }}
                                />
                            </div>
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
                            onClick={handleSendOtp}
                            disabled={loading || !isValidPhone}
                        >
                            {loading ? `⏳ ${t('otpSending')}` : `📩 ${t('otpSendCode')}`}
                        </button>
                        <button className="login-btn login-btn-back" onClick={() => { setMode('welcome'); setError(''); }}>
                            ← {t('loginBack')}
                        </button>
                    </div>
                )}

                {mode === 'otp' && (
                    <div className="login-form otp-form">
                        <div className="otp-icon">🔐</div>
                        <h2>{t('otpVerifyTitle')}</h2>
                        <p className="login-form-hint">
                            {otpSmsSent
                                ? `${t('otpSentToPhone')} ${maskedPhone}`
                                : `${t('otpEnterCode')} ${maskedPhone}`
                            }
                        </p>

                        {/* OTP code banner — always shown as backup in case SMS doesn't arrive */}
                        {demoOtp && (
                            <div className="otp-demo-banner">
                                <span className="otp-demo-label">🔑 {t('otpDemoLabel')}</span>
                                <span className="otp-demo-code">{demoOtp}</span>
                                <span className="otp-demo-hint">{otpSmsSent ? t('otpSmsFallback') : t('otpDemoHint')}</span>
                            </div>
                        )}

                        {/* OTP digit inputs */}
                        <div className="otp-inputs" onPaste={handleOtpPaste}>
                            {otpDigits.map((digit, i) => (
                                <input
                                    key={i}
                                    ref={el => otpRefs.current[i] = el}
                                    type="text"
                                    inputMode="numeric"
                                    maxLength={1}
                                    value={digit}
                                    onChange={(e) => handleOtpChange(i, e.target.value)}
                                    onKeyDown={(e) => handleOtpKeyDown(i, e)}
                                    className={`otp-digit ${digit ? 'filled' : ''}`}
                                    autoFocus={i === 0}
                                />
                            ))}
                        </div>

                        {/* Timer */}
                        <div className="otp-timer">
                            {otpTimer > 0 ? (
                                <span>{t('otpExpiresIn')} <strong>{formatTimer(otpTimer)}</strong></span>
                            ) : (
                                <span className="otp-expired">{t('otpExpired')}</span>
                            )}
                        </div>

                        {error && <div className="login-error">{error}</div>}

                        <button
                            className="login-btn login-btn-primary"
                            onClick={handleVerifyOtp}
                            disabled={loading || otpDigits.join('').length !== 6 || otpTimer === 0}
                        >
                            {loading ? `⏳ ${t('otpVerifying')}` : `✅ ${t('otpVerifyBtn')}`}
                        </button>

                        <div className="otp-actions">
                            <button
                                className="otp-resend-btn"
                                onClick={handleResendOtp}
                                disabled={loading || otpTimer > 240}
                            >
                                🔄 {t('otpResend')} {otpTimer > 240 ? `(${otpTimer - 240}s)` : ''}
                            </button>
                            <button
                                className="otp-change-btn"
                                onClick={() => { setMode('returning'); setError(''); setOtpDigits(['', '', '', '', '', '']); setDemoOtp(''); }}
                            >
                                ✏️ {t('otpChangeNumber')}
                            </button>
                        </div>
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
