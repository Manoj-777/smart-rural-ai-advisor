// src/config.js

import LANGUAGES from './languages';

const config = {
    // API Gateway URL
    API_URL: import.meta.env.VITE_API_URL || 'https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod',
    
    // Mock mode
    MOCK_AI: import.meta.env.VITE_MOCK_AI === 'true',

    // Cognito User Pool
    COGNITO_USER_POOL_ID: import.meta.env.VITE_COGNITO_USER_POOL_ID || 'ap-south-1_X58lNMEcn',
    COGNITO_CLIENT_ID: import.meta.env.VITE_COGNITO_CLIENT_ID || '4c3c6he88im15hmv5rdkv3m6h0',

    // Reference the standalone LANGUAGES export
    LANGUAGES,
    
    DEFAULT_LANGUAGE: 'en-IN',

    // Nominatim geocoding service base URL (no trailing slash)
    NOMINATIM_BASE_URL: 'https://nominatim.openstreetmap.org',

    // Country code prefix for phone numbers
    COUNTRY_CODE: '+91',
};

export default config;
