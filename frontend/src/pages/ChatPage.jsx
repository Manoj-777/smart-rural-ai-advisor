// src/pages/ChatPage.jsx

import { useState, useRef, useEffect, useCallback } from 'react';
import config from '../config';
import { useLanguage } from '../contexts/LanguageContext';
import VoiceInput from '../components/VoiceInput';
import ChatMessage from '../components/ChatMessage';
import { mockChat } from '../services/mockApi';

const STORAGE_KEY = 'sra_chat_history';
const MAX_STORED = 50;

function ChatPage() {
    const { language, t } = useLanguage();
    const [messages, setMessages] = useState(() => {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            return saved ? JSON.parse(saved) : [];
        } catch { return []; }
    });
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId] = useState(() => {
        const stored = sessionStorage.getItem('sra_session_id');
        if (stored) return stored;
        const id = crypto.randomUUID();
        sessionStorage.setItem('sra_session_id', id);
        return id;
    });
    const chatEndRef = useRef(null);

    // Persist messages to localStorage
    useEffect(() => {
        try {
            const toStore = messages.slice(-MAX_STORED);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
        } catch { /* storage full — ignore */ }
    }, [messages]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const clearHistory = useCallback(() => {
        setMessages([]);
        localStorage.removeItem(STORAGE_KEY);
    }, []);

    const handleVoiceResult = useCallback((text) => {
        if (text?.trim()) setInput(text);
    }, []);

    const sendMessage = useCallback(async (text) => {
        if (!text.trim()) return;
        const userMsg = { role: 'user', content: text, timestamp: Date.now() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            let data;
            if (config.MOCK_AI) {
                data = await mockChat(text, sessionId, language);
            } else {
                const res = await fetch(`${config.API_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text,
                        session_id: sessionId,
                        farmer_id: 'demo_farmer',
                        language: language
                    })
                });
                data = await res.json();
            }

            if (data.status === 'success') {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: data.data.reply,
                    audioUrl: data.data.audio_url,
                    timestamp: Date.now()
                }]);
            } else {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: '❌ ' + (data.message || t('connectionError')),
                    timestamp: Date.now()
                }]);
            }
        } catch {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '❌ ' + t('connectionError'),
                timestamp: Date.now()
            }]);
        } finally {
            setLoading(false);
        }
    }, [sessionId, language, t]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input);
        }
    };

    const langName = config.LANGUAGES[language]?.name || 'English';

    const suggestions = [
        t('chatSuggestion1'),
        t('chatSuggestion2'),
        t('chatSuggestion3'),
        t('chatSuggestion4'),
    ];

    return (
        <div className="chat-page">
            <div className="page-header">
                <div className="page-header-top">
                    <h2>
                        💬 {t('chatTitle')}
                        {config.MOCK_AI && <span className="demo-badge">{t('demoMode')}</span>}
                    </h2>
                    <span className="lang-badge">🌐 {langName}</span>
                </div>
                <p>{t('chatSubtitle')}</p>
                {messages.length > 0 && (
                    <button className="clear-history-btn" onClick={clearHistory} title={t('chatClearHistory') || 'Clear chat'}>
                        🗑️ {t('chatClearHistory') || 'Clear'}
                    </button>
                )}
            </div>

            <div className="chat-container">
                {messages.length === 0 && (
                    <div className="chat-empty">
                        <div className="empty-illustration">
                            <span className="empty-icon">🌾</span>
                            <span className="empty-icon-sub">🤖</span>
                        </div>
                        <h3>{t('chatEmpty')}</h3>
                        <p className="chat-empty-hint">{t('chatSubtitle')}</p>
                        <div className="suggestions">
                            {suggestions.map((s, i) => (
                                <button key={i} className="suggestion-chip" onClick={() => sendMessage(s)}>
                                    {['🌾', '🐛', '📋', '💧'][i]} {s}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
                {messages.map((msg, i) => (
                    <ChatMessage key={i} message={msg} />
                ))}
                {loading && (
                    <div className="message assistant">
                        <div className="message-avatar">🤖</div>
                        <div className="message-body">
                            <span className="thinking">
                                <span className="typing-dots">
                                    <span></span><span></span><span></span>
                                </span>
                                {t('chatThinking')}
                            </span>
                        </div>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            <div className="input-bar">
                <VoiceInput language={language} onTranscript={handleVoiceResult} />
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={t('chatPlaceholder')}
                    disabled={loading}
                />
                <button className="send-btn" onClick={() => sendMessage(input)} disabled={loading || !input.trim()}>
                    <span className="send-icon">➤</span> {t('send')}
                </button>
            </div>
        </div>
    );
}

export default ChatPage;
