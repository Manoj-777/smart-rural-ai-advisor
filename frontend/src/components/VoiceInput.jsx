// src/components/VoiceInput.jsx

import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useLanguage } from '../contexts/LanguageContext';

const LISTENING_TEXT = {
    'en-IN': 'Recording...', 'hi-IN': 'रिकॉर्डिंग...', 'ta-IN': 'பதிவு செய்கிறது...',
    'te-IN': 'రికార్డింగ్...', 'kn-IN': 'ರೆಕಾರ್ಡಿಂಗ್...', 'ml-IN': 'റെക്കോർഡ് ചെയ്യുന്നു...',
    'bn-IN': 'রেকর্ডিং...', 'mr-IN': 'रेकॉर्डिंग...', 'gu-IN': 'રેકોર્ડિંગ...',
    'pa-IN': 'ਰਿਕਾਰਡਿੰਗ...', 'or-IN': 'ରେକର୍ଡିଂ...', 'as-IN': 'ৰেকৰ্ডিং...',
    'ur-IN': 'ریکارڈنگ...',
};

const PROCESSING_TEXT = {
    'en-IN': 'Processing...', 'hi-IN': 'प्रोसेसिंग...', 'ta-IN': 'செயலாக்குகிறது...',
    'te-IN': 'ప్రాసెస్ చేస్తోంది...', 'kn-IN': 'ಪ್ರಕ್ರಿಯೆ...', 'ml-IN': 'പ്രോസസ്സ് ചെയ്യുന്നു...',
    'bn-IN': 'প্রসেসিং...', 'mr-IN': 'प्रक्रिया...', 'gu-IN': 'પ્રોસેસિંગ...',
    'pa-IN': 'ਪ੍ਰੋਸੈਸਿੰਗ...', 'or-IN': 'ପ୍ରକ୍ରିୟାକରଣ...', 'as-IN': 'প্ৰচেছিং...',
    'ur-IN': 'پروسیسنگ...',
};

function VoiceInput({ language, onTranscript }) {
    const { t } = useLanguage();
    const { isListening, isProcessing, error, startListening, stopListening } = 
        useSpeechRecognition(language, onTranscript);

    const listeningLabel = LISTENING_TEXT[language] || 'Recording...';
    const processingLabel = PROCESSING_TEXT[language] || 'Processing...';

    const isActive = isListening || isProcessing;

    return (
        <div className="voice-input-group">
            <button 
                className={`mic-btn ${isListening ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
                onClick={isListening ? stopListening : startListening}
                disabled={isProcessing}
                title={isListening ? (t('voiceStopListening') || 'Stop recording') : (t('voiceClickToSpeak') || 'Click to speak')}
            >
                {isListening ? '🔴' : isProcessing ? '⏳' : '🎤'}
            </button>
            {isListening && <span className="voice-status listening">{listeningLabel}</span>}
            {isProcessing && <span className="voice-status processing">{processingLabel}</span>}
            {error && !isActive && <span className="voice-status error">{error}</span>}
        </div>
    );
}

export default VoiceInput;
