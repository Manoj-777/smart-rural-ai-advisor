import os
import sys
from unittest.mock import MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock optional modules before importing handler
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

from lambdas.agent_orchestrator import handler as orchestrator_handler


def test_apply_tool_input_policy_locks_scheme_state_to_profile_state():
    tool_input = {'query': 'subsidy', 'state': 'Karnataka'}
    farmer_context = {'state': 'Tamil Nadu', 'district': 'Madurai'}

    adjusted = orchestrator_handler._apply_tool_input_policy(
        'search_schemes',
        tool_input,
        farmer_context=farmer_context,
        user_prompt='show me schemes',
    )

    assert adjusted['state'] == 'Tamil Nadu'
    assert adjusted['query'] == 'subsidy'


def test_enforce_tool_result_policy_filters_other_states():
    result = {
        'status': 'success',
        'data': {
            'schemes': {'pm_kisan': {'name': 'PM-KISAN'}},
            'state_schemes': {
                'Tamil Nadu': [{'name': 'TN Scheme'}],
                'Karnataka': [{'name': 'KA Scheme'}],
            },
        },
    }

    filtered = orchestrator_handler._enforce_tool_result_policy(
        'search_schemes',
        result,
        farmer_context={'state': 'Tamil Nadu'},
    )

    assert list(filtered['data']['state_schemes'].keys()) == ['Tamil Nadu']
    assert filtered['data']['state_scope_applied'] == 'Tamil Nadu'


def test_soil_specific_query_detection_and_enrichment_guard():
    tool_input = {'query': 'best crops for black soil', 'soil_type': 'black soil'}
    user_prompt = 'Which crops are suitable for black soil in my district?'

    assert orchestrator_handler._is_soil_specific_recommendation_query(user_prompt, tool_input)

    raw_result = {'advisory_data': [{'content': 'Some generic snippet'}]}
    enriched = orchestrator_handler._enrich_tool_result(
        raw_result,
        'get_crop_advisory',
        tool_input,
        user_prompt,
    )

    assert '_soil_evidence_policy' in enriched
    assert '_enrichment' not in enriched


def test_apply_tool_input_policy_allows_explicit_cross_state_scheme_request():
    tool_input = {'query': 'karnataka subsidy schemes'}
    farmer_context = {'state': 'Tamil Nadu', 'district': 'Madurai'}

    adjusted = orchestrator_handler._apply_tool_input_policy(
        'search_schemes',
        tool_input,
        farmer_context=farmer_context,
        user_prompt='show me Karnataka schemes and compare with my state',
    )

    assert adjusted.get('state') != 'Tamil Nadu'
    assert adjusted['query'] == 'karnataka subsidy schemes'


def test_enforce_tool_result_policy_skips_state_filter_for_cross_state_query():
    result = {
        'status': 'success',
        'data': {
            'schemes': {'pm_kisan': {'name': 'PM-KISAN'}},
            'state_schemes': {
                'Tamil Nadu': [{'name': 'TN Scheme'}],
                'Karnataka': [{'name': 'KA Scheme'}],
            },
        },
    }

    passthrough = orchestrator_handler._enforce_tool_result_policy(
        'search_schemes',
        result,
        farmer_context={'state': 'Tamil Nadu'},
        user_prompt='compare Tamil Nadu and Karnataka schemes',
    )

    assert 'Tamil Nadu' in passthrough['data']['state_schemes']
    assert 'Karnataka' in passthrough['data']['state_schemes']


def test_strict_soil_response_guard_rewrites_when_disallowed_crop_is_present():
    tool_data_log = [
        {
            'tool': 'get_crop_advisory',
            'output': {
                'advisory_data': [
                    {'content': 'Black soil suitable crops include cotton and soybean in this region.'}
                ]
            },
        }
    ]

    guarded = orchestrator_handler._apply_strict_soil_response_guard(
        'For black soil, grow cotton, soybean, and banana for better returns.',
        'best crops for black soil in my area',
        farmer_context={'state': 'Tamil Nadu'},
        tool_data_log=tool_data_log,
    )

    assert 'banana' not in guarded.lower()
    assert 'cotton' in guarded.lower()
    assert 'soybean' in guarded.lower()


def test_soil_guard_aliases_cover_all_crop_reference_keys():
    soil_keys = set(orchestrator_handler._SOIL_GUARD_CROP_ALIASES.keys())
    crop_ref_keys = {k.strip().lower() for k in orchestrator_handler._CROP_REF.keys()}

    assert crop_ref_keys.issubset(soil_keys)


def test_crop_key_alias_generation_includes_stable_variants():
    aliases = orchestrator_handler._crop_key_aliases('black gram')

    assert 'black gram' in aliases
    assert 'blackgram' in aliases
    assert 'black grams' in aliases


def test_tool_signal_guard_redirects_scheme_queries_to_authority_when_tool_not_used():
    guarded = orchestrator_handler._apply_tool_signal_response_guard(
        'Here are a few scheme details from general crop guidance.',
        'what schemes are available for drip irrigation?',
        tools_used=['get_crop_advisory'],
        tool_data_log=[
            {
                'tool': 'get_crop_advisory',
                'output': {
                    'data': {
                        'source_authority': 'govt_schemes',
                        'message': 'Please ask your scheme query and I will fetch it from the dedicated government schemes service.',
                    }
                },
            }
        ],
    )

    assert 'dedicated government schemes service' in guarded.lower()


def test_tool_signal_guard_does_not_redirect_when_scheme_tool_already_used():
    guarded = orchestrator_handler._apply_tool_signal_response_guard(
        'Eligible schemes include PM-KUSUM and state subsidy windows.',
        'show me irrigation subsidy schemes',
        tools_used=['get_crop_advisory', 'search_schemes'],
        tool_data_log=[
            {
                'tool': 'get_crop_advisory',
                'output': {
                    'data': {
                        'source_authority': 'govt_schemes',
                        'message': 'Redirect if schemes tool missing.',
                    }
                },
            }
        ],
    )

    assert 'eligible schemes include' in guarded.lower()


def test_tool_signal_guard_prefixes_when_insufficient_evidence_without_caution_markers():
    guarded = orchestrator_handler._apply_tool_signal_response_guard(
        'Rice and maize can be considered based on your area.',
        'suggest crops for this season',
        tools_used=['get_crop_advisory'],
        tool_data_log=[
            {
                'tool': 'get_crop_advisory',
                'output': {
                    'data': {
                        'insufficient_evidence': True,
                        'evidence_message': 'Retrieved evidence confidence is limited for this query.',
                    }
                },
            }
        ],
    )

    assert guarded.lower().startswith('retrieved evidence confidence is limited')


def test_tool_signal_guard_appends_staleness_warning_for_time_sensitive_query():
    guarded = orchestrator_handler._apply_tool_signal_response_guard(
        'You can apply in the announced window with required documents.',
        'is this year subsidy still active?',
        tools_used=['get_crop_advisory'],
        tool_data_log=[
            {
                'tool': 'get_crop_advisory',
                'output': {
                    'data': {
                        'freshness': {
                            'staleness_warning': 'Referenced year 2021 may be stale compared to current year 2026.'
                        }
                    }
                },
            }
        ],
    )

    assert 'note:' in guarded.lower()
    assert 'may be stale' in guarded.lower()


def test_normalize_translated_agri_terms_fixes_cardiff_to_kharif():
    text = 'Please provide your district so I can recommend crops for the Cardiff season.'

    normalized = orchestrator_handler._normalize_translated_agri_terms(text)

    assert 'cardiff' not in normalized.lower()
    assert 'kharif season' in normalized.lower()


def test_normalize_translated_agri_terms_keeps_unrelated_text_unchanged():
    text = 'Please provide your location for weather forecast in your area.'

    normalized = orchestrator_handler._normalize_translated_agri_terms(text)

    assert normalized == text


def test_resolve_reply_language_prefers_detected_for_mixed_session_switch():
    resolved = orchestrator_handler._resolve_reply_language(
        preferred_language='ta',
        detected_language='hi',
        raw_user_message='नमस्ते, मेरी फसल के लिए सुझाव दें',
    )

    assert resolved == 'hi'


def test_resolve_reply_language_uses_detected_without_preferred_language():
    resolved = orchestrator_handler._resolve_reply_language(
        preferred_language=None,
        detected_language='te',
        raw_user_message='నా పంటకు సూచనలు ఇవ్వండి',
    )

    assert resolved == 'te'


def test_post_process_response_normalizes_cardiff_season_term():
    text = 'Please provide your district so I can give you the best crop recommendation for the Cardiff season.'

    processed = orchestrator_handler._post_process_response(text)

    assert 'cardiff' not in processed.lower()
    assert 'kharif season' in processed.lower()
