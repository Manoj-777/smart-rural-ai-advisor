// src/pages/SchemesPage.jsx

import { useState, useEffect } from 'react';
import config from '../config';
import { useLanguage } from '../contexts/LanguageContext';
import { SchemesSkeleton } from '../components/SkeletonLoader';

function SchemesPage() {
    const { t } = useLanguage();
    const [schemes, setSchemes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

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

    const filtered = schemes.filter(s =>
        s.name?.toLowerCase().includes(search.toLowerCase()) ||
        s.full_name?.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div>
            <div className="page-header">
                <h2>📋 {t('schemesTitle')}</h2>
                <p>{t('schemesSubtitle')}</p>
            </div>

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
                <div>
                    {filtered.map((scheme, i) => (
                        <div key={i} className="scheme-card" style={{ animationDelay: `${i * 0.05}s` }}>
                            <h3>{scheme.name}</h3>
                            {scheme.full_name && (
                                <p className="scheme-fullname">{scheme.full_name}</p>
                            )}
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
                        </div>
                    ))}
                    {filtered.length === 0 && (
                        <div className="alert alert-warning">
                            {t('schemesNoMatch')} "{search}"
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default SchemesPage;
