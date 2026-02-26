// src/hooks/useSpeechRecognition.js

import { useState, useRef, useCallback } from 'react';
import config from '../config';

const HAS_WEB_SPEECH = ('webkitSpeechRecognition' in window) || 
                       ('SpeechRecognition' in window);

export function useSpeechRecognition(language = config.DEFAULT_LANGUAGE) {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [error, setError] = useState('');
    const recognitionRef = useRef(null);
    const mediaRecorderRef = useRef(null);

    const startListening = useCallback(async () => {
        setError('');
        setTranscript('');
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

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                setTranscript(text);
                setIsListening(false);
            };

            recognition.onerror = (event) => {
                setError(event.error === 'no-speech' 
                    ? 'No speech detected. Try again.' 
                    : `Error: ${event.error}`);
                setIsListening(false);
            };

            recognition.onend = () => setIsListening(false);

            try {
                recognition.start();
            } catch (err) {
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
                    
                    // Convert to base64 and send to Lambda
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
                            if (data.transcript?.trim()) {
                                setTranscript(data.transcript);
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

    return { isListening, transcript, error, startListening, stopListening };
}
