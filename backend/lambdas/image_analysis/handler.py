# backend/lambdas/image_analysis/handler.py
# Crop disease image analysis using Claude Sonnet 4.5 Vision
# Owner: Manoj RS
# Endpoint: POST /image-analyze
# See: Detailed_Implementation_Guide.md Section 17

import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock = boto3.client('bedrock-runtime')
translate_client = boto3.client('translate')

# CORS headers — MUST be on EVERY response (200, 400, 500)
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
}

# Claude Vision accepts these image formats
SUPPORTED_TYPES = {
    '/9j/': 'image/jpeg',       # JPEG magic bytes in base64
    'iVBORw0KGgo': 'image/png', # PNG magic bytes in base64
    'R0lGOD': 'image/gif',      # GIF magic bytes in base64
    'UklGR': 'image/webp'       # WebP magic bytes in base64
}

MAX_IMAGE_SIZE_MB = 4  # Lambda payload limit is 6 MB; base64 adds ~33%


def detect_media_type(image_base64):
    """Detect image format from the first few base64 characters."""
    for prefix, media_type in SUPPORTED_TYPES.items():
        if image_base64.startswith(prefix):
            return media_type
    return 'image/jpeg'  # Safe default


def make_response(status_code, body_dict):
    """Helper — always includes CORS headers."""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body_dict)
    }


def lambda_handler(event, context):
    """
    Analyzes crop disease image using Claude Sonnet 4.5 Vision.
    Supports: JPEG, PNG, GIF, WebP  |  Max 4 MB  |  Auto-translates response.
    """
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return make_response(200, {})

    try:
        body = json.loads(event.get('body', '{}'))
        image_base64 = body.get('image_base64', '')
        crop_name = body.get('crop_name', 'unknown crop')
        farmer_state = body.get('state', 'India')
        target_language = body.get('language', 'en')

        # Validation
        if not image_base64:
            return make_response(400, {
                'error': 'Image is required. Please upload a photo of the crop.'
            })

        # Strip data-URI prefix if frontend sends "data:image/jpeg;base64,..."
        if ',' in image_base64[:100]:
            image_base64 = image_base64.split(',', 1)[1]

        # Check size (base64 chars * 0.75 ≈ actual bytes)
        image_size_mb = (len(image_base64) * 0.75) / (1024 * 1024)
        if image_size_mb > MAX_IMAGE_SIZE_MB:
            return make_response(400, {
                'error': f'Image too large ({image_size_mb:.1f} MB). '
                         f'Please use a photo under {MAX_IMAGE_SIZE_MB} MB.'
            })

        # Detect format
        media_type = detect_media_type(image_base64)
        logger.info(f"Crop: {crop_name} | Size: {image_size_mb:.1f} MB | "
                    f"Type: {media_type} | State: {farmer_state}")

        # Call Nova Pro Vision via Converse API (supports APAC inference profiles)
        VISION_MODEL = 'apac.amazon.nova-pro-v1:0'
        system_prompt = (
            "You are an expert Indian agricultural scientist with "
            "20 years of field experience across major Indian crops. "
            "You diagnose crop diseases from photos.\n\n"
            "RULES:\n"
            "1. Be HONEST about confidence. If the image is blurry, "
            "too far away, or shows something you cannot identify "
            "with confidence, SAY SO. Never guess a specific disease "
            "name if you are not reasonably sure.\n"
            "2. When confident, give practical farmer-friendly advice "
            "using products and remedies available in Indian markets.\n"
            "3. Always recommend the nearest KVK for confirmation.\n"
            "4. Use bullet points and short sentences. The farmer "
            "may be reading on a small phone screen."
        )
        user_prompt = (
            f"Analyze this image of a {crop_name} crop from {farmer_state}, India.\n\n"
            "Provide your assessment in EXACTLY this format:\n\n"
            "**🔍 Confidence:** [High / Medium / Low] — explain briefly why\n\n"
            "**🦠 Disease/Pest:** [Name of disease, pest, or deficiency — or 'Unable to identify clearly' if unsure]\n\n"
            "**⚠️ Severity:** [Low / Medium / High]\n\n"
            "**❓ Cause:** What causes this condition?\n\n"
            f"**🌿 Organic Treatment:** Traditional/organic remedies available locally in {farmer_state}\n\n"
            "**💊 Chemical Treatment:** Recommended pesticides/fungicides with dosage (use Indian brand names if possible)\n\n"
            "**🛡️ Prevention:** How to prevent this in the future (2-3 short steps)\n\n"
            "**⏰ Urgency:** How quickly should the farmer act?\n\n"
            "**🏥 Next Step:** Always end with: 'Visit your nearest Krishi Vigyan Kendra (KVK) to confirm this diagnosis.'\n\n"
            "IMPORTANT: If the image is unclear, blurry, or does not clearly show a crop disease, say so honestly. "
            "Do NOT fabricate a diagnosis.\n\nRespond in simple, farmer-friendly language. Use short sentences."
        )

        # Map our media_type to Converse API format name
        format_map = {'image/jpeg': 'jpeg', 'image/png': 'png', 'image/gif': 'gif', 'image/webp': 'webp'}
        img_format = format_map.get(media_type, 'jpeg')

        import base64
        image_bytes = base64.b64decode(image_base64)

        response = bedrock.converse(
            modelId=VISION_MODEL,
            system=[{"text": system_prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": img_format,
                                "source": {"bytes": image_bytes}
                            }
                        },
                        {"text": user_prompt}
                    ]
                }
            ],
            inferenceConfig={"maxTokens": 1024, "temperature": 0.3}
        )

        analysis = response['output']['message']['content'][0]['text']

        # Extract confidence from Claude's response
        confidence = 'MEDIUM'
        for level in ['HIGH', 'MEDIUM', 'LOW']:
            if level.lower() in analysis.lower()[:200]:
                confidence = level
                break

        # Translate response to farmer's language
        if target_language and target_language != 'en':
            try:
                translated = translate_client.translate_text(
                    Text=analysis,
                    SourceLanguageCode='en',
                    TargetLanguageCode=target_language
                )
                analysis = translated['TranslatedText']
            except Exception as te:
                logger.warning(f"Translation to {target_language} failed, "
                               f"returning English: {str(te)}")

        return make_response(200, {
            'status': 'success',
            'data': {
                'analysis': analysis,
                'confidence': confidence,
                'crop': crop_name,
                'language': target_language,
                'image_size_mb': round(image_size_mb, 1)
            }
        })

    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}")
        return make_response(500, {
            'error': 'Analysis failed. Please try again or consult your local KVK.'
        })
