// src/hooks/useSpeechRecognition.js

import { useState, useRef, useCallback, useEffect } from 'react';
import config from '../config';

const HAS_WEB_SPEECH = typeof window !== 'undefined' && 
    (('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window));

export function useSpeechRecognition(language = config.DEFAULT_LANGUAGE, onResult) {
    const [isListening, setIsListening] = useState(false);
    const [error, setError] = useState('');
    const recognitionRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const onResultRef = useRef(onResult);
    const gotResultRef = useRef(false);

    // Always keep the callback ref synced with the latest value
    useEffect(() => { onResultRef.current = onResult; }, [onResult]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (recognitionRef.current) {
                try { recognitionRef.current.abort(); } catch { /* */ }
            }
            if (mediaRecorderRef.current?.state === 'recording') {
                try { mediaRecorderRef.current.stop(); } catch { /* */ }
            }
        };
    }, []);

    const startListening = useCallback(async () => {
        setError('');
        gotResultRef.current = false;

        // Abort any previous session
        if (recognitionRef.current) {
            try { recognitionRef.current.abort(); } catch { /* */ }
            recognitionRef.current = null;
        }
        if (mediaRecorderRef.current?.state === 'recording') {
            try { mediaRecorderRef.current.stop(); } catch { /* */ }
            mediaRecorderRef.current = null;
        }

        setIsListening(true);

        if (HAS_WEB_SPEECH) {
            // ═══ PATH 1: Web Speech API (Chrome, Edge, Safari) ═══
            try {
                const SpeechRecognition = window.SpeechRecognition || 
                                          window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognitionRef.current = recognition;

                recognition.lang = language;
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.maxAlternatives = 1;

                // Auto-stop after 12 seconds max
                const autoStopTimer = setTimeout(() => {
                    if (recognitionRef.current) {
                        try { recognitionRef.current.stop(); } catch { /* */ }
                    }
                }, 12000);

                recognition.onresult = (event) => {
                    // Collect the latest transcript (interim or final)
                    let finalTranscript = '';
                    let interimTranscript = '';
                    for (let i = 0; i < event.results.length; i++) {
                        const result = event.results[i];
                        if (result.isFinal) {
                            finalTranscript += result[0].transcript;
                        } else {
                            interimTranscript += result[0].transcript;
                        }
                    }

                    const text = finalTranscript || interimTranscript;
                    if (finalTranscript && onResultRef.current) {
                        gotResultRef.current = true;
                        onResultRef.current(finalTranscript.trim());
                        clearTimeout(autoStopTimer);
                        try { recognition.stop(); } catch { /* */ }
                    }
                };

                recognition.onerror = (event) => {
                    clearTimeout(autoStopTimer);
                    console.error('Speech recognition error:', event.error);
                    if (event.error === 'no-speech') {
                        setError('No speech detected. Please tap the mic and speak clearly.');
                    } else if (event.error === 'not-allowed') {
                        setError('Microphone permission denied. Please allow access in browser settings.');
                    } else if (event.error === 'network') {
                        setError('Network error. Speech recognition requires internet connection.');
                    } else if (event.error === 'aborted') {
                        // User or code aborted — no error needed
                    } else {
                        setError(`Speech error: ${event.error}. Try again.`);
                    }
                    setIsListening(false);
                };

                recognition.onend = () => {
                    clearTimeout(autoStopTimer);
                    setIsListening(false);
                    if (!gotResultRef.current) {
                        setError(prev => prev || 'No speech detected. Please tap the mic and speak clearly.');
                    }
                };

                recognition.start();
            } catch (err) {
                console.error('Speech start error:', err);
                setError('Could not start microphone. Please try again.');
                setIsListening(false);
            }
        } else {
            // ═══ PATH 2: Amazon Transcribe Fallback (Firefox, etc.) ═══
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: { sampleRate: 16000, channelCount: 1 } 
                });
                
                const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                    ? 'audio/webm;codecs=opus' : 'audio/ogg;codecs=opus';
                
                const recorder = new MediaRecorder(stream, { mimeType });
                mediaRecorderRef.current = recorder;
                const chunks = [];
                
                recorder.ondataavailable = (e) => {
                    if (e.data.size > 0) chunks.push(e.data);
                };
                
                recorder.onstop = async () => {
                    stream.getTracks().forEach(t => t.stop());
                    if (chunks.length === 0) {
                        setError('No audio captured. Please try again.');
                        setIsListening(false);
                        return;
                    }
                    const blob = new Blob(chunks, { type: mimeType });
                    
                    const reader = new FileReader();
                    reader.onloadend = async () => {
                        const base64 = reader.result.split(',')[1];
                        try {
                            const res = await fetch(`${config.API_URL}/transcribe`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ audio: base64, language, format: mimeType })
                            });
                            const data = await res.json();
                            const transcript = data?.data?.transcript || data?.transcript;
                            if (transcript?.trim() && onResultRef.current) {
                                onResultRef.current(transcript.trim());
                            } else {
                                setError('Could not understand. Please speak clearly and try again.');
                            }
                        } catch {
                            setError('Connection error. Please check your internet and try again.');
                        }
                        setIsListening(false);
                    };
                    reader.readAsDataURL(blob);
                };
                
                recorder.start();
                setTimeout(() => {
                    if (recorder.state === 'recording') recorder.stop();
                }, 12000);
                
            } catch (err) {
                setError(err.name === 'NotAllowedError' 
                    ? 'Microphone permission denied. Please allow access in browser settings.' 
                    : 'Microphone not available on this device.');
                setIsListening(false);
            }
        }
    }, [language]);

    const stopListening = useCallback(() => {
        if (recognitionRef.current) recognitionRef.current.stop();
        if (mediaRecorderRef.current?.state === 'recording') {
            mediaRecorderRef.current.stop();
        }
        setIsListening(false);
    }, []);

    return { isListening, error, startListening, stopListening };
}
