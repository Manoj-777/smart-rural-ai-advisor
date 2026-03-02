// src/pages/SoilAnalysisPage.jsx
// AI-powered soil health analysis and fertilizer recommendation

import { useState, useRef } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import config from '../config';

const PH_RANGES = [
    { value: 'Below 4.5 (Very Acidic)', key: 'phVeryAcidic' },
    { value: '4.5 - 5.5 (Acidic)', key: 'phAcidic' },
    { value: '5.5 - 6.5 (Slightly Acidic)', key: 'phSlightlyAcidic' },
    { value: '6.5 - 7.5 (Neutral)', key: 'phNeutral' },
    { value: '7.5 - 8.5 (Alkaline)', key: 'phAlkaline' },
    { value: 'Above 8.5 (Very Alkaline)', key: 'phVeryAlkaline' },
    { value: "Don't know", key: 'phDontKnow' },
];
const NUTRIENT_LEVELS = [
    { value: 'Low', key: 'nutrientLow' },
    { value: 'Medium', key: 'nutrientMedium' },
    { value: 'High', key: 'nutrientHigh' },
    { value: "Don't know", key: 'nutrientDontKnow' },
];
const SOIL_COLORS = [
    { value: 'Dark Brown/Black', key: 'colorDarkBrown' },
    { value: 'Red/Reddish', key: 'colorRed' },
    { value: 'Yellow/Light Brown', key: 'colorYellow' },
    { value: 'Grey', key: 'colorGrey' },
    { value: 'White (salt crust)', key: 'colorWhiteSalt' },
];
const DRAINAGE = [
    { value: 'Water stands for days', key: 'drainageStands' },
    { value: 'Drains in a few hours', key: 'drainageHours' },
    { value: 'Drains quickly', key: 'drainageQuick' },
    { value: 'Very dry, cracks easily', key: 'drainageDryCracks' },
];
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

const LANG_NAMES = {
    'en-IN': 'English', 'hi-IN': 'Hindi', 'ta-IN': 'Tamil', 'te-IN': 'Telugu',
    'kn-IN': 'Kannada', 'ml-IN': 'Malayalam', 'bn-IN': 'Bengali', 'mr-IN': 'Marathi',
    'gu-IN': 'Gujarati', 'pa-IN': 'Punjabi', 'or-IN': 'Odia', 'as-IN': 'Assamese', 'ur-IN': 'Urdu'
};

function SoilAnalysisPage() {
    const { language, t } = useLanguage();
    const { farmerId, farmerProfile } = useFarmer();
    const [ph, setPh] = useState('');
    const [nitrogen, setNitrogen] = useState('');
    const [phosphorus, setPhosphorus] = useState('');
    const [potassium, setPotassium] = useState('');
    const [soilColor, setSoilColor] = useState('');
    const [drainage, setDrainage] = useState('');
    const [crop, setCrop] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const resultRef = useRef(null);

    const handleAnalyze = async () => {
        if (!ph && !soilColor && !drainage) {
            setError(t('soilSelectRequired') || 'Please fill in at least one soil parameter.');
            return;
        }
        setError('');
        setLoading(true);
        setResult(null);

        const soilDetails = [];
        if (ph) soilDetails.push(`pH Level: ${ph}`);
        if (nitrogen) soilDetails.push(`Nitrogen (N): ${nitrogen}`);
        if (phosphorus) soilDetails.push(`Phosphorus (P): ${phosphorus}`);
        if (potassium) soilDetails.push(`Potassium (K): ${potassium}`);
        if (soilColor) soilDetails.push(`Soil Color/Appearance: ${soilColor}`);
        if (drainage) soilDetails.push(`Water Drainage: ${drainage}`);
        const targetCrop = crop || 'General';
        const location = [farmerProfile?.district, farmerProfile?.state].filter(Boolean).join(', ') || 'India';

        const prompt = `Analyze the following soil test data and provide a detailed agricultural soil health report for an Indian farmer.

Soil Data:
${soilDetails.length ? soilDetails.map(d => `- ${d}`).join('\n') : '- No lab data provided (use visual observations)'}
- Target Crop: ${targetCrop}
- Location: ${location}

Provide these sections:
1. Soil Health Rating (Good / Moderate / Poor) with brief explanation
2. Key Issues Found — list specific problems based on the inputs
3. Fertilizer Recommendation — exact NPK ratio, brand names available in India, dosage per acre
4. Organic Amendments — compost, vermicompost, green manure suggestions
5. 3-Month Soil Improvement Plan — month-wise action items
6. Best Crops for This Soil — top 5 crops suited to these soil conditions
7. Warning Signs to Watch — what to look for in the field
8. Estimated Cost — approximate cost per acre in INR

Keep advice practical for Indian farmers. Use bullet points.`;

        const callAPI = async () => {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 55000);
            try {
                const res = await fetch(`${config.API_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: prompt,
                        session_id: 'soil-analysis-' + Date.now(),
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

    // TTS
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
                    <h2>🧪 {t('soilTitle') || 'AI Soil Health Analyzer'}</h2>
                </div>
                <p>{t('soilSubtitle') || 'Enter your soil test results or observations to get AI-powered fertilizer and improvement recommendations.'}</p>
            </div>

            <div className="ai-feature-form">
                {/* Soil test results section */}
                <h4 className="ai-form-section-title">🔬 {t('soilTestResults') || 'Soil Test Results'} <span className="ai-optional">({t('soilIfAvailable') || 'if available from soil testing lab'})</span></h4>
                <div className="ai-form-grid">
                    <div className="ai-form-group">
                        <label>pH {t('soilLevel') || 'Level'}</label>
                        <select value={ph} onChange={e => setPh(e.target.value)}>
                            <option value="">{t('soilSelect') || 'Select...'}</option>
                            {PH_RANGES.map(p => <option key={p.value} value={p.value}>{t(p.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>🟢 {t('soilNitrogen') || 'Nitrogen (N)'}</label>
                        <select value={nitrogen} onChange={e => setNitrogen(e.target.value)}>
                            <option value="">{t('soilSelect') || 'Select...'}</option>
                            {NUTRIENT_LEVELS.map(n => <option key={n.value} value={n.value}>{t(n.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>🔵 {t('soilPhosphorus') || 'Phosphorus (P)'}</label>
                        <select value={phosphorus} onChange={e => setPhosphorus(e.target.value)}>
                            <option value="">{t('soilSelect') || 'Select...'}</option>
                            {NUTRIENT_LEVELS.map(n => <option key={n.value} value={n.value}>{t(n.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>🟠 {t('soilPotassium') || 'Potassium (K)'}</label>
                        <select value={potassium} onChange={e => setPotassium(e.target.value)}>
                            <option value="">{t('soilSelect') || 'Select...'}</option>
                            {NUTRIENT_LEVELS.map(n => <option key={n.value} value={n.value}>{t(n.key)}</option>)}
                        </select>
                    </div>
                </div>

                {/* Visual observation section */}
                <h4 className="ai-form-section-title" style={{ marginTop: '20px' }}>👁️ {t('soilObservations') || 'Visual Observations'}</h4>
                <div className="ai-form-grid">
                    <div className="ai-form-group">
                        <label>🎨 {t('soilColor') || 'Soil Color'}</label>
                        <select value={soilColor} onChange={e => setSoilColor(e.target.value)}>
                            <option value="">{t('soilSelect') || 'Select...'}</option>
                            {SOIL_COLORS.map(c => <option key={c.value} value={c.value}>{t(c.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>💧 {t('soilDrainage') || 'Water Drainage'}</label>
                        <select value={drainage} onChange={e => setDrainage(e.target.value)}>
                            <option value="">{t('soilSelect') || 'Select...'}</option>
                            {DRAINAGE.map(d => <option key={d.value} value={d.value}>{t(d.key)}</option>)}
                        </select>
                    </div>
                    <div className="ai-form-group">
                        <label>🌾 {t('soilTargetCrop') || 'Target Crop'}</label>
                        <select value={crop} onChange={e => setCrop(e.target.value)}>
                            <option value="">{t('soilSelectCrop') || 'Select crop...'}</option>
                            <option value="General">{t('cropGeneral') || 'General (all crops)'}</option>
                            {CROP_OPTIONS.map(c => <option key={c.value} value={c.value}>{t(c.key)}</option>)}
                        </select>
                    </div>
                </div>

                {error && <div className="ai-error">{error}</div>}

                <button className="ai-submit-btn" onClick={handleAnalyze} disabled={loading}>
                    {loading ? (
                        <><span className="spinner-sm"></span> {t('soilAnalyzing') || 'Analyzing soil health...'}</>
                    ) : (
                        <>🧪 {t('soilAnalyzeBtn') || 'Analyze Soil & Get Recommendations'}</>
                    )}
                </button>
            </div>

            {result && (
                <div className="ai-result-card" ref={resultRef}>
                    <div className="ai-result-header">
                        <h3>🧪 {t('soilResultTitle') || 'Soil Health Analysis Report'}</h3>
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
                        {t('soilDisclaimer') || '⚠️ AI-generated analysis. For accurate results, get your soil tested at a government soil testing lab (₹50-100).'}
                    </p>
                </div>
            )}
        </div>
    );
}

export default SoilAnalysisPage;
