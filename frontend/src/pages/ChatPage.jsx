// src/pages/ChatPage.jsx

import { useState, useRef, useEffect, useCallback } from 'react';
import config from '../config';
import { useLanguage } from '../contexts/LanguageContext';
import VoiceInput from '../components/VoiceInput';
import ChatMessage from '../components/ChatMessage';
import { mockChat } from '../services/mockApi';

const STORAGE_KEY = 'sra_chat_history';
const SESSIONS_KEY = 'sra_chat_sessions';
const ACTIVE_SESSION_KEY = 'sra_active_session';
const MAX_STORED = 50;

/* -- helpers -- */
function generateId() {
    if (typeof window !== 'undefined' && window.crypto?.randomUUID) {
        return window.crypto.randomUUID();
    }
    return session-+Date.now()+-+Math.random().toString(36).slice(2, 10);
}

function formatSessionDate(ts, t) {
    const d = new Date(ts);
    const now = new Date();
    const diff = now - d;
    const oneDay = 86400000;
    const todayLabel = (t && t('chatToday')) || 'Today';
    const yesterdayLabel = (t && t('chatYesterday')) || 'Yesterday';

    if (diff < oneDay && d.getDate() === now.getDate()) {
        return todayLabel + ', ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    if (diff < 2 * oneDay && d.getDate() === now.getDate() - 1) {
        return yesterdayLabel + ', ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' })
        + ', ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function loadSessions() {
    try { return JSON.parse(localStorage.getItem(SESSIONS_KEY)) || []; } catch { return []; }
}
function saveSessions(sessions) {
    try { localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions)); } catch { /* */ }
}
function loadSessionMessages(sessionId) {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY + '_' + sessionId)) || []; } catch { return []; }
}
function saveSessionMessages(sessionId, messages) {
    try { localStorage.setItem(STORAGE_KEY + '_' + sessionId, JSON.stringify(messages.slice(-MAX_STORED))); } catch { /* */ }
}

function ChatPage() {
    const { language, t } = useLanguage();
    const [sessions, setSessions] = useState(loadSessions);

    // Active session
    const [activeSessionId, setActiveSessionId] = useState(() => {
        const stored = localStorage.getItem(ACTIVE_SESSION_KEY);
        if (stored) return stored;
        const id = generateId();
        localStorage.setItem(ACTIVE_SESSION_KEY, id);
        return id;
    });

    const [messages, setMessages] = useState(() => loadSessionMessages(activeSessionId));
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const chatEndRef = useRef(null);

    // Track whether we're in the middle of a session switch to avoid cross-saving
    const switchingRef = useRef(false);
    const activeIdRef = useRef(activeSessionId);

    // Keep ref in sync
    useEffect(() => {
        activeIdRef.current = activeSessionId;
    }, [activeSessionId]);

    // Persist messages -- only when NOT switching sessions
    useEffect(() => {
        if (switchingRef.current) return;
        const sid = activeIdRef.current;
        saveSessionMessages(sid, messages);
        // Update session metadata
        if (messages.length > 0) {
            setSessions(prev => {
                const existing = prev.find(s => s.id === sid);
                const firstUserMsg = messages.find(m => m.role === 'user');
                const preview = firstUserMsg?.content?.slice(0, 60) || t('newChatPreview') || 'New chat';
                const lastTs = messages[messages.length - 1].timestamp;
                if (existing) {
                    const updated = prev.map(s => s.id === sid
                        ? { ...s, preview, lastTimestamp: lastTs, messageCount: messages.length }
                        : s);
                    saveSessions(updated);
                    return updated;
                } else {
                    const newSessions = [{ id: sid, preview, createdAt: messages[0].timestamp, lastTimestamp: lastTs, messageCount: messages.length }, ...prev];
                    saveSessions(newSessions);
                    return newSessions;
                }
            });
        }
    }, [messages]);

    // Auto-scroll to bottom when new message arrives
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const startNewChat = useCallback(() => {
        switchingRef.current = true;
        const id = generateId();
        activeIdRef.current = id;
        setActiveSessionId(id);
        localStorage.setItem(ACTIVE_SESSION_KEY, id);
        setMessages([]);
        setInput('');
        // Allow persist again on next tick
        setTimeout(() => { switchingRef.current = false; }, 0);
    }, []);

    const switchToSession = useCallback((sid) => {
        if (sid === activeIdRef.current) return;
        switchingRef.current = true;
        activeIdRef.current = sid;
        setActiveSessionId(sid);
        localStorage.setItem(ACTIVE_SESSION_KEY, sid);
        setMessages(loadSessionMessages(sid));
        setInput('');
        // Allow persist again on next tick
        setTimeout(() => { switchingRef.current = false; }, 0);
    }, []);

    const deleteSession = useCallback((sid, e) => {
        e.stopPropagation();
        setSessions(prev => {
            const updated = prev.filter(s => s.id !== sid);
            saveSessions(updated);
            return updated;
        });
        localStorage.removeItem(STORAGE_KEY + '_' + sid);
        if (sid === activeSessionId) startNewChat();
    }, [activeSessionId, startNewChat]);

    const clearHistory = useCallback(() => {
        setMessages([]);
        saveSessionMessages(activeSessionId, []);
        setSessions(prev => {
            const updated = prev.filter(s => s.id !== activeSessionId);
            saveSessions(updated);
            return updated;
        });
    }, [activeSessionId]);

    const handleVoiceResult = useCallback((text) => {
        if (text?.trim()) setInput(text);
    }, []);

    const sendMessage = useCallback(async (text) => {
        if (!text.trim()) return;
        const userMsg = { role: 'user', content: text, timestamp: Date.now() };
        // Capture which session this message belongs to
        const targetSessionId = activeIdRef.current;

        setMessages(prev => [...prev, userMsg]);
        // Immediately persist the user message to the correct session
        const currentMsgs = loadSessionMessages(targetSessionId);
        currentMsgs.push(userMsg);
        saveSessionMessages(targetSessionId, currentMsgs);
        setInput('');
        setLoading(true);

        try {
            let data;
            if (config.MOCK_AI) {
                data = await mockChat(text, targetSessionId, language);
            } else {
                const res = await fetch(`${config.API_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text,
                        session_id: targetSessionId,
                        farmer_id: 'demo_farmer',
                        language: language
                    })
                });
                data = await res.json();
            }

            let assistantMsg;
            if (data.status === 'success') {
                assistantMsg = {
                    role: 'assistant',
                    content: data.data.reply,
                    audioUrl: data.data.audio_url,
                    timestamp: Date.now()
                };
            } else {
                assistantMsg = {
                    role: 'assistant',
                    content: '❌ ' + (data.message || t('connectionError')),
                    timestamp: Date.now()
                };
            }

            // If user is still on the same session, update state normally
            if (activeIdRef.current === targetSessionId) {
                setMessages(prev => [...prev, assistantMsg]);
            } else {
                // User switched away -- save directly to the original session's storage
                const storedMsgs = loadSessionMessages(targetSessionId);
                storedMsgs.push(assistantMsg);
                saveSessionMessages(targetSessionId, storedMsgs);
                // Update session metadata
                setSessions(prev => {
                    const firstUser = storedMsgs.find(m => m.role === 'user');
                    const preview = firstUser?.content?.slice(0, 60) || t('newChatPreview') || 'New chat';
                    const updated = prev.map(s => s.id === targetSessionId
                        ? { ...s, preview, lastTimestamp: assistantMsg.timestamp, messageCount: storedMsgs.length }
                        : s);
                    saveSessions(updated);
                    return updated;
                });
            }
        } catch {
            const errorMsg = {
                role: 'assistant',
                content: '❌ ' + t('connectionError'),
                timestamp: Date.now()
            };
            if (activeIdRef.current === targetSessionId) {
                setMessages(prev => [...prev, errorMsg]);
            } else {
                const storedMsgs = loadSessionMessages(targetSessionId);
                storedMsgs.push(errorMsg);
                saveSessionMessages(targetSessionId, storedMsgs);
            }
        } finally {
            setLoading(false);
        }
    }, [activeSessionId, language, t]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input);
        }
    };

    const suggestions = [
        t('chatSuggestion1'),
        t('chatSuggestion2'),
        t('chatSuggestion3'),
        t('chatSuggestion4'),
    ];

    return (
        <div className="chat-page">
            {/* History Side Panel */}
            <div className="chat-history-panel">
                <div className="chat-history-header">
                    <h3>💬 {t('yourChats') || 'Your Chats'}</h3>
                </div>
                <button className="chat-history-new" onClick={startNewChat}>
                    ＋ {t('newChat') || 'New Chat'}
                </button>
                <div className="chat-history-list">
                    {sessions.length === 0 && (
                        <p className="chat-history-empty">{t('noPreviousChats') || 'No previous chats'}</p>
                    )}
                    {sessions
                        .sort((a, b) => b.lastTimestamp - a.lastTimestamp)
                        .map(session => (
                        <div
                            key={session.id}
                            className={`chat-history-item ${session.id === activeSessionId ? 'active' : ''}`}
                            onClick={() => switchToSession(session.id)}
                        >
                            <div className="chat-history-item-content">
                                <span className="chat-history-preview">{session.preview}</span>
                                <span className="chat-history-meta">
                                    {formatSessionDate(session.lastTimestamp, t)} · {session.messageCount} {t('chatMsgs')}
                                </span>
                            </div>
                            <button
                                className="chat-history-delete"
                                onClick={(e) => deleteSession(session.id, e)}
                                title={t('chatDeleteChat')}
                            >
                                🗑️
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main chat area */}
            <div className="chat-main">
                <div className="page-header">
                    <div className="page-header-top">
                        <h2>
                            💬 {t('chatTitle')}
                        </h2>
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
                    <div className="chat-welcome">
                        <div style={{ textAlign: 'center', color: 'var(--text-light)', padding: '20px 40px 10px' }}>
                            🌾 Ask me about crops, weather, pests, or government schemes!
                        </div>
                        <div className="suggestions">
                            {suggestions.map((s, i) => (
                                <button
                                    key={i}
                                    className="suggestion-chip"
                                    onClick={() => sendMessage(s)}
                                >
                                    {s}
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
                        <span className="typing-dots">🌾 Thinking...</span>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            {/* Input bar with voice */}
            <div className="input-bar">
                <VoiceInput 
                    language={language} 
                    onTranscript={handleVoiceResult} 
                />
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={t('chatPlaceholder')}
                    disabled={loading}
                />
                <button 
                    className="send-btn" 
                    onClick={() => sendMessage(input)}
                    disabled={loading || !input.trim()}
                >
                    {t('send')}
                </button>
            </div>
            </div>{/* end chat-main */}
        </div>
    );
}

export default ChatPage;
