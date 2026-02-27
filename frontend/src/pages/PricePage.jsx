// src/pages/PricePage.jsx

import { useState, useMemo } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { getPriceT } from '../i18n/priceTranslations';

/* ── Crop market price data (MSP + simulated market prices) ─────── */
const CROP_PRICES = [
    { name: 'Rice', season: 'Kharif', msp: 2300, marketMin: 2100, marketMax: 2800, unit: '₹/quintal', trend: 'up' },
    { name: 'Wheat', season: 'Rabi', msp: 2275, marketMin: 2200, marketMax: 2900, unit: '₹/quintal', trend: 'stable' },
    { name: 'Cotton', season: 'Kharif', msp: 7020, marketMin: 6500, marketMax: 8200, unit: '₹/quintal', trend: 'up' },
    { name: 'Sugarcane', season: 'Annual', msp: 3150, marketMin: 2900, marketMax: 3600, unit: '₹/quintal', trend: 'stable' },
    { name: 'Maize', season: 'Kharif', msp: 2090, marketMin: 1900, marketMax: 2500, unit: '₹/quintal', trend: 'down' },
    { name: 'Groundnut', season: 'Kharif', msp: 6377, marketMin: 5800, marketMax: 7500, unit: '₹/quintal', trend: 'up' },
    { name: 'Soybean', season: 'Kharif', msp: 4600, marketMin: 4200, marketMax: 5500, unit: '₹/quintal', trend: 'up' },
    { name: 'Toor Dal', season: 'Kharif', msp: 7000, marketMin: 6500, marketMax: 8500, unit: '₹/quintal', trend: 'up' },
    { name: 'Mustard', season: 'Rabi', msp: 5650, marketMin: 5200, marketMax: 6800, unit: '₹/quintal', trend: 'stable' },
    { name: 'Chana', season: 'Rabi', msp: 5440, marketMin: 5000, marketMax: 6500, unit: '₹/quintal', trend: 'down' },
    { name: 'Green Gram', season: 'Kharif', msp: 8558, marketMin: 7800, marketMax: 9500, unit: '₹/quintal', trend: 'up' },
    { name: 'Black Gram', season: 'Kharif', msp: 6950, marketMin: 6400, marketMax: 8000, unit: '₹/quintal', trend: 'stable' },
    { name: 'Sunflower', season: 'Kharif', msp: 6760, marketMin: 6200, marketMax: 7800, unit: '₹/quintal', trend: 'down' },
    { name: 'Sesame', season: 'Kharif', msp: 8635, marketMin: 8000, marketMax: 10500, unit: '₹/quintal', trend: 'up' },
    { name: 'Jowar', season: 'Kharif', msp: 3180, marketMin: 2900, marketMax: 3800, unit: '₹/quintal', trend: 'stable' },
    { name: 'Bajra', season: 'Kharif', msp: 2500, marketMin: 2300, marketMax: 3000, unit: '₹/quintal', trend: 'stable' },
    { name: 'Ragi', season: 'Kharif', msp: 3846, marketMin: 3500, marketMax: 4500, unit: '₹/quintal', trend: 'up' },
    { name: 'Barley', season: 'Rabi', msp: 1735, marketMin: 1600, marketMax: 2100, unit: '₹/quintal', trend: 'down' },
    { name: 'Jute', season: 'Kharif', msp: 5050, marketMin: 4600, marketMax: 5800, unit: '₹/quintal', trend: 'stable' },
    { name: 'Lentil', season: 'Rabi', msp: 6425, marketMin: 5900, marketMax: 7200, unit: '₹/quintal', trend: 'up' },
    { name: 'Coconut', season: 'Perennial', msp: 10860, marketMin: 9800, marketMax: 12500, unit: '₹/quintal (copra)', trend: 'up' },
    { name: 'Safflower', season: 'Rabi', msp: 5800, marketMin: 5300, marketMax: 6500, unit: '₹/quintal', trend: 'stable' },
    { name: 'Castor', season: 'Kharif', msp: 6291, marketMin: 5800, marketMax: 7200, unit: '₹/quintal', trend: 'up' },
    { name: 'Tomato', season: 'Year-round', msp: null, marketMin: 800, marketMax: 4500, unit: '₹/quintal', trend: 'up' },
    { name: 'Onion', season: 'Rabi', msp: null, marketMin: 600, marketMax: 3500, unit: '₹/quintal', trend: 'down' },
    { name: 'Potato', season: 'Rabi', msp: null, marketMin: 500, marketMax: 2000, unit: '₹/quintal', trend: 'stable' },
    { name: 'Okra', season: 'Kharif', msp: null, marketMin: 1200, marketMax: 3000, unit: '₹/quintal', trend: 'stable' },
];

/* ── Pesticide / Input prices ─────── */
const PEST_RATES = [
    { name: 'Neem Oil (1L)', category: 'Bio-pesticide', price: 350, unit: '₹/litre', usage: 'General pest control' },
    { name: 'Chlorpyrifos 20% EC', category: 'Insecticide', price: 480, unit: '₹/litre', usage: 'Termites, Borers, Aphids' },
    { name: 'Imidacloprid 17.8% SL', category: 'Insecticide', price: 650, unit: '₹/250ml', usage: 'Whitefly, Aphids, Jassids' },
    { name: 'Mancozeb 75% WP', category: 'Fungicide', price: 320, unit: '₹/500g', usage: 'Blight, Downy Mildew, Rust' },
    { name: 'Carbendazim 50% WP', category: 'Fungicide', price: 280, unit: '₹/500g', usage: 'Wilt, Rot, Blast' },
    { name: 'Glyphosate 41% SL', category: 'Herbicide', price: 520, unit: '₹/litre', usage: 'Broad-spectrum weed control' },
    { name: 'Trichoderma viride', category: 'Bio-fungicide', price: 180, unit: '₹/kg', usage: 'Soil-borne diseases' },
    { name: 'Beauveria bassiana', category: 'Bio-insecticide', price: 250, unit: '₹/kg', usage: 'Borers, Whitefly, Mealybug' },
    { name: 'Lambda Cyhalothrin 5% EC', category: 'Insecticide', price: 420, unit: '₹/litre', usage: 'Bollworm, Pod Borer, Army Worm' },
    { name: 'Copper Oxychloride 50% WP', category: 'Fungicide', price: 290, unit: '₹/500g', usage: 'Bacterial Blight, Leaf Spot' },
    { name: 'Thiamethoxam 25% WG', category: 'Insecticide', price: 580, unit: '₹/100g', usage: 'Sucking pests, Stem Borer' },
    { name: 'Propiconazole 25% EC', category: 'Fungicide', price: 750, unit: '₹/litre', usage: 'Rust, Sheath Blight, Smut' },
    { name: 'Emamectin Benzoate 5% SG', category: 'Insecticide', price: 620, unit: '₹/100g', usage: 'Fall Armyworm, Fruit Borer' },
    { name: 'Pseudomonas fluorescens', category: 'Bio-fungicide', price: 200, unit: '₹/kg', usage: 'Wilt, Root Rot, Damping Off' },
    { name: 'Yellow Sticky Traps (20 pcs)', category: 'Trap', price: 150, unit: '₹/pack', usage: 'Whitefly, Aphids monitoring' },
    { name: 'Pheromone Traps (set of 5)', category: 'Trap', price: 350, unit: '₹/set', usage: 'Fruit Fly, Bollworm monitoring' },
];

const SEASONS = ['All', 'Kharif', 'Rabi', 'Annual', 'Perennial', 'Year-round'];
const PEST_CATEGORIES = ['All', 'Bio-pesticide', 'Bio-fungicide', 'Bio-insecticide', 'Insecticide', 'Fungicide', 'Herbicide', 'Trap'];

function TrendBadge({ trend, pt }) {
    const icons = { up: ['📈', '#16a34a'], down: ['📉', '#dc2626'], stable: ['➡️', '#d97706'] };
    const labels = { up: pt.trendRising, down: pt.trendFalling, stable: pt.trendStable };
    const [icon, color] = icons[trend] || icons.stable;
    const label = labels[trend] || labels.stable;
    return <span className="price-trend" style={{ color, background: color + '14' }}>{icon} {label}</span>;
}

function PricePage() {
    const { language, t } = useLanguage();
    const pt = getPriceT(language);
    const [tab, setTab] = useState('crops');
    const [search, setSearch] = useState('');
    const [seasonFilter, setSeasonFilter] = useState('All');
    const [pestCatFilter, setPestCatFilter] = useState('All');

    /* translate a crop name for display */
    const cropName = (en) => pt.crops?.[en] || en;
    /* translate a season for display */
    const seasonName = (en) => pt.seasons?.[en] || en;
    /* translate a pest category for display */
    const catName = (en) => pt.categories?.[en] || en;
    /* translate pest usage */
    const pestUsage = (en, fallback) => pt.pestUsage?.[en] || fallback;
    /* translate pest name */
    const pestName = (en) => pt.pestNames?.[en] || en;

    const filteredCrops = useMemo(() => {
        return CROP_PRICES.filter(c => {
            const translated = cropName(c.name);
            const matchSearch = c.name.toLowerCase().includes(search.toLowerCase()) ||
                                translated.toLowerCase().includes(search.toLowerCase());
            const matchSeason = seasonFilter === 'All' || c.season === seasonFilter;
            return matchSearch && matchSeason;
        });
    }, [search, seasonFilter, language]);

    const filteredPests = useMemo(() => {
        return PEST_RATES.filter(p => {
            const translated = pestName(p.name);
            const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) ||
                                translated.toLowerCase().includes(search.toLowerCase());
            const matchCat = pestCatFilter === 'All' || p.category === pestCatFilter;
            return matchSearch && matchCat;
        });
    }, [search, pestCatFilter, language]);

    return (
        <div className="price-page">
            <div className="page-header">
                <h2>💰 {pt.pageTitle}</h2>
                <p>{pt.pageSubtitle}</p>
            </div>

            {/* Tabs */}
            <div className="price-tabs">
                <button className={`price-tab ${tab === 'crops' ? 'active' : ''}`} onClick={() => { setTab('crops'); setSearch(''); }}>
                    🌾 {pt.tabCrops}
                </button>
                <button className={`price-tab ${tab === 'pests' ? 'active' : ''}`} onClick={() => { setTab('pests'); setSearch(''); }}>
                    🧪 {pt.tabPests}
                </button>
            </div>

            {/* Search & Filter */}
            <div className="price-toolbar">
                <input
                    type="text"
                    className="price-search"
                    placeholder={tab === 'crops' ? `🔍 ${pt.searchCrops}` : `🔍 ${pt.searchPests}`}
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                />
                {tab === 'crops' ? (
                    <select className="price-filter" value={seasonFilter} onChange={e => setSeasonFilter(e.target.value)}>
                        {SEASONS.map(s => <option key={s} value={s}>{s === 'All' ? `📅 ${pt.allSeasons}` : seasonName(s)}</option>)}
                    </select>
                ) : (
                    <select className="price-filter" value={pestCatFilter} onChange={e => setPestCatFilter(e.target.value)}>
                        {PEST_CATEGORIES.map(c => <option key={c} value={c}>{c === 'All' ? `📂 ${pt.allCategories}` : catName(c)}</option>)}
                    </select>
                )}
            </div>

            {/* Crop Prices Table */}
            {tab === 'crops' && (
                <div className="price-table-wrap">
                    <table className="price-table">
                        <thead>
                            <tr>
                                <th>{pt.thCrop}</th>
                                <th>{pt.thSeason}</th>
                                <th>{pt.thMSP}</th>
                                <th>{pt.thMarketRange}</th>
                                <th>{pt.thTrend}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredCrops.map((c, i) => (
                                <tr key={i}>
                                    <td className="price-crop-name">🌱 {cropName(c.name)}</td>
                                    <td><span className="price-season-badge">{seasonName(c.season)}</span></td>
                                    <td className="price-msp">{c.msp ? `₹${c.msp.toLocaleString()}` : '—'}</td>
                                    <td className="price-range">
                                        ₹{c.marketMin.toLocaleString()} – ₹{c.marketMax.toLocaleString()}
                                        <span className="price-unit">{c.unit}</span>
                                    </td>
                                    <td><TrendBadge trend={c.trend} pt={pt} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {filteredCrops.length === 0 && (
                        <p className="price-empty">{pt.emptyCrops}</p>
                    )}
                    <p className="price-disclaimer">
                        ⚠️ {pt.disclaimerCrops}
                    </p>
                </div>
            )}

            {/* Pesticide Rates Table */}
            {tab === 'pests' && (
                <div className="price-table-wrap">
                    <table className="price-table">
                        <thead>
                            <tr>
                                <th>{pt.thProduct}</th>
                                <th>{pt.thCategory}</th>
                                <th>{pt.thPrice}</th>
                                <th>{pt.thUsage}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredPests.map((p, i) => (
                                <tr key={i}>
                                    <td className="price-crop-name">🧴 {pestName(p.name)}</td>
                                    <td><span className={`pest-cat-badge cat-${p.category.toLowerCase().replace(/[^a-z]/g, '')}`}>{catName(p.category)}</span></td>
                                    <td className="price-msp">₹{p.price} <span className="price-unit">{p.unit}</span></td>
                                    <td className="price-usage">{pestUsage(p.name, p.usage)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {filteredPests.length === 0 && (
                        <p className="price-empty">{pt.emptyPests}</p>
                    )}
                    <p className="price-disclaimer">
                        ⚠️ {pt.disclaimerPests}
                    </p>
                </div>
            )}
        </div>
    );
}

export default PricePage;
