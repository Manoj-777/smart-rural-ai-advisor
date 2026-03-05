"""
Bug 1.1 Unit Tests: Flag ON - Verify Timeout Protection

**Validates: Requirements 3.1**

This test suite verifies that when ENABLE_TIMEOUT_PROTECTION flag is ON,
the system correctly detects approaching timeouts and returns graceful fallback responses.

Test Coverage:
- Mock context.get_remaining_time_in_millis() to return 4000ms (approaching timeout)
- Verify _check_timeout_approaching() returns True
- Verify _timeout_fallback_response() is called
- Verify response includes timeout_fallback: true

Requirement 3.1: When feature flags are ON, system activates new timeout protection logic
"""

import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock missing modules before importing handler
sys.modules['utils.chat_history'] = MagicMock()
sys.modules['utils.response_cache'] = MagicMock()

# Import the handler module
import lambdas.agent_orchestrator.handler as handler
from lambdas.agent_orchestrator.handler import (
    _timeout_fallback_response,
    _check_timeout_approaching
)


class TestBug11UnitFlagOn:
    """
    Unit Tests for Bug 1.1: Verify timeout protection when flag is ON
    
    These tests verify that with ENABLE_TIMEOUT_PROTECTION='true',
    the timeout protection logic correctly detects approaching timeouts
    and returns graceful fallback responses.
    
    Test Strategy:
    - Mock context.get_remaining_time_in_millis() to return 4000ms (approaching)
    - Verify _check_timeout_approaching() returns True
    - Verify _timeout_fallback_response() returns correct structure
    - Verify response includes timeout_fallback: true flag
    """
    
    def _create_mock_context(self, remaining_time_ms):
        """Helper to create a mock Lambda context with specified remaining time."""
        mock_context = Mock()
        mock_context.get_remaining_time_in_millis.return_value = remaining_time_ms
        mock_context.aws_request_id = 'test-request-123'
        mock_context.function_name = "test-agent-orchestrator"
        mock_context.invoked_function_arn = "arn:aws:lambda:ap-south-1:123456789012:function:test"
        return mock_context
    
    @patch.dict(os.environ, {'ENABLE_TIMEOUT_PROTECTION': 'true', 'TIMEOUT_BUFFER_MS': '5000'})
    def test_check_timeout_approaching_returns_true_when_time_low(self):
        """
        Test that _check_timeout_approaching() returns True when remaining time < buffer.
        
        Given: ENABLE_TIMEOUT_PROTECTION='true', TIMEOUT_BUFFER_MS='5000'
        When: context.get_remaining_time_in_millis() returns 4000ms
        Then: _check_timeout_approaching() returns (True, 4000)
        """
        # Arrange
        mock_context = self._create_mock_context(remaining_time_ms=4000)
        
        # Act
        is_approaching, remaining_ms = _check_timeout_approaching(mock_context)
        
        # Assert
        assert is_approaching is True, "Expected timeout to be approaching when remaining time < buffer"
        assert remaining_ms == 4000, f"Expected remaining_ms=4000, got {remaining_ms}"
        mock_context.get_remaining_time_in_millis.assert_called_once()
    
    @patch.dict(os.environ, {'ENABLE_TIMEOUT_PROTECTION': 'true', 'TIMEOUT_BUFFER_MS': '5000'})
    def test_check_timeout_approaching_returns_false_when_time_sufficient(self):
        """
        Test that _check_timeout_approaching() returns False when remaining time >= buffer.
        
        Given: ENABLE_TIMEOUT_PROTECTION='true', TIMEOUT_BUFFER_MS='5000'
        When: context.get_remaining_time_in_millis() returns 10000ms
        Then: _check_timeout_approaching() returns (False, 10000)
        """
        # Arrange
        mock_context = self._create_mock_context(remaining_time_ms=10000)
        
        # Act
        is_approaching, remaining_ms = _check_timeout_approaching(mock_context)
        
        # Assert
        assert is_approaching is False, "Expected timeout NOT to be approaching when remaining time >= buffer"
        assert remaining_ms == 10000, f"Expected remaining_ms=10000, got {remaining_ms}"
    
    @patch.dict(os.environ, {'ENABLE_TIMEOUT_PROTECTION': 'true', 'TIMEOUT_BUFFER_MS': '5000'})
    def test_check_timeout_approaching_boundary_condition(self):
        """
        Test boundary condition: exactly at buffer threshold.
        
        Given: ENABLE_TIMEOUT_PROTECTION='true', TIMEOUT_BUFFER_MS='5000'
        When: context.get_remaining_time_in_millis() returns 5000ms (exactly at threshold)
        Then: _check_timeout_approaching() returns (False, 5000) - not approaching yet
        """
        # Arrange
        mock_context = self._create_mock_context(remaining_time_ms=5000)
        
        # Act
        is_approaching, remaining_ms = _check_timeout_approaching(mock_context)
        
        # Assert
        assert is_approaching is False, "Expected timeout NOT approaching at exact threshold"
        assert remaining_ms == 5000
    
    @patch.dict(os.environ, {'ENABLE_TIMEOUT_PROTECTION': 'true', 'TIMEOUT_BUFFER_MS': '5000'})
    def test_check_timeout_approaching_very_low_time(self):
        """
        Test extreme case: very low remaining time (1 second).
        
        Given: ENABLE_TIMEOUT_PROTECTION='true', TIMEOUT_BUFFER_MS='5000'
        When: context.get_remaining_time_in_millis() returns 1000ms
        Then: _check_timeout_approaching() returns (True, 1000)
        """
        # Arrange
        mock_context = self._create_mock_context(remaining_time_ms=1000)
        
        # Act
        is_approaching, remaining_ms = _check_timeout_approaching(mock_context)
        
        # Assert
        assert is_approaching is True, "Expected timeout approaching with only 1s remaining"
        assert remaining_ms == 1000
    
    def test_timeout_fallback_response_structure_english(self):
        """
        Test that _timeout_fallback_response() returns correct structure for English.
        
        Given: language='en'
        When: _timeout_fallback_response('en') is called
        Then: Returns dict with 'reply', 'audio_url': None, 'timeout_fallback': True
        """
        # Act
        response = _timeout_fallback_response(language='en')
        
        # Assert
        assert isinstance(response, dict), "Expected response to be a dict"
        assert 'reply' in response, "Expected 'reply' key in response"
        assert 'audio_url' in response, "Expected 'audio_url' key in response"
        assert 'timeout_fallback' in response, "Expected 'timeout_fallback' key in response"
        
        assert response['timeout_fallback'] is True, "Expected timeout_fallback=True"
        assert response['audio_url'] is None, "Expected audio_url=None for timeout fallback"
        assert isinstance(response['reply'], str), "Expected reply to be a string"
        assert len(response['reply']) > 0, "Expected non-empty reply message"
    
    def test_timeout_fallback_response_structure_hindi(self):
        """
        Test that _timeout_fallback_response() returns correct structure for Hindi.
        
        Given: language='hi'
        When: _timeout_fallback_response('hi') is called
        Then: Returns dict with Hindi message and timeout_fallback: True
        """
        # Act
        response = _timeout_fallback_response(language='hi')
        
        # Assert
        assert response['timeout_fallback'] is True
        assert response['audio_url'] is None
        assert isinstance(response['reply'], str)
        assert len(response['reply']) > 0
        # Verify it contains Hindi characters (Devanagari script)
        assert any('\u0900' <= char <= '\u097F' for char in response['reply']), \
            "Expected Hindi (Devanagari) characters in response"
    
    def test_timeout_fallback_response_default_language(self):
        """
        Test that _timeout_fallback_response() defaults to English for unknown languages.
        
        Given: language='unknown'
        When: _timeout_fallback_response('unknown') is called
        Then: Returns English message with timeout_fallback: True
        """
        # Act
        response = _timeout_fallback_response(language='unknown')
        
        # Assert
        assert response['timeout_fallback'] is True
        assert response['audio_url'] is None
        assert 'longer than expected' in response['reply'].lower(), \
            "Expected English fallback message"
    
    def test_timeout_fallback_response_no_language_parameter(self):
        """
        Test that _timeout_fallback_response() works with default parameter.
        
        Given: No language parameter
        When: _timeout_fallback_response() is called
        Then: Returns English message (default)
        """
        # Act
        response = _timeout_fallback_response()
        
        # Assert
        assert response['timeout_fallback'] is True
        assert response['audio_url'] is None
        assert isinstance(response['reply'], str)
        assert len(response['reply']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
