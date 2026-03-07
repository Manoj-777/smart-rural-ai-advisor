import json
import os
import sys
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lambdas.crop_advisory import handler as crop_handler


def test_apply_retrieval_quality_gate_filters_low_score_chunks():
    retrieval_results = [
        {'content': {'text': 'High relevance chunk'}, 'score': 0.83, 'location': {'s3Location': {'uri': 's3://kb/a.md'}}},
        {'content': {'text': 'Borderline chunk'}, 'score': 0.36, 'location': {'s3Location': {'uri': 's3://kb/b.md'}}},
        {'content': {'text': 'Low relevance chunk'}, 'score': 0.12, 'location': {'s3Location': {'uri': 's3://kb/c.md'}}},
    ]

    selected, metrics = crop_handler._apply_retrieval_quality_gate(
        retrieval_results,
        min_score=0.35,
        max_chunks=5,
    )

    assert len(selected) == 2
    assert selected[0]['score'] >= selected[1]['score']
    assert metrics['good_count'] == 2
    assert metrics['selected_count'] == 2


def test_rewrite_search_query_for_recall_by_query_type():
    assert 'irrigation schedule' in crop_handler._rewrite_search_query_for_recall('x', 'irrigation', 'rice')
    assert 'pest disease symptoms' in crop_handler._rewrite_search_query_for_recall('x', 'pest', 'cotton')
    assert 'crop advisory' in crop_handler._rewrite_search_query_for_recall('x', 'general', 'maize')


def test_lambda_handler_marks_insufficient_evidence_when_quality_is_low():
    event = {
        'queryStringParameters': {
            'query': 'best crop for my soil',
            'location': 'Madurai',
            'query_type': 'recommendation',
        }
    }

    first_retrieve = {
        'retrievalResults': [
            {'content': {'text': 'weak chunk 1'}, 'score': 0.20, 'location': {'s3Location': {'uri': 's3://kb/x.md'}}},
            {'content': {'text': 'weak chunk 2'}, 'score': 0.25, 'location': {'s3Location': {'uri': 's3://kb/y.md'}}},
        ]
    }
    second_retrieve = {
        'retrievalResults': [
            {'content': {'text': 'still weak'}, 'score': 0.18, 'location': {'s3Location': {'uri': 's3://kb/z.md'}}},
        ]
    }

    with patch.object(crop_handler, 'KB_ID', 'dummy-kb'):
        with patch.object(crop_handler, '_kb_retrieve_with_retry', side_effect=[first_retrieve, second_retrieve]):
            response = crop_handler.lambda_handler(event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    data = body['data']

    assert data['insufficient_evidence'] is True
    assert data['retrieval_quality']['used_fallback_query'] is True
    assert data['retrieval_quality']['good_count'] < crop_handler.KB_MIN_GOOD_CHUNKS


def test_extract_year_tokens_handles_ranges_and_single_years():
    text = 'MSP 2025-26 revised from 2024 and projected to 2026.'
    years = crop_handler._extract_year_tokens(text)

    assert 2024 in years
    assert 2025 in years
    assert 2026 in years


def test_build_freshness_metadata_warns_on_old_time_sensitive_content():
    advisory_data = [
        {'content': 'MSP values as of 2000 and old procurement windows.'}
    ]

    freshness = crop_handler._build_freshness_metadata(
        'latest msp for rice',
        'general',
        advisory_data,
    )

    assert freshness['time_sensitive_query'] is True
    assert freshness['stale_reference_detected'] is True
    assert 'verify latest' in freshness['staleness_warning'].lower()


def test_lambda_handler_redirects_scheme_intent_to_authoritative_source():
    event = {
        'queryStringParameters': {
            'query': 'what subsidy schemes are available for me',
            'location': 'Madurai',
            'query_type': 'general',
        }
    }

    with patch.object(crop_handler, 'KB_ID', 'dummy-kb'):
        response = crop_handler.lambda_handler(event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    data = body['data']

    assert data['source_authority'] == 'govt_schemes'
    assert data['redirect_tool'] == 'search_schemes'
    assert data['advisory_data'] == []
