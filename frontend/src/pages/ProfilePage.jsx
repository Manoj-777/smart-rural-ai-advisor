// src/pages/ProfilePage.jsx

import { useState, useEffect, useCallback, useRef } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import { CROP_KEYS, CROP_VALUES_EN, SOIL_KEYS, SOIL_VALUES_EN, DISTRICT_MAP } from '../i18n/translations';
import { getDistrictName } from '../i18n/districtTranslations';
import { apiFetch } from '../utils/apiFetch';
import * as cognitoAuth from '../services/cognitoAuth';

// Delete account confirmation phrase

// State options with translation keys for localized display
const STATE_OPTION_OBJECTS = [
    { value: 'Andhra Pradesh', key: 'stateAP' },
    { value: 'Arunachal Pradesh', key: 'stateAR' },
    { value: 'Assam', key: 'stateAS' },
    { value: 'Bihar', key: 'stateBR' },
    { value: 'Chhattisgarh', key: 'stateCG' },
    { value: 'Goa', key: 'stateGA' },
    { value: 'Gujarat', key: 'stateGJ' },
    { value: 'Haryana', key: 'stateHR' },
    { value: 'Himachal Pradesh', key: 'stateHP' },
    { value: 'Jharkhand', key: 'stateJH' },
    { value: 'Karnataka', key: 'stateKA' },
    { value: 'Kerala', key: 'stateKL' },
    { value: 'Madhya Pradesh', key: 'stateMP' },
    { value: 'Maharashtra', key: 'stateMH' },
    { value: 'Manipur', key: 'stateMN' },
    { value: 'Meghalaya', key: 'stateML' },
    { value: 'Mizoram', key: 'stateMZ' },
    { value: 'Nagaland', key: 'stateNL' },
    { value: 'Odisha', key: 'stateOD' },
    { value: 'Punjab', key: 'statePB' },
    { value: 'Rajasthan', key: 'stateRJ' },
    { value: 'Sikkim', key: 'stateSK' },
    { value: 'Tamil Nadu', key: 'stateTN' },
    { value: 'Telangana', key: 'stateTS' },
    { value: 'Tripura', key: 'stateTR' },
    { value: 'Uttar Pradesh', key: 'stateUP' },
    { value: 'Uttarakhand', key: 'stateUK' },
    { value: 'West Bengal', key: 'stateWB' },
];

function ProfilePage() {
    const { t, language, setLanguage } = useLanguage();
    const { farmerId, farmerPhone, updateProfile, deleteAccount } = useFarmer();
    const [profile, setProfile] = useState({
        name: '', state: 'Tamil Nadu', district: '', crops: [],
        soil_type: 'Alluvial', land_size_acres: 0, language: 'ta-IN'
    });
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const debounceRef = useRef(null);
    const hasLoadedRef = useRef(false);

    // Change PIN state
    const [oldPin, setOldPin] = useState('');
    const [newPin, setNewPin] = useState('');
    const [confirmNewPin, setConfirmNewPin] = useState('');
    const [pinMessage, setPinMessage] = useState(null);
    const [changingPin, setChangingPin] = useState(false);

    // Email for recovery
    const [recoveryEmail, setRecoveryEmail] = useState('');
    const [emailMessage, setEmailMessage] = useState(null);
    const [savingEmail, setSavingEmail] = useState(false);

    // Delete account
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        const loadProfile = async () => {
            try {
                const res = await apiFetch(`/profile/${farmerId}`);
                const data = await res.json();
                if (data.data) setProfile(prev => ({ ...prev, ...data.data }));
            } catch { /* New user — use defaults */ }
            hasLoadedRef.current = true;
        };
        loadProfile();
    }, [farmerId]);

    const handleCropToggle = (crop) => {
        setProfile(prev => ({
            ...prev,
            crops: prev.crops.includes(crop)
                ? prev.crops.filter(c => c !== crop)
                : [...prev.crops, crop]
        }));
    };

    // Auto-save with debounce (2s after last edit)
    const autoSave = useCallback((updatedProfile) => {
        if (!hasLoadedRef.current) return; // don't auto-save before initial load
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(async () => {
            try {
                await apiFetch(`/profile/${farmerId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedProfile)
                });
                updateProfile(updatedProfile);
                setMessage({ type: 'success', text: '✅ ' + t('profileAutoSaved') });
                setTimeout(() => setMessage(null), 2000);
            } catch {
                setMessage({ type: 'error', text: '❌ ' + t('profileSaveFailed') });
            }
        }, 2000);
    }, [farmerId, t, updateProfile]);

    // Trigger auto-save when profile changes
    useEffect(() => {
        if (hasLoadedRef.current) autoSave(profile);
    }, [profile, autoSave]);

    const handleSave = async () => {
        if (debounceRef.current) clearTimeout(debounceRef.current); // cancel pending auto-save
        setSaving(true);
        setMessage(null);
        try {
            await apiFetch(`/profile/${farmerId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profile)
            });
            updateProfile(profile);
            setMessage({ type: 'success', text: '✅ ' + t('profileSaved') });
        } catch {
            setMessage({ type: 'error', text: '❌ ' + t('profileSaveFailed') });
        }
        setSaving(false);
    };

    // ── Change PIN handler ──
    const handleChangePin = async () => {
        if (!oldPin) { setPinMessage({ type: 'error', text: '❌ ' + t('changePinOldLabel') }); return; }
        if (newPin.length < 6) { setPinMessage({ type: 'error', text: '❌ ' + t('changePinTooShort') }); return; }
        if (newPin !== confirmNewPin) { setPinMessage({ type: 'error', text: '❌ ' + t('changePinMismatch') }); return; }
        setChangingPin(true);
        setPinMessage(null);
        try {
            await cognitoAuth.changePassword(oldPin, newPin);
            setPinMessage({ type: 'success', text: '✅ ' + t('changePinSuccess') });
            setOldPin('');
            setNewPin('');
            setConfirmNewPin('');
        } catch (err) {
            const msg = err?.message || '';
            if (msg.includes('NotAuthorizedException') || msg.includes('Incorrect')) {
                setPinMessage({ type: 'error', text: '❌ ' + t('changePinWrongOld') });
            } else {
                setPinMessage({ type: 'error', text: '❌ ' + (msg || t('error')) });
            }
        }
        setChangingPin(false);
    };

    // ── Save recovery email ──
    const handleSaveEmail = async () => {
        if (!recoveryEmail.trim() || !recoveryEmail.includes('@')) {
            setEmailMessage({ type: 'error', text: '❌ Please enter a valid email.' });
            return;
        }
        setSavingEmail(true);
        setEmailMessage(null);
        try {
            await cognitoAuth.updateEmail(recoveryEmail.trim());
            setEmailMessage({ type: 'success', text: '✅ Email saved for PIN recovery!' });
        } catch (err) {
            setEmailMessage({ type: 'error', text: '❌ ' + (err?.message || 'Could not save email.') });
        }
        setSavingEmail(false);
    };

    // Find localized crop name for display
    const localizedCrop = (enValue) => {
        const idx = CROP_VALUES_EN.indexOf(enValue);
        return idx >= 0 ? t(CROP_KEYS[idx]) : enValue;
    };


    const handleDeleteAccount = async () => {
        setDeleting(true);
        try {
            await deleteAccount();
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to delete account. Please try again.' });
            setDeleting(false);
            setShowDeleteConfirm(false);
        }
    };

    return (
        <div className="profile-page">
            <div className="page-header">
                <h2>👤 {t('profileTitle')}</h2>
                <p>{t('profileSubtitle')}</p>
                <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginTop: 4 }}>
                    {t('profileFarmerId')}: {farmerId}
                    {farmerPhone && ` • 📞 +91 ${farmerPhone}`}
                </p>
            </div>

            <div className="profile-page-scroll">

            {message && (
                <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-error'}`}>
                    {message.text}
                </div>
            )}

            {/* Personal Details */}
            <div className="card">
                <h3>📋 {t('profilePersonalDetails')}</h3>
                <div className="form-grid">
                    <div className="form-group">
                        <label>{t('profileName')}</label>
                        <input className="form-input" type="text" value={profile.name}
                            onChange={e => setProfile(p => ({ ...p, name: e.target.value }))}
                            onKeyDown={e => e.key === 'Enter' && handleSave()}
                            placeholder={t('profileNamePlaceholder')} />
                    </div>
                    <div className="form-group">
                        <label>{t('profileDistrict')}</label>
                        <select className="form-input" value={profile.district}
                            onChange={e => setProfile(p => ({ ...p, district: e.target.value }))}>
                            <option value="" disabled>{t('loginSelectDistrict')}</option>
                            {(DISTRICT_MAP[profile.state] || []).map(d =>
                                <option key={d} value={d}>{getDistrictName(d, language)}</option>
                            )}
                        </select>
                    </div>
                    <div className="form-group">
                        <label>{t('profileState')}</label>
                        <select className="form-input" value={profile.state}
                            onChange={e => setProfile(p => ({ ...p, state: e.target.value, district: '' }))}>
                            {STATE_OPTION_OBJECTS.map(s => <option key={s.value} value={s.value}>{t(s.key)}</option>)}
                        </select>
                    </div>
                    <div className="form-group">
                        <label>{t('profileLanguage')}</label>
                        <select className="form-input" value={profile.language}
                            onChange={e => {
                                const lang = e.target.value;
                                setProfile(p => ({ ...p, language: lang }));
                                setLanguage(lang); // instantly switch the app UI language
                            }}>
                            {Object.entries(config.LANGUAGES).map(([code, lang]) =>
                                <option key={code} value={code}>{lang.name}</option>
                            )}
                        </select>
                    </div>
                </div>
            </div>

            {/* Farm Details */}
            <div className="card">
                <h3>🌾 {t('profileFarmDetails')}</h3>
                <div className="form-group">
                    <label>{t('profileCrops')}</label>
                    <div className="crop-chips">
                        {CROP_KEYS.map((key, i) => (
                            <button
                                key={key}
                                className={`crop-chip ${profile.crops.includes(CROP_VALUES_EN[i]) ? 'selected' : ''}`}
                                onClick={() => handleCropToggle(CROP_VALUES_EN[i])}
                            >
                                {t(key)}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="form-grid" style={{ marginTop: '16px' }}>
                    <div className="form-group">
                        <label>{t('profileSoilType')}</label>
                        <select className="form-input" value={profile.soil_type}
                            onChange={e => setProfile(p => ({ ...p, soil_type: e.target.value }))}>
                            {SOIL_KEYS.map((key, i) =>
                                <option key={key} value={SOIL_VALUES_EN[i]}>{t(key)}</option>
                            )}
                        </select>
                    </div>
                    <div className="form-group">
                        <label>{t('profileLandSize')}</label>
                        <input className="form-input" type="number" value={profile.land_size_acres} min="0" step="0.5"
                            onChange={e => setProfile(p => ({ ...p, land_size_acres: parseFloat(e.target.value) || 0 }))}
                            onKeyDown={e => e.key === 'Enter' && handleSave()} />
                    </div>
                </div>
            </div>

            {/* Save */}
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '8px' }}>
                <button onClick={handleSave} disabled={saving} className="send-btn"
                    style={{ padding: '12px 48px', fontSize: '15px', borderRadius: '12px' }}>
                    {saving ? `⏳ ${t('saving')}` : `💾 ${t('profileSaveBtn')}`}
                </button>
            </div>

            {/* Change PIN */}
            <div className="card" style={{ marginTop: '18px' }}>
                <h3>🔐 {t('changePinTitle')}</h3>
                <p style={{ fontSize: '13px', color: '#666', marginBottom: '12px' }}>{t('changePinSubtitle')}</p>
                <div className="form-grid">
                    <div className="form-group">
                        <label>{t('changePinOldLabel')}</label>
                        <input className="form-input" type="password" maxLength={20}
                            value={oldPin} onChange={e => setOldPin(e.target.value)}
                            placeholder={t('changePinOldPlaceholder')} />
                    </div>
                    <div className="form-group">
                        <label>{t('changePinNewLabel')}</label>
                        <input className="form-input" type="password" maxLength={20}
                            value={newPin} onChange={e => setNewPin(e.target.value)}
                            placeholder={t('changePinNewPlaceholder')} />
                    </div>
                    <div className="form-group">
                        <label>{t('changePinConfirmLabel')}</label>
                        <input className="form-input" type="password" maxLength={20}
                            value={confirmNewPin} onChange={e => setConfirmNewPin(e.target.value)}
                            placeholder={t('changePinConfirmPlaceholder')}
                            onKeyDown={e => e.key === 'Enter' && !changingPin && handleChangePin()} />
                    </div>
                </div>
                {pinMessage && (
                    <div className={`alert ${pinMessage.type === 'success' ? 'alert-success' : 'alert-error'}`}>
                        {pinMessage.text}
                    </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: '8px' }}>
                    <button onClick={handleChangePin} disabled={changingPin || !oldPin || newPin.length < 6 || !confirmNewPin}
                        className="send-btn" style={{ padding: '10px 36px', fontSize: '14px', borderRadius: '10px' }}>
                        {changingPin ? '⏳ ...' : `🔐 ${t('changePinBtn')}`}
                    </button>
                </div>
            </div>

            {/* Recovery Email */}
            <div className="card" style={{ marginTop: '18px' }}>
                <h3>📧 {t('profileEmailLabel')}</h3>
                <p style={{ fontSize: '13px', color: '#666', marginBottom: '12px' }}>{t('profileEmailHint')}</p>
                <div className="form-grid">
                    <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                        <label>{t('profileEmailLabel')}</label>
                        <input className="form-input" type="email"
                            value={recoveryEmail} onChange={e => setRecoveryEmail(e.target.value)}
                            placeholder={t('profileEmailPlaceholder')}
                            onKeyDown={e => e.key === 'Enter' && !savingEmail && handleSaveEmail()} />
                    </div>
                </div>
                {emailMessage && (
                    <div className={`alert ${emailMessage.type === 'success' ? 'alert-success' : 'alert-error'}`}>
                        {emailMessage.text}
                    </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: '8px' }}>
                    <button onClick={handleSaveEmail}
                        disabled={savingEmail || !recoveryEmail.includes('@')}
                        className="send-btn" style={{ padding: '10px 36px', fontSize: '14px', borderRadius: '10px' }}>
                        {savingEmail ? '⏳ ...' : '💾 Save Email'}
                    </button>
                </div>
            </div>

            {/* Profile Summary */}
            {profile.name && (
                <div className="card" style={{ marginTop: '18px' }}>
                    <h3>📊 {t('profileSummary')}</h3>
                    <div className="profile-summary">
                        <div className="summary-item">
                            <span className="summary-label">{t('profileSumName')}</span>
                            <span className="summary-value">{profile.name}</span>
                        </div>
                        <div className="summary-item">
                            <span className="summary-label">{t('profileSumLocation')}</span>
                            <span className="summary-value">{getDistrictName(profile.district, language)}, {t(STATE_OPTION_OBJECTS.find(s => s.value === profile.state)?.key || 'selectState')}</span>
                        </div>
                        <div className="summary-item">
                            <span className="summary-label">{t('profileSumCrops')}</span>
                            <span className="summary-value">
                                {profile.crops.length > 0
                                    ? profile.crops.map(c => localizedCrop(c)).join(', ')
                                    : t('profileNoneSelected')}
                            </span>
                        </div>
                        <div className="summary-item">
                            <span className="summary-label">{t('profileSumSoil')}</span>
                            <span className="summary-value">
                                {t(SOIL_KEYS[SOIL_VALUES_EN.indexOf(profile.soil_type)] || 'soilAlluvial')}
                            </span>
                        </div>
                        <div className="summary-item">
                            <span className="summary-label">{t('profileSumLand')}</span>
                            <span className="summary-value">{profile.land_size_acres} {t('profileAcres')}</span>
                        </div>
                    </div>
                </div>
            )}

            <div className="tip-box" style={{ marginTop: '18px' }}>
                <span className="tip-icon">💡</span>
                <span>{t('profileTip')}</span>
            </div>
            {/* ── Delete Account ── */}
            <div className="delete-zone-card">
                <div className="delete-zone-inner">
                    <div className="delete-zone-badge">⚠️</div>
                    <div className="delete-zone-text">
                        <h4 className="delete-zone-title">{t('deleteProfileTitle')}</h4>
                        <p className="delete-zone-desc">{t('deleteProfileWarning')}</p>
                    </div>
                    <button
                        className="delete-zone-btn"
                        onClick={() => setShowDeleteConfirm(true)}
                        disabled={deleting}
                    >
                        🗑️ {t('deleteProfileBtn')}
                    </button>
                </div>
            </div>

            </div>{/* end profile-page-scroll */}

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div className="delete-modal-overlay" onClick={() => !deleting && setShowDeleteConfirm(false)}>
                    <div className="delete-modal" onClick={e => e.stopPropagation()}>
                        <div className="delete-modal-top">
                            <div className="delete-modal-icon-ring">
                                <span style={{ fontSize: '28px' }}>🗑️</span>
                            </div>
                            <h3>{t('deleteProfileConfirmTitle')}</h3>
                            <p>{t('deleteProfileConfirmMsg')}</p>
                        </div>
                        <div className="delete-modal-actions">
                            <button
                                className="delete-modal-cancel"
                                onClick={() => setShowDeleteConfirm(false)}
                                disabled={deleting}
                            >
                                {t('deleteProfileCancel')}
                            </button>
                            <button
                                className="delete-modal-confirm"
                                onClick={handleDeleteAccount}
                                disabled={deleting}
                            >
                                {deleting
                                    ? <span className="delete-spinner" />
                                    : <><span>🗑️</span> {t('deleteProfileConfirmBtn')}</>}
                            </button>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
}

export default ProfilePage;
