// src/components/ChatMessage.jsx

import { useState, useCallback } from 'react';

function formatMessage(text) {
    if (!text) return '';
    return text
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Numbered list items
        .replace(/^(\d+)\.\s/gm, '<span class="list-num">$1.</span> ')
        // Bullet list items with dash
        .replace(/^-\s(.+)/gm, '<span class="list-bullet">•</span> $1')
        // Line breaks
        .replace(/\n/g, '<br/>');
}

function formatTimestamp(ts) {
    if (!ts) return '';
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Strip markdown/HTML for speech
function stripForSpeech(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/\|[^\n]+\|/g, '') // remove table rows
        .replace(/[-]+\|/g, '')     // remove table separators
        .replace(/#{1,6}\s/g, '')   // remove markdown headings
        .replace(/[🌾🌡️💧💨🌧️📅🌽🫘🌿💡📞📱📈🐛✅🧪⚠️💰👤📝🔍🩺💊🌱☁️📍📊🌊🏞️🌻]/g, '') // remove emojis
        .replace(/\n{2,}/g, '. ')
        .replace(/\n/g, '. ')
        .replace(/\s{2,}/g, ' ')
        .trim();
}

// Map our language codes to BCP-47 for speechSynthesis
const SPEECH_LANG_MAP = {
    'en-IN': 'en-IN',
    'hi-IN': 'hi-IN',
    'ta-IN': 'ta-IN',
    'te-IN': 'te-IN',
    'kn-IN': 'kn-IN',
    'ml-IN': 'ml-IN',
    'bn-IN': 'bn-IN',
    'mr-IN': 'mr-IN',
    'gu-IN': 'gu-IN',
    'pa-IN': 'pa-IN',
};

function ChatMessage({ message }) {
    const isUser = message.role === 'user';
    const [speaking, setSpeaking] = useState(false);

    const handleSpeak = useCallback(() => {
        if (!window.speechSynthesis) return;

        // If already speaking, stop
        if (speaking) {
            window.speechSynthesis.cancel();
            setSpeaking(false);
            return;
        }

        const plainText = stripForSpeech(message.content);
        if (!plainText) return;

        // Chunk long text (speechSynthesis has a ~200-300 char limit in some browsers)
        const MAX_CHUNK = 250;
        const sentences = plainText.match(/[^.!?]+[.!?]*/g) || [plainText];
        const chunks = [];
        let current = '';
        for (const sent of sentences) {
            if ((current + sent).length > MAX_CHUNK && current) {
                chunks.push(current.trim());
                current = sent;
            } else {
                current += sent;
            }
        }
        if (current.trim()) chunks.push(current.trim());

        // Detect language from detected_language or content script
        const lang = message.detected_language || detectSpeechLang(message.content);
        const speechLang = SPEECH_LANG_MAP[lang] || 'en-IN';

        setSpeaking(true);

        // Speak chunks sequentially
        let idx = 0;
        function speakNext() {
            if (idx >= chunks.length) {
                setSpeaking(false);
                return;
            }
            const utter = new SpeechSynthesisUtterance(chunks[idx]);
            utter.lang = speechLang;
            utter.rate = 0.9;
            utter.pitch = 1;
            utter.onend = () => { idx++; speakNext(); };
            utter.onerror = () => { setSpeaking(false); };
            window.speechSynthesis.speak(utter);
        }
        speakNext();
    }, [message, speaking]);

    // Simple script detection for speech lang
    function detectSpeechLang(text) {
        if (!text) return 'en-IN';
        if (/[\u0B80-\u0BFF]/.test(text)) return 'ta-IN';
        if (/[\u0C80-\u0CFF]/.test(text)) return 'kn-IN';
        if (/[\u0C00-\u0C7F]/.test(text)) return 'te-IN';
        if (/[\u0D00-\u0D7F]/.test(text)) return 'ml-IN';
        if (/[\u0900-\u097F]/.test(text)) return 'hi-IN';
        if (/[\u0980-\u09FF]/.test(text)) return 'bn-IN';
        if (/[\u0A80-\u0AFF]/.test(text)) return 'gu-IN';
        if (/[\u0A00-\u0A7F]/.test(text)) return 'pa-IN';
        return 'en-IN';
    }

    return (
        <div className={`message ${message.role}`}>
            <div className="message-avatar">
                {isUser ? '👨‍🌾' : '🤖'}
            </div>
            <div className="message-body">
                <div 
                    className="message-text"
                    dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }} 
                />
                {/* Audio player if API returned audio URL */}
                {message.audioUrl && (
                    <audio controls src={message.audioUrl} className="message-audio" />
                )}
                {message.timestamp && (
                    <span className="message-time">{formatTimestamp(message.timestamp)}</span>
                )}
            </div>
        </div>
    );
}

export default ChatMessage;
