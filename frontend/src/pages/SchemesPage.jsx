// src/pages/SchemesPage.jsx

import { useState, useEffect } from 'react';
import config from '../config';
import { useLanguage } from '../contexts/LanguageContext';
import { SchemesSkeleton } from '../components/SkeletonLoader';
import schemeTranslations from '../i18n/schemeTranslations';

function SchemesPage() {
    const { language, t } = useLanguage();
    const [schemes, setSchemes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [expandedId, setExpandedId] = useState(null);

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
