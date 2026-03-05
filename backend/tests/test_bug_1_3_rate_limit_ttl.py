"""
Bug 1.3 Unit Tests: Rate limiter TTL attribute gating.

Validates:
- ENABLE_RATE_LIMIT_TTL=true includes ttl_epoch in update expressions
- ENABLE_RATE_LIMIT_TTL=false preserves legacy update shape (no ttl_epoch)
"""

import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import rate_limiter as shared_rl
from lambdas.agent_orchestrator.utils import rate_limiter as local_rl


def _assert_ttl_gating(module):
    with patch.dict(os.environ, {'ENABLE_RATE_LIMIT_TTL': 'true'}):
        module.ENABLE_RATE_LIMIT_TTL = True
        expr, attrs = module._rate_update_parts(123, '2026-01-01T00:00:00')
        assert 'ttl_epoch = :ttl' in expr
        assert attrs[':ttl'] == 123

    with patch.dict(os.environ, {'ENABLE_RATE_LIMIT_TTL': 'false'}):
        module.ENABLE_RATE_LIMIT_TTL = False
        expr, attrs = module._rate_update_parts(123, '2026-01-01T00:00:00')
        assert 'ttl_epoch = :ttl' not in expr
        assert ':ttl' not in attrs


def test_shared_rate_limiter_ttl_flag_gates_update_expression():
    _assert_ttl_gating(shared_rl)


def test_local_rate_limiter_ttl_flag_gates_update_expression():
    _assert_ttl_gating(local_rl)
