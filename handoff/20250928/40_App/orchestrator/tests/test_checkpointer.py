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
    """P3 Follow-up: Tests for successful checkpointer initialization paths

    Note (Dec 2025): Connection Pooling Architecture Change
    - PostgreSQL checkpointer now uses postgres_checkpointer_context() for proper connection lifecycle
    - get_checkpointer() only handles Redis/Memory checkpointers to prevent connection leaks
    """

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_postgres_checkpointer_context_returns_checkpointer(self):
        """Test postgres_checkpointer_context() returns ResilientPostgresSaver wrapper

        Note (Dec 2025): PostgreSQL checkpointer now uses:
        1. Per-operation connection borrowing (PostgresSaver receives pool directly)
        2. ResilientPostgresSaver wrapper for auto-retry on transient errors

        Architecture change (Issue #2968):
        - OLD: PostgresSaver(pool) - no retry on transient errors
        - NEW: ResilientPostgresSaver(PostgresSaver(pool)) - auto-retry with backoff

        This test verifies:
        1. The returned checkpointer is a ResilientPostgresSaver wrapper
        2. The wrapper's inner saver is PostgresSaver initialized with the pool
        3. PostgresSaver.setup() is called during initialization
        """
        try:
            pytest.importorskip("langgraph.checkpoint.postgres")
            pytest.importorskip("psycopg_pool")
        except pytest.skip.Exception:
            pytest.skip("langgraph-checkpoint-postgres or psycopg_pool not installed")

        from unittest.mock import MagicMock

        mock_pg_instance = MagicMock()
        mock_pg_class = MagicMock(return_value=mock_pg_instance)

        # Create a mock pool - this is what gets passed to PostgresSaver now
        mock_pool = MagicMock()
        # Mock get_stats() for logging
        mock_stats = MagicMock()
        mock_stats.pool_size = 5
        mock_stats.pool_available = 4
        mock_pool.get_stats.return_value = mock_stats

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.database_url = "postgresql://user:pass@localhost:5432/db"

            with patch('langgraph_orchestrator.logger'):
                with patch('langgraph_orchestrator._get_postgres_pool', return_value=mock_pool):
                    with patch('langgraph.checkpoint.postgres.PostgresSaver', mock_pg_class):
                        from langgraph_orchestrator import (
                            postgres_checkpointer_context,
                            ResilientPostgresSaver,
                        )

                        with postgres_checkpointer_context() as checkpointer:
                            # Verify PostgresSaver was instantiated with the POOL (not connection)
                            # This is the critical change: per-operation connection borrowing
                            mock_pg_class.assert_called_once_with(mock_pool)
                            mock_pg_instance.setup.assert_called_once()

                            # Issue #2968: Verify the returned checkpointer is wrapped
                            # with ResilientPostgresSaver for auto-retry on transient errors
                            assert isinstance(checkpointer, ResilientPostgresSaver), \
                                "Expected ResilientPostgresSaver wrapper for transient error handling"

                            # Verify the wrapper contains the correct inner PostgresSaver
                            assert checkpointer._inner is mock_pg_instance, \
                                "ResilientPostgresSaver should wrap the PostgresSaver instance"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_postgres_checkpointer_context_returns_none_when_pool_unavailable(self):
        """Test postgres_checkpointer_context() yields None when pool is unavailable"""
        with patch('langgraph_orchestrator.logger'):
            with patch('langgraph_orchestrator._get_postgres_pool', return_value=None):
                from langgraph_orchestrator import postgres_checkpointer_context

                with postgres_checkpointer_context() as checkpointer:
                    assert checkpointer is None

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
    """P3 Follow-up: Tests for fallback behavior when checkpointer initialization fails

    Note (Dec 2025): Connection Pooling Architecture Change
    - get_checkpointer() now only handles Redis/Memory checkpointers
    - PostgreSQL checkpointer uses postgres_checkpointer_context() for proper connection lifecycle
    - This prevents connection leaks that caused health check timeouts
    """

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_postgres_configured_falls_back_to_redis(self):
        """Test that when PostgreSQL is configured, get_checkpointer() falls back to Redis

        Note (Dec 2025): get_checkpointer() no longer attempts PostgreSQL connections directly.
        PostgreSQL checkpointer should be used via postgres_checkpointer_context() instead.
        When PostgreSQL is configured but get_checkpointer() is called, it logs a message
        and falls back to Redis if available.
        """
        try:
            pytest.importorskip("langgraph.checkpoint.redis")
        except pytest.skip.Exception:
            pytest.skip("langgraph-checkpoint-redis not installed")

        from unittest.mock import MagicMock

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
                with patch('langgraph.checkpoint.redis.RedisSaver', mock_redis_class):
                    from langgraph_orchestrator import get_checkpointer
                    result = get_checkpointer()

                    # Verify info was logged about PostgreSQL being configured
                    mock_logger.info.assert_called()

                    # Verify Redis was used (since get_checkpointer skips PostgreSQL)
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
    def test_postgres_configured_redis_fails_falls_back_to_memory(self):
        """Test fallback chain when PostgreSQL configured and Redis fails -> MemorySaver

        Note (Dec 2025): Connection Pooling Architecture Change
        - get_checkpointer() no longer attempts PostgreSQL connections directly
        - PostgreSQL checkpointer should be used via postgres_checkpointer_context()
        - When PostgreSQL is configured and Redis fails, get_checkpointer() falls back to MemorySaver
        """
        try:
            pytest.importorskip("langgraph.checkpoint.redis")
        except pytest.skip.Exception:
            pytest.skip("langgraph-checkpoint-redis not installed")

        from unittest.mock import MagicMock

        # Redis will fail
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
                with patch('langgraph.checkpoint.redis.RedisSaver', mock_redis_class):
                    with patch('langgraph_orchestrator.MemorySaver', return_value=mock_memory_instance):
                        from langgraph_orchestrator import get_checkpointer
                        result = get_checkpointer()

                        # Verify info was logged about PostgreSQL being configured
                        mock_logger.info.assert_called()

                        # Verify Redis was attempted and failed
                        mock_redis_class.assert_called_once()
                        mock_redis_instance.setup.assert_called_once()

                        # Verify error was logged for Redis failure
                        mock_logger.error.assert_called()

                        # Verify MemorySaver was used as final fallback
                        assert result is mock_memory_instance


class TestResilientPostgresSaver:
    """Tests for ResilientPostgresSaver retry mechanism (Issue #2968)

    These tests verify:
    1. Transient errors trigger retry with exponential backoff
    2. Non-transient errors are raised immediately without retry
    3. Max retries limit is respected
    4. Sleep delays follow exponential backoff pattern
    5. Final exception is propagated after all retries exhausted
    """

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_transient_error_triggers_retry(self):
        """Test that transient errors trigger retry with exponential backoff"""
        from unittest.mock import MagicMock, call

        # Import ResilientPostgresSaver
        from langgraph_orchestrator import ResilientPostgresSaver

        # Create mock inner saver that fails twice then succeeds
        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("SSL connection has been closed unexpectedly"),
            Exception("the connection is closed"),
            {"checkpoint": "data"},  # Success on third attempt
        ]

        # Create wrapper with known parameters
        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        # Mock time.sleep to avoid actual delays
        with patch('langgraph_orchestrator.time.sleep') as mock_sleep:
            with patch('langgraph_orchestrator.logger'):
                result = wrapper.get({"config": "test"})

        # Verify result
        assert result == {"checkpoint": "data"}

        # Verify inner.get was called 3 times (2 failures + 1 success)
        assert mock_inner.get.call_count == 3

        # Verify sleep was called with exponential backoff (0.5, 1.0)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(0.5), call(1.0)])

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_non_transient_error_raises_immediately(self):
        """Test that non-transient errors are raised without retry"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        # Create mock inner saver that fails with non-transient error
        mock_inner = MagicMock()
        mock_inner.put.side_effect = Exception("syntax error at or near SELECT")

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        with patch('langgraph_orchestrator.time.sleep') as mock_sleep:
            with patch('langgraph_orchestrator.logger'):
                with pytest.raises(Exception) as exc_info:
                    wrapper.put({"config": "test"}, {}, {}, {})

        # Verify error message
        assert "syntax error" in str(exc_info.value)

        # Verify inner.put was called only once (no retry for non-transient)
        assert mock_inner.put.call_count == 1

        # Verify sleep was never called
        mock_sleep.assert_not_called()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_max_retries_exhausted_raises_last_exception(self):
        """Test that after max retries, the last exception is raised"""
        from unittest.mock import MagicMock, call

        from langgraph_orchestrator import ResilientPostgresSaver

        # Create mock inner saver that always fails with transient error
        mock_inner = MagicMock()
        mock_inner.get_tuple.side_effect = Exception("connection reset by peer")

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        with patch('langgraph_orchestrator.time.sleep') as mock_sleep:
            with patch('langgraph_orchestrator.logger'):
                with pytest.raises(Exception) as exc_info:
                    wrapper.get_tuple({"config": "test"})

        # Verify the last exception is raised
        assert "connection reset by peer" in str(exc_info.value)

        # Verify inner.get_tuple was called max_retries + 1 times (4 total)
        assert mock_inner.get_tuple.call_count == 4

        # Verify sleep was called 3 times with exponential backoff
        assert mock_sleep.call_count == 3
        mock_sleep.assert_has_calls([call(0.5), call(1.0), call(2.0)])

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pipeline_bad_error_triggers_retry(self):
        """Test that Pipeline [BAD] errors trigger retry"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.put_writes.side_effect = [
            Exception("psycopg.Pipeline [BAD] state"),
            None,  # Success on second attempt
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        with patch('langgraph_orchestrator.time.sleep') as mock_sleep:
            with patch('langgraph_orchestrator.logger'):
                wrapper.put_writes({"config": "test"}, [], "task_id")

        # Verify retry occurred
        assert mock_inner.put_writes.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_transient_error_patterns_coverage(self):
        """Test that all documented transient error patterns are recognized"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        # Create a wrapper instance to test _is_transient_error
        mock_inner = MagicMock()
        wrapper = ResilientPostgresSaver(inner_saver=mock_inner)

        # All these should be recognized as transient
        transient_errors = [
            Exception("SSL connection has been closed unexpectedly"),
            Exception("the connection is closed"),
            Exception("connection is closed"),
            Exception("server closed the connection unexpectedly"),
            Exception("connection reset by peer"),
            Exception("connection timed out"),
            Exception("could not connect to server: Connection refused"),
            Exception("consuming input failed: SSL error"),
            Exception("psycopg.Pipeline [BAD] state"),
            # PR #3104: Pool closed patterns for race condition fix
            Exception("pool is closed"),
            Exception("pool is already closed"),  # Exact pattern match
            Exception("the pool 'pool-1' is already closed"),  # Compound check match
        ]

        for error in transient_errors:
            assert wrapper._is_transient_error(error), \
                f"Expected '{error}' to be recognized as transient"

        # These should NOT be recognized as transient
        non_transient_errors = [
            Exception("syntax error at or near"),
            Exception("permission denied for table"),
            Exception("duplicate key value violates unique constraint"),
            Exception("authentication failed"),
        ]

        for error in non_transient_errors:
            assert not wrapper._is_transient_error(error), \
                f"Expected '{error}' to NOT be recognized as transient"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_getattr_delegates_to_inner(self):
        """Test that __getattr__ delegates unknown attributes to inner saver"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.some_custom_attribute = "custom_value"
        mock_inner.some_custom_method.return_value = "method_result"

        wrapper = ResilientPostgresSaver(inner_saver=mock_inner)

        # Verify attribute delegation
        assert wrapper.some_custom_attribute == "custom_value"

        # Verify method delegation
        assert wrapper.some_custom_method() == "method_result"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_setup_with_retry(self):
        """Test that setup() also has retry logic"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.setup.side_effect = [
            Exception("connection timed out"),
            None,  # Success on second attempt
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        with patch('langgraph_orchestrator.time.sleep') as mock_sleep:
            with patch('langgraph_orchestrator.logger'):
                wrapper.setup()

        # Verify retry occurred
        assert mock_inner.setup.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_list_with_retry(self):
        """Test that list() has retry logic with keyword arguments"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.list.side_effect = [
            Exception("SSL connection has been closed"),
            [{"checkpoint": 1}, {"checkpoint": 2}],  # Success
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        with patch('langgraph_orchestrator.time.sleep') as mock_sleep:
            with patch('langgraph_orchestrator.logger'):
                result = wrapper.list(
                    {"config": "test"},
                    filter={"key": "value"},
                    before=None,
                    limit=10,
                )

        # Verify result
        assert result == [{"checkpoint": 1}, {"checkpoint": 2}]

        # Verify retry occurred
        assert mock_inner.list.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_circuit_breaker_opens_after_threshold_failures(self):
        """Test that circuit breaker opens after consecutive failures reach threshold"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import (
            ResilientPostgresSaver,
            ResilientPostgresSaverCircuitOpen,
        )

        mock_inner = MagicMock()
        # Always fail with transient error
        mock_inner.get.side_effect = Exception("SSL connection has been closed")

        # Use threshold of 2 for faster testing
        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=0,  # No retries, fail immediately
            base_delay=0.1,
            circuit_breaker_threshold=2,
        )

        with patch('langgraph_orchestrator.time.sleep'):
            with patch('langgraph_orchestrator.logger'):
                # First failure - circuit still closed
                with pytest.raises(Exception, match="SSL connection"):
                    wrapper.get({"config": "test1"})
                assert wrapper._consecutive_failures == 1
                assert wrapper._circuit_open is False

                # Second failure - circuit opens
                with pytest.raises(Exception, match="SSL connection"):
                    wrapper.get({"config": "test2"})
                assert wrapper._consecutive_failures == 2
                assert wrapper._circuit_open is True

                # Third call - circuit is open, should fail fast
                with pytest.raises(ResilientPostgresSaverCircuitOpen) as exc_info:
                    wrapper.get({"config": "test3"})
                assert "Circuit breaker open" in str(exc_info.value)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_circuit_breaker_resets_on_success(self):
        """Test that consecutive failure counter resets on successful operation"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        # First call fails, second succeeds
        mock_inner.get.side_effect = [
            Exception("SSL connection has been closed"),
            {"checkpoint": "data"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=0,  # No retries
            base_delay=0.1,
            circuit_breaker_threshold=3,
        )

        with patch('langgraph_orchestrator.time.sleep'):
            with patch('langgraph_orchestrator.logger'):
                # First call fails
                with pytest.raises(Exception, match="SSL connection"):
                    wrapper.get({"config": "test1"})
                assert wrapper._consecutive_failures == 1

                # Second call succeeds - counter should reset
                result = wrapper.get({"config": "test2"})
                assert result == {"checkpoint": "data"}
                assert wrapper._consecutive_failures == 0
                assert wrapper._circuit_open is False

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_circuit_breaker_no_operation_when_open(self):
        """Test that no DB operation is attempted when circuit is open"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import (
            ResilientPostgresSaver,
            ResilientPostgresSaverCircuitOpen,
        )

        mock_inner = MagicMock()

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.1,
            circuit_breaker_threshold=2,
        )

        # Manually open the circuit
        wrapper._circuit_open = True
        wrapper._consecutive_failures = 2

        with patch('langgraph_orchestrator.logger'):
            with pytest.raises(ResilientPostgresSaverCircuitOpen):
                wrapper.get({"config": "test"})

        # Verify inner saver was never called
        mock_inner.get.assert_not_called()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_circuit_breaker_threshold_configurable(self):
        """Test that circuit breaker threshold can be configured"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = Exception("SSL connection has been closed")

        # Use high threshold
        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=0,
            base_delay=0.1,
            circuit_breaker_threshold=5,
        )

        with patch('langgraph_orchestrator.time.sleep'):
            with patch('langgraph_orchestrator.logger'):
                # 4 failures - circuit should still be closed
                for i in range(4):
                    with pytest.raises(Exception, match="SSL connection"):
                        wrapper.get({"config": f"test{i}"})

                assert wrapper._consecutive_failures == 4
                assert wrapper._circuit_open is False

                # 5th failure - circuit should open
                with pytest.raises(Exception, match="SSL connection"):
                    wrapper.get({"config": "test5"})

                assert wrapper._consecutive_failures == 5
                assert wrapper._circuit_open is True

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_circuit_breaker_exception_inherits_database_exception(self):
        """Test that ResilientPostgresSaverCircuitOpen inherits from DatabaseException"""
        from langgraph_orchestrator import ResilientPostgresSaverCircuitOpen
        from exceptions import DatabaseException

        # Verify inheritance
        assert issubclass(ResilientPostgresSaverCircuitOpen, DatabaseException)

        # Verify exception can be caught as DatabaseException
        try:
            raise ResilientPostgresSaverCircuitOpen("Test error")
        except DatabaseException as e:
            assert "Test error" in str(e)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_is_closed_error_triggers_retry(self):
        """Test that 'pool is closed' error triggers retry (PR #3104 fix)

        This test verifies the fix for the production incident where pool reset
        races with checkpoint operations, causing 'pool is closed' errors that
        were incorrectly classified as non-transient.
        """
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.put.side_effect = [
            Exception("pool is closed"),
            None,  # Success on second attempt
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        with patch('langgraph_orchestrator.time.sleep') as mock_sleep:
            with patch('langgraph_orchestrator.logger'):
                wrapper.put({"config": "test"}, {}, {}, {})

        # Verify retry occurred
        assert mock_inner.put.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_is_already_closed_error_triggers_retry(self):
        """Test that 'pool is already closed' error triggers retry (PR #3104 fix)

        This test verifies the fix for the production error message:
        "the pool 'pool-1' is already closed"
        """
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("the pool 'pool-1' is already closed"),
            {"checkpoint": "data"},  # Success on second attempt
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        with patch('langgraph_orchestrator.time.sleep') as mock_sleep:
            with patch('langgraph_orchestrator.logger'):
                result = wrapper.get({"config": "test"})

        # Verify result
        assert result == {"checkpoint": "data"}

        # Verify retry occurred
        assert mock_inner.get.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_closed_compound_check_avoids_false_positives(self):
        """Test that _is_pool_closed_with_name() compound check avoids false positives

        This test ensures the compound check requires BOTH "the pool '" prefix
        AND "' is closed" / "' is already closed" suffix to match.
        This prevents misclassifying errors from other resources as pool errors.

        Assumption: Only psycopg_pool errors with format "the pool '<name>' is [already] closed"
        should be matched by this helper. Other quote/format variants are tracked in #3117.

        Note: This test specifically tests _is_pool_closed_with_name(), NOT _is_transient_error().
        Some of these error strings (e.g., "connection is closed") ARE transient errors via
        other patterns in TRANSIENT_ERROR_PATTERNS, but they should NOT match the pool-closed
        compound check.
        """
        from langgraph_orchestrator import ResilientPostgresSaver

        # These should NOT match the pool-closed compound check
        # They test various false positive scenarios for _is_pool_closed_with_name()
        non_pool_error_strings = [
            # Generic "is already closed" without pool prefix
            "connection is already closed",
            "file handle is already closed",
            "socket is already closed",
            # Generic "is closed" without pool prefix
            "connection is closed",
            "file 'foo' is closed",
            "resource is closed",
            # Pool-like but missing proper format
            "the pool is closed",  # Missing pool name in quotes
            "pool 'pool-1' is closed",  # Missing "the " prefix
            'the pool "pool-1" is closed',  # Double quotes instead of single
            # Partial matches that should not trigger
            "the pool 'pool-1' was closed",  # Different verb tense
            "closing the pool 'pool-1'",  # Different phrasing
        ]

        for error_str in non_pool_error_strings:
            result = ResilientPostgresSaver._is_pool_closed_with_name(error_str.lower())
            assert not result, \
                f"Error '{error_str}' should NOT match pool-closed compound check"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_closed_compound_check_matches_valid_patterns(self):
        """Test that _is_pool_closed_with_name() matches valid pool-closed patterns

        This test ensures the compound check correctly identifies both variants:
        1. "the pool '<name>' is closed"
        2. "the pool '<name>' is already closed"
        """
        from langgraph_orchestrator import ResilientPostgresSaver

        # These SHOULD match the pool-closed compound check
        valid_pool_error_strings = [
            # Standard format - "is closed" variant
            "the pool 'pool-1' is closed",
            "the pool 'my-pool' is closed",
            # Standard format - "is already closed" variant
            "the pool 'pool-1' is already closed",
            "the pool 'my-pool' is already closed",
            # Special characters in pool name
            "the pool 'pool-with-dashes-123' is closed",
            "the pool 'pool_with_underscores' is already closed",
        ]

        for error_str in valid_pool_error_strings:
            result = ResilientPostgresSaver._is_pool_closed_with_name(error_str.lower())
            assert result, \
                f"Error '{error_str}' SHOULD match pool-closed compound check"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_closed_with_special_characters_in_name(self):
        """Test that pool closed errors with special characters in pool name are matched

        This test ensures the compound check handles edge cases where pool names
        contain special characters, Unicode, or unusual formatting.
        """
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        special_pool_name_errors = [
            Exception("the pool 'pool-with-dashes-123' is already closed"),
            Exception("the pool 'pool_with_underscores' is already closed"),
            Exception("the pool 'pool.with.dots' is already closed"),
            Exception("the pool 'pool:with:colons' is already closed"),
            Exception("the pool 'pool/with/slashes' is already closed"),
            Exception("the pool 'pool@special#chars!' is already closed"),
            Exception("the pool 'unicode-pool' is already closed"),
        ]

        for error in special_pool_name_errors:
            assert wrapper._is_transient_error(error), \
                f"Error '{error}' should be classified as transient"
            error_str = str(error).lower()
            assert wrapper._is_connection_lost_error(error_str), \
                f"Error '{error}' should trigger pool reset"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_is_closed_variant_triggers_retry(self):
        """Test that 'the pool is closed' variant (without 'already') triggers retry

        This test verifies the fix for the production error message observed in Sentry:
        "the pool 'pool-1' is closed" (different from "is already closed")

        psycopg_pool emits two different error formats:
        1. "the pool 'pool-1' is closed" - PoolClosed exception
        2. "the pool 'pool-1' is already closed" - PoolClosed exception (different code path)
        """
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("the pool 'pool-1' is closed"),  # Note: "is closed" not "is already closed"
            {"checkpoint": "data"},  # Success on second attempt
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        with patch('langgraph_orchestrator.time.sleep') as mock_sleep:
            with patch('langgraph_orchestrator.logger'):
                result = wrapper.get({"config": "test"})

        # Verify result
        assert result == {"checkpoint": "data"}

        # Verify retry occurred
        assert mock_inner.get.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_both_pool_closed_variants_classified_correctly(self):
        """Test that both 'is closed' and 'is already closed' variants are classified as transient

        This test ensures the compound check handles both production error formats.
        """
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.5,
        )

        # Both variants should be classified as transient
        pool_closed_variants = [
            Exception("the pool 'pool-1' is closed"),  # Variant 1: "is closed"
            Exception("the pool 'pool-1' is already closed"),  # Variant 2: "is already closed"
            Exception("the pool 'my-custom-pool' is closed"),
            Exception("the pool 'my-custom-pool' is already closed"),
        ]

        for error in pool_closed_variants:
            assert wrapper._is_transient_error(error), \
                f"Error '{error}' should be classified as transient"
            error_str = str(error).lower()
            assert wrapper._is_connection_lost_error(error_str), \
                f"Error '{error}' should trigger pool reset"


class TestResilientPostgresSaverOOMFix:
    """Tests for OOM fix (Dec 2025): pool reset and memory release

    These tests verify:
    1. Pool reset is triggered only for CONNECTION_LOST_PATTERNS
    2. Inner factory is called to recreate saver after pool reset
    3. Sleep happens outside except block (traceback cleared before sleep)
    4. Non-connection-lost transient errors do NOT trigger pool reset
    """

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_connection_lost_error_triggers_pool_reset(self):
        """Test that connection-lost errors trigger pool reset"""
        from unittest.mock import MagicMock, patch
        import time

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("psycopg.Pipeline [BAD] state"),
            {"checkpoint": "data"},
        ]

        factory_called = []

        def mock_factory():
            factory_called.append(True)
            return mock_inner

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.01,
            inner_factory=mock_factory,
        )

        with patch('langgraph_orchestrator._reset_postgres_pool') as mock_reset:
            mock_reset.return_value = MagicMock()
            with patch('langgraph_orchestrator.logger'):
                with patch.object(time, 'sleep'):
                    result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "data"}
        mock_reset.assert_called_once()
        assert len(factory_called) == 1

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_ssl_closed_error_triggers_pool_reset(self):
        """Test that SSL connection closed errors trigger pool reset"""
        from unittest.mock import MagicMock, patch
        import time

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("SSL connection has been closed unexpectedly"),
            {"checkpoint": "data"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.01,
            inner_factory=lambda: mock_inner,
        )

        with patch('langgraph_orchestrator._reset_postgres_pool') as mock_reset:
            mock_reset.return_value = MagicMock()
            with patch('langgraph_orchestrator.logger'):
                with patch.object(time, 'sleep'):
                    result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "data"}
        mock_reset.assert_called_once()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_timeout_error_does_not_trigger_pool_reset(self):
        """Test that timeout errors (transient but not connection-lost) do NOT trigger pool reset"""
        from unittest.mock import MagicMock, patch
        import time

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("connection timed out"),
            {"checkpoint": "data"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.01,
        )

        with patch('langgraph_orchestrator._reset_postgres_pool') as mock_reset:
            with patch('langgraph_orchestrator.logger'):
                with patch.object(time, 'sleep'):
                    result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "data"}
        mock_reset.assert_not_called()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_inner_factory_recreates_saver_after_pool_reset(self):
        """Test that inner_factory is called to recreate saver after pool reset"""
        from unittest.mock import MagicMock, patch
        import time

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner_original = MagicMock()
        mock_inner_new = MagicMock()

        mock_inner_original.get.side_effect = Exception("pipeline [bad]")
        mock_inner_new.get.return_value = {"checkpoint": "data"}

        factory_calls = []

        def mock_factory():
            factory_calls.append(True)
            return mock_inner_new

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner_original,
            max_retries=3,
            base_delay=0.01,
            inner_factory=mock_factory,
        )

        with patch('langgraph_orchestrator._reset_postgres_pool') as mock_reset:
            mock_reset.return_value = MagicMock()
            with patch('langgraph_orchestrator.logger'):
                with patch.object(time, 'sleep'):
                    result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "data"}
        assert len(factory_calls) == 1
        assert wrapper._inner is mock_inner_new

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_sleep_called_after_traceback_cleared(self):
        """Test that sleep is called after exception traceback is cleared (OOM fix)

        This test verifies the key OOM fix: time.sleep() must be called OUTSIDE
        the except block, after traceback.clear_frames() has been called.
        """
        from unittest.mock import MagicMock, patch
        import time
        import traceback

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("connection timed out"),
            {"checkpoint": "data"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.1,
        )

        call_order = []

        def track_clear_frames(tb):
            call_order.append('clear_frames')

        def track_sleep(seconds):
            call_order.append('sleep')

        with patch('langgraph_orchestrator.logger'):
            with patch.object(traceback, 'clear_frames', side_effect=track_clear_frames):
                with patch.object(time, 'sleep', side_effect=track_sleep):
                    result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "data"}
        assert 'clear_frames' in call_order
        assert 'sleep' in call_order
        assert call_order.index('clear_frames') < call_order.index('sleep'), \
            "traceback.clear_frames() must be called before time.sleep()"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_connection_lost_patterns_coverage(self):
        """Test that all CONNECTION_LOST_PATTERNS trigger pool reset"""
        from unittest.mock import MagicMock, patch
        import time

        from langgraph_orchestrator import ResilientPostgresSaver

        connection_lost_patterns = [
            "ssl connection has been closed",
            "the connection is closed",
            "connection is closed",
            "server closed the connection",
            "connection reset by peer",
            "pipeline [bad]",
            # PR #3104: Pool closed patterns for race condition fix
            "pool is closed",
            "pool is already closed",  # Exact pattern match
            "the pool 'pool-1' is already closed",  # Compound check match
        ]

        for pattern in connection_lost_patterns:
            mock_inner = MagicMock()
            mock_inner.get.side_effect = [
                Exception(f"Error: {pattern}"),
                {"checkpoint": "data"},
            ]

            wrapper = ResilientPostgresSaver(
                inner_saver=mock_inner,
                max_retries=3,
                base_delay=0.01,
                inner_factory=lambda: mock_inner,
            )

            with patch('langgraph_orchestrator._reset_postgres_pool') as mock_reset:
                mock_reset.return_value = MagicMock()
                with patch('langgraph_orchestrator.logger'):
                    with patch.object(time, 'sleep'):
                        result = wrapper.get({"config": "test"})

            assert result == {"checkpoint": "data"}, f"Failed for pattern: {pattern}"
            mock_reset.assert_called_once(), f"Pool reset not called for pattern: {pattern}"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_no_inner_factory_still_resets_pool(self):
        """Test that pool reset still happens even without inner_factory"""
        from unittest.mock import MagicMock, patch
        import time

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("pipeline [bad]"),
            {"checkpoint": "data"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.01,
        )

        with patch('langgraph_orchestrator._reset_postgres_pool') as mock_reset:
            mock_reset.return_value = MagicMock()
            with patch('langgraph_orchestrator.logger'):
                with patch.object(time, 'sleep'):
                    result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "data"}
        mock_reset.assert_called_once()
        assert wrapper._inner is mock_inner

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_is_closed_error_triggers_pool_reset(self):
        """Test that 'pool is closed' error triggers pool reset (PR #3104 fix)

        This test verifies that the new 'pool is closed' pattern in
        CONNECTION_LOST_PATTERNS triggers pool reset, not just retry.
        """
        from unittest.mock import MagicMock, patch
        import time

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("pool is closed"),
            {"checkpoint": "data"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.01,
            inner_factory=lambda: mock_inner,
        )

        with patch('langgraph_orchestrator._reset_postgres_pool') as mock_reset:
            mock_reset.return_value = MagicMock()
            with patch('langgraph_orchestrator.logger'):
                with patch.object(time, 'sleep'):
                    result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "data"}
        mock_reset.assert_called_once()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_is_already_closed_error_triggers_pool_reset(self):
        """Test that 'pool is already closed' error triggers pool reset (PR #3104 fix)

        This test verifies that the production error message
        "the pool 'pool-1' is already closed" triggers pool reset.
        """
        from unittest.mock import MagicMock, patch
        import time

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.put.side_effect = [
            Exception("the pool 'pool-1' is already closed"),
            None,  # Success on second attempt
        ]

        factory_called = []

        def mock_factory():
            factory_called.append(True)
            return mock_inner

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.01,
            inner_factory=mock_factory,
        )

        with patch('langgraph_orchestrator._reset_postgres_pool') as mock_reset:
            mock_reset.return_value = MagicMock()
            with patch('langgraph_orchestrator.logger'):
                with patch.object(time, 'sleep'):
                    wrapper.put({"config": "test"}, {}, {}, {})

        # Verify pool was reset
        mock_reset.assert_called_once()
        # Verify factory was called to recreate inner saver
        assert len(factory_called) == 1

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_consecutive_connection_lost_triggers_multiple_resets(self):
        """Test that consecutive connection-lost errors trigger multiple pool resets

        This test verifies that:
        1. Multiple consecutive connection-lost errors each trigger a pool reset
        2. Each reset calls inner_factory to create a new saver
        3. Each retry uses the newly created inner saver
        """
        from unittest.mock import MagicMock, patch
        import time

        from langgraph_orchestrator import ResilientPostgresSaver

        # Create distinct mock inners to track which one is used
        mock_inner_1 = MagicMock(name="inner_1")
        mock_inner_2 = MagicMock(name="inner_2")
        mock_inner_3 = MagicMock(name="inner_3")

        # First inner fails with connection-lost, second inner also fails, third succeeds
        mock_inner_1.get.side_effect = Exception("pipeline [bad] - first failure")
        mock_inner_2.get.side_effect = Exception("ssl connection has been closed - second failure")
        mock_inner_3.get.return_value = {"checkpoint": "success"}

        factory_calls = []
        inner_sequence = [mock_inner_2, mock_inner_3]

        def mock_factory():
            factory_calls.append(len(factory_calls) + 1)
            return inner_sequence.pop(0)

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner_1,
            max_retries=4,  # Allow enough retries for 2 failures + 1 success
            base_delay=0.01,
            inner_factory=mock_factory,
        )

        with patch('langgraph_orchestrator._reset_postgres_pool') as mock_reset:
            mock_reset.return_value = MagicMock()
            with patch('langgraph_orchestrator.logger'):
                with patch.object(time, 'sleep'):
                    result = wrapper.get({"config": "test"})

        # Verify result
        assert result == {"checkpoint": "success"}

        # Verify pool was reset twice (once for each connection-lost error)
        assert mock_reset.call_count == 2

        # Verify factory was called twice to create new inners
        assert len(factory_calls) == 2
        assert factory_calls == [1, 2]

        # Verify the final inner is the third one (the successful one)
        assert wrapper._inner is mock_inner_3

        # Verify each inner was called exactly once
        mock_inner_1.get.assert_called_once()
        mock_inner_2.get.assert_called_once()
        mock_inner_3.get.assert_called_once()


class TestResilientPostgresSaverRateLimitedLogging:
    """Tests for rate-limited logging in ResilientPostgresSaver (Issue #3109)

    During prolonged database outages, each retry generates a log entry which can
    overwhelm log systems. This test class verifies the rate-limited logging behavior:
    - First retry is always logged
    - Last retry is always logged
    - Intermediate retries are sampled based on retry_log_sample_rate
    - Total retry attempts are tracked even when logs are sampled out
    """

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_default_sample_rate_logs_all_retries(self):
        """Test that default sample_rate=1 logs all retry attempts"""
        import time
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("ssl connection has been closed unexpectedly"),
            Exception("ssl connection has been closed unexpectedly"),
            {"checkpoint": "success"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=2,
            base_delay=0.01,
            retry_log_sample_rate=1,
        )

        with patch('langgraph_orchestrator.logger') as mock_logger:
            with patch.object(time, 'sleep'):
                result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "success"}
        warning_calls = [c for c in mock_logger.warning.call_args_list
                         if "Transient error" in str(c)]
        assert len(warning_calls) == 2

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_sample_rate_5_logs_first_and_sampled_retries(self):
        """Test that sample_rate=5 logs first retry and every 5th retry"""
        import time
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        errors = [Exception("ssl connection has been closed unexpectedly")] * 10
        errors.append({"checkpoint": "success"})
        mock_inner.get.side_effect = errors

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=10,
            base_delay=0.001,
            retry_log_sample_rate=5,
        )

        with patch('langgraph_orchestrator.logger') as mock_logger:
            with patch.object(time, 'sleep'):
                result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "success"}
        warning_calls = [c for c in mock_logger.warning.call_args_list
                         if "Transient error" in str(c)]
        assert len(warning_calls) >= 2
        assert wrapper._total_retry_attempts == 10

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_first_retry_always_logged(self):
        """Test that first retry (attempt=0) is always logged regardless of sample rate"""
        import time
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("ssl connection has been closed unexpectedly"),
            {"checkpoint": "success"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=1,
            base_delay=0.01,
            retry_log_sample_rate=100,
        )

        with patch('langgraph_orchestrator.logger') as mock_logger:
            with patch.object(time, 'sleep'):
                result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "success"}
        warning_calls = [c for c in mock_logger.warning.call_args_list
                         if "Transient error" in str(c)]
        assert len(warning_calls) == 1

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_last_retry_always_logged(self):
        """Test that last retry is always logged regardless of sample rate"""
        import time
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("ssl connection has been closed unexpectedly"),
            Exception("ssl connection has been closed unexpectedly"),
            {"checkpoint": "success"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=2,
            base_delay=0.01,
            retry_log_sample_rate=100,
        )

        with patch('langgraph_orchestrator.logger') as mock_logger:
            with patch.object(time, 'sleep'):
                result = wrapper.get({"config": "test"})

        assert result == {"checkpoint": "success"}
        warning_calls = [c for c in mock_logger.warning.call_args_list
                         if "Transient error" in str(c)]
        assert len(warning_calls) == 2

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_total_retry_attempts_counter_increments(self):
        """Test that _total_retry_attempts counter increments for every retry"""
        import time
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        errors = [Exception("ssl connection has been closed unexpectedly")] * 5
        errors.append({"checkpoint": "success"})
        mock_inner.get.side_effect = errors

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=5,
            base_delay=0.001,
            retry_log_sample_rate=10,
        )

        assert wrapper._total_retry_attempts == 0

        with patch('langgraph_orchestrator.logger'):
            with patch.object(time, 'sleep'):
                wrapper.get({"config": "test"})

        assert wrapper._total_retry_attempts == 5

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_retry_log_count_increments(self):
        """Test that _retry_log_count increments for every retry"""
        import time
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        errors = [Exception("ssl connection has been closed unexpectedly")] * 3
        errors.append({"checkpoint": "success"})
        mock_inner.get.side_effect = errors

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.001,
            retry_log_sample_rate=1,
        )

        assert wrapper._retry_log_count == 0

        with patch('langgraph_orchestrator.logger'):
            with patch.object(time, 'sleep'):
                wrapper.get({"config": "test"})

        assert wrapper._retry_log_count == 3

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_sample_rate_minimum_is_1(self):
        """Test that sample_rate is clamped to minimum of 1"""
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.01,
            retry_log_sample_rate=0,
        )

        assert wrapper._retry_log_sample_rate == 1

        wrapper2 = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.01,
            retry_log_sample_rate=-5,
        )

        assert wrapper2._retry_log_sample_rate == 1

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_log_extra_includes_total_retry_attempts(self):
        """Test that log extra includes total_retry_attempts for metrics"""
        import time
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("ssl connection has been closed unexpectedly"),
            {"checkpoint": "success"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=1,
            base_delay=0.01,
            retry_log_sample_rate=1,
        )

        with patch('langgraph_orchestrator.logger') as mock_logger:
            with patch.object(time, 'sleep'):
                wrapper.get({"config": "test"})

        warning_calls = [c for c in mock_logger.warning.call_args_list
                         if "Transient error" in str(c)]
        assert len(warning_calls) == 1
        extra = warning_calls[0][1].get('extra', {})
        assert 'total_retry_attempts' in extra
        assert extra['total_retry_attempts'] == 1

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_log_extra_includes_log_sampled_flag(self):
        """Test that log extra includes log_sampled flag"""
        import time
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("ssl connection has been closed unexpectedly"),
            {"checkpoint": "success"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=1,
            base_delay=0.01,
            retry_log_sample_rate=5,
        )

        with patch('langgraph_orchestrator.logger') as mock_logger:
            with patch.object(time, 'sleep'):
                wrapper.get({"config": "test"})

        warning_calls = [c for c in mock_logger.warning.call_args_list
                         if "Transient error" in str(c)]
        assert len(warning_calls) == 1
        extra = warning_calls[0][1].get('extra', {})
        assert 'log_sampled' in extra
        assert extra['log_sampled'] is True

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_should_log_retry_method_directly(self):
        """Test _should_log_retry method behavior directly

        Note: _should_log_retry is now a pure function with no side effects.
        Counter increments are handled by the caller (_retry_with_backoff).
        The method signature is _should_log_retry(is_first, is_last).
        """
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=10,
            base_delay=0.01,
            retry_log_sample_rate=5,
        )

        # First retry is always logged
        assert wrapper._should_log_retry(is_first=True, is_last=False) is True

        # Last retry is always logged
        assert wrapper._should_log_retry(is_first=False, is_last=True) is True

        # Intermediate retries depend on counter and sample rate
        # Simulate counter increments (normally done by caller)
        wrapper._retry_log_count = 1
        assert wrapper._should_log_retry(is_first=False, is_last=False) is False

        wrapper._retry_log_count = 5
        assert wrapper._should_log_retry(is_first=False, is_last=False) is True

        wrapper._retry_log_count = 10
        assert wrapper._should_log_retry(is_first=False, is_last=False) is True

        wrapper._retry_log_count = 7
        assert wrapper._should_log_retry(is_first=False, is_last=False) is False

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_backward_compatibility_default_logs_all(self):
        """Test backward compatibility: default behavior logs all retries"""
        import time
        from unittest.mock import MagicMock

        from langgraph_orchestrator import ResilientPostgresSaver

        mock_inner = MagicMock()
        mock_inner.get.side_effect = [
            Exception("ssl connection has been closed unexpectedly"),
            Exception("ssl connection has been closed unexpectedly"),
            Exception("ssl connection has been closed unexpectedly"),
            {"checkpoint": "success"},
        ]

        wrapper = ResilientPostgresSaver(
            inner_saver=mock_inner,
            max_retries=3,
            base_delay=0.001,
        )

        assert wrapper._retry_log_sample_rate == 1

        with patch('langgraph_orchestrator.logger') as mock_logger:
            with patch.object(time, 'sleep'):
                wrapper.get({"config": "test"})

        warning_calls = [c for c in mock_logger.warning.call_args_list
                         if "Transient error" in str(c)]
        assert len(warning_calls) == 3


class TestOOMProtectedMemorySaver:
    """Tests for OOMProtectedMemorySaver wrapper class (Issue #3027)"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_workflow_count_tracks_unique_thread_ids(self):
        """Test that workflow_count correctly counts unique thread_ids"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=10,
            memory_warning_mb=512,
            trace_id="test-trace",
        )

        assert wrapper.workflow_count == 0

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp1"}},
            {"v": 1, "id": "cp1", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )
        assert wrapper.workflow_count == 1

        wrapper.put(
            {"configurable": {"thread_id": "thread-2", "checkpoint_ns": "", "checkpoint_id": "cp2"}},
            {"v": 1, "id": "cp2", "ts": "2024-01-01T00:00:01Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )
        assert wrapper.workflow_count == 2

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp3"}},
            {"v": 1, "id": "cp3", "ts": "2024-01-01T00:00:02Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 1, "writes": None, "parents": {}},
            {},
        )
        assert wrapper.workflow_count == 2

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_checkpoint_count_tracks_total_checkpoints(self):
        """Test that checkpoint_count correctly counts total checkpoints"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=10,
            memory_warning_mb=512,
            trace_id="test-trace",
        )

        assert wrapper.checkpoint_count == 0

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp1"}},
            {"v": 1, "id": "cp1", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )
        assert wrapper.checkpoint_count == 1

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp2"}},
            {"v": 1, "id": "cp2", "ts": "2024-01-01T00:00:01Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 1, "writes": None, "parents": {}},
            {},
        )
        assert wrapper.checkpoint_count == 2

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_capacity_exceeded_raises_exception(self):
        """Test that exceeding max_workflows raises DegradedCheckpointerCapacityExceeded"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import (
            OOMProtectedMemorySaver,
            DegradedCheckpointerCapacityExceeded,
        )

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=2,
            memory_warning_mb=512,
            trace_id="test-trace",
        )

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp1"}},
            {"v": 1, "id": "cp1", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )
        wrapper.put(
            {"configurable": {"thread_id": "thread-2", "checkpoint_ns": "", "checkpoint_id": "cp2"}},
            {"v": 1, "id": "cp2", "ts": "2024-01-01T00:00:01Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )

        with pytest.raises(DegradedCheckpointerCapacityExceeded):
            wrapper.put(
                {"configurable": {"thread_id": "thread-3", "checkpoint_ns": "", "checkpoint_id": "cp3"}},
                {"v": 1, "id": "cp3", "ts": "2024-01-01T00:00:02Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
                {"source": "input", "step": 0, "writes": None, "parents": {}},
                {},
            )

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_existing_workflow_does_not_count_toward_limit(self):
        """Test that existing workflows can continue without hitting capacity limit"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=2,
            memory_warning_mb=512,
            trace_id="test-trace",
        )

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp1"}},
            {"v": 1, "id": "cp1", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )
        wrapper.put(
            {"configurable": {"thread_id": "thread-2", "checkpoint_ns": "", "checkpoint_id": "cp2"}},
            {"v": 1, "id": "cp2", "ts": "2024-01-01T00:00:01Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp3"}},
            {"v": 1, "id": "cp3", "ts": "2024-01-01T00:00:02Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 1, "writes": None, "parents": {}},
            {},
        )
        assert wrapper.workflow_count == 2
        assert wrapper.checkpoint_count == 3

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_get_metrics_returns_correct_values(self):
        """Test that get_metrics returns correct metric values"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=512,
            trace_id="test-trace",
        )

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp1"}},
            {"v": 1, "id": "cp1", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )

        metrics = wrapper.get_metrics()

        assert metrics["degraded_workflow_count"] == 1
        assert metrics["checkpoint_count"] == 1
        assert metrics["max_workflows"] == 100
        assert metrics["memory_warning_mb"] == 512
        assert "checkpoint_memory_bytes" in metrics
        assert metrics["checkpoint_memory_bytes"] > 0

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_memory_warning_logged_once(self):
        """Test that memory warning is logged only once until reset"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=0,
            trace_id="test-trace",
        )

        with patch('langgraph_orchestrator.logger') as mock_logger:
            wrapper.put(
                {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp1"}},
                {"v": 1, "id": "cp1", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
                {"source": "input", "step": 0, "writes": None, "parents": {}},
                {},
            )

            wrapper.put(
                {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp2"}},
                {"v": 1, "id": "cp2", "ts": "2024-01-01T00:00:01Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
                {"source": "input", "step": 1, "writes": None, "parents": {}},
                {},
            )

            warning_calls = [
                c for c in mock_logger.warning.call_args_list
                if "MEMORY WARNING" in str(c)
            ]
            assert len(warning_calls) == 1

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_get_memory_estimate_bytes_returns_positive_value(self):
        """Test that get_memory_estimate_bytes returns a positive value"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=512,
            trace_id="test-trace",
        )

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp1"}},
            {"v": 1, "id": "cp1", "ts": "2024-01-01T00:00:00Z", "channel_values": {"data": "x" * 1000}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )

        memory_bytes = wrapper.get_memory_estimate_bytes()
        assert memory_bytes > 0

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_exception_inherits_database_exception(self):
        """Test that DegradedCheckpointerCapacityExceeded inherits from DatabaseException"""
        from langgraph_orchestrator import (
            DegradedCheckpointerCapacityExceeded,
            DatabaseException,
        )

        assert issubclass(DegradedCheckpointerCapacityExceeded, DatabaseException)

        exc = DegradedCheckpointerCapacityExceeded("test message")
        assert isinstance(exc, DatabaseException)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_delegates_to_inner_saver(self):
        """Test that operations are delegated to inner MemorySaver"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=512,
            trace_id="test-trace",
        )

        config = {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp1"}}
        checkpoint = {"v": 1, "id": "cp1", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []}
        metadata = {"source": "input", "step": 0, "writes": None, "parents": {}}

        wrapper.put(config, checkpoint, metadata, {})

        result = wrapper.get_tuple(config)
        assert result is not None
        assert result.checkpoint["id"] == "cp1"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_delete_thread_removes_workflow(self):
        """Test that delete_thread removes the workflow from storage"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=512,
            trace_id="test-trace",
        )

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp1"}},
            {"v": 1, "id": "cp1", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )
        assert wrapper.workflow_count == 1

        wrapper.delete_thread("thread-1")
        assert wrapper.workflow_count == 0


class TestGetDegradedPersistenceCheckpointerOOMIntegration:
    """Tests for OOM protection integration in get_degraded_persistence_checkpointer"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_factory_wraps_with_oom_protected_memory_saver(self):
        """Test that factory function wraps fallback with OOMProtectedMemorySaver"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            mock_settings.max_degraded_workflows_per_worker = 50
            mock_settings.degraded_checkpoint_memory_warning_mb = 256

            result = get_degraded_persistence_checkpointer(
                primary=mock_primary,
                trace_id="test-trace",
            )

        assert hasattr(result, '_fallback')
        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._max_workflows == 50
        assert result._fallback._memory_warning_mb == 256

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_factory_uses_default_values_when_settings_missing(self):
        """Test that factory uses defaults when settings attributes are missing"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            del mock_settings.max_degraded_workflows_per_worker
            del mock_settings.degraded_checkpoint_memory_warning_mb

            result = get_degraded_persistence_checkpointer(
                primary=mock_primary,
                trace_id="test-trace",
            )

        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._max_workflows == 100
        assert result._fallback._memory_warning_mb == 512

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_factory_returns_primary_when_failover_disabled(self):
        """Test that factory returns primary when failover is disabled"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import get_degraded_persistence_checkpointer

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = False

            result = get_degraded_persistence_checkpointer(
                primary=mock_primary,
                trace_id="test-trace",
            )

        assert result is mock_primary


class TestPostgresPoolConfiguration:
    """Tests for _get_postgres_pool() configuration parameters.

    SSL Connection Fix (Dec 2025): These tests verify the connection pool parameters
    that were introduced to fix "SSL connection has been closed unexpectedly" errors.
    The configuration acts as a regression guard to prevent accidental changes to
    critical pool settings (max_lifetime, max_idle, TCP keepalive).
    """

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_initialized_with_correct_recycling_params(self):
        """Test that ConnectionPool is initialized with aggressive recycling parameters.

        SSL Connection Fix (Dec 2025): Aggressive recycling prevents stale connections
        that cause "SSL connection has been closed unexpectedly" errors.
        - max_lifetime: 600s (10 min) - recycle connections before they go stale
        - max_idle: 120s (2 min) - recycle idle connections before NAT/LB drops them
        """
        from unittest.mock import MagicMock

        mock_pool_instance = MagicMock()
        captured_kwargs = {}

        def capture_init(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return mock_pool_instance

        mock_pool_class = MagicMock(side_effect=capture_init)
        mock_pool_class.check_connection = MagicMock()
        mock_dict_row = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.database_url = "postgresql://user:pass@localhost:5432/db"

            with patch('langgraph_orchestrator.logger'):
                with patch('langgraph_orchestrator._postgres_pool', None):
                    with patch('psycopg_pool.ConnectionPool', mock_pool_class):
                        with patch('psycopg.rows.dict_row', mock_dict_row):
                            from langgraph_orchestrator import _get_postgres_pool
                            import langgraph_orchestrator
                            langgraph_orchestrator._postgres_pool = None

                            _get_postgres_pool()

                            assert captured_kwargs.get('max_lifetime') == 600, \
                                "max_lifetime should be 600s (10 min) for aggressive recycling"
                            assert captured_kwargs.get('max_idle') == 120, \
                                "max_idle should be 120s (2 min) for aggressive recycling"
                            assert captured_kwargs.get('min_size') == 1
                            assert captured_kwargs.get('max_size') == 5
                            assert captured_kwargs.get('reconnect_timeout') == 60

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_initialized_with_tcp_keepalive_params(self):
        """Test that ConnectionPool kwargs include TCP keepalive settings.

        SSL Connection Fix (Dec 2025): TCP keepalive prevents NAT/LB from dropping
        idle connections before the pool's timeout.
        - keepalives: 1 (enabled)
        - keepalives_idle: 30s (start probing after 30s idle)
        - keepalives_interval: 10s (probe every 10s)
        - keepalives_count: 5 (give up after 5 failed probes)
        - Worst-case detection: ~80s (idle + interval * count)
        """
        from unittest.mock import MagicMock

        mock_pool_instance = MagicMock()
        captured_kwargs = {}

        def capture_init(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return mock_pool_instance

        mock_pool_class = MagicMock(side_effect=capture_init)
        mock_pool_class.check_connection = MagicMock()
        mock_dict_row = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.database_url = "postgresql://user:pass@localhost:5432/db"

            with patch('langgraph_orchestrator.logger'):
                with patch('langgraph_orchestrator._postgres_pool', None):
                    with patch('psycopg_pool.ConnectionPool', mock_pool_class):
                        with patch('psycopg.rows.dict_row', mock_dict_row):
                            from langgraph_orchestrator import _get_postgres_pool
                            import langgraph_orchestrator
                            langgraph_orchestrator._postgres_pool = None

                            _get_postgres_pool()

                            conn_kwargs = captured_kwargs.get('kwargs', {})
                            assert conn_kwargs.get('keepalives') == 1, \
                                "keepalives should be 1 (enabled)"
                            assert conn_kwargs.get('keepalives_idle') == 30, \
                                "keepalives_idle should be 30s (libpq seconds)"
                            assert conn_kwargs.get('keepalives_interval') == 10, \
                                "keepalives_interval should be 10s (libpq seconds)"
                            assert conn_kwargs.get('keepalives_count') == 5, \
                                "keepalives_count should be 5 (give up after 5 failed probes)"

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_wait_called_after_initialization(self):
        """Test that pool.wait() is called to ensure connections are ready."""
        from unittest.mock import MagicMock

        mock_pool_instance = MagicMock()
        mock_pool_class = MagicMock(return_value=mock_pool_instance)
        mock_pool_class.check_connection = MagicMock()
        mock_dict_row = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.database_url = "postgresql://user:pass@localhost:5432/db"

            with patch('langgraph_orchestrator.logger'):
                with patch('langgraph_orchestrator._postgres_pool', None):
                    with patch('psycopg_pool.ConnectionPool', mock_pool_class):
                        with patch('psycopg.rows.dict_row', mock_dict_row):
                            from langgraph_orchestrator import _get_postgres_pool
                            import langgraph_orchestrator
                            langgraph_orchestrator._postgres_pool = None

                            _get_postgres_pool()

                            mock_pool_instance.wait.assert_called_once()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_returns_none_when_database_url_missing(self):
        """Test that _get_postgres_pool() returns None when DATABASE_URL is not configured."""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.database_url = None

            with patch('langgraph_orchestrator.logger') as mock_logger:
                env_copy = os.environ.copy()
                if 'DATABASE_URL' in env_copy:
                    del env_copy['DATABASE_URL']
                with patch.dict(os.environ, env_copy, clear=True):
                    from langgraph_orchestrator import _get_postgres_pool
                    import langgraph_orchestrator
                    langgraph_orchestrator._postgres_pool = None

                    result = _get_postgres_pool()

                    assert result is None
                    mock_logger.warning.assert_called()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_pool_logs_keepalive_params_on_success(self):
        """Test that successful pool initialization logs keepalive parameters."""
        from unittest.mock import MagicMock

        mock_pool_instance = MagicMock()
        mock_pool_class = MagicMock(return_value=mock_pool_instance)
        mock_pool_class.check_connection = MagicMock()
        mock_dict_row = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.database_url = "postgresql://user:pass@localhost:5432/db"

            with patch('langgraph_orchestrator.logger') as mock_logger:
                with patch('langgraph_orchestrator._postgres_pool', None):
                    with patch('psycopg_pool.ConnectionPool', mock_pool_class):
                        with patch('psycopg.rows.dict_row', mock_dict_row):
                            from langgraph_orchestrator import _get_postgres_pool
                            import langgraph_orchestrator
                            langgraph_orchestrator._postgres_pool = None

                            _get_postgres_pool()

                            mock_logger.info.assert_called()
                            call_args = mock_logger.info.call_args
                            extra = call_args[1].get('extra', {}) if call_args[1] else {}
                            assert extra.get('keepalives') == 1
                            assert extra.get('keepalives_idle') == 30
                            assert extra.get('keepalives_interval') == 10
                            assert extra.get('keepalives_count') == 5


class TestOOMProtectedMemorySaverHardLimit:
    """Tests for Hard Memory Limit feature in OOMProtectedMemorySaver (Issue #3027 Dec 2025)

    The hard memory limit is the 'safety airbag' that terminates tasks when memory
    usage exceeds the threshold, protecting the worker from OOM kills.
    """

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_hard_limit_raises_exception_when_exceeded(self):
        """Test that exceeding hard memory limit raises DegradedCheckpointerMemoryExceeded"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import (
            OOMProtectedMemorySaver,
            DegradedCheckpointerMemoryExceeded,
        )

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=1,
            memory_hard_limit_mb=1,
            max_checkpoints_per_thread=100,
            trace_id="test-trace",
        )

        with patch.object(wrapper, 'get_memory_estimate_bytes', return_value=2 * 1024 * 1024):
            with pytest.raises(DegradedCheckpointerMemoryExceeded) as exc_info:
                wrapper.put(
                    {"configurable": {"thread_id": "thread-2", "checkpoint_ns": "", "checkpoint_id": "cp2"}},
                    {"v": 1, "id": "cp2", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
                    {"source": "input", "step": 0, "writes": None, "parents": {}},
                    {},
                )

        assert "hard limit exceeded" in str(exc_info.value).lower()
        assert "test-trace" in str(exc_info.value)

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_hard_limit_not_triggered_when_below_threshold(self):
        """Test that operations succeed when memory is below hard limit"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=512,
            memory_hard_limit_mb=1024,
            max_checkpoints_per_thread=100,
            trace_id="test-trace",
        )

        wrapper.put(
            {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp1"}},
            {"v": 1, "id": "cp1", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )

        assert wrapper.checkpoint_count == 1

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_hard_limit_exception_inherits_database_exception(self):
        """Test that DegradedCheckpointerMemoryExceeded inherits from DatabaseException"""
        from langgraph_orchestrator import DegradedCheckpointerMemoryExceeded

        assert DegradedCheckpointerMemoryExceeded.__bases__[0].__name__ == "DatabaseException"


class TestOOMProtectedMemorySaverEviction:
    """Tests for Checkpoint Eviction (LRU) feature in OOMProtectedMemorySaver (Issue #3027 Dec 2025)

    The eviction mechanism keeps only the most recent N checkpoints per thread
    to prevent unbounded growth in MemorySaver.
    """

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_eviction_removes_old_checkpoints(self):
        """Test that old checkpoints are evicted when limit is exceeded"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=512,
            memory_hard_limit_mb=1024,
            max_checkpoints_per_thread=3,
            trace_id="test-trace",
        )

        for i in range(5):
            wrapper.put(
                {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": f"cp{i}"}},
                {"v": 1, "id": f"cp{i}", "ts": f"2024-01-01T00:00:0{i}Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
                {"source": "input", "step": i, "writes": None, "parents": {}},
                {},
            )

        thread_data = inner.storage.get("thread-1", {})
        checkpoint_count = sum(len(ns_data) for ns_data in thread_data.values() if isinstance(ns_data, dict))
        assert checkpoint_count <= 3

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_eviction_keeps_most_recent_checkpoints(self):
        """Test that eviction keeps the most recent checkpoints (LRU policy)"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=512,
            memory_hard_limit_mb=1024,
            max_checkpoints_per_thread=2,
            trace_id="test-trace",
        )

        for i in range(4):
            wrapper.put(
                {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": f"cp{i}"}},
                {"v": 1, "id": f"cp{i}", "ts": f"2024-01-01T00:00:0{i}Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
                {"source": "input", "step": i, "writes": None, "parents": {}},
                {},
            )

        thread_data = inner.storage.get("thread-1", {})
        checkpoint_count = sum(len(ns_data) for ns_data in thread_data.values() if isinstance(ns_data, dict))
        assert checkpoint_count <= 2

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_eviction_does_not_affect_other_threads(self):
        """Test that eviction only affects the specific thread"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=512,
            memory_hard_limit_mb=1024,
            max_checkpoints_per_thread=2,
            trace_id="test-trace",
        )

        for i in range(4):
            wrapper.put(
                {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": f"cp1-{i}"}},
                {"v": 1, "id": f"cp1-{i}", "ts": f"2024-01-01T00:00:0{i}Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
                {"source": "input", "step": i, "writes": None, "parents": {}},
                {},
            )

        wrapper.put(
            {"configurable": {"thread_id": "thread-2", "checkpoint_ns": "", "checkpoint_id": "cp2-0"}},
            {"v": 1, "id": "cp2-0", "ts": "2024-01-01T00:00:00Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
            {"source": "input", "step": 0, "writes": None, "parents": {}},
            {},
        )

        thread2_data = inner.storage.get("thread-2", {})
        checkpoint_count = sum(len(ns_data) for ns_data in thread2_data.values() if isinstance(ns_data, dict))
        assert checkpoint_count == 1

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_eviction_logs_when_checkpoints_removed(self):
        """Test that eviction logs when checkpoints are removed"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph_orchestrator import OOMProtectedMemorySaver

        inner = MemorySaver()
        wrapper = OOMProtectedMemorySaver(
            inner_saver=inner,
            max_workflows=100,
            memory_warning_mb=512,
            memory_hard_limit_mb=1024,
            max_checkpoints_per_thread=2,
            trace_id="test-trace",
        )

        for i in range(2):
            wrapper.put(
                {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": f"cp{i}"}},
                {"v": 1, "id": f"cp{i}", "ts": f"2024-01-01T00:00:0{i}Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
                {"source": "input", "step": i, "writes": None, "parents": {}},
                {},
            )

        with patch('langgraph_orchestrator.logger') as mock_logger:
            wrapper.put(
                {"configurable": {"thread_id": "thread-1", "checkpoint_ns": "", "checkpoint_id": "cp2"}},
                {"v": 1, "id": "cp2", "ts": "2024-01-01T00:00:02Z", "channel_values": {}, "channel_versions": {}, "versions_seen": {}, "pending_sends": []},
                {"source": "input", "step": 2, "writes": None, "parents": {}},
                {},
            )

            info_calls = [c for c in mock_logger.info.call_args_list if "EVICTION" in str(c)]
            assert len(info_calls) >= 1


class TestOOMProtectedMemorySaverFactoryNewSettings:
    """Tests for factory function with new hard limit and eviction settings (Issue #3027 Dec 2025)"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_factory_uses_hard_limit_setting(self):
        """Test that factory function uses degraded_checkpoint_memory_hard_limit_mb setting"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            mock_settings.max_degraded_workflows_per_worker = 50
            mock_settings.degraded_checkpoint_memory_warning_mb = 256
            mock_settings.degraded_checkpoint_memory_hard_limit_mb = 512
            mock_settings.degraded_checkpoint_max_per_thread = 5

            result = get_degraded_persistence_checkpointer(
                primary=mock_primary,
                trace_id="test-trace",
            )

        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._memory_hard_limit_mb == 512
        assert result._fallback._max_checkpoints_per_thread == 5

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_factory_uses_default_hard_limit_when_setting_missing(self):
        """Test that factory uses default hard limit when setting is missing"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            mock_settings.max_degraded_workflows_per_worker = 100
            mock_settings.degraded_checkpoint_memory_warning_mb = 512
            del mock_settings.degraded_checkpoint_memory_hard_limit_mb
            del mock_settings.degraded_checkpoint_max_per_thread

            result = get_degraded_persistence_checkpointer(
                primary=mock_primary,
                trace_id="test-trace",
            )

        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._memory_hard_limit_mb == 1024
        assert result._fallback._max_checkpoints_per_thread == 10


class TestConfigBoundaryValidation:
    """Tests for config boundary validation (Issue #3181 Dec 2025)"""

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_negative_max_workflows_clamped_to_minimum(self):
        """Test that negative max_workflows is clamped to minimum value of 1"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            mock_settings.max_degraded_workflows_per_worker = -10
            mock_settings.degraded_checkpoint_memory_warning_mb = 512
            mock_settings.degraded_checkpoint_memory_hard_limit_mb = 1024
            mock_settings.degraded_checkpoint_max_per_thread = 10

            with patch('langgraph_orchestrator.logger') as mock_logger:
                result = get_degraded_persistence_checkpointer(
                    primary=mock_primary,
                    trace_id="test-trace",
                )

        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._max_workflows == 1
        mock_logger.warning.assert_called()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_zero_max_checkpoints_clamped_to_minimum(self):
        """Test that zero max_checkpoints_per_thread is clamped to minimum value of 1"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            mock_settings.max_degraded_workflows_per_worker = 100
            mock_settings.degraded_checkpoint_memory_warning_mb = 512
            mock_settings.degraded_checkpoint_memory_hard_limit_mb = 1024
            mock_settings.degraded_checkpoint_max_per_thread = 0

            with patch('langgraph_orchestrator.logger') as mock_logger:
                result = get_degraded_persistence_checkpointer(
                    primary=mock_primary,
                    trace_id="test-trace",
                )

        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._max_checkpoints_per_thread == 1
        mock_logger.warning.assert_called()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_negative_memory_hard_limit_clamped_to_minimum(self):
        """Test that negative memory_hard_limit_mb is clamped to minimum value of 1"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            mock_settings.max_degraded_workflows_per_worker = 100
            mock_settings.degraded_checkpoint_memory_warning_mb = 512
            mock_settings.degraded_checkpoint_memory_hard_limit_mb = -100
            mock_settings.degraded_checkpoint_max_per_thread = 10

            with patch('langgraph_orchestrator.logger') as mock_logger:
                result = get_degraded_persistence_checkpointer(
                    primary=mock_primary,
                    trace_id="test-trace",
                )

        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._memory_hard_limit_mb == 1
        mock_logger.warning.assert_called()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_invalid_string_value_falls_back_to_default(self):
        """Test that invalid string value falls back to default"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            mock_settings.max_degraded_workflows_per_worker = "invalid"
            mock_settings.degraded_checkpoint_memory_warning_mb = 512
            mock_settings.degraded_checkpoint_memory_hard_limit_mb = 1024
            mock_settings.degraded_checkpoint_max_per_thread = 10

            with patch('langgraph_orchestrator.logger') as mock_logger:
                result = get_degraded_persistence_checkpointer(
                    primary=mock_primary,
                    trace_id="test-trace",
                )

        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._max_workflows == 100
        mock_logger.warning.assert_called()

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_float_value_converted_to_int(self):
        """Test that float values are converted to int"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            mock_settings.max_degraded_workflows_per_worker = 50.7
            mock_settings.degraded_checkpoint_memory_warning_mb = 512.5
            mock_settings.degraded_checkpoint_memory_hard_limit_mb = 1024.9
            mock_settings.degraded_checkpoint_max_per_thread = 10.3

            result = get_degraded_persistence_checkpointer(
                primary=mock_primary,
                trace_id="test-trace",
            )

        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._max_workflows == 50
        assert result._fallback._memory_warning_mb == 512
        assert result._fallback._memory_hard_limit_mb == 1024
        assert result._fallback._max_checkpoints_per_thread == 10

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_valid_positive_values_unchanged(self):
        """Test that valid positive values are not modified"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            mock_settings.max_degraded_workflows_per_worker = 200
            mock_settings.degraded_checkpoint_memory_warning_mb = 256
            mock_settings.degraded_checkpoint_memory_hard_limit_mb = 2048
            mock_settings.degraded_checkpoint_max_per_thread = 20

            with patch('langgraph_orchestrator.logger') as mock_logger:
                result = get_degraded_persistence_checkpointer(
                    primary=mock_primary,
                    trace_id="test-trace",
                )

        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._max_workflows == 200
        assert result._fallback._memory_warning_mb == 256
        assert result._fallback._memory_hard_limit_mb == 2048
        assert result._fallback._max_checkpoints_per_thread == 20
        warning_calls = [call for call in mock_logger.warning.call_args_list
                        if 'config_validation' in str(call)]
        assert len(warning_calls) == 0

    @pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph not installed")
    def test_all_settings_invalid_uses_all_defaults(self):
        """Test that all invalid settings fall back to defaults"""
        from unittest.mock import MagicMock
        from langgraph_orchestrator import (
            get_degraded_persistence_checkpointer,
            OOMProtectedMemorySaver,
        )

        mock_primary = MagicMock()

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_checkpoint_failover = True
            mock_settings.max_degraded_workflows_per_worker = "not_a_number"
            mock_settings.degraded_checkpoint_memory_warning_mb = None
            mock_settings.degraded_checkpoint_memory_hard_limit_mb = []
            mock_settings.degraded_checkpoint_max_per_thread = {}

            with patch('langgraph_orchestrator.logger'):
                result = get_degraded_persistence_checkpointer(
                    primary=mock_primary,
                    trace_id="test-trace",
                )

        assert isinstance(result._fallback, OOMProtectedMemorySaver)
        assert result._fallback._max_workflows == 100
        assert result._fallback._memory_warning_mb == 512
        assert result._fallback._memory_hard_limit_mb == 1024
        assert result._fallback._max_checkpoints_per_thread == 10
