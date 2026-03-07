"""
Bug 1.8 Unit Tests: Profile cache thread safety.

Validates:
- Requirement 2.8 (profile cache reads/writes are lock-protected)
- Existing TTL cache behavior remains intact
"""

import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import dynamodb_helper


class _RaceDetectingCache(dict):
    """Dictionary-like cache that counts overlapping method entry."""

    def __init__(self):
        super().__init__()
        self._in_critical = False
        self.collision_count = 0

    def _enter(self):
        if self._in_critical:
            self.collision_count += 1
        self._in_critical = True

    def _exit(self):
        self._in_critical = False

    def get(self, key, default=None):
        self._enter()
        try:
            time.sleep(0.001)
            return super().get(key, default)
        finally:
            self._exit()

    def __setitem__(self, key, value):
        self._enter()
        try:
            time.sleep(0.001)
            return super().__setitem__(key, value)
        finally:
            self._exit()


def test_profile_cache_concurrent_access_is_lock_protected():
    race_cache = _RaceDetectingCache()
    fake_item = {'farmer_id': 'f-100', 'name': 'Thread Safe Farmer'}

    with patch.dict(os.environ, {'ENABLE_PROFILE_CACHE': 'true', 'PROFILE_CACHE_TTL_SEC': '120'}):
        with patch.object(dynamodb_helper, '_profile_cache', race_cache):
            with patch.object(dynamodb_helper, 'profiles_table') as mock_table:
                mock_table.get_item.return_value = {'Item': fake_item}

                def _read_profile():
                    return dynamodb_helper.get_farmer_profile('f-100')

                with ThreadPoolExecutor(max_workers=16) as executor:
                    futures = [executor.submit(_read_profile) for _ in range(80)]
                    for future in futures:
                        assert future.result() == fake_item

    assert race_cache.collision_count == 0


def test_profile_cache_ttl_behavior_preserved():
    fake_item = {'farmer_id': 'f-200', 'name': 'TTL Farmer'}

    with patch.dict(os.environ, {'ENABLE_PROFILE_CACHE': 'true', 'PROFILE_CACHE_TTL_SEC': '120'}):
        with patch.object(dynamodb_helper, '_profile_cache', {}):
            with patch.object(dynamodb_helper, 'profiles_table') as mock_table:
                mock_table.get_item.return_value = {'Item': fake_item}

                with patch('utils.dynamodb_helper._time.time', return_value=1000.0):
                    first = dynamodb_helper.get_farmer_profile('f-200')

                with patch('utils.dynamodb_helper._time.time', return_value=1001.0):
                    second = dynamodb_helper.get_farmer_profile('f-200')

                with patch('utils.dynamodb_helper._time.time', return_value=1125.0):
                    third = dynamodb_helper.get_farmer_profile('f-200')

    assert first == fake_item
    assert second == fake_item
    assert third == fake_item
    assert mock_table.get_item.call_count == 2
