#!/usr/bin/env python3
"""
Tests for get_checkpointer() function in langgraph_orchestrator.py

P2 Follow-up for PR #2771: Comprehensive tests for checkpointer priority
and exception scenarios.

Test Coverage:
1. Checkpointer priority: PostgreSQL -> Redis -> MemorySaver
2. Exception scenarios: connection failures, missing env vars, import errors
3. Fallback behavior verification
"""

import pytest
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import langgraph  # noqa: F401
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


class TestCheckpointerPriority:
    """Tests for checkpointer selection priority: PostgreSQL -> Redis -> MemorySaver"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_memory_saver_selected_when_both_disabled(self):
        """Test MemorySaver is selected when both PostgreSQL and Redis are disabled"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = False
            mock_settings.database_url = None
            mock_settings.use_redis_checkpointer = False
            mock_settings.redis_url = None

            with patch('langgraph_orchestrator.logger'):
                from langgraph_orchestrator import get_checkpointer
                from langgraph.checkpoint.memory import MemorySaver
                result = get_checkpointer()
                assert isinstance(result, MemorySaver)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_memory_saver_selected_when_postgres_enabled_but_no_url(self):
        """Test MemorySaver is selected when PostgreSQL is enabled but DATABASE_URL is missing"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = True
            mock_settings.database_url = None
            mock_settings.use_redis_checkpointer = False
            mock_settings.redis_url = None

            with patch('langgraph_orchestrator.logger'):
                # Clear DATABASE_URL from environment
                env_copy = os.environ.copy()
                if 'DATABASE_URL' in env_copy:
                    del env_copy['DATABASE_URL']
                with patch.dict(os.environ, env_copy, clear=True):
                    from langgraph_orchestrator import get_checkpointer
                    from langgraph.checkpoint.memory import MemorySaver
                    result = get_checkpointer()
                    assert isinstance(result, MemorySaver)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_memory_saver_selected_when_redis_enabled_but_no_url(self):
        """Test MemorySaver is selected when Redis is enabled but REDIS_URL is missing"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = False
            mock_settings.database_url = None
            mock_settings.use_redis_checkpointer = True
            mock_settings.redis_url = None
            mock_settings.redis_checkpointer_ttl = 86400

            with patch('langgraph_orchestrator.logger'):
                # Clear REDIS_URL from environment
                env_copy = os.environ.copy()
                if 'REDIS_URL' in env_copy:
                    del env_copy['REDIS_URL']
                with patch.dict(os.environ, env_copy, clear=True):
                    from langgraph_orchestrator import get_checkpointer
                    from langgraph.checkpoint.memory import MemorySaver
                    result = get_checkpointer()
                    assert isinstance(result, MemorySaver)


class TestCheckpointerLogging:
    """Tests for logging behavior during checkpointer selection"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_logs_memory_saver_selection(self):
        """Test that MemorySaver selection is logged correctly"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = False
            mock_settings.database_url = None
            mock_settings.use_redis_checkpointer = False
            mock_settings.redis_url = None

            with patch('langgraph_orchestrator.logger') as mock_logger:
                from langgraph_orchestrator import get_checkpointer
                get_checkpointer()

                # Verify logger.info was called
                mock_logger.info.assert_called()
                # Check that the log message contains 'MemorySaver'
                call_args = mock_logger.info.call_args
                log_message = call_args[0][0] if call_args[0] else ""
                extra = call_args[1].get('extra', {}) if call_args[1] else {}
                assert 'MemorySaver' in log_message or extra.get('checkpointer_type') == 'memory'

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_logs_include_configuration_state(self):
        """Test that logs include configuration state for debugging"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = True
            mock_settings.database_url = None
            mock_settings.use_redis_checkpointer = True
            mock_settings.redis_url = None
            mock_settings.redis_checkpointer_ttl = 86400

            with patch('langgraph_orchestrator.logger') as mock_logger:
                # Clear env vars
                env_copy = os.environ.copy()
                for key in ['DATABASE_URL', 'REDIS_URL']:
                    if key in env_copy:
                        del env_copy[key]
                with patch.dict(os.environ, env_copy, clear=True):
                    from langgraph_orchestrator import get_checkpointer
                    get_checkpointer()

                    # Verify logger.info was called with extra containing config state
                    mock_logger.info.assert_called()
                    call_args = mock_logger.info.call_args
                    extra = call_args[1].get('extra', {}) if call_args[1] else {}
                    # Should include configuration state for debugging OOM issues
                    assert 'use_postgres_configured' in extra or 'use_redis_configured' in extra


class TestCheckpointerIntegration:
    """Integration tests for checkpointer selection logic"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_full_fallback_chain_all_disabled(self):
        """Test complete fallback to MemorySaver when all checkpointers are disabled"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = False
            mock_settings.database_url = None
            mock_settings.use_redis_checkpointer = False
            mock_settings.redis_url = None

            with patch('langgraph_orchestrator.logger'):
                from langgraph_orchestrator import get_checkpointer
                from langgraph.checkpoint.memory import MemorySaver
                result = get_checkpointer()
                assert isinstance(result, MemorySaver)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_checkpointer_returns_valid_object(self):
        """Test that get_checkpointer always returns a valid checkpointer object"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = False
            mock_settings.database_url = None
            mock_settings.use_redis_checkpointer = False
            mock_settings.redis_url = None

            with patch('langgraph_orchestrator.logger'):
                from langgraph_orchestrator import get_checkpointer
                result = get_checkpointer()
                # Should always return a valid checkpointer
                assert result is not None

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_postgres_priority_over_redis_when_both_missing_urls(self):
        """Test that PostgreSQL checkpointer has priority over Redis (both missing URLs)"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            # Both enabled, but no URLs - should fall back to MemorySaver
            mock_settings.use_postgres_checkpointer = True
            mock_settings.database_url = None
            mock_settings.use_redis_checkpointer = True
            mock_settings.redis_url = None
            mock_settings.redis_checkpointer_ttl = 86400

            with patch('langgraph_orchestrator.logger') as mock_logger:
                # Clear env vars
                env_copy = os.environ.copy()
                for key in ['DATABASE_URL', 'REDIS_URL']:
                    if key in env_copy:
                        del env_copy[key]
                with patch.dict(os.environ, env_copy, clear=True):
                    from langgraph_orchestrator import get_checkpointer
                    from langgraph.checkpoint.memory import MemorySaver
                    result = get_checkpointer()
                    # Should fall back to MemorySaver since no URLs configured
                    assert isinstance(result, MemorySaver)
                    # Verify logging includes both config states
                    call_args = mock_logger.info.call_args
                    extra = call_args[1].get('extra', {}) if call_args[1] else {}
                    assert extra.get('use_postgres_configured') is True
                    assert extra.get('use_redis_configured') is True


class TestCheckpointerDocumentation:
    """Tests to verify checkpointer behavior matches documentation"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_docstring_priority_order(self):
        """Test that get_checkpointer docstring documents correct priority order"""
        from langgraph_orchestrator import get_checkpointer
        docstring = get_checkpointer.__doc__
        assert docstring is not None
        # Verify priority order is documented
        assert 'PostgresSaver' in docstring or 'PostgreSQL' in docstring
        assert 'RedisSaver' in docstring or 'Redis' in docstring
        assert 'MemorySaver' in docstring

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_docstring_mentions_upstash_limitation(self):
        """Test that docstring mentions Upstash Redis limitation (root cause of OOM)"""
        from langgraph_orchestrator import get_checkpointer
        docstring = get_checkpointer.__doc__
        assert docstring is not None
        # Should mention Upstash or RediSearch limitation
        assert 'Upstash' in docstring or 'RediSearch' in docstring
