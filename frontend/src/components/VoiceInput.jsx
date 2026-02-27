// src/components/VoiceInput.jsx

import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useLanguage } from '../contexts/LanguageContext';

const LISTENING_TEXT = {
    'en-IN': 'Listening...', 'hi-IN': 'सुन रहा हूं...', 'ta-IN': 'கேட்கிறது...',
    'te-IN': 'వింటుంది...', 'kn-IN': 'ಆಲಿಸುತ್ತಿದೆ...', 'ml-IN': 'കേൾക്കുന്നു...',
    'bn-IN': 'শুনছি...', 'mr-IN': 'ऐकत आहे...', 'gu-IN': 'સાંભળી રહ્યું છે...',
    'pa-IN': 'ਸੁਣ ਰਿਹਾ ਹਾਂ...', 'or-IN': 'ଶୁଣୁଛି...', 'as-IN': 'শুনি আছে...',
    'ur-IN': 'سن رہا ہوں...',
};

function VoiceInput({ language, onTranscript }) {
    const { t } = useLanguage();
    const { isListening, error, startListening, stopListening } = 
        useSpeechRecognition(language, onTranscript);

    const listeningLabel = LISTENING_TEXT[language] || 'Listening...';

    return (
        <div className="voice-input-group">
            <button 
                className={`mic-btn ${isListening ? 'recording' : ''}`}
                onClick={isListening ? stopListening : startListening}
                title={isListening ? (t('voiceStopListening') || 'Stop listening') : (t('voiceClickToSpeak') || 'Click to speak')}
            >
                {isListening ? '🔴' : '🎤'}
            </button>
            {isListening && <span className="voice-status listening">{listeningLabel}</span>}
            {error && <span className="voice-status error">{error}</span>}
        </div>
    );
}

export default VoiceInput;
