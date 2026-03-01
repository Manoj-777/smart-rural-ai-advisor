// src/contexts/LanguageContext.jsx
// Global language state — persisted to localStorage, accessible everywhere

import { createContext, useContext, useState, useCallback } from 'react';
import translations from '../i18n/translations';
import config from '../config';

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
    const [language, setLanguageState] = useState(() => {
        const stored = localStorage.getItem('app_language');
        return stored && translations[stored] ? stored : config.DEFAULT_LANGUAGE;
    });

    const setLanguage = useCallback((lang) => {
        if (translations[lang]) {
            setLanguageState(lang);
            localStorage.setItem('app_language', lang);

            // Sync language preference to DynamoDB profile (fire-and-forget)
            const farmerId = localStorage.getItem('farmer_id');
            if (farmerId) {
                fetch(`${config.API_URL}/profile/${farmerId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ language: lang })
                }).catch(() => {}); // background sync — don't block UI
            }
        }
    }, []);

    // t('key') returns the localized string, fallback to English
    const t = useCallback((key) => {
        return translations[language]?.[key]
            || translations['en-IN']?.[key]
            || key;
    }, [language]);

    return (
        <LanguageContext.Provider value={{ language, setLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
}

export function useLanguage() {
    const ctx = useContext(LanguageContext);
    if (!ctx) throw new Error('useLanguage must be used within LanguageProvider');
    return ctx;
}
