# backend/utils/translate_helper.py
# Amazon Translate helper for multilingual support
# Owner: Manoj RS
# See: Detailed_Implementation_Guide.md Section 12

import boto3

translate = boto3.client('translate')

# Supported languages
SUPPORTED_LANGUAGES = ["en", "hi", "ta", "te", "kn", "ml", "mr", "bn"]

# Language code reference:
# Tamil: 'ta'    | Telugu: 'te'   | Hindi: 'hi'
# English: 'en'  | Kannada: 'kn'  | Malayalam: 'ml'
# Marathi: 'mr'  | Bengali: 'bn'


def detect_and_translate(text, target_language='en'):
    """
    Auto-detect source language and translate to target.

    Args:
        text: Input text in any supported language
        target_language: Language code to translate to ('en', 'ta', 'hi', 'te')

    Returns:
        dict with detected_language, translated_text, target_language
    """
    try:
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode='auto',  # Auto-detect!
            TargetLanguageCode=target_language
        )

        return {
            'detected_language': response['SourceLanguageCode'],
            'translated_text': response['TranslatedText'],
            'target_language': target_language
        }

    except Exception as e:
        print(f"Translate error: {e}")
        # Fallback: return original text assuming English
        return {
            'detected_language': 'en',
            'translated_text': text,
            'target_language': target_language
        }


def translate_response(text, source_language='en', target_language='ta'):
    """
    Translate AI response from English to farmer's language.
    """
    if source_language == target_language:
        return text

    try:
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_language,
            TargetLanguageCode=target_language
        )
        return response['TranslatedText']

    except Exception as e:
        print(f"Translate error: {e}")
        return text  # Return original if translation fails
