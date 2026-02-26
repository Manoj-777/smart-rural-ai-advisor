// src/pages/CropDoctorPage.jsx

import { useState, useRef } from 'react';
import config from '../config';

function CropDoctorPage() {
    const [image, setImage] = useState(null);
    const [preview, setPreview] = useState(null);
    const [cropName, setCropName] = useState('Rice');
    const [state, setState] = useState('Tamil Nadu');
    const [analysis, setAnalysis] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const fileInputRef = useRef(null);

    const crops = ['Rice', 'Wheat', 'Cotton', 'Sugarcane', 'Maize', 'Groundnut', 
                   'Banana', 'Coconut', 'Tomato', 'Onion', 'Millets', 'Pulses', 
                   'Soybean', 'Potato', 'Mango', 'Chilli', 'Brinjal'];

    const states = ['Tamil Nadu', 'Andhra Pradesh', 'Telangana', 'Karnataka', 
                    'Kerala', 'Maharashtra', 'Punjab', 'Uttar Pradesh', 'Bihar',
                    'West Bengal', 'Madhya Pradesh', 'Gujarat', 'Rajasthan'];

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validate size (5 MB max)
        if (file.size > 5 * 1024 * 1024) {
            setError('Image too large. Please use a photo under 5 MB.');
            return;
        }

        setImage(file);
        setPreview(URL.createObjectURL(file));
        setError('');
        setAnalysis('');
    };

    const analyzeImage = async () => {
        if (!image) return;
        setLoading(true);
        setError('');

        try {
            // Compress image using Canvas
            const compressed = await compressImage(image, 1024, 0.85);
            
            // Convert to base64
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
                            language: 'en'
                        })
                    });
                    const data = await res.json();

                    if (data.status === 'success') {
                        setAnalysis(data.data.analysis);
                    } else {
                        setError(data.error || 'Analysis failed.');
                    }
                } catch (err) {
                    setError('Connection error. Try again.');
                }
                setLoading(false);
            };
            reader.readAsDataURL(compressed);
            
        } catch (err) {
            setError('Failed to process image.');
            setLoading(false);
        }
    };

    // Compress image to max width + JPEG quality
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

    return (
        <div>
            <h2>📸 Crop Doctor — AI Disease Diagnosis</h2>
            <p style={{ color: 'var(--text-light)', marginBottom: '20px' }}>
                Upload a photo of your sick crop. Our AI will identify the problem.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
                {/* Left: Image upload area */}
                <div className="card">
                    <div 
                        onClick={() => fileInputRef.current.click()}
                        style={{
                            border: '2px dashed var(--border)',
                            borderRadius: 'var(--radius)',
                            padding: '40px',
                            textAlign: 'center',
                            cursor: 'pointer',
                            background: preview ? 'transparent' : 'var(--primary-light)',
                            transition: 'border-color 0.2s'
                        }}
                    >
                        {preview ? (
                            <img src={preview} alt="Crop" 
                                 style={{ maxWidth: '100%', borderRadius: '8px' }} />
                        ) : (
                            <div>
                                <div style={{ fontSize: '48px', marginBottom: '12px' }}>📷</div>
                                <p><strong>Click to upload</strong> or drag & drop</p>
                                <p style={{ color: 'var(--text-light)', fontSize: '13px' }}>
                                    JPG, PNG, WebP — Max 5 MB
                                </p>
                            </div>
                        )}
                    </div>
                    <input 
                        ref={fileInputRef}
                        type="file" 
                        accept="image/jpeg,image/png,image/webp"
                        onChange={handleFileChange}
                        style={{ display: 'none' }}
                    />
                    
                    {image && (
                        <button 
                            onClick={analyzeImage}
                            disabled={loading}
                            style={{
                                marginTop: '16px',
                                width: '100%',
                                padding: '14px',
                                background: loading ? '#999' : 'var(--primary)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '8px',
                                fontSize: '16px',
                                fontWeight: '600',
                                cursor: loading ? 'not-allowed' : 'pointer'
                            }}
                        >
                            {loading ? '🌾 Analyzing... (15-30 sec)' : '🔍 Analyze Disease'}
                        </button>
                    )}
                </div>

                {/* Right: Settings */}
                <div className="card">
                    <label style={{ display: 'block', marginBottom: '12px' }}>
                        <strong>Crop Name</strong>
                        <select value={cropName} onChange={(e) => setCropName(e.target.value)}
                                style={{ width: '100%', padding: '8px', marginTop: '4px', borderRadius: '8px' }}>
                            {crops.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </label>
                    <label style={{ display: 'block', marginBottom: '12px' }}>
                        <strong>Your State</strong>
                        <select value={state} onChange={(e) => setState(e.target.value)}
                                style={{ width: '100%', padding: '8px', marginTop: '4px', borderRadius: '8px' }}>
                            {states.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                    </label>
                    <div style={{ 
                        background: 'var(--primary-light)', padding: '12px', 
                        borderRadius: '8px', fontSize: '13px' 
                    }}>
                        💡 <strong>Tips:</strong> Take a close-up of the affected leaf/stem. 
                        Good lighting helps accuracy.
                    </div>
                </div>
            </div>

            {/* Error */}
            {error && (
                <div className="card" style={{ borderLeft: '4px solid var(--error)', marginTop: '16px' }}>
                    ❌ {error}
                </div>
            )}

            {/* Analysis Result */}
            {analysis && (
                <div className="card" style={{ marginTop: '16px', borderLeft: '4px solid var(--success)' }}>
                    <h3 style={{ marginBottom: '12px' }}>✅ Analysis Result</h3>
                    <div dangerouslySetInnerHTML={{ 
                        __html: analysis.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                        .replace(/\n/g, '<br/>') 
                    }} />
                    <p style={{ marginTop: '16px', fontSize: '13px', color: 'var(--text-light)' }}>
                        🏥 Disclaimer: AI diagnosis is advisory only. For severe infections, 
                        consult your local KVK or district agricultural officer.
                    </p>
                </div>
            )}
        </div>
    );
}

export default CropDoctorPage;
