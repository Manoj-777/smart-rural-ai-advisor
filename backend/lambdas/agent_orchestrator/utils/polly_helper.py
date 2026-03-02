# backend/utils/polly_helper.py
# Amazon Polly text-to-speech helper
# Owner: Manoj RS
# See: Detailed_Implementation_Guide.md Section 11

import boto3
import os
import uuid
import io
import threading

polly = boto3.client('polly')
s3 = boto3.client('s3')

S3_BUCKET = os.environ.get('S3_KNOWLEDGE_BUCKET', 'smart-rural-ai-knowledge-base')
POLLY_FORCE_HINDI_FALLBACK = os.environ.get('POLLY_FORCE_HINDI_FALLBACK', 'false').lower() == 'true'
TTS_FAILOVER_TO_POLLY = os.environ.get('TTS_FAILOVER_TO_POLLY', 'true').lower() == 'true'

LANGUAGE_ALIASES = {
    'en-in': 'en',
    'en-us': 'en',
    'hi-in': 'hi',
    'ta-in': 'ta',
    'te-in': 'te',
    'kn-in': 'kn',
}

LANGUAGE_ALIASES = {
    'en-in': 'en',
    'en-us': 'en',
    'hi-in': 'hi',
    'ta-in': 'ta',
    'te-in': 'te',
    'kn-in': 'kn',
}

# Language → Polly voice mapping
# Polly has Hindi + English (Indian) neural voices.
# Tamil/Telugu fall back to Hindi voice (Kajal).
VOICE_MAP = {
    'en': 'Kajal',    # English Indian Neural
    'hi': 'Kajal',    # Hindi Neural
}

# Language code for Polly (LanguageCode parameter)
POLLY_LANG_MAP = {
    'en': 'en-IN',
    'hi': 'hi-IN',
}

POLLY_NATIVE_LANGS = {'en', 'hi'}

# gTTS: free Google Translate TTS – supports ta, te, kn, ml, mr, bn, gu, pa etc.
# No API key needed. Used as primary path for non-Polly languages.
GTTS_SUPPORTED_LANGS = {'ta', 'te', 'kn', 'ml', 'mr', 'bn', 'gu', 'pa', 'or', 'as', 'ur'}
USE_GTTS = os.environ.get('USE_GTTS', 'true').lower() == 'true'


def normalize_language_code(language_code, default='en'):
    normalized = (language_code or '').strip().lower().replace('_', '-')
    if not normalized:
        return default
    return LANGUAGE_ALIASES.get(normalized, normalized)

MAX_POLLY_TEXT_LENGTH = 2800
MAX_GTTS_TEXT_LENGTH = 800  # gTTS is slow from Lambda; keep text short for faster response
GTTS_TIMEOUT_SEC = 8  # max seconds to wait for gTTS before giving up


def _prepare_text_for_polly(text):
    normalized = (text or '').strip()
    if len(normalized) <= MAX_POLLY_TEXT_LENGTH:
        return normalized

    truncated = normalized[:MAX_POLLY_TEXT_LENGTH]
    last_space = truncated.rfind(' ')
    if last_space > int(MAX_POLLY_TEXT_LENGTH * 0.7):
        truncated = truncated[:last_space]

    return f"{truncated}..."


def _upload_audio_bytes(audio_bytes):
    audio_key = f"audio/{uuid.uuid4()}.mp3"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=audio_key,
        Body=audio_bytes,
        ContentType='audio/mpeg'
    )

    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': audio_key},
        ExpiresIn=3600
    )


def _polly_tts(safe_text, language_code, voice_id=None):
    selected_voice = voice_id or VOICE_MAP.get(language_code, 'Kajal')
    response = polly.synthesize_speech(
        Text=safe_text,
        OutputFormat='mp3',
        VoiceId=selected_voice,
        Engine='neural',
        LanguageCode=POLLY_LANG_MAP.get(language_code, 'en-IN')
    )
    return _upload_audio_bytes(response['AudioStream'].read())


def _gtts_tts(safe_text, language_code):
    """Free Google Translate TTS. No API key. Supports all major Indian languages.
    Truncated to MAX_GTTS_TEXT_LENGTH and guarded by GTTS_TIMEOUT_SEC to prevent
    Lambda timeouts (gTTS makes external HTTP calls which can be slow)."""
    try:
        from gtts import gTTS
    except ImportError:
        print('gTTS not installed, skipping free TTS path')
        return None

    # Truncate text to keep gTTS fast — long text causes very slow HTTP calls
    truncated_text = safe_text
    if len(safe_text) > MAX_GTTS_TEXT_LENGTH:
        truncated_text = safe_text[:MAX_GTTS_TEXT_LENGTH]
        last_space = truncated_text.rfind(' ')
        if last_space > int(MAX_GTTS_TEXT_LENGTH * 0.7):
            truncated_text = truncated_text[:last_space]
        truncated_text += '...'

    result = [None]
    error = [None]

    def _run():
        try:
            tts = gTTS(text=truncated_text, lang=language_code, slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            result[0] = _upload_audio_bytes(buf.read())
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=GTTS_TIMEOUT_SEC)

    if t.is_alive():
        print(f'gTTS timed out after {GTTS_TIMEOUT_SEC}s — skipping audio')
        return None
    if error[0]:
        raise error[0]
    return result[0]


def text_to_speech(text, language_code='en', voice_id=None, return_metadata=False):
    """
    Convert text to speech using Amazon Polly.

    Args:
        text: The text to convert
        language_code: 'en' for English, 'hi' for Hindi, 'ta' for Tamil
        voice_id: Specific Polly voice (auto-selected if None)
        return_metadata: If True, returns {'audio_url': ..., 'truncated': ...}

    Returns:
        Presigned S3 URL (default), or metadata dict if return_metadata=True
    """
    language_code = normalize_language_code(language_code, default='en')

    safe_text = _prepare_text_for_polly(text)
    was_truncated = (text or '').strip() != safe_text
    if not safe_text:
        if return_metadata:
            return {'audio_url': None, 'truncated': False}
        return None

    safe_text = _prepare_text_for_polly(text)
    was_truncated = (text or '').strip() != safe_text
    if not safe_text:
        if return_metadata:
            return {'audio_url': None, 'truncated': False}
        return None

    try:
        audio_url = None

        if language_code in POLLY_NATIVE_LANGS:
            audio_url = _polly_tts(safe_text, language_code, voice_id=voice_id)
        elif POLLY_FORCE_HINDI_FALLBACK:
            audio_url = _polly_tts(safe_text, 'hi', voice_id='Kajal')
        elif USE_GTTS and language_code in GTTS_SUPPORTED_LANGS:
            # Primary free path: gTTS (Google Translate TTS)
            try:
                audio_url = _gtts_tts(safe_text, language_code)
            except Exception as gtts_err:
                print(f"gTTS error ({language_code}): {gtts_err}")
                if TTS_FAILOVER_TO_POLLY:
                    audio_url = _polly_tts(safe_text, 'hi', voice_id='Kajal')
        else:
            audio_url = None

        if return_metadata:
            return {'audio_url': audio_url, 'truncated': was_truncated}
        return audio_url

    except Exception as e:
        print(f"Polly error: {e}")
        if return_metadata:
            return {'audio_url': None, 'truncated': was_truncated}
        return None
