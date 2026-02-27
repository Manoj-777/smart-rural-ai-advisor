// src/pages/DashboardPage.jsx

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import config from '../config';

// Daily tips rotate based on day-of-year
const DAILY_TIPS = {
    'en-IN': [
        'Apply neem-based pesticides early morning for best results.',
        'Mulching helps retain soil moisture during dry spells.',
        'Rotate crops every season to maintain soil health.',
        'Drip irrigation saves up to 60% water compared to flood irrigation.',
        'Sow green manure crops like dhaincha between main seasons.',
        'Test your soil every 2 years to optimize fertilizer use.',
        'Install yellow sticky traps near crops to catch whiteflies.',
    ],
    'hi-IN': [
        'सबसे अच्छे परिणाम के लिए सुबह जल्दी नीम आधारित कीटनाशक लगाएं।',
        'सूखे मौसम में मल्चिंग से मिट्टी की नमी बनी रहती है।',
        'मिट्टी की सेहत बनाए रखने के लिए हर मौसम फसल बदलें।',
        'ड्रिप सिंचाई से बाढ़ सिंचाई की तुलना में 60% पानी बचता है।',
        'मुख्य मौसम के बीच ढैंचा जैसी हरी खाद की फसलें बोएं।',
        'उर्वरक उपयोग को अनुकूलित करने के लिए हर 2 साल में मिट्टी की जांच करें।',
        'सफेद मक्खी पकड़ने के लिए फसलों के पास पीले चिपचिपे जाल लगाएं।',
    ],
    'ta-IN': [
        'சிறந்த முடிவுகளுக்கு அதிகாலையில் வேப்பம் பூச்சிக்கொல்லிகளைப் பயன்படுத்தவும்.',
        'வறண்ட காலத்தில் மண்ணின் ஈரப்பதத்தைத் தக்கவைக்க மல்ச்சிங் உதவுகிறது.',
        'மண் ஆரோக்கியத்தை பராமரிக்க ஒவ்வொரு பருவத்திலும் பயிர் சுழற்சி செய்யுங்கள்.',
        'சொட்டு நீர் பாசனம் வெள்ள பாசனத்தை விட 60% தண்ணீரை சேமிக்கிறது.',
        'முக்கிய பருவங்களுக்கு இடையே தக்கை போன்ற பசுந்தாள் உரப் பயிர்களை விதைக்கவும்.',
        'உர பயன்பாட்டை மேம்படுத்த ஒவ்வொரு 2 ஆண்டுகளுக்கும் மண் பரிசோதனை செய்யுங்கள்.',
        'வெள்ளை ஈக்களைப் பிடிக்க பயிர்களுக்கு அருகில் மஞ்சள் ஒட்டும் பொறிகளை நிறுவவும்.',
    ],
    'kn-IN': [
        'ಉತ್ತಮ ಫಲಿತಾಂಶಗಳಿಗಾಗಿ ಬೆಳಗ್ಗೆ ಬೇಗನೆ ಬೇವಿನ ಕೀಟನಾಶಕಗಳನ್ನು ಬಳಸಿ.',
        'ಒಣ ಸಮಯದಲ್ಲಿ ಮಣ್ಣಿನ ತೇವಾಂಶವನ್ನು ಉಳಿಸಿಕೊಳ್ಳಲು ಮಲ್ಚಿಂಗ್ ಸಹಾಯ ಮಾಡುತ್ತದೆ.',
        'ಮಣ್ಣಿನ ಆರೋಗ್ಯವನ್ನು ಕಾಪಾಡಲು ಪ್ರತಿ ಋತುವಿನಲ್ಲಿ ಬೆಳೆ ಸರದಿ ಮಾಡಿ.',
        'ಹನಿ ನೀರಾವರಿ ಪ್ರವಾಹ ನೀರಾವರಿಗೆ ಹೋಲಿಸಿದರೆ 60% ನೀರನ್ನು ಉಳಿಸುತ್ತದೆ.',
        'ಮುಖ್ಯ ಋತುಗಳ ನಡುವೆ ಹಸಿರು ಗೊಬ್ಬರ ಬೆಳೆಗಳನ್ನು ಬಿತ್ತಿ.',
        'ರಸಗೊಬ್ಬರ ಬಳಕೆಯನ್ನು ಅತ್ಯುತ್ತಮವಾಗಿಸಲು ಪ್ರತಿ 2 ವರ್ಷಕ್ಕೊಮ್ಮೆ ಮಣ್ಣು ಪರೀಕ್ಷೆ ಮಾಡಿ.',
        'ಬಿಳಿ ನೊಣಗಳನ್ನು ಹಿಡಿಯಲು ಬೆಳೆಗಳ ಬಳಿ ಹಳದಿ ಅಂಟು ಬಲೆಗಳನ್ನು ಅಳವಡಿಸಿ.',
    ],
    'te-IN': [
        'ఉత్తమ ఫలితాల కోసం ఉదయాన్నే వేప ఆధారిత పురుగుమందులను వర్తింపజేయండి.',
        'ఎండ కాలంలో నేల తేమను నిలుపుకోవడానికి మల్చింగ్ సహాయపడుతుంది.',
        'నేల ఆరోగ్యాన్ని కాపాడుకోవడానికి ప్రతి సీజన్‌లో పంటలను మార్చండి.',
        'డ్రిప్ ఇరిగేషన్ వరద సేద్యంతో పోలిస్తే 60% నీటిని ఆదా చేస్తుంది.',
        'ప్రధాన సీజన్ల మధ్య జీలుగ వంటి పచ్చి ఎరువు పంటలను విత్తండి.',
        'ఎరువుల వినియోగాన్ని మెరుగుపరచడానికి ప్రతి 2 సంవత్సరాలకు నేల పరీక్ష చేయండి.',
        'తెల్ల ఈగలను పట్టుకోవడానికి పంటల దగ్గర పసుపు అంటుకునే ట్రాప్‌లను ఏర్పాటు చేయండి.',
    ],
};

function DashboardPage() {
    const { language, t } = useLanguage();
    const navigate = useNavigate();
    const [greeting, setGreeting] = useState('');
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const hour = new Date().getHours();
        if (hour < 12) setGreeting(t('dashGreetMorning'));
        else if (hour < 17) setGreeting(t('dashGreetAfternoon'));
        else setGreeting(t('dashGreetEvening'));

        const timer = setInterval(() => setCurrentTime(new Date()), 60000);
        return () => clearInterval(timer);
    }, [t]);

    const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0)) / 86400000);
    const tips = DAILY_TIPS[language] || DAILY_TIPS['en-IN'];
    const dailyTip = tips[dayOfYear % tips.length];

    const quickActions = [
        { icon: '💬', title: t('dashActionChat'), desc: t('dashActionChatDesc'), path: '/chat', color: '#16a34a' },
        { icon: '🌤️', title: t('dashActionWeather'), desc: t('dashActionWeatherDesc'), path: '/weather', color: '#0284c7' },
        { icon: '📋', title: t('dashActionSchemes'), desc: t('dashActionSchemesDesc'), path: '/schemes', color: '#d97706' },
        { icon: '📸', title: t('dashActionCropDoc'), desc: t('dashActionCropDocDesc'), path: '/crop-doctor', color: '#7c3aed' },
    ];

    const seasonInfo = (() => {
        const month = new Date().getMonth() + 1;
        if (month >= 6 && month <= 9) return { name: t('dashSeasonKharif'), icon: '🌧️', months: 'Jun–Sep' };
        if (month >= 10 && month <= 2) return { name: t('dashSeasonRabi'), icon: '❄️', months: 'Oct–Feb' };
        return { name: t('dashSeasonZaid'), icon: '☀️', months: 'Mar–May' };
    })();

    return (
        <div className="dashboard">
            {/* Hero greeting */}
            <div className="dash-hero">
                <div className="dash-hero-text">
                    <h1>{greeting} 👋</h1>
                    <p className="dash-subtitle">{t('dashWelcome')}</p>
                    <div className="dash-meta">
                        <span className="dash-meta-item">
                            📅 {currentTime.toLocaleDateString(language, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                        </span>
                        <span className="dash-meta-item">
                            {seasonInfo.icon} {seasonInfo.name} ({seasonInfo.months})
                        </span>
                    </div>
                </div>
                <div className="dash-hero-art">🌾</div>
            </div>

            {/* Quick Actions */}
            <h3 className="dash-section-title">{t('dashQuickActions')}</h3>
            <div className="dash-actions">
                {quickActions.map((action, i) => (
                    <button key={i} className="dash-action-card" onClick={() => navigate(action.path)}
                        style={{ '--action-color': action.color }}>
                        <span className="dash-action-icon">{action.icon}</span>
                        <span className="dash-action-title">{action.title}</span>
                        <span className="dash-action-desc">{action.desc}</span>
                    </button>
                ))}
            </div>

            {/* Daily Tip */}
            <div className="dash-tip-card">
                <div className="dash-tip-icon">💡</div>
                <div>
                    <h4>{t('dashDailyTip')}</h4>
                    <p>{dailyTip}</p>
                </div>
            </div>

            {/* Info Grid */}
            <div className="dash-info-grid">
                <div className="dash-info-card">
                    <span className="dash-info-icon">📞</span>
                    <h4>{t('dashHelplineTitle')}</h4>
                    <p>1800-180-1551</p>
                    <p className="dash-info-sub">{t('dashHelplineSub')}</p>
                </div>
                <div className="dash-info-card">
                    <span className="dash-info-icon">🏛️</span>
                    <h4>{t('dashKVKTitle')}</h4>
                    <p>{t('dashKVKDesc')}</p>
                </div>
                <div className="dash-info-card">
                    <span className="dash-info-icon">📱</span>
                    <h4>{t('dashVoiceTitle')}</h4>
                    <p>{t('dashVoiceDesc')}</p>
                </div>
            </div>
        </div>
    );
}

export default DashboardPage;
