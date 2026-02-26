// src/pages/SchemesPage.jsx

import { useState, useEffect } from 'react';
import config from '../config';

function SchemesPage() {
    const [schemes, setSchemes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => {
        const fetchSchemes = async () => {
            try {
                const res = await fetch(`${config.API_URL}/schemes`);
                const data = await res.json();
                // API returns { schemes: { "pm-kisan": {...}, ... } } — convert object to array
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
            <h2>📋 Government Schemes for Farmers</h2>
            <input 
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search schemes..."
                style={{ width: '100%', padding: '12px', margin: '16px 0', 
                         borderRadius: '8px', border: '2px solid var(--border)' }}
            />

            {loading ? <p>Loading schemes...</p> : (
                <div>
                    {filtered.map((scheme, i) => (
                        <div key={i} className="card">
                            <h3>{scheme.name}</h3>
                            {scheme.full_name && (
                                <p style={{ marginBottom: '8px', fontStyle: 'italic' }}>{scheme.full_name}</p>
                            )}
                            {scheme.benefit && (
                                <p style={{ fontSize: '14px', color: 'var(--success)' }}>
                                    <strong>💰 Benefit:</strong> {scheme.benefit}
                                </p>
                            )}
                            {scheme.eligibility && (
                                <p style={{ fontSize: '14px', color: 'var(--text-light)' }}>
                                    <strong>👤 Eligibility:</strong> {scheme.eligibility}
                                </p>
                            )}
                            {scheme.how_to_apply && (
                                <p style={{ fontSize: '14px', whiteSpace: 'pre-line' }}>
                                    <strong>📝 How to Apply:</strong> {scheme.how_to_apply}
                                </p>
                            )}
                            {scheme.helpline && (
                                <p style={{ fontSize: '14px' }}>
                                    <strong>📞 Helpline:</strong> {scheme.helpline}
                                </p>
                            )}
                        </div>
                    ))}
                    {filtered.length === 0 && <p>No schemes found matching "{search}"</p>}
                </div>
            )}
        </div>
    );
}

export default SchemesPage;
