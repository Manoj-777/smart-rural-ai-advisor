// src/config.js

const config = {
    // Replace with your API Gateway URL after deploying
    API_URL: import.meta.env.VITE_API_URL || 'https://YOUR_API_GATEWAY_URL/prod',
    
    // Supported languages
    LANGUAGES: {
        'ta-IN': { name: 'தமிழ் (Tamil)', code: 'ta' },
        'en-IN': { name: 'English', code: 'en' },
        'te-IN': { name: 'తెలుగు (Telugu)', code: 'te' },
        'hi-IN': { name: 'हिन्दी (Hindi)', code: 'hi' }
    },
    
    DEFAULT_LANGUAGE: 'ta-IN'
};

export default config;
