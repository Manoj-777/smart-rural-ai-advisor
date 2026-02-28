// src/pages/ProfilePage.jsx

import { useState, useEffect, useCallback, useRef } from 'react';
import config from '../config';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import { CROP_KEYS, CROP_VALUES_EN, SOIL_KEYS, SOIL_VALUES_EN, STATE_OPTIONS, DISTRICT_MAP } from '../i18n/translations';

function ProfilePage() {
    const { t, setLanguage } = useLanguage();
    const { farmerId, farmerPhone, updateProfile } = useFarmer();
    const [profile, setProfile] = useState({
        name: '', state: 'Tamil Nadu', district: '', crops: [],
        soil_type: 'Alluvial', land_size_acres: 0, language: 'ta-IN'
    });
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);
    const debounceRef = useRef(null);
    const hasLoadedRef = useRef(false);

    useEffect(() => {
        const loadProfile = async () => {
            try {
                const res = await fetch(`${config.API_URL}/profile/${farmerId}`);
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
                await fetch(`${config.API_URL}/profile/${farmerId}`, {
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
            await fetch(`${config.API_URL}/profile/${farmerId}`, {
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

    // Find localized crop name for display
    const localizedCrop = (enValue) => {
        const idx = CROP_VALUES_EN.indexOf(enValue);
        return idx >= 0 ? t(CROP_KEYS[idx]) : enValue;
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
                            placeholder={t('profileNamePlaceholder')} />
                    </div>
                    <div className="form-group">
                        <label>{t('profileDistrict')}</label>
                        <select className="form-input" value={profile.district}
                            onChange={e => setProfile(p => ({ ...p, district: e.target.value }))}>
                            <option value="">{t('profileDistrictPlaceholder')}</option>
                            {(DISTRICT_MAP[profile.state] || []).map(d =>
                                <option key={d} value={d}>{d}</option>
                            )}
                        </select>
                    </div>
                    <div className="form-group">
                        <label>{t('profileState')}</label>
                        <select className="form-input" value={profile.state}
                            onChange={e => setProfile(p => ({ ...p, state: e.target.value, district: '' }))}>
                            {STATE_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
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
                            onChange={e => setProfile(p => ({ ...p, land_size_acres: parseFloat(e.target.value) || 0 }))} />
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
                            <span className="summary-value">{profile.district}, {profile.state}</span>
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
            </div>{/* end profile-page-scroll */}
        </div>
    );
}

export default ProfilePage;
