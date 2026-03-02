# backend/utils/polly_helper.py
# Amazon Polly text-to-speech helper
# Owner: Manoj RS
# See: Detailed_Implementation_Guide.md Section 11

import boto3
import os
import uuid
import io

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
# gTTS is ~10× slower than Polly (HTTP calls to Google Translate per chunk).
# Keep gTTS text short to finish within API Gateway's 29-second window.
MAX_GTTS_TEXT_LENGTH = 800


def _truncate_text(text, max_length):
    """Truncate text to max_length, breaking at a word boundary."""
    normalized = (text or '').strip()
    if len(normalized) <= max_length:
        return normalized
    truncated = normalized[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > int(max_length * 0.7):
        truncated = truncated[:last_space]
    return f"{truncated}..."


def _prepare_text_for_polly(text):
    return _truncate_text(text, MAX_POLLY_TEXT_LENGTH)


def _upload_audio_bytes(audio_bytes):
    audio_key = f"audio/{uuid.uuid4()}.mp3"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=audio_key,
        Body=audio_bytes,
        ContentType='audio/mpeg'
    )

    presigned = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': audio_key},
        ExpiresIn=3600
    )
    return {'url': presigned, 'key': audio_key}


def refresh_audio_url(audio_key):
    """Generate a fresh presigned URL for an existing audio file."""
    if not audio_key or not audio_key.startswith('audio/'):
        return None
    try:
        # Verify the file exists
        s3.head_object(Bucket=S3_BUCKET, Key=audio_key)
        return s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': audio_key},
            ExpiresIn=3600
        )
    except Exception:
        return None


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
    """Free Google Translate TTS. No API key. Supports all major Indian languages."""
    try:
        from gtts import gTTS
    except ImportError:
        print('gTTS not installed, skipping free TTS path')
        return None

    # Aggressively truncate for gTTS — it's much slower than Polly.
    gtts_text = _truncate_text(safe_text, MAX_GTTS_TEXT_LENGTH)
    print(f'gTTS: {len(safe_text)} chars → {len(gtts_text)} chars for lang={language_code}')
    tts = gTTS(text=gtts_text, lang=language_code, slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return _upload_audio_bytes(buf.read())


def text_to_speech(text, language_code='en', voice_id=None, return_metadata=False):
    """
    Convert text to speech using Amazon Polly or gTTS.

    Args:
        text: The text to convert
        language_code: 'en' for English, 'hi' for Hindi, 'ta' for Tamil
        voice_id: Specific Polly voice (auto-selected if None)
        return_metadata: If True, returns {'audio_url': ..., 'audio_key': ..., 'truncated': ...}

    Returns:
        Presigned S3 URL (default), or metadata dict if return_metadata=True
    """
    language_code = normalize_language_code(language_code, default='en')

    safe_text = _prepare_text_for_polly(text)
    was_truncated = (text or '').strip() != safe_text
    if not safe_text:
        if return_metadata:
            return {'audio_url': None, 'audio_key': None, 'truncated': False}
        return None

    try:
        result = None  # will be {'url': ..., 'key': ...} or None

        if language_code in POLLY_NATIVE_LANGS:
            result = _polly_tts(safe_text, language_code, voice_id=voice_id)
        elif POLLY_FORCE_HINDI_FALLBACK:
            result = _polly_tts(safe_text, 'hi', voice_id='Kajal')
        elif USE_GTTS and language_code in GTTS_SUPPORTED_LANGS:
            try:
                result = _gtts_tts(safe_text, language_code)
            except Exception as gtts_err:
                print(f"gTTS error ({language_code}): {gtts_err}")
                if TTS_FAILOVER_TO_POLLY:
                    result = _polly_tts(safe_text, 'hi', voice_id='Kajal')

        # Unpack result — _upload_audio_bytes now returns {'url': ..., 'key': ...}
        if isinstance(result, dict):
            audio_url = result.get('url')
            audio_key = result.get('key')
        else:
            audio_url = result
            audio_key = None

        if return_metadata:
            return {'audio_url': audio_url, 'audio_key': audio_key, 'truncated': was_truncated}
        return audio_url

    except Exception as e:
        print(f"Polly error: {e}")
        if return_metadata:
            return {'audio_url': None, 'audio_key': None, 'truncated': was_truncated}
        return None
