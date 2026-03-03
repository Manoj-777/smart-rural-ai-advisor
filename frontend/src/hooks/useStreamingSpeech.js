// src/hooks/useStreamingSpeech.js
// ChatGPT-style live speech-to-text using browser native SpeechRecognition.
// Uses continuous=false (single utterance) + interimResults=true → words appear
// live in the input field, and the browser auto-finalises when the user pauses.
// This is the most reliable mode across Chrome, Edge, Safari and all Chromium.

import { useState, useRef, useCallback, useEffect } from 'react';
import config from '../config';

const STREAMING_SUPPORTED =
    typeof window !== 'undefined' &&
    !!(window.SpeechRecognition || window.webkitSpeechRecognition);

export function useStreamingSpeech(language = config.DEFAULT_LANGUAGE, onFinalTranscript) {
    const [isListening, setIsListening] = useState(false);
    const [partialTranscript, setPartialTranscript] = useState('');
    const [error, setError] = useState('');
    const [failed, setFailed] = useState(false);

    const recognitionRef = useRef(null);
    const onFinalRef = useRef(onFinalTranscript);
    const manualStopRef = useRef(false);
    const deliveredRef = useRef(false);     // prevent double-delivery
    const partialRef = useRef('');
    const finalTextRef = useRef('');         // accumulates isFinal segments
    const safetyTimerRef = useRef(null);
    const silenceTimerRef = useRef(null);    // auto-stop after silence (Edge fix)

    useEffect(() => { onFinalRef.current = onFinalTranscript; }, [onFinalTranscript]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current);
            if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
            if (recognitionRef.current) {
                try { recognitionRef.current.abort(); } catch { /* */ }
            }
        };
    }, []);

    // Helper: deliver final text exactly once and reset all state
    const _deliver = useCallback((text) => {
        if (deliveredRef.current) return;
        deliveredRef.current = true;
        setIsListening(false);
        setPartialTranscript('');
        partialRef.current = '';
        finalTextRef.current = '';
        if (safetyTimerRef.current) {
            clearTimeout(safetyTimerRef.current);
            safetyTimerRef.current = null;
        }
        if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
        }
        if (text && onFinalRef.current) {
            onFinalRef.current(text);
        }
    }, []);

    /* ── start ─────────────────────────────────────────── */
    const startListening = useCallback(() => {
        if (!STREAMING_SUPPORTED) return false;
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) return false;

        // Tear down previous
        if (recognitionRef.current) {
            try { recognitionRef.current.abort(); } catch { /* */ }
        }
        if (safetyTimerRef.current) {
            clearTimeout(safetyTimerRef.current);
            safetyTimerRef.current = null;
        }

        setError('');
        setPartialTranscript('');
        partialRef.current = '';
        finalTextRef.current = '';
        manualStopRef.current = false;
        deliveredRef.current = false;
        if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
        }

        try {
            const recognition = new SR();
            recognitionRef.current = recognition;
            recognition.lang = language || config.DEFAULT_LANGUAGE;
            recognition.continuous = false;       // single utterance — reliable on ALL browsers
            recognition.interimResults = true;    // live partial transcripts
            recognition.maxAlternatives = 1;

            recognition.onresult = (event) => {
                let final = '';
                let interim = '';
                for (let i = 0; i < event.results.length; i++) {
                    const r = event.results[i];
                    if (r.isFinal) {
                        final += r[0].transcript;
                    } else {
                        interim += r[0].transcript;
                    }
                }
                if (final) finalTextRef.current = final;
                const display = (final || finalTextRef.current) + interim;
                partialRef.current = display;
                setPartialTranscript(display);

                // Silence watchdog: if no new results for 2.5s, auto-stop.
                // This fixes Edge which doesn't auto-finalize on silence like Chrome.
                if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
                silenceTimerRef.current = setTimeout(() => {
                    if (recognitionRef.current && !deliveredRef.current) {
                        try { recognitionRef.current.stop(); } catch { /* */ }
                    }
                }, 2500);
            };

            recognition.onerror = (event) => {
                const code = event?.error || 'unknown';
                if (code === 'aborted' && manualStopRef.current) return;
                if (code === 'not-allowed' || code === 'service-not-allowed') {
                    setError('Microphone permission denied. Please allow mic access.');
                    _deliver('');
                } else if (code === 'no-speech') {
                    setError('No speech detected. Please try again.');
                    _deliver('');
                } else {
                    console.warn('[StreamingSpeech] error, falling back to AWS:', code);
                    setFailed(true);
                    _deliver('');
                }
            };

            recognition.onend = () => {
                // Browser auto-stopped (user paused speaking) → deliver final text
                const text = (finalTextRef.current || partialRef.current).trim();
                _deliver(text);
            };

            recognition.start();
            setIsListening(true);

            // Safety: force-stop after 15s to avoid UI hanging
            safetyTimerRef.current = setTimeout(() => {
                if (recognitionRef.current) {
                    try { recognitionRef.current.stop(); } catch { /* */ }
                }
            }, 15000);

            return true;
        } catch (err) {
            console.error('[StreamingSpeech] start error:', err);
            setFailed(true);
            return false;
        }
    }, [language, _deliver]);

    /* ── stop ──────────────────────────────────────────── */
    const stopListening = useCallback(() => {
        manualStopRef.current = true;
        const text = (finalTextRef.current || partialRef.current).trim();
        _deliver(text);
        // Force-kill — onend will no-op because deliveredRef is true
        if (recognitionRef.current) {
            try { recognitionRef.current.abort(); } catch { /* */ }
            recognitionRef.current = null;
        }
    }, [_deliver]);

    return {
        supported: STREAMING_SUPPORTED && !failed,
        isListening,
        partialTranscript,
        error,
        startListening,
        stopListening,
    };
}
