# backend/utils/polly_helper.py
# Amazon Polly text-to-speech helper
# Owner: Manoj RS
# See: Detailed_Implementation_Guide.md Section 11

import boto3
import os
import uuid

polly = boto3.client('polly')
s3 = boto3.client('s3')

S3_BUCKET = os.environ.get('S3_KNOWLEDGE_BUCKET', 'smart-rural-ai-knowledge-base')

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
    'ta': 'Kajal',    # Fallback to Hindi (Polly has no Tamil)
    'te': 'Kajal',    # Fallback to Hindi (Polly has no Telugu)
    'kn': 'Kajal',    # Fallback to Hindi
}

# Language code for Polly (LanguageCode parameter)
POLLY_LANG_MAP = {
    'en': 'en-IN',
    'hi': 'hi-IN',
    'ta': 'hi-IN',  # Fallback
    'te': 'hi-IN',  # Fallback
    'kn': 'hi-IN',  # Fallback
}


def normalize_language_code(language_code, default='en'):
    normalized = (language_code or '').strip().lower().replace('_', '-')
    if not normalized:
        return default
    return LANGUAGE_ALIASES.get(normalized, normalized)

MAX_POLLY_TEXT_LENGTH = 2800


def _prepare_text_for_polly(text):
    normalized = (text or '').strip()
    if len(normalized) <= MAX_POLLY_TEXT_LENGTH:
        return normalized

    truncated = normalized[:MAX_POLLY_TEXT_LENGTH]
    last_space = truncated.rfind(' ')
    if last_space > int(MAX_POLLY_TEXT_LENGTH * 0.7):
        truncated = truncated[:last_space]

    return f"{truncated}..."


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

    # Select voice based on language
    if voice_id is None:
        voice_id = VOICE_MAP.get(language_code, 'Kajal')

    safe_text = _prepare_text_for_polly(text)
    was_truncated = (text or '').strip() != safe_text
    if not safe_text:
        if return_metadata:
            return {'audio_url': None, 'truncated': False}
        return None

    try:
        response = polly.synthesize_speech(
            Text=safe_text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine='neural',  # Neural sounds much better
            LanguageCode=POLLY_LANG_MAP.get(language_code, 'en-IN')
        )

        # Save to S3
        audio_key = f"audio/{uuid.uuid4()}.mp3"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=audio_key,
            Body=response['AudioStream'].read(),
            ContentType='audio/mpeg'
        )

        # Generate presigned URL (valid for 1 hour)
        audio_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': audio_key},
            ExpiresIn=3600
        )

        if return_metadata:
            return {'audio_url': audio_url, 'truncated': was_truncated}
        return audio_url

    except Exception as e:
        print(f"Polly error: {e}")
        if return_metadata:
            return {'audio_url': None, 'truncated': was_truncated}
        return None
