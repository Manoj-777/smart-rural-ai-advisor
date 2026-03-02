// src/pages/SchemesPage.jsx

import { useState, useEffect, useCallback } from 'react';
import config from '../config';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import { SchemesSkeleton } from '../components/SkeletonLoader';
import schemeTranslations from '../i18n/schemeTranslations';

// Map English state name → translation key (same as ProfilePage)
const STATE_KEY_MAP = {
    'Andhra Pradesh': 'stateAP', 'Arunachal Pradesh': 'stateAR', 'Assam': 'stateAS',
    'Bihar': 'stateBR', 'Chhattisgarh': 'stateCG', 'Goa': 'stateGA',
    'Gujarat': 'stateGJ', 'Haryana': 'stateHR', 'Himachal Pradesh': 'stateHP',
    'Jharkhand': 'stateJH', 'Karnataka': 'stateKA', 'Kerala': 'stateKL',
    'Madhya Pradesh': 'stateMP', 'Maharashtra': 'stateMH', 'Manipur': 'stateMN',
    'Meghalaya': 'stateML', 'Mizoram': 'stateMZ', 'Nagaland': 'stateNL',
    'Odisha': 'stateOD', 'Puducherry': 'statePY', 'Punjab': 'statePB',
    'Rajasthan': 'stateRJ', 'Sikkim': 'stateSK', 'Tamil Nadu': 'stateTN',
    'Telangana': 'stateTS', 'Tripura': 'stateTR', 'Uttar Pradesh': 'stateUP',
    'Uttarakhand': 'stateUK', 'West Bengal': 'stateWB',
};

function SchemesPage() {
    const { language, t } = useLanguage();
    const { farmerProfile } = useFarmer();
    const [schemes, setSchemes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [expandedId, setExpandedId] = useState(null);

    // State-specific schemes from KB
    const [stateSchemes, setStateSchemes] = useState('');
    const [stateLoading, setStateLoading] = useState(false);
    const farmerState = farmerProfile?.state || '';

    useEffect(() => {
        const fetchSchemes = async () => {
            try {
                const res = await fetch(`${config.API_URL}/schemes`);
                const data = await res.json();
                const schemesObj = data.data?.schemes || data.schemes || {};
                const schemesArray = Array.isArray(schemesObj)
                    ? schemesObj
                    : Object.values(schemesObj);
                setSchemes(schemesArray);
            } catch {
                setSchemes([]);
            }
            setLoading(false);
        };
        fetchSchemes();
    }, []);

    // Auto-fetch state-specific schemes from Knowledge Base
    const fetchStateSchemes = useCallback(async (state) => {
        if (!state) return;
        setStateLoading(true);
        setStateSchemes('');
        try {
            const query = `List all government schemes and subsidies available specifically for farmers in ${state} state, India. Include central government schemes applicable in ${state} and state-specific schemes. For each scheme mention: scheme name, benefit amount, eligibility, and how to apply.`;
            const res = await fetch(`${config.API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: query, language, session_id: 'schemes-state' }),
            });
            if (res.ok) {
                const data = await res.json();
                let reply = data.data?.reply || data.response || data.message || '';
                reply = reply.replace(/\n\s*Sources:\s*.+$/m, '').trim();
                setStateSchemes(reply);
            }
        } catch (err) {
            console.error('State schemes fetch error:', err);
            setStateSchemes('');
        } finally {
            setStateLoading(false);
        }
    }, [language]);

    useEffect(() => {
        if (farmerState) {
            fetchStateSchemes(farmerState);
        }
    }, [farmerState, fetchStateSchemes]);

    // Get translated scheme data — fall back to English, then to raw API data
    const getTranslated = (scheme) => {
        const langData = schemeTranslations[language] || schemeTranslations['en-IN'] || {};
        const translated = langData[scheme.name] || (schemeTranslations['en-IN'] || {})[scheme.name];
        if (translated) return { ...scheme, ...translated };
        return scheme;
    };

    const applyNowText = (schemeTranslations[language] || schemeTranslations['en-IN'] || {}).applyNow || 'Apply Now';

    const filtered = schemes.map(getTranslated).filter(s =>
        s.name?.toLowerCase().includes(search.toLowerCase()) ||
        s.full_name?.toLowerCase().includes(search.toLowerCase())
    );

    const toggleCard = (i) => {
        setExpandedId(expandedId === i ? null : i);
    };

    return (
        <div className="schemes-page">
            <div className="page-header">
                <h2>📋 {t('schemesTitle')}</h2>
                <p>{t('schemesSubtitle')}</p>
            </div>

            <div className="schemes-page-scroll">

            {/* State-specific schemes from Knowledge Base */}
            {farmerState && (
                <div className="state-schemes-section" style={{ marginBottom: '24px' }}>
                    <div className="state-schemes-header">
                        <h3>🏛️ {t('schemesForState')} {t(STATE_KEY_MAP[farmerState]) || farmerState}</h3>
                        <button
                            className="send-btn"
                            style={{ padding: '6px 16px', fontSize: '13px', borderRadius: '8px' }}
                            onClick={() => fetchStateSchemes(farmerState)}
                            disabled={stateLoading}
                        >
                            🔄 {stateLoading ? '...' : t('schemesRefresh')}
                        </button>
                    </div>
                    {stateLoading ? (
                        <div className="card" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-light)' }}>
                            ⏳ {t('schemesFetchingAI')}
                        </div>
                    ) : stateSchemes ? (
                        <div className="card" style={{ borderLeft: '4px solid var(--primary)', lineHeight: 1.7 }}>
                            <div
                                dangerouslySetInnerHTML={{
                                    __html: stateSchemes
                                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                        .replace(/\n/g, '<br/>')
                                }}
                            />
                        </div>
                    ) : null}
                </div>
            )}

            <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>
                📋 {t('schemesCentral')}
            </h3>

            <div className="search-bar">
                <span className="search-icon">🔍</span>
                <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder={t('schemesSearch')}
                />
            </div>

            {loading ? (
                <SchemesSkeleton />
            ) : (
                <div className="schemes-grid">
                    {filtered.map((scheme, i) => {
                        const isOpen = expandedId === i;
                        return (
                            <div
                                key={i}
                                className={`scheme-card ${isOpen ? 'scheme-card--expanded' : ''}`}
                                style={{ animationDelay: `${i * 0.05}s` }}
                            >
                                {/* Clickable header — always visible */}
                                <div className="scheme-card__header" onClick={() => toggleCard(i)}>
                                    <div className="scheme-card__title-group">
                                        <h3 className="scheme-card__name">{scheme.name}</h3>
                                        {scheme.full_name && (
                                            <p className="scheme-card__fullname">{scheme.full_name}</p>
                                        )}
                                    </div>
                                    <span className={`scheme-card__chevron ${isOpen ? 'open' : ''}`}>▼</span>
                                </div>

                                {/* Expandable details */}
                                {isOpen && (
                                    <div className="scheme-card__body">
                                        {scheme.benefit && (
                                            <div className="scheme-detail">
                                                <span className="detail-icon">💰</span>
                                                <span><span className="detail-label">{t('schemesBenefit')}:</span> {scheme.benefit}</span>
                                            </div>
                                        )}
                                        {scheme.eligibility && (
                                            <div className="scheme-detail">
                                                <span className="detail-icon">👤</span>
                                                <span><span className="detail-label">{t('schemesEligibility')}:</span> {scheme.eligibility}</span>
                                            </div>
                                        )}
                                        {scheme.how_to_apply && (
                                            <div className="scheme-detail">
                                                <span className="detail-icon">📝</span>
                                                <span><span className="detail-label">{t('schemesHowToApply')}:</span> {scheme.how_to_apply}</span>
                                            </div>
                                        )}
                                        {scheme.helpline && (
                                            <div className="scheme-detail">
                                                <span className="detail-icon">📞</span>
                                                <span><span className="detail-label">{t('schemesHelpline')}:</span> {scheme.helpline}</span>
                                            </div>
                                        )}
                                        {scheme.website && (
                                            <a
                                                href={scheme.website}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="scheme-apply-btn"
                                            >
                                                🔗 {applyNowText} — {scheme.website.replace(/^https?:\/\//, '')}
                                            </a>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                    {filtered.length === 0 && (
                        <div className="alert alert-warning">
                            {t('schemesNoMatch')} "{search}"
                        </div>
                    )}
                </div>
            )}
            </div>{/* end schemes-page-scroll */}
        </div>
    );
}

export default SchemesPage;
