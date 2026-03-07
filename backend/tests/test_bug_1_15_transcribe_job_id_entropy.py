import os
import re
import sys
import uuid
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.transcribe_speech import handler as transcribe_handler


def test_generate_job_id_uses_full_uuid_entropy():
    fixed_uuid = uuid.UUID('12345678-1234-5678-9abc-def012345678')

    with patch('lambdas.transcribe_speech.handler.uuid.uuid4', return_value=fixed_uuid):
        job_id = transcribe_handler._generate_job_id()

    assert job_id == 'voice-12345678123456789abcdef012345678'
    assert len(job_id) == len('voice-') + 32


def test_generate_job_id_matches_transcribe_safe_pattern():
    pattern = re.compile(r'^[0-9A-Za-z._-]+$')

    job_id = transcribe_handler._generate_job_id()

    assert pattern.match(job_id) is not None
    assert len(job_id) <= 200


def test_generate_job_id_uniqueness_in_small_sample():
    ids = {transcribe_handler._generate_job_id() for _ in range(100)}

    assert len(ids) == 100
