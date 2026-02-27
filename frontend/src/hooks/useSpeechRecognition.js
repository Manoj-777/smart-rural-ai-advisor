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

    // Always keep the callback ref synced with the latest value
    useEffect(() => { onResultRef.current = onResult; }, [onResult]);

    const startListening = useCallback(async () => {
        setError('');
        setIsListening(true);

        if (HAS_WEB_SPEECH) {
            // ═══ PATH 1: Web Speech API (Chrome, Edge, Safari) ═══
            const SpeechRecognition = window.SpeechRecognition || 
                                      window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognitionRef.current = recognition;

            recognition.lang = language;
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                if (text && onResultRef.current) {
                    onResultRef.current(text);
                }
                setIsListening(false);
            };

            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                setError(event.error === 'no-speech' 
                    ? 'No speech detected. Try again.' 
                    : event.error === 'not-allowed'
                    ? 'Microphone permission denied. Please allow access in browser settings.'
                    : `Error: ${event.error}`);
                setIsListening(false);
            };

            recognition.onend = () => setIsListening(false);

            try {
                recognition.start();
            } catch (err) {
                console.error('Speech start error:', err);
                setError('Could not start microphone.');
                setIsListening(false);
            }
        } else {
            // ═══ PATH 2: Amazon Transcribe Fallback (Firefox) ═══
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
                            if (data.transcript?.trim() && onResultRef.current) {
                                onResultRef.current(data.transcript);
                            } else {
                                setError('Could not understand. Try again.');
                            }
                        } catch {
                            setError('Connection error. Please type instead.');
                        }
                        setIsListening(false);
                    };
                    reader.readAsDataURL(blob);
                };
                
                recorder.start();
                setTimeout(() => {
                    if (recorder.state === 'recording') recorder.stop();
                }, 15000);
                
            } catch (err) {
                setError(err.name === 'NotAllowedError' 
                    ? 'Microphone permission denied.' 
                    : 'Microphone not available.');
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
