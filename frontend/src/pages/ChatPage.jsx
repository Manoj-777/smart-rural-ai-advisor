// src/pages/ChatPage.jsx

import { useState, useRef, useEffect, useCallback } from 'react';
import config from '../config';
import { useLanguage } from '../contexts/LanguageContext';
import { useFarmer } from '../contexts/FarmerContext';
import VoiceInput from '../components/VoiceInput';
import ChatMessage from '../components/ChatMessage';
import { mockChat } from '../services/mockApi';
import { apiFetch } from '../utils/apiFetch';

const STORAGE_KEY = 'sra_chat_history';
const SESSIONS_KEY = 'sra_chat_sessions';
const ACTIVE_SESSION_KEY = 'sra_active_session';
const MAX_STORED = 50;

/* -- helpers -- */
function generateId() {
    if (typeof window !== 'undefined' && window.crypto?.randomUUID) {
        return window.crypto.randomUUID();
    }
    return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
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

/* ── Local cache (fast reads, same-browser fallback) ──────── */
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

/* ── DynamoDB sync (cross-device, per-farmer) ──────────────── */
async function dbListSessions(farmerId) {
    try {
        const res = await apiFetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'list_sessions', farmer_id: farmerId }),
        });
        const data = await res.json();
        return data?.data?.sessions || [];
    } catch { return []; }
}

async function dbGetSessionMessages(farmerId, sessionId) {
    try {
        const res = await apiFetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'get_session', farmer_id: farmerId, session_id: sessionId }),
        });
        const data = await res.json();
        return data?.data?.messages || [];
    } catch { return []; }
}

async function dbSaveSession(farmerId, sessionId, messages, preview) {
    try {
        await apiFetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'save_session', farmer_id: farmerId, session_id: sessionId, messages, preview }),
        });
    } catch { /* fire-and-forget */ }
}

async function dbDeleteSession(farmerId, sessionId) {
    try {
        await apiFetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'delete_session', farmer_id: farmerId, session_id: sessionId }),
        });
    } catch { /* fire-and-forget */ }
}

async function dbRenameSession(farmerId, sessionId, title) {
    try {
        await apiFetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'rename_session', farmer_id: farmerId, session_id: sessionId, title }),
        });
    } catch { /* fire-and-forget */ }
}

function ChatPage() {
    const { language, t } = useLanguage();
    const { farmerId, resolvedLocation, resolvedCoords } = useFarmer();
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
    const [liveTranscript, setLiveTranscript] = useState('');  // streaming partial text
    const [loading, setLoading] = useState(false);
    const [sessionFull, setSessionFull] = useState(false);  // true when session hits message limit
    const [renamingSessionId, setRenamingSessionId] = useState(null);  // session being renamed
    const [renameValue, setRenameValue] = useState('');  // current rename input value
    const chatEndRef = useRef(null);

    // Track whether we're in the middle of a session switch to avoid cross-saving
    const switchingRef = useRef(false);
    const activeIdRef = useRef(activeSessionId);
    const dbSyncedRef = useRef(false);  // has DB fetch happened this mount?

    // Keep ref in sync
    useEffect(() => {
        activeIdRef.current = activeSessionId;
    }, [activeSessionId]);

    // ── On mount: fetch sessions from DB and merge with local cache ──
    useEffect(() => {
        if (!farmerId || farmerId === 'anonymous' || dbSyncedRef.current) return;
        dbSyncedRef.current = true;

        (async () => {
            const dbSessions = await dbListSessions(farmerId);
            if (dbSessions.length > 0) {
                setSessions(prev => {
                    // Merge: DB sessions win, local-only sessions kept
                    const dbIds = new Set(dbSessions.map(s => s.id));
                    const localOnly = prev.filter(s => !dbIds.has(s.id));
                    const merged = [...dbSessions, ...localOnly];
                    saveSessions(merged);
                    return merged;
                });

                // If current session has messages in DB but not locally, load them
                const sid = activeIdRef.current;
                const localMsgs = loadSessionMessages(sid);
                if (localMsgs.length === 0) {
                    const dbMsgs = await dbGetSessionMessages(farmerId, sid);
                    if (dbMsgs.length > 0) {
                        saveSessionMessages(sid, dbMsgs);
                        setMessages(dbMsgs);
                    }
                }
            }
        })();
    }, [farmerId]);

    // Persist messages locally + sync to DB -- only when NOT switching sessions
    useEffect(() => {
        if (switchingRef.current) return;
        const sid = activeIdRef.current;
        saveSessionMessages(sid, messages);
        // Update session metadata
        if (messages.length > 0) {
            const firstUserMsg = messages.find(m => m.role === 'user');
            const preview = firstUserMsg?.content?.slice(0, 60) || t('newChatPreview') || 'New chat';
            const lastTs = messages[messages.length - 1].timestamp;

            setSessions(prev => {
                const existing = prev.find(s => s.id === sid);
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

            // Async DB save (fire-and-forget, won't block UI)
            if (farmerId && farmerId !== 'anonymous') {
                dbSaveSession(farmerId, sid, messages, preview);
            }
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
        setSessionFull(false);  // Reset session-full state for new chat
        // Allow persist again on next tick
        setTimeout(() => { switchingRef.current = false; }, 0);
    }, []);

    const switchToSession = useCallback((sid) => {
        if (sid === activeIdRef.current) return;
        switchingRef.current = true;
        activeIdRef.current = sid;
        setActiveSessionId(sid);
        localStorage.setItem(ACTIVE_SESSION_KEY, sid);
        // Load from local first, then try DB if empty
        const localMsgs = loadSessionMessages(sid);
        setMessages(localMsgs);
        setInput('');
        setSessionFull(false);  // Will be re-detected on next send if still full
        setTimeout(() => { switchingRef.current = false; }, 0);
        // If local is empty, try DB
        if (localMsgs.length === 0 && farmerId && farmerId !== 'anonymous') {
            dbGetSessionMessages(farmerId, sid).then(dbMsgs => {
                if (dbMsgs.length > 0) {
                    saveSessionMessages(sid, dbMsgs);
                    if (activeIdRef.current === sid) setMessages(dbMsgs);
                }
            });
        }
    }, [farmerId]);

    const deleteSession = useCallback((sid, e) => {
        e.stopPropagation();
        setSessions(prev => {
            const updated = prev.filter(s => s.id !== sid);
            saveSessions(updated);
            return updated;
        });
        localStorage.removeItem(STORAGE_KEY + '_' + sid);
        // Also delete from DB
        if (farmerId && farmerId !== 'anonymous') {
            dbDeleteSession(farmerId, sid);
        }
        if (sid === activeSessionId) startNewChat();
    }, [activeSessionId, startNewChat, farmerId]);

    const startRenaming = useCallback((sid, currentPreview, e) => {
        e.stopPropagation();
        setRenamingSessionId(sid);
        setRenameValue(currentPreview || '');
    }, []);

    const confirmRename = useCallback((sid) => {
        const trimmed = renameValue.trim().slice(0, 80);
        if (!trimmed) {
            setRenamingSessionId(null);
            return;
        }
        setSessions(prev => {
            const updated = prev.map(s => s.id === sid ? { ...s, preview: trimmed } : s);
            saveSessions(updated);
            return updated;
        });
        setRenamingSessionId(null);
        // Sync to DB
        if (farmerId && farmerId !== 'anonymous') {
            dbRenameSession(farmerId, sid, trimmed);
        }
    }, [renameValue, farmerId]);

    const cancelRename = useCallback(() => {
        setRenamingSessionId(null);
        setRenameValue('');
    }, []);

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
        setLiveTranscript('');  // clear partial on final delivery
    }, []);

    // ChatGPT-style: show partial speech text live in the input field
    const handlePartialTranscript = useCallback((text) => {
        setLiveTranscript(text || '');
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

        const MAX_RETRIES = 1; // 1 original + 1 retry
        const FETCH_TIMEOUT_MS = 35000; // 35s (API GW is 29s + margin)

        try {
            let data;
            if (config.MOCK_AI) {
                data = await mockChat(text, targetSessionId, language);
            } else {
                let lastError;
                for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
                    const controller = new AbortController();
                    const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
                    try {
                        const res = await apiFetch(`/chat`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                message: text,
                                session_id: targetSessionId,
                                farmer_id: farmerId || 'anonymous',
                                language: language,
                                ...(resolvedLocation && { gps_location: resolvedLocation }),
                                ...(resolvedCoords && { gps_coords: resolvedCoords }),
                            }),
                            signal: controller.signal
                        });
                        clearTimeout(timeout);
                        if (res.status >= 500 && attempt < MAX_RETRIES) {
                            lastError = new Error(`Server error ${res.status}`);
                            await new Promise(r => setTimeout(r, 1500)); // wait before retry
                            continue;
                        }
                        data = await res.json();
                        break;
                    } catch (fetchErr) {
                        clearTimeout(timeout);
                        lastError = fetchErr;
                        if (fetchErr.name === 'AbortError') {
                            lastError = new Error('Request timed out. Please try again.');
                        }
                        if (attempt < MAX_RETRIES) {
                            await new Promise(r => setTimeout(r, 1500));
                            continue;
                        }
                        throw lastError;
                    }
                }
                if (!data) throw lastError || new Error('No response');
            }

            let assistantMsg;
            if (data.status === 'success') {
                // Check if session has hit its message limit
                if (data.data?.session_full) {
                    setSessionFull(true);
                }

                // Strip any leftover "Sources: ..." from AI reply
                let reply = (data.data.reply || '').replace(/\n\s*Sources:\s*.+$/m, '').trim();
                assistantMsg = {
                    role: 'assistant',
                    content: reply,
                    audioUrl: data.data.audio_url,
                    audioKey: data.data.audio_key,
                    audioPending: data.data.audio_pending || false,
                    detected_language: data.data.detected_language,
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

    // Persist refreshed audio URL for a message (when expired URL is re-signed or async TTS completes)
    const handleUpdateAudioUrl = useCallback((timestamp, newUrl, newKey) => {
        setMessages(prev => {
            const updated = prev.map(m =>
                m.timestamp === timestamp
                    ? { ...m, audioUrl: newUrl, ...(newKey ? { audioKey: newKey, audioPending: false } : {}) }
                    : m
            );
            saveSessionMessages(activeIdRef.current, updated);
            return updated;
        });
    }, []);

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
                                {renamingSessionId === session.id ? (
                                    <input
                                        className="chat-history-rename-input"
                                        value={renameValue}
                                        onChange={(e) => setRenameValue(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') { e.preventDefault(); confirmRename(session.id); }
                                            if (e.key === 'Escape') cancelRename();
                                        }}
                                        onBlur={() => confirmRename(session.id)}
                                        onClick={(e) => e.stopPropagation()}
                                        autoFocus
                                        maxLength={80}
                                        placeholder={t('chatRenameChat') || 'Rename chat'}
                                    />
                                ) : (
                                    <span className="chat-history-preview">{session.preview}</span>
                                )}
                                <span className="chat-history-meta">
                                    {formatSessionDate(session.lastTimestamp, t)} · {session.messageCount} {t('chatMsgs')}
                                </span>
                            </div>
                            <div className="chat-history-actions">
                                <button
                                    className="chat-history-rename"
                                    onClick={(e) => startRenaming(session.id, session.preview, e)}
                                    title={t('chatRenameChat') || 'Rename chat'}
                                >
                                    ✏️
                                </button>
                                <button
                                    className="chat-history-delete"
                                    onClick={(e) => deleteSession(session.id, e)}
                                    title={t('chatDeleteChat')}
                                >
                                    🗑️
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main chat area */}
            <div className="chat-main">
                <div className="page-header" style={{ paddingLeft: '24px', marginBottom: '8px' }}>
                    <div className="page-header-top">
                        <h2>
                            💬 {t('chatTitle')}
                        </h2>
                    </div>
                    <p>{t('chatSubtitle')}</p>
                </div>

            <div className="chat-container">
                {messages.length === 0 && (
                    <div className="chat-welcome">
                        <div style={{ textAlign: 'center', color: 'var(--text-light)', padding: '20px 40px 10px' }}>
                            🌾 {t('chatWelcomeHint')}
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
                    <ChatMessage key={i} message={msg} onUpdateAudioUrl={handleUpdateAudioUrl} />
                ))}
                {loading && (
                    <div className="message assistant">
                        <span className="typing-dots">🤖 {t('chatThinking')}</span>
                    </div>
                )}
                {sessionFull && (
                    <div className="session-full-banner">
                        <div className="session-full-icon">💬</div>
                        <p className="session-full-text">
                            {t('sessionFullMessage') || 'This chat has reached its message limit. Start a new chat to continue your conversation.'}
                        </p>
                        <button className="session-full-btn" onClick={startNewChat}>
                            ➕ {t('startNewChat') || 'Start New Chat'}
                        </button>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            {/* Input bar with voice */}
            <div className={`input-bar ${sessionFull ? 'input-bar-disabled' : ''}`}>
                <VoiceInput 
                    language={language} 
                    onTranscript={handleVoiceResult}
                    onPartialTranscript={handlePartialTranscript}
                />
                <input
                    type="text"
                    className={liveTranscript ? 'live-transcript' : ''}
                    value={liveTranscript || input}
                    onChange={(e) => { if (!liveTranscript) setInput(e.target.value); }}
                    onKeyDown={handleKeyDown}
                    placeholder={sessionFull ? (t('sessionFullPlaceholder') || 'Chat limit reached — start a new chat ↑') : (liveTranscript ? '' : t('chatPlaceholder'))}
                    disabled={loading || sessionFull}
                    readOnly={!!liveTranscript}
                />
                <button 
                    className="send-btn" 
                    onClick={() => sendMessage(input)}
                    disabled={loading || !input.trim() || sessionFull}
                >
                    {t('send')}
                </button>
            </div>
            </div>{/* end chat-main */}
        </div>
    );
}

export default ChatPage;
