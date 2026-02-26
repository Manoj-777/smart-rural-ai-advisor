# backend/lambdas/transcribe_speech/handler.py
# Fallback voice handler: Amazon Transcribe (Firefox fallback)
# Owner: Manoj RS
# Endpoint: POST /transcribe
# See: Detailed_Implementation_Guide.md Section 12

import json
import boto3
import base64
import uuid
import time
import os
import logging
from utils.response_helper import success_response, error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

transcribe = boto3.client('transcribe')
s3 = boto3.client('s3')

BUCKET = os.environ.get('S3_KNOWLEDGE_BUCKET', 'smart-rural-ai-data')

# Map frontend language codes to Transcribe language codes
LANGUAGE_MAP = {
    'ta-IN': 'ta-IN',   # Tamil
    'te-IN': 'te-IN',   # Telugu
    'hi-IN': 'hi-IN',   # Hindi
    'en-IN': 'en-IN',   # English (Indian)
    'en-US': 'en-US',   # English (US)
}


def lambda_handler(event, context):
    """
    Receives base64-encoded audio, sends to Amazon Transcribe,
    returns transcribed text. Used as fallback for non-Chrome browsers.
    """
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return success_response({}, message='OK')

    try:
        body = json.loads(event.get('body', '{}'))
        audio_base64 = body.get('audio')
        language = body.get('language', 'ta-IN')

        if not audio_base64:
            return error_response('No audio provided', 400)

        # Decode audio and upload to S3 (Transcribe reads from S3)
        audio_bytes = base64.b64decode(audio_base64)
        job_id = f"voice-{uuid.uuid4().hex[:8]}"
        s3_key = f"audio-uploads/{job_id}.webm"

        s3.put_object(
            Bucket=BUCKET,
            Key=s3_key,
            Body=audio_bytes,
            ContentType='audio/webm'
        )

        # Start transcription job
        transcribe_language = LANGUAGE_MAP.get(language, 'ta-IN')

        transcribe.start_transcription_job(
            TranscriptionJobName=job_id,
            Media={'MediaFileUri': f's3://{BUCKET}/{s3_key}'},
            MediaFormat='webm',
            LanguageCode=transcribe_language,
            OutputBucketName=BUCKET,
            OutputKey=f'transcriptions/{job_id}.json'
        )

        # Poll for completion (max 30 seconds)
        for _ in range(30):
            status = transcribe.get_transcription_job(
                TranscriptionJobName=job_id
            )
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']

            if job_status == 'COMPLETED':
                # Read the transcription result from S3
                result = s3.get_object(
                    Bucket=BUCKET,
                    Key=f'transcriptions/{job_id}.json'
                )
                transcript_data = json.loads(result['Body'].read().decode('utf-8'))
                transcript = transcript_data['results']['transcripts'][0]['transcript']

                # Cleanup: delete audio and transcription files
                s3.delete_object(Bucket=BUCKET, Key=s3_key)
                s3.delete_object(Bucket=BUCKET, Key=f'transcriptions/{job_id}.json')

                return success_response({'transcript': transcript})

            elif job_status == 'FAILED':
                logger.error(f"Transcription failed: {status}")
                return error_response('Transcription failed. Please try again.', 500)

            time.sleep(1)  # Wait 1 second before polling again

        return error_response('Transcription timed out. Please try again.', 504)

    except Exception as e:
        logger.error(f"Transcribe error: {str(e)}")
        return error_response(str(e), 500)
