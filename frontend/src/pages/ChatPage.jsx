// src/pages/ChatPage.jsx

import { useState, useRef, useEffect } from 'react';
import config from '../config';
import VoiceInput from '../components/VoiceInput';
import ChatMessage from '../components/ChatMessage';

function generateSessionId() {
    if (typeof window !== 'undefined' && window.crypto?.randomUUID) {
        return window.crypto.randomUUID();
    }
    return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function ChatPage() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [language, setLanguage] = useState(config.DEFAULT_LANGUAGE);
    const [sessionId] = useState(() => generateSessionId());
    const chatEndRef = useRef(null);

    // Auto-scroll to bottom when new message arrives
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMessage = async (text) => {
        if (!text.trim()) return;

        // Add user message
        const userMsg = { role: 'user', content: text };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await fetch(`${config.API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId,
                    farmer_id: 'demo_farmer'
                })
            });
            const data = await res.json();

            if (data.status === 'success') {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: data.data.reply,
                    audioUrl: data.data.audio_url
                }]);
            } else {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: '❌ ' + (data.message || 'Something went wrong.')
                }]);
            }
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '❌ Connection error. Please try again.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input);
        }
    };

    return (
        <div>
            <h2 style={{ marginBottom: '8px' }}>💬 Farm Advisor Chat</h2>
            <p style={{ color: 'var(--text-light)', marginBottom: '16px' }}>
                Ask anything about farming — in Tamil, English, Telugu, or Hindi
            </p>

            {/* Language selector */}
            <select 
                value={language} 
                onChange={(e) => setLanguage(e.target.value)}
                style={{ marginBottom: '16px', padding: '8px', borderRadius: '8px' }}
            >
                {Object.entries(config.LANGUAGES).map(([code, lang]) => (
                    <option key={code} value={code}>{lang.name}</option>
                ))}
            </select>

            {/* Chat messages */}
            <div className="chat-container">
                {messages.length === 0 && (
                    <div style={{ textAlign: 'center', color: 'var(--text-light)', padding: '40px' }}>
                        🌾 Ask me about crops, weather, pests, or government schemes!
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
                    onTranscript={(text) => sendMessage(text)} 
                />
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="உங்கள் கேள்வியை தட்டச்சு செய்யவும் / Type here..."
                    disabled={loading}
                />
                <button 
                    className="send-btn" 
                    onClick={() => sendMessage(input)}
                    disabled={loading || !input.trim()}
                >
                    Send
                </button>
            </div>
        </div>
    );
}

export default ChatPage;
