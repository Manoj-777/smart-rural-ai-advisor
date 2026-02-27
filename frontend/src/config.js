// src/config.js

const config = {
    // API Gateway URL — reads from .env (VITE_API_URL)
    API_URL: import.meta.env.VITE_API_URL || 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod',
    
    // Mock mode — when true, Chat and Crop Doctor use realistic fake responses
    // so the UI works without Bedrock backend. Set VITE_MOCK_AI=true in .env
    MOCK_AI: import.meta.env.VITE_MOCK_AI === 'true',

    // Supported languages
    LANGUAGES: {
        'en-IN': { name: 'English', code: 'en' },
        'hi-IN': { name: 'हिन्दी (Hindi)', code: 'hi' },
        'ta-IN': { name: 'தமிழ் (Tamil)', code: 'ta' },
        'te-IN': { name: 'తెలుగు (Telugu)', code: 'te' },
        'kn-IN': { name: 'ಕನ್ನಡ (Kannada)', code: 'kn' },
        'ml-IN': { name: 'മലയാളം (Malayalam)', code: 'ml' },
        'bn-IN': { name: 'বাংলা (Bengali)', code: 'bn' },
        'mr-IN': { name: 'मराठी (Marathi)', code: 'mr' },
        'gu-IN': { name: 'ગુજરાતી (Gujarati)', code: 'gu' },
        'pa-IN': { name: 'ਪੰਜਾਬੀ (Punjabi)', code: 'pa' },
        'or-IN': { name: 'ଓଡ଼ିଆ (Odia)', code: 'or' },
        'as-IN': { name: 'অসমীয়া (Assamese)', code: 'as' },
        'ur-IN': { name: 'اردو (Urdu)', code: 'ur' }
    },
    
    DEFAULT_LANGUAGE: 'en-IN'
};

export default config;
