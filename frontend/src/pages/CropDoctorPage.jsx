// src/pages/CropDoctorPage.jsx

import { useState, useRef } from 'react';
import config from '../config';
import { useLanguage } from '../contexts/LanguageContext';
import { mockImageAnalyze } from '../services/mockApi';
import { STATE_OPTIONS } from '../i18n/translations';

function CropDoctorPage() {
    const { language, t } = useLanguage();
    const [image, setImage] = useState(null);
    const [preview, setPreview] = useState(null);
    const [cropName, setCropName] = useState('Rice');
    const [state, setState] = useState('Tamil Nadu');
    const [analysis, setAnalysis] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const fileInputRef = useRef(null);

    const cropKeys = [
        'cropRice', 'cropWheat', 'cropCotton', 'cropSugarcane', 'cropMaize',
        'cropGroundnut', 'cropBanana', 'cropCoconut', 'cropTomato', 'cropOnion',
        'cropMillets', 'cropPulses', 'cropSoybean', 'cropPotato', 'cropMango',
        'cropChilli', 'cropBrinjal'
    ];
    const cropValuesEn = [
        'Rice', 'Wheat', 'Cotton', 'Sugarcane', 'Maize', 'Groundnut', 'Banana',
        'Coconut', 'Tomato', 'Onion', 'Millets', 'Pulses', 'Soybean', 'Potato',
        'Mango', 'Chilli', 'Brinjal'
    ];

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (file.size > 5 * 1024 * 1024) {
            setError(t('cropDocImageTooLarge'));
            return;
        }
        setImage(file);
        setPreview(URL.createObjectURL(file));
        setError('');
        setAnalysis('');
    };

    const compressImage = (file, maxWidth, quality) => {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;
                if (width > maxWidth) {
                    height = (height * maxWidth) / width;
                    width = maxWidth;
                }
                canvas.width = width;
                canvas.height = height;
                canvas.getContext('2d').drawImage(img, 0, 0, width, height);
                canvas.toBlob(resolve, 'image/jpeg', quality);
            };
            img.src = URL.createObjectURL(file);
        });
    };

    const analyzeImage = async () => {
        if (!image) return;
        setLoading(true);
        setError('');

        try {
            if (config.MOCK_AI) {
                const data = await mockImageAnalyze(null, cropName, state, language);
                if (data.status === 'success') {
                    setAnalysis(data.data.analysis);
                } else {
                    setError(t('error'));
                }
                setLoading(false);
                return;
            }

            const compressed = await compressImage(image, 1024, 0.85);
            const reader = new FileReader();
            reader.onloadend = async () => {
                const base64 = reader.result.split(',')[1];
                try {
                    const res = await fetch(`${config.API_URL}/image-analyze`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            image_base64: base64,
                            crop_name: cropName,
                            state: state,
                            language: language
                        })
                    });
                    const data = await res.json();
                    if (data.status === 'success') {
                        setAnalysis(data.data.analysis);
                    } else {
                        setError(data.error || t('error'));
                    }
                } catch {
                    setError(t('connectionError'));
                }
                setLoading(false);
            };
            reader.readAsDataURL(compressed);
        } catch {
            setError(t('connectionError'));
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="page-header">
                <h2>
                    📸 {t('cropDocTitle')}
                    {config.MOCK_AI && <span className="demo-badge">{t('demoMode')}</span>}
                </h2>
                <p>{t('cropDocSubtitle')}</p>
            </div>

            <div className="two-col">
                {/* Left: Upload */}
                <div>
                    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                        <div
                            className={preview ? '' : 'upload-zone'}
                            onClick={() => fileInputRef.current.click()}
                            style={preview ? { cursor: 'pointer', padding: '16px' } : {}}
                        >
                            {preview ? (
                                <img src={preview} alt="Crop" style={{ width: '100%', borderRadius: '12px', display: 'block' }} />
                            ) : (
                                <>
                                    <span className="upload-icon">📷</span>
                                    <p><strong>{t('cropDocUpload')}</strong></p>
                                    <p>{t('cropDocDragDrop')}</p>
                                    <p style={{ fontSize: '12px', color: 'var(--text-light)', marginTop: 8 }}>{t('cropDocFormats')}</p>
                                </>
                            )}
                        </div>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/jpeg,image/png,image/webp"
                            onChange={handleFileChange}
                            style={{ display: 'none' }}
                        />
                    </div>

                    {image && (
                        <button
                            onClick={analyzeImage}
                            disabled={loading}
                            className="send-btn"
                            style={{ width: '100%', padding: '16px', fontSize: '16px', borderRadius: '12px', marginTop: '12px' }}
                        >
                            {loading ? `⏳ ${t('cropDocAnalyzing')}` : `🔍 ${t('cropDocAnalyze')}`}
                        </button>
                    )}
                </div>

                {/* Right: Settings */}
                <div>
                    <div className="card">
                        <div className="form-group">
                            <label>{t('cropDocCropName')}</label>
                            <select className="form-input" value={cropName} onChange={(e) => setCropName(e.target.value)}>
                                {cropKeys.map((key, i) => (
                                    <option key={key} value={cropValuesEn[i]}>{t(key)}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label>{t('cropDocState')}</label>
                            <select className="form-input" value={state} onChange={(e) => setState(e.target.value)}>
                                {STATE_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                        <div className="tip-box">
                            <span className="tip-icon">💡</span>
                            <span><strong>{t('cropDocTips')}:</strong> {t('cropDocTipsText')}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Error */}
            {error && (
                <div className="alert alert-error" style={{ marginTop: '18px' }}>
                    ❌ {error}
                </div>
            )}

            {/* Analysis Result */}
            {analysis && (
                <div className="card" style={{ marginTop: '18px', borderLeft: '4px solid var(--success)' }}>
                    <h3>✅ {t('cropDocResult')}</h3>
                    <div
                        style={{ lineHeight: 1.7, color: 'var(--text-secondary)' }}
                        dangerouslySetInnerHTML={{
                            __html: analysis.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                             .replace(/\n/g, '<br/>')
                        }}
                    />
                    <div className="alert alert-warning" style={{ marginTop: '16px', marginBottom: 0 }}>
                        🏥 {t('cropDocDisclaimer')}
                    </div>
                </div>
            )}
        </div>
    );
}

export default CropDoctorPage;
