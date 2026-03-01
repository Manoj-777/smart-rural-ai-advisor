// src/pages/CropRecommendPage.jsx
// AI-powered crop recommendation based on soil, season, water, and location

import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import { DISTRICT_MAP } from '../i18n/translations';
import { getDistrictName } from '../i18n/districtTranslations';
import config from '../config';

const SOIL_TYPES = [
    { value: 'Alluvial', key: 'soilAlluvial' },
    { value: 'Black (Regur)', key: 'soilBlack' },
    { value: 'Red', key: 'soilRed' },
    { value: 'Laterite', key: 'soilLaterite' },
    { value: 'Sandy', key: 'soilSandy' },
    { value: 'Clay', key: 'soilClay' },
    { value: 'Loamy', key: 'soilLoamy' },
    { value: 'Saline', key: 'soilSaline' },
];
const WATER_OPTIONS = [
    { value: 'Rainfed only', key: 'waterRainfed' },
    { value: 'Canal irrigation', key: 'waterCanal' },
    { value: 'Borewell / Tubewell', key: 'waterBorewell' },
    { value: 'Drip irrigation', key: 'waterDrip' },
    { value: 'Sprinkler', key: 'waterSprinkler' },
];
const SEASON_OPTIONS = [
    { value: 'Kharif (Jun-Sep)', key: 'seasonKharifFull' },
    { value: 'Rabi (Oct-Feb)', key: 'seasonRabiFull' },
    { value: 'Zaid (Mar-May)', key: 'seasonZaidFull' },
];
const BUDGET_OPTIONS = [
    { value: 'Low (< ₹10,000/acre)', key: 'budgetLow' },
    { value: 'Medium (₹10,000-25,000/acre)', key: 'budgetMedium' },
    { value: 'High (> ₹25,000/acre)', key: 'budgetHigh' },
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

const LANG_NAMES = {
    'en-IN': 'English', 'hi-IN': 'Hindi', 'ta-IN': 'Tamil', 'te-IN': 'Telugu',
    'kn-IN': 'Kannada', 'ml-IN': 'Malayalam', 'bn-IN': 'Bengali', 'mr-IN': 'Marathi',
    'gu-IN': 'Gujarati', 'pa-IN': 'Punjabi', 'or-IN': 'Odia', 'as-IN': 'Assamese', 'ur-IN': 'Urdu'
};

function CropRecommendPage() {
    const { language, t } = useLanguage();
    const { farmerId, farmerProfile } = useFarmer();
    const [soilType, setSoilType] = useState(farmerProfile?.soil_type || '');
    const [season, setSeason] = useState('');
    const [water, setWater] = useState('');
    const [budget, setBudget] = useState('');
    const [state, setState] = useState(farmerProfile?.state || '');
    const [district, setDistrict] = useState(farmerProfile?.district || '');
    const [landSize, setLandSize] = useState(farmerProfile?.land_size_acres || '');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const resultRef = useRef(null);

    // Auto-detect season
    useEffect(() => {
        const month = new Date().getMonth() + 1;
        if (month >= 6 && month <= 9) setSeason('Kharif (Jun-Sep)');
        else if (month >= 10 || month <= 2) setSeason('Rabi (Oct-Feb)');
        else setSeason('Zaid (Mar-May)');
    }, []);

    const handleRecommend = async () => {
        if (!soilType || !season) {
            setError(t('cropRecSelectRequired') || 'Please select soil type and season.');
            return;
        }
        setError('');
        setLoading(true);
        setResult(null);

        const prompt = `You are an expert Indian agricultural advisor. Based on the following farm details, recommend the top 5 best crops to grow. For each crop, provide the crop name, expected yield per acre, estimated profit per acre, water requirement, key care tips, and market demand status.

Farm Details:
- Soil Type: ${soilType}
- Season: ${season}
- Water Source: ${water || 'Not specified'}
- Budget: ${budget || 'Not specified'}
- District/Location: ${[state, district].filter(Boolean).join(', ') || 'Not specified'}
- Land Size: ${landSize ? landSize + ' acres' : 'Not specified'}

Format clearly with numbered recommendations. Include practical advice specific to Indian farming conditions.`;

        const callAPI = async () => {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 55000);
            try {
                const res = await fetch(`${config.API_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: prompt,
                        session_id: 'crop-recommend-' + Date.now(),
                        farmer_id: farmerId || 'anonymous',
                        language: language
                    }),
                    signal: controller.signal
                });
                clearTimeout(timeout);
                return await res.json();
            } catch (err) {
                clearTimeout(timeout);
                throw err;
            }
        };

        const maxRetries = 2;
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const data = await callAPI();
                if (data.status === 'success') {
                    setResult({
                        text: data.data.reply,
                        audioUrl: data.data.audio_url
                    });
                    setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth' }), 200);
                    setLoading(false);
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

    // TTS for result
    const [speaking, setSpeaking] = useState(false);
    const handleSpeak = () => {
        if (!result?.text) return;
        if (speaking) { window.speechSynthesis?.cancel(); setSpeaking(false); return; }
        const text = result.text.replace(/\*\*/g, '').replace(/\*/g, '').replace(/\n/g, '. ');
        const utter = new SpeechSynthesisUtterance(text.slice(0, 3000));
        utter.lang = language.replace('_', '-');
        utter.rate = 0.9;
        utter.onend = () => setSpeaking(false);
        utter.onerror = () => setSpeaking(false);
        setSpeaking(true);
        window.speechSynthesis.speak(utter);
    };

    // Simple markdown formatting
    function formatText(text) {
        if (!text) return '';
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^(\d+)\.\s/gm, '<span class="list-num">$1.</span> ')
            .replace(/^-\s(.+)/gm, '<span class="list-bullet">•</span> $1')
            .replace(/\n/g, '<br/>');
    }

    return (
        <div className="ai-feature-page">
            <div className="page-header" style={{ paddingLeft: '24px', marginBottom: '8px' }}>
                <div className="page-header-top">
                    <h2>🌱 {t('cropRecTitle') || 'AI Crop Recommendation'}</h2>
                </div>
                <p>{t('cropRecSubtitle') || 'Get personalized crop suggestions based on your farm conditions.'}</p>
            </div>

            <div className="ai-feature-form">
                <div className="ai-form-grid">
                    <div className="ai-form-group">
                        <label>🏜️ {t('profileSoilType') || 'Soil Type'} *</label>
                        <select value={soilType} onChange={e => setSoilType(e.target.value)}>
                            <option value="">{t('cropRecSelectSoil') || 'Select soil type...'}</option>
                            {SOIL_TYPES.map(s => <option key={s.value} value={s.value}>{t(s.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>📅 {t('cropRecSeason') || 'Season'} *</label>
                        <select value={season} onChange={e => setSeason(e.target.value)}>
                            <option value="">{t('cropRecSelectSeason') || 'Select season...'}</option>
                            {SEASON_OPTIONS.map(s => <option key={s.value} value={s.value}>{t(s.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>💧 {t('cropRecWater') || 'Water Source'}</label>
                        <select value={water} onChange={e => setWater(e.target.value)}>
                            <option value="">{t('cropRecSelectWater') || 'Select water source...'}</option>
                            {WATER_OPTIONS.map(w => <option key={w.value} value={w.value}>{t(w.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>💰 {t('cropRecBudget') || 'Budget'}</label>
                        <select value={budget} onChange={e => setBudget(e.target.value)}>
                            <option value="">{t('cropRecSelectBudget') || 'Select budget range...'}</option>
                            {BUDGET_OPTIONS.map(b => <option key={b.value} value={b.value}>{t(b.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>📍 {t('profileState') || 'State'}</label>
                        <select value={state} onChange={e => { setState(e.target.value); setDistrict(''); }}>
                            <option value="">{t('selectState') || 'Select state...'}</option>
                            {STATE_OPTIONS.map(s => <option key={s.value} value={s.value}>{t(s.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>🏘️ {t('profileDistrict') || 'District'}</label>
                        <select value={district} onChange={e => setDistrict(e.target.value)}>
                            <option value="">{t('selectDistrict') || 'Select district...'}</option>
                            {(DISTRICT_MAP[state] || []).map(d => (
                                <option key={d} value={d}>{getDistrictName(d, language)}</option>
                            ))}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>📐 {t('profileLandSize') || 'Land Size (acres)'}</label>
                        <input type="number" value={landSize} onChange={e => setLandSize(e.target.value)}
                            placeholder={t('cropRecLandPlaceholder') || 'e.g. 5'} min="0" step="0.5" />
                    </div>
                </div>

                {error && <div className="ai-error">{error}</div>}

                <button className="ai-submit-btn" onClick={handleRecommend} disabled={loading}>
                    {loading ? (
                        <><span className="spinner-sm"></span> {t('cropRecAnalyzing') || 'Analyzing your farm...'}</>
                    ) : (
                        <>🌾 {t('cropRecGetBtn') || 'Get Crop Recommendations'}</>
                    )}
                </button>
            </div>

            {result && (
                <div className="ai-result-card" ref={resultRef}>
                    <div className="ai-result-header">
                        <h3>🌾 {t('cropRecResultTitle') || 'Recommended Crops for Your Farm'}</h3>
                        <button className={`tts-btn ${speaking ? 'tts-active' : ''}`} onClick={handleSpeak}
                            title={speaking ? t('ttsStopReading') : t('ttsReadAloud')}>
                            {speaking ? (
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/></svg>
                            ) : (
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
                            )}
                            <span className="tts-label">{speaking ? t('ttsStop') : t('ttsListen')}</span>
                        </button>
                    </div>
                    {result.audioUrl && (
                        <audio controls src={result.audioUrl} className="ai-result-audio" />
                    )}
                    <div className="ai-result-body"
                        dangerouslySetInnerHTML={{ __html: formatText(result.text) }} />
                    <p className="ai-disclaimer">
                        {t('cropRecDisclaimer') || '⚠️ AI-generated recommendation. Consult your local KVK or agriculture officer for region-specific guidance.'}
                    </p>
                </div>
            )}
        </div>
    );
}

export default CropRecommendPage;
