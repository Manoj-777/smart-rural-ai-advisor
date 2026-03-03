// src/hooks/useStreamingSpeech.js
// ChatGPT-style live speech-to-text using browser native SpeechRecognition
// with continuous mode and interim results for real-time partial transcripts.
// Completely separate from useSpeechRecognition (AWS Transcribe path).
// Returns supported=false on Edge or unsupported browsers so VoiceInput
// can seamlessly fall back to the AWS recorder hook.

import { useState, useRef, useCallback, useEffect } from 'react';
import config from '../config';

// Detect once at module level — never changes at runtime
const _hasSpeechRecognition =
    typeof window !== 'undefined' &&
    !!(window.SpeechRecognition || window.webkitSpeechRecognition);

const _isEdge =
    typeof navigator !== 'undefined' && /Edg\//.test(navigator.userAgent || '');

const STREAMING_SUPPORTED = _hasSpeechRecognition && !_isEdge;

export function useStreamingSpeech(language = config.DEFAULT_LANGUAGE, onFinalTranscript) {
    const [isListening, setIsListening] = useState(false);
    const [partialTranscript, setPartialTranscript] = useState('');
    const [error, setError] = useState('');

    const recognitionRef = useRef(null);
    const onFinalRef = useRef(onFinalTranscript);
    const manualStopRef = useRef(false);
    const partialRef = useRef('');           // mirror of partialTranscript for use inside callbacks
    const autoStopTimerRef = useRef(null);

    // Keep callback ref synced
    useEffect(() => { onFinalRef.current = onFinalTranscript; }, [onFinalTranscript]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (autoStopTimerRef.current) clearTimeout(autoStopTimerRef.current);
            if (recognitionRef.current) {
                try { recognitionRef.current.abort(); } catch { /* noop */ }
            }
        };
    }, []);

    /* ── start ─────────────────────────────────────────── */
    const startListening = useCallback(() => {
        if (!STREAMING_SUPPORTED) return false;

        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) return false;

        // Tear down any previous session
        if (recognitionRef.current) {
            try { recognitionRef.current.abort(); } catch { /* noop */ }
        }
        if (autoStopTimerRef.current) {
            clearTimeout(autoStopTimerRef.current);
            autoStopTimerRef.current = null;
        }

        setError('');
        setPartialTranscript('');
        partialRef.current = '';
        manualStopRef.current = false;

        try {
            const recognition = new SR();
            recognitionRef.current = recognition;
            recognition.lang = language || config.DEFAULT_LANGUAGE;
            recognition.continuous = true;       // keep listening until stopped
            recognition.interimResults = true;   // stream partial results
            recognition.maxAlternatives = 1;

            recognition.onresult = (event) => {
                let finalText = '';
                let interimText = '';
                for (let i = 0; i < event.results.length; i++) {
                    const result = event.results[i];
                    if (result.isFinal) {
                        finalText += result[0].transcript;
                    } else {
                        interimText += result[0].transcript;
                    }
                }
                const fullText = finalText + interimText;
                partialRef.current = fullText;
                setPartialTranscript(fullText);
            };

            recognition.onerror = (event) => {
                const code = event?.error || 'unknown';

                // Ignore abort triggered by manual stop
                if (code === 'aborted' && manualStopRef.current) return;

                if (code === 'not-allowed' || code === 'service-not-allowed') {
                    setError('Microphone permission denied. Please allow mic access.');
                    setIsListening(false);
                } else if (code === 'no-speech') {
                    setError('No speech detected. Please try again.');
                } else {
                    setError('Speech recognition error. Please try again.');
                }
            };

            recognition.onend = () => {
                setIsListening(false);

                if (autoStopTimerRef.current) {
                    clearTimeout(autoStopTimerRef.current);
                    autoStopTimerRef.current = null;
                }

                // Deliver the accumulated transcript to the parent
                const text = partialRef.current.trim();
                if (text && onFinalRef.current) {
                    onFinalRef.current(text);
                }

                // Reset partial state
                setPartialTranscript('');
                partialRef.current = '';
            };

            recognition.start();
            setIsListening(true);

            // Safety: auto-stop after 30 seconds to prevent infinite listening
            autoStopTimerRef.current = setTimeout(() => {
                if (recognitionRef.current) {
                    try { recognitionRef.current.stop(); } catch { /* noop */ }
                }
            }, 30000);

            return true;
        } catch (err) {
            console.error('[StreamingSpeech] start error:', err);
            setError('Could not start speech recognition.');
            return false;
        }
    }, [language]);

    /* ── stop ──────────────────────────────────────────── */
    const stopListening = useCallback(() => {
        manualStopRef.current = true;

        if (autoStopTimerRef.current) {
            clearTimeout(autoStopTimerRef.current);
            autoStopTimerRef.current = null;
        }

        if (recognitionRef.current) {
            // .stop() finishes gracefully → fires onend which delivers final transcript
            try { recognitionRef.current.stop(); } catch { /* noop */ }
        }
    }, []);

    return {
        supported: STREAMING_SUPPORTED,
        isListening,
        partialTranscript,
        error,
        startListening,
        stopListening,
    };
}
