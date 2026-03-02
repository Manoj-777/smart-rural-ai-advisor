// src/pages/FarmCalendarPage.jsx
// AI-powered seasonal farming calendar & activity planner

import { useState, useRef } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { sanitizeHtml } from '../utils/sanitize';
import { useFarmer } from '../contexts/FarmerContext';
import { DISTRICT_MAP } from '../i18n/translations';
import { getDistrictName } from '../i18n/districtTranslations';
import config from '../config';
import { generateAsyncTts } from '../utils/asyncTts';
import { apiFetch } from '../utils/apiFetch';

const CROP_OPTIONS = [
    { value: 'Rice', key: 'cropRice' },
    { value: 'Wheat', key: 'cropWheat' },
    { value: 'Cotton', key: 'cropCotton' },
    { value: 'Sugarcane', key: 'cropSugarcane' },
    { value: 'Maize', key: 'cropMaize' },
    { value: 'Groundnut', key: 'cropGroundnut' },
    { value: 'Banana', key: 'cropBanana' },
    { value: 'Coconut', key: 'cropCoconut' },
    { value: 'Tomato', key: 'cropTomato' },
    { value: 'Onion', key: 'cropOnion' },
    { value: 'Millets', key: 'cropMillets' },
    { value: 'Pulses', key: 'cropPulses' },
    { value: 'Soybean', key: 'cropSoybean' },
    { value: 'Potato', key: 'cropPotato' },
    { value: 'Mango', key: 'cropMango' },
    { value: 'Chilli', key: 'cropChilli' },
    { value: 'Brinjal', key: 'cropBrinjal' },
    { value: 'Turmeric', key: 'cropTurmeric' },
    { value: 'Mustard', key: 'cropMustard' },
    { value: 'Jute', key: 'cropJute' },
    { value: 'Tea', key: 'cropTea' },
    { value: 'Coffee', key: 'cropCoffee' },
];

const STATE_OPTIONS = [
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

const MONTH_KEYS = [
    'monthJan', 'monthFeb', 'monthMar', 'monthApr', 'monthMay', 'monthJun',
    'monthJul', 'monthAug', 'monthSep', 'monthOct', 'monthNov', 'monthDec'
];
const MONTH_SHORT_KEYS = [
    'monthJanShort', 'monthFebShort', 'monthMarShort', 'monthAprShort', 'monthMayShort', 'monthJunShort',
    'monthJulShort', 'monthAugShort', 'monthSepShort', 'monthOctShort', 'monthNovShort', 'monthDecShort'
];
const MONTH_NAMES_EN = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];
const SEASON_KEYS = { Kharif: 'seasonKharif', Rabi: 'seasonRabi', Zaid: 'seasonZaid' };

const LANG_NAMES = {
    'en-IN': 'English', 'hi-IN': 'Hindi', 'ta-IN': 'Tamil', 'te-IN': 'Telugu',
    'kn-IN': 'Kannada', 'ml-IN': 'Malayalam', 'bn-IN': 'Bengali', 'mr-IN': 'Marathi',
    'gu-IN': 'Gujarati', 'pa-IN': 'Punjabi', 'or-IN': 'Odia', 'as-IN': 'Assamese', 'ur-IN': 'Urdu'
};

function FarmCalendarPage() {
    const { language, t } = useLanguage();
    const { farmerId, farmerProfile } = useFarmer();
    const currentMonth = new Date().getMonth();
    const [selectedMonth, setSelectedMonth] = useState(currentMonth);
    const [selectedCrops, setSelectedCrops] = useState(farmerProfile?.crops || []);
    const [state, setState] = useState(farmerProfile?.state || '');
    const [district, setDistrict] = useState(farmerProfile?.district || '');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const resultRef = useRef(null);

    const getSeason = (monthIdx) => {
        if (monthIdx >= 5 && monthIdx <= 8) return 'Kharif';
        if (monthIdx >= 9 || monthIdx <= 1) return 'Rabi';
        return 'Zaid';
    };
    const getSeasonLabel = (monthIdx) => t(SEASON_KEYS[getSeason(monthIdx)]);

    const callChatAPI = async (prompt, sessionPrefix) => {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 55000);
        try {
            const res = await apiFetch(`/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: prompt,
                    session_id: `${sessionPrefix}-${Date.now()}`,
                    farmer_id: farmerId || 'anonymous',
                    language: language
                }),
                signal: controller.signal
            });
            clearTimeout(timeout);
            const data = await res.json();
            return data;
        } catch (err) {
            clearTimeout(timeout);
            throw err;
        }
    };

    const handleGenerate = async () => {
        setError('');
        setLoading(true);
        setResult(null);

        const monthName = MONTH_NAMES_EN[selectedMonth];
        const season = getSeason(selectedMonth);

        const prompt = `Generate a detailed Indian farming activity calendar for **${monthName}** (${season} season).

${selectedCrops.length ? `Farmer's crops: ${selectedCrops.join(', ')}` : ''}
${[state, district].filter(Boolean).length ? `Location: ${[state, district].filter(Boolean).join(', ')}` : ''}

Please provide a comprehensive monthly farming calendar covering: week-by-week activities, land preparation, sowing/planting, irrigation schedule, fertilizer & nutrient management, pest & disease watch, harvesting, market tips, and weather precautions.

Be practical and specific to Indian farming conditions. Use bullet points and organize clearly.`;

        const maxRetries = 2;
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const data = await callChatAPI(prompt, 'farm-calendar');
                if (data.status === 'success') {
                    const newResult = {
                        text: data.data.reply,
                        audioUrl: data.data.audio_url,
                        audioKey: data.data.audio_key,
                        audioLoading: !!data.data.audio_pending
                    };
                    setResult(newResult);
                    setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth' }), 200);
                    setLoading(false);
                    if (data.data.audio_pending && data.data.reply) {
                        generateAsyncTts(data.data.reply, data.data.detected_language).then(tts => {
                            if (tts) {
                                setResult(prev => ({ ...prev, audioUrl: tts.audioUrl, audioKey: tts.audioKey, audioLoading: false }));
                            } else {
                                setResult(prev => ({ ...prev, audioLoading: false }));
                            }
                        });
                    }
                    return;
                } else if (attempt === maxRetries) {
                    setError(data.message || t('connectionError'));
                }
            } catch {
                if (attempt === maxRetries) {
                    setError(t('connectionError'));
                }
            }
        }
        setLoading(false);
    };

    function formatText(text) {
        if (!text) return '';
        const html = text
            .replace(/^###\s*(.+)$/gm, '<div class="ai-section-title">$1</div>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^(\d+)\.\s+(.+)/gm, '<div class="ai-list-item"><span class="list-num">$1.</span> $2</div>')
            .replace(/^[•\-]\s+(.+)/gm, '<div class="ai-list-item"><span class="list-bullet">•</span> $1</div>')
            .replace(/^\s{2,}[\-•]\s+(.+)/gm, '<div class="ai-list-item ai-sub-item"><span class="list-bullet">◦</span> $1</div>')
            .replace(/\n\n/g, '<div class="ai-section-gap"></div>')
            .replace(/\n/g, '<br/>');
        return sanitizeHtml(html);
    }

    return (
        <div className="ai-feature-page">
            <div className="page-header" style={{ paddingLeft: '24px', marginBottom: '8px' }}>
                <div className="page-header-top">
                    <h2>📅 {t('farmCalTitle') || 'AI Farming Calendar'}</h2>
                </div>
                <p>{t('farmCalSubtitle') || 'Get month-wise farming activities, tips, and a smart planner for your farm.'}</p>
            </div>

            {/* Month selector - visual calendar strip */}
            <div className="calendar-month-strip">
                {MONTH_KEYS.map((mk, idx) => {
                    const season = getSeason(idx);
                    const seasonColor = season === 'Kharif' ? '#16a34a' : season === 'Rabi' ? '#0284c7' : '#d97706';
                    return (
                        <button
                            key={mk}
                            className={`calendar-month-btn ${idx === selectedMonth ? 'active' : ''} ${idx === currentMonth ? 'current' : ''}`}
                            onClick={() => setSelectedMonth(idx)}
                            style={{ '--season-color': seasonColor }}
                        >
                            <span className="cal-month-name">{t(MONTH_SHORT_KEYS[idx])}</span>
                            <span className="cal-season-tag">{t(SEASON_KEYS[season])}</span>
                        </button>
                    );
                })}
            </div>

            <div className="ai-feature-form" style={{ marginTop: '16px' }}>
                <div className="ai-form-grid">
                    <div className="ai-form-group">
                        <label>🌾 {t('farmCalCrops') || 'Your Crops (optional)'}</label>
                        <select
                            value=""
                            onChange={e => {
                                const val = e.target.value;
                                if (val && !selectedCrops.includes(val)) {
                                    setSelectedCrops([...selectedCrops, val]);
                                }
                            }}
                        >
                            <option value="">{t('soilSelectCrop') || 'Select crop...'}</option>
                            {CROP_OPTIONS.filter(c => !selectedCrops.includes(c.value)).map(c => (
                                <option key={c.value} value={c.value}>{t(c.key)}</option>
                            ))}
                        </select>
                        {selectedCrops.length > 0 && (
                            <div className="crop-tags" style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
                                {selectedCrops.map(crop => {
                                    const opt = CROP_OPTIONS.find(c => c.value === crop);
                                    return (
                                        <span key={crop} style={{
                                            display: 'inline-flex', alignItems: 'center', gap: '4px',
                                            background: '#e8f5e9', color: '#2e7d32', padding: '4px 10px',
                                            borderRadius: '16px', fontSize: '0.85rem', fontWeight: 500
                                        }}>
                                            {opt ? t(opt.key) : crop}
                                            <button type="button" onClick={() => setSelectedCrops(selectedCrops.filter(c => c !== crop))}
                                                style={{
                                                    background: 'none', border: 'none', color: '#c62828',
                                                    cursor: 'pointer', fontSize: '1rem', lineHeight: 1, padding: '0 2px'
                                                }}>×</button>
                                        </span>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                    <div className="ai-form-group">
                        <label>📍 {t('profileState') || 'State'}</label>
                        <select value={state} onChange={e => { setState(e.target.value); setDistrict(''); }}>
                            <option value="">{t('selectState') || 'Select state...'}</option>
                            {STATE_OPTIONS.map(s => <option key={s.value} value={s.value}>{t(s.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>🏘️ {t('profileDistrict') || 'District (optional)'}</label>
                        <select value={district} onChange={e => setDistrict(e.target.value)}>
                            <option value="">{t('selectDistrict') || 'Select district...'}</option>
                            {(DISTRICT_MAP[state] || []).map(d => (
                                <option key={d} value={d}>{getDistrictName(d, language)}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {error && <div className="ai-error">{error}</div>}

                <button className="ai-submit-btn" onClick={handleGenerate} disabled={loading}>
                    {loading ? (
                        <><span className="spinner-sm"></span> {t('farmCalGenerating') || 'Generating calendar...'}</>
                    ) : (
                        <>📅 {t(MONTH_KEYS[selectedMonth])} — {t('farmCalGenBtn') || 'Get Farming Plan'}</>
                    )}
                </button>
            </div>

            {result && (
                <div className="ai-result-card" ref={resultRef}>
                    <div className="ai-result-header">
                        <h3>📅 {t(MONTH_KEYS[selectedMonth])} — {t('farmCalResultTitle') || 'Farming Activity Plan'}</h3>
                    </div>
                    {result.audioUrl && (
                        <audio controls src={result.audioUrl} className="ai-result-audio"
                            onError={async (e) => {
                                if (result.audioKey) {
                                    try {
                                        const res = await apiFetch(`/chat`, {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ refresh_audio_key: result.audioKey })
                                        });
                                        const d = await res.json();
                                        if (d.status === 'success' && d.data?.audio_url) {
                                            e.target.src = d.data.audio_url;
                                            setResult(prev => ({ ...prev, audioUrl: d.data.audio_url }));
                                        }
                                    } catch { /* silent */ }
                                }
                            }}
                        />
                    )}
                    {result.audioLoading && (
                        <div className="audio-loading-indicator">
                            <span className="spinner-sm"></span> {t('ttsGenerating') || 'Generating audio...'}
                        </div>
                    )}
                    <div className="ai-result-body"
                        dangerouslySetInnerHTML={{ __html: formatText(result.text) }} />
                    <p className="ai-disclaimer">
                        {t('farmCalDisclaimer') || '⚠️ AI-generated plan. Adjust based on local conditions and consult your KVK for expert advice.'}
                    </p>
                </div>
            )}
        </div>
    );
}

export default FarmCalendarPage;
