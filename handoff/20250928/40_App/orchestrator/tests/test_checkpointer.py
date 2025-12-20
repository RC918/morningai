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


class TestCheckpointerSuccessPaths:
    """P3 Follow-up: Tests for successful checkpointer initialization paths"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_postgres_checkpointer_selected_when_configured(self):
        """Test PostgresSaver is selected when USE_POSTGRES_CHECKPOINTER=true and DATABASE_URL exists"""
        try:
            pytest.importorskip("langgraph.checkpoint.postgres")
        except pytest.skip.Exception:
            pytest.skip("langgraph-checkpoint-postgres not installed")

        from unittest.mock import MagicMock

        mock_pg_instance = MagicMock()
        mock_pg_class = MagicMock()
        mock_pg_class.from_conn_string.return_value = mock_pg_instance

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = True
            mock_settings.database_url = "postgresql://user:pass@localhost:5432/db"
            mock_settings.use_redis_checkpointer = False
            mock_settings.redis_url = None

            with patch('langgraph_orchestrator.logger'):
                with patch('langgraph.checkpoint.postgres.PostgresSaver', mock_pg_class):
                    from langgraph_orchestrator import get_checkpointer
                    result = get_checkpointer()

                    # Verify PostgresSaver was used
                    mock_pg_class.from_conn_string.assert_called_once()
                    mock_pg_instance.setup.assert_called_once()
                    assert result is mock_pg_instance

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_redis_checkpointer_selected_when_configured(self):
        """Test RedisSaver is selected when USE_REDIS_CHECKPOINTER=true and REDIS_URL exists"""
        try:
            pytest.importorskip("langgraph.checkpoint.redis")
        except pytest.skip.Exception:
            pytest.skip("langgraph-checkpoint-redis not installed")

        from unittest.mock import MagicMock

        mock_redis_instance = MagicMock()
        mock_redis_class = MagicMock(return_value=mock_redis_instance)

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = False
            mock_settings.database_url = None
            mock_settings.use_redis_checkpointer = True
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.redis_checkpointer_ttl = 86400

            with patch('langgraph_orchestrator.logger'):
                with patch('langgraph.checkpoint.redis.RedisSaver', mock_redis_class):
                    from langgraph_orchestrator import get_checkpointer
                    result = get_checkpointer()

                    # Verify RedisSaver was used
                    mock_redis_class.assert_called_once()
                    mock_redis_instance.setup.assert_called_once()
                    assert result is mock_redis_instance


class TestCheckpointerFallbackOnFailure:
    """P3 Follow-up: Tests for fallback behavior when checkpointer initialization fails"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_fallback_to_redis_when_postgres_connection_fails(self):
        """Test fallback to Redis when PostgreSQL connection fails"""
        try:
            pytest.importorskip("langgraph.checkpoint.postgres")
            pytest.importorskip("langgraph.checkpoint.redis")
        except pytest.skip.Exception:
            pytest.skip("langgraph-checkpoint-postgres or langgraph-checkpoint-redis not installed")

        from unittest.mock import MagicMock

        # PostgreSQL will fail on setup
        mock_pg_instance = MagicMock()
        mock_pg_instance.setup.side_effect = Exception("Connection refused")
        mock_pg_class = MagicMock()
        mock_pg_class.from_conn_string.return_value = mock_pg_instance

        # Redis will succeed
        mock_redis_instance = MagicMock()
        mock_redis_class = MagicMock(return_value=mock_redis_instance)

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = True
            mock_settings.database_url = "postgresql://user:pass@localhost:5432/db"
            mock_settings.use_redis_checkpointer = True
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.redis_checkpointer_ttl = 86400

            with patch('langgraph_orchestrator.logger') as mock_logger:
                with patch('langgraph.checkpoint.postgres.PostgresSaver', mock_pg_class):
                    with patch('langgraph.checkpoint.redis.RedisSaver', mock_redis_class):
                        from langgraph_orchestrator import get_checkpointer
                        result = get_checkpointer()

                        # Verify PostgreSQL was attempted and failed
                        mock_pg_class.from_conn_string.assert_called_once()
                        mock_pg_instance.setup.assert_called_once()

                        # Verify error was logged
                        mock_logger.error.assert_called()

                        # Verify Redis was used as fallback
                        mock_redis_class.assert_called_once()
                        mock_redis_instance.setup.assert_called_once()
                        assert result is mock_redis_instance

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_fallback_to_memory_when_redis_connection_fails(self):
        """Test fallback to MemorySaver when Redis connection fails (e.g., RediSearch not available)"""
        try:
            pytest.importorskip("langgraph.checkpoint.redis")
        except pytest.skip.Exception:
            pytest.skip("langgraph-checkpoint-redis not installed")

        from unittest.mock import MagicMock

        # Redis will fail on setup (simulating RediSearch not available - the OOM root cause)
        mock_redis_instance = MagicMock()
        mock_redis_instance.setup.side_effect = Exception("FT._LIST command not available")
        mock_redis_class = MagicMock(return_value=mock_redis_instance)

        # MemorySaver will be used as fallback
        mock_memory_instance = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = False
            mock_settings.database_url = None
            mock_settings.use_redis_checkpointer = True
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.redis_checkpointer_ttl = 86400

            with patch('langgraph_orchestrator.logger') as mock_logger:
                with patch('langgraph.checkpoint.redis.RedisSaver', mock_redis_class):
                    with patch('langgraph_orchestrator.MemorySaver', return_value=mock_memory_instance):
                        from langgraph_orchestrator import get_checkpointer
                        result = get_checkpointer()

                        # Verify Redis was attempted and failed
                        mock_redis_class.assert_called_once()
                        mock_redis_instance.setup.assert_called_once()

                        # Verify error was logged
                        mock_logger.error.assert_called()

                        # Verify MemorySaver was used as fallback
                        assert result is mock_memory_instance

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_fallback_chain_postgres_to_redis_to_memory(self):
        """Test complete fallback chain: PostgreSQL fails -> Redis fails -> MemorySaver"""
        try:
            pytest.importorskip("langgraph.checkpoint.postgres")
            pytest.importorskip("langgraph.checkpoint.redis")
        except pytest.skip.Exception:
            pytest.skip("langgraph-checkpoint-postgres or langgraph-checkpoint-redis not installed")

        from unittest.mock import MagicMock

        # PostgreSQL will fail
        mock_pg_instance = MagicMock()
        mock_pg_instance.setup.side_effect = Exception("PostgreSQL connection refused")
        mock_pg_class = MagicMock()
        mock_pg_class.from_conn_string.return_value = mock_pg_instance

        # Redis will also fail
        mock_redis_instance = MagicMock()
        mock_redis_instance.setup.side_effect = Exception("Redis connection refused")
        mock_redis_class = MagicMock(return_value=mock_redis_instance)

        # MemorySaver will be used as final fallback
        mock_memory_instance = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.use_postgres_checkpointer = True
            mock_settings.database_url = "postgresql://user:pass@localhost:5432/db"
            mock_settings.use_redis_checkpointer = True
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.redis_checkpointer_ttl = 86400

            with patch('langgraph_orchestrator.logger') as mock_logger:
                with patch('langgraph.checkpoint.postgres.PostgresSaver', mock_pg_class):
                    with patch('langgraph.checkpoint.redis.RedisSaver', mock_redis_class):
                        with patch('langgraph_orchestrator.MemorySaver', return_value=mock_memory_instance):
                            from langgraph_orchestrator import get_checkpointer
                            result = get_checkpointer()

                            # Verify both PostgreSQL and Redis were attempted
                            mock_pg_class.from_conn_string.assert_called_once()
                            mock_redis_class.assert_called_once()

                            # Verify errors were logged for both
                            assert mock_logger.error.call_count >= 2

                            # Verify MemorySaver was used as final fallback
                            assert result is mock_memory_instance
