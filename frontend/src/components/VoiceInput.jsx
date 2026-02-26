// src/components/VoiceInput.jsx

import { useEffect } from 'react';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';

function VoiceInput({ language, onTranscript }) {
    const { isListening, transcript, error, startListening, stopListening } = 
        useSpeechRecognition(language);

    // When transcript changes, send it up to parent
    useEffect(() => {
        if (transcript) {
            onTranscript(transcript);
        }
    }, [transcript, onTranscript]);

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button 
                className={`mic-btn ${isListening ? 'recording' : ''}`}
                onClick={isListening ? stopListening : startListening}
                title={isListening ? 'Stop listening' : 'Click to speak'}
            >
                {isListening ? '🔴' : '🎤'}
            </button>
            {isListening && <span style={{color: '#e53e3e', fontSize: '14px'}}>Listening...</span>}
            {error && <span style={{color: '#e53e3e', fontSize: '13px'}}>{error}</span>}
        </div>
    );
}

export default VoiceInput;
