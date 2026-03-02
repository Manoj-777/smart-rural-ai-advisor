// src/hooks/useSpeechRecognition.js
// ALWAYS uses MediaRecorder + AWS Transcribe — reliable for all 13 languages
// and all browsers (Chrome, Firefox, Edge, Safari)

import { useState, useRef, useCallback, useEffect } from 'react';
import config from '../config';

export function useSpeechRecognition(language = config.DEFAULT_LANGUAGE, onResult) {
    const [isListening, setIsListening] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState('');
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const streamRef = useRef(null);
    const onResultRef = useRef(onResult);
    const autoStopTimerRef = useRef(null);

    // Always keep the callback ref synced with the latest value
    useEffect(() => { onResultRef.current = onResult; }, [onResult]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (autoStopTimerRef.current) clearTimeout(autoStopTimerRef.current);
            if (mediaRecorderRef.current?.state === 'recording') {
                try { mediaRecorderRef.current.stop(); } catch { /* */ }
            }
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(t => t.stop());
            }
        };
    }, []);

    const _sendToTranscribe = useCallback(async (chunks, mimeType) => {
        if (chunks.length === 0) {
            setError('No audio captured. Please try again.');
            setIsProcessing(false);
            return;
        }

        const blob = new Blob(chunks, { type: mimeType });

        // Skip tiny recordings (likely noise/silence)
        if (blob.size < 1000) {
            setError('Recording too short. Please hold the mic button and speak clearly.');
            setIsProcessing(false);
            return;
        }

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
                    setError('');
                } else {
                    setError('Could not understand. Please speak clearly and try again.');
                }
            } catch {
                setError('Connection error. Please check your internet and try again.');
            }
            setIsProcessing(false);
        };
        reader.readAsDataURL(blob);
    }, [language]);

    const startListening = useCallback(async () => {
        setError('');
        setIsProcessing(false);

        // Stop any previous recording
        if (mediaRecorderRef.current?.state === 'recording') {
            try { mediaRecorderRef.current.stop(); } catch { /* */ }
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop());
            streamRef.current = null;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    channelCount: 1,
                }
            });
            streamRef.current = stream;

            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : MediaRecorder.isTypeSupported('audio/webm')
                    ? 'audio/webm'
                    : MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')
                        ? 'audio/ogg;codecs=opus'
                        : 'audio/mp4';  // Safari fallback

            const recorder = new MediaRecorder(stream, { mimeType });
            mediaRecorderRef.current = recorder;
            chunksRef.current = [];

            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            recorder.onstop = () => {
                // Release mic immediately
                stream.getTracks().forEach(t => t.stop());
                streamRef.current = null;

                setIsListening(false);
                setIsProcessing(true);

                // Send captured audio to Transcribe
                _sendToTranscribe(chunksRef.current, mimeType);
            };

            // Request data every 250ms for reliability
            recorder.start(250);
            setIsListening(true);

            // Auto-stop after 20 seconds
            autoStopTimerRef.current = setTimeout(() => {
                if (mediaRecorderRef.current?.state === 'recording') {
                    mediaRecorderRef.current.stop();
                }
            }, 20000);

        } catch (err) {
            console.error('Mic access error:', err);
            if (err.name === 'NotAllowedError') {
                setError('Microphone permission denied. Please allow mic access in your browser settings.');
            } else if (err.name === 'NotFoundError') {
                setError('No microphone found. Please connect a mic and try again.');
            } else {
                setError('Could not access microphone. Please try again.');
            }
            setIsListening(false);
        }
    }, [language, _sendToTranscribe]);

    const stopListening = useCallback(() => {
        if (autoStopTimerRef.current) {
            clearTimeout(autoStopTimerRef.current);
            autoStopTimerRef.current = null;
        }
        if (mediaRecorderRef.current?.state === 'recording') {
            mediaRecorderRef.current.stop();
        }
    }, []);

    return { isListening, isProcessing, error, startListening, stopListening };
}
