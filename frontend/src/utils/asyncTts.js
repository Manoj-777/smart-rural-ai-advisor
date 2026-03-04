// src/utils/asyncTts.js
// Shared utility for generating TTS audio asynchronously (for gTTS languages)

import { apiFetch } from './apiFetch';

/**
 * Generate TTS audio via a separate API call.
 * Used when main response returns audio_pending=true (gTTS languages are slow).
 *
 * @param {string} text - The text to convert to speech
 * @param {string} language - Language code (e.g. 'ta', 'te', 'kn')
 * @returns {Promise<{audioUrl: string, audioKey: string}|null>}
 */
export async function generateAsyncTts(text, language) {
    if (!text) return null;
    try {
        const res = await apiFetch(`/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                generate_tts: true,
                tts_text: text,
                tts_language: language || 'en'
            })
        });
        const data = await res.json();
        if (data.status === 'success' && data.data?.audio_url) {
            return {
                audioUrl: data.data.audio_url,
                audioKey: data.data.audio_key
            };
        }
    } catch { /* silent */ }
    return null;
}
