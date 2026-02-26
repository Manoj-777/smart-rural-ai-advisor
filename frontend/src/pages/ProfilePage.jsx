// src/pages/ProfilePage.jsx

import { useState, useEffect } from 'react';
import config from '../config';

function ProfilePage() {
    const [profile, setProfile] = useState({
        name: '', state: 'Tamil Nadu', district: '', crops: [],
        soil_type: 'Alluvial', land_size_acres: 0, language: 'ta-IN'
    });
    const [farmerId] = useState(() => {
        const stored = localStorage.getItem('farmer_id');
        if (stored) return stored;
        const newId = `f_${crypto.randomUUID().slice(0, 8)}`;
        localStorage.setItem('farmer_id', newId);
        return newId;
    });
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);

    const CROP_OPTIONS = [
        'Rice', 'Wheat', 'Cotton', 'Sugarcane', 'Maize',
        'Groundnut', 'Banana', 'Coconut', 'Tomato', 'Onion',
        'Millets', 'Pulses', 'Soybean', 'Potato', 'Mango'
    ];
    const SOIL_OPTIONS = ['Alluvial', 'Black (Regur)', 'Red', 'Laterite', 'Sandy', 'Clayey', 'Loamy'];
    const STATE_OPTIONS = [
        'Tamil Nadu', 'Andhra Pradesh', 'Telangana', 'Karnataka', 'Kerala',
        'Maharashtra', 'Punjab', 'Haryana', 'Uttar Pradesh', 'West Bengal',
        'Madhya Pradesh', 'Rajasthan', 'Gujarat', 'Odisha', 'Bihar'
    ];

    useEffect(() => {
        const loadProfile = async () => {
            try {
                const res = await fetch(`${config.API_URL}/profile/${farmerId}`);
                const data = await res.json();
                if (data.data) setProfile(prev => ({ ...prev, ...data.data }));
            } catch { /* New user — use defaults */ }
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

    const handleSave = async () => {
        setSaving(true);
        setMessage(null);
        try {
            await fetch(`${config.API_URL}/profile/${farmerId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profile)
            });
            setMessage({ type: 'success', text: '✅ Profile saved! AI will now give personalized advice.' });
        } catch {
            setMessage({ type: 'error', text: '❌ Save failed. Check connection.' });
        }
        setSaving(false);
    };

    return (
        <div>
            <h2>👤 My Farm Profile</h2>
            <p style={{ color: 'var(--text-light)', marginBottom: '8px' }}>
                Save your details so the AI gives <strong>personalized</strong> advice.
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-light)' }}>Farmer ID: {farmerId}</p>

            {message && (
                <div style={{
                    padding: '12px', borderRadius: '8px', marginBottom: '16px',
                    background: message.type === 'success' ? '#f0f7e8' : '#fdecea',
                    color: message.type === 'success' ? '#2d5016' : '#c62828'
                }}>{message.text}</div>
            )}

            <div className="card">
                <h3>📋 Personal Details</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                        <label>Full Name</label>
                        <input type="text" value={profile.name}
                            onChange={e => setProfile(p => ({ ...p, name: e.target.value }))}
                            placeholder="Enter your name"
                            style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '2px solid var(--border)' }} />
                    </div>
                    <div>
                        <label>District</label>
                        <input type="text" value={profile.district}
                            onChange={e => setProfile(p => ({ ...p, district: e.target.value }))}
                            placeholder="e.g., Thanjavur"
                            style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '2px solid var(--border)' }} />
                    </div>
                    <div>
                        <label>State</label>
                        <select value={profile.state}
                            onChange={e => setProfile(p => ({ ...p, state: e.target.value }))}
                            style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '2px solid var(--border)' }}>
                            {STATE_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                    </div>
                    <div>
                        <label>Preferred Language</label>
                        <select value={profile.language}
                            onChange={e => setProfile(p => ({ ...p, language: e.target.value }))}
                            style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '2px solid var(--border)' }}>
                            {Object.entries(config.LANGUAGES).map(([code, lang]) =>
                                <option key={code} value={code}>{lang.name}</option>
                            )}
                        </select>
                    </div>
                </div>
            </div>

            <div className="card" style={{ marginTop: '16px' }}>
                <h3>🌾 Farm Details</h3>
                <div style={{ marginBottom: '12px' }}>
                    <label>My Crops (click to select)</label>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
                        {CROP_OPTIONS.map(crop => (
                            <button key={crop} onClick={() => handleCropToggle(crop)}
                                style={{
                                    padding: '6px 14px', borderRadius: '20px', cursor: 'pointer',
                                    border: profile.crops.includes(crop) ? '2px solid var(--primary)' : '2px solid var(--border)',
                                    background: profile.crops.includes(crop) ? 'var(--primary)' : 'white',
                                    color: profile.crops.includes(crop) ? 'white' : 'var(--text)'
                                }}>{crop}</button>
                        ))}
                    </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                        <label>Soil Type</label>
                        <select value={profile.soil_type}
                            onChange={e => setProfile(p => ({ ...p, soil_type: e.target.value }))}
                            style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '2px solid var(--border)' }}>
                            {SOIL_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                    </div>
                    <div>
                        <label>Land Size (acres)</label>
                        <input type="number" value={profile.land_size_acres} min="0" step="0.5"
                            onChange={e => setProfile(p => ({ ...p, land_size_acres: parseFloat(e.target.value) || 0 }))}
                            style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '2px solid var(--border)' }} />
                    </div>
                </div>
            </div>

            <button onClick={handleSave} disabled={saving} className="send-btn"
                style={{ marginTop: '16px', width: '100%', padding: '14px' }}>
                {saving ? '⏳ Saving...' : '💾 Save Profile'}
            </button>

            {profile.name && (
                <div className="card" style={{ marginTop: '16px' }}>
                    <h3>📊 Profile Summary</h3>
                    <p><strong>Name:</strong> {profile.name}</p>
                    <p><strong>Location:</strong> {profile.district}, {profile.state}</p>
                    <p><strong>Crops:</strong> {profile.crops.join(', ') || 'None selected'}</p>
                    <p><strong>Soil:</strong> {profile.soil_type}</p>
                    <p><strong>Land:</strong> {profile.land_size_acres} acres</p>
                </div>
            )}

            <p style={{ marginTop: '16px', fontSize: '13px', color: 'var(--text-light)' }}>
                💡 <strong>Tip:</strong> When you ask the AI a crop question, it automatically uses your profile data to give better answers!
            </p>
        </div>
    );
}

export default ProfilePage;
