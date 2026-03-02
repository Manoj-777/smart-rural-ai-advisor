# backend/utils/translate_helper.py
# Amazon Translate helper for multilingual support
# Owner: Manoj RS
# See: Detailed_Implementation_Guide.md Section 12

import boto3

translate = boto3.client('translate')

# Supported languages (must match frontend config.js)
SUPPORTED_LANGUAGES = ["en", "hi", "ta", "te", "kn", "ml", "mr", "bn", "gu", "pa", "or", "as", "ur"]

LANGUAGE_ALIASES = {
    'en-in': 'en',
    'en-us': 'en',
    'hi-in': 'hi',
    'ta-in': 'ta',
    'te-in': 'te',
    'kn-in': 'kn',
    'ml-in': 'ml',
    'mr-in': 'mr',
    'bn-in': 'bn',
    'gu-in': 'gu',
    'pa-in': 'pa',
    'or-in': 'or',
    'as-in': 'as',
    'ur-in': 'ur',
}

# Language code reference:
# Tamil: 'ta'    | Telugu: 'te'   | Hindi: 'hi'
# English: 'en'  | Kannada: 'kn'  | Malayalam: 'ml'
# Marathi: 'mr'  | Bengali: 'bn'  | Gujarati: 'gu'
# Punjabi: 'pa'  | Odia: 'or'     | Assamese: 'as'
# Urdu: 'ur'


def normalize_language_code(language_code, default='en'):
    normalized = (language_code or '').strip().lower().replace('_', '-')
    if not normalized:
        return default
    normalized = LANGUAGE_ALIASES.get(normalized, normalized)
    return normalized if normalized in SUPPORTED_LANGUAGES else default


def detect_and_translate(text, target_language='en'):
    """
    Auto-detect source language and translate to target.

    Args:
        text: Input text in any supported language
        target_language: Language code to translate to ('en', 'ta', 'hi', 'te')

    Returns:
        dict with detected_language, translated_text, target_language
    """
    normalized_target = normalize_language_code(target_language, default='en')
    try:
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode='auto',  # Auto-detect!
            TargetLanguageCode=normalized_target
        )

        return {
            'detected_language': normalize_language_code(response['SourceLanguageCode'], default='en'),
            'translated_text': response['TranslatedText'],
            'target_language': normalized_target
        }

    except Exception as e:
        print(f"Translate error: {e}")
        # Fallback: return original text assuming English
        return {
            'detected_language': 'en',
            'translated_text': text,
            'target_language': normalized_target
        }


def translate_response(text, source_language='en', target_language='ta'):
    """
    Translate AI response from English to farmer's language.
    Preserves markdown formatting markers (###, **, *, -, numbered lists)
    by wrapping them in translate="no" spans when using ContentType=text/html.
    """
    normalized_source = normalize_language_code(source_language, default='en')
    normalized_target = normalize_language_code(target_language, default='en')

    if normalized_source == normalized_target:
        return text

    import re

    # Protect markdown markers by wrapping in <span translate="no">...</span>
    # AWS Translate respects this when ContentType='text/html'
    def _protect_markdown(t):
        # Protect heading markers: ### heading → <span translate="no">### </span>heading
        t = re.sub(r'^(#{1,4})\s+', r'<span translate="no">\1 </span>', t, flags=re.MULTILINE)
        # Protect bold markers: **text** → <span translate="no">**</span>text<span translate="no">**</span>
        t = re.sub(r'\*\*(.+?)\*\*', r'<span translate="no">**</span>\1<span translate="no">**</span>', t)
        # Protect italic markers: *text* → <span translate="no">*</span>text<span translate="no">*</span>
        t = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<span translate="no">*</span>\1<span translate="no">*</span>', t)
        # Protect bullet list markers: - item → <span translate="no">- </span>item
        t = re.sub(r'^(\s*[\-•])\s+', r'<span translate="no">\1 </span>', t, flags=re.MULTILINE)
        # Protect numbered list markers: 1. item → <span translate="no">1. </span>item
        t = re.sub(r'^(\s*\d+\.)\s+', r'<span translate="no">\1 </span>', t, flags=re.MULTILINE)
        return t

    def _restore_markdown(t):
        # Remove the protective spans after translation
        t = re.sub(r'<span translate="no">(.*?)</span>', r'\1', t)
        return t

    try:
        protected_text = _protect_markdown(text)
        response = translate.translate_text(
            Text=protected_text,
            SourceLanguageCode=normalized_source,
            TargetLanguageCode=normalized_target,
        )
        translated = _restore_markdown(response['TranslatedText'])
        return translated
    except Exception as e:
        # Fallback: try plain text translation without markdown protection
        try:
            response = translate.translate_text(
                Text=text,
                SourceLanguageCode=normalized_source,
                TargetLanguageCode=normalized_target
            )
            return response['TranslatedText']
        except Exception as e2:
            print(f"Translate error: {e2}")
            return text  # Return original if translation fails
