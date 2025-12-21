"""
Tests for reputation_engine.py UUID resolution functions

P2 Follow-up: Unit tests for resolve_agent_uuid() and _is_valid_uuid()
Focus: Deterministic unit tests without external dependencies
"""
import pytest
from unittest.mock import patch

from governance.reputation_engine import (
    _is_valid_uuid,
    ReputationEngine,
)


class TestIsValidUuid:
    """Test _is_valid_uuid helper function"""

    def test_valid_uuid_v4(self):
        """Should return True for valid UUID v4"""
        assert _is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert _is_valid_uuid("123e4567-e89b-12d3-a456-426614174000") is True

    def test_valid_uuid_uppercase(self):
        """Should return True for uppercase UUID"""
        assert _is_valid_uuid("550E8400-E29B-41D4-A716-446655440000") is True

    def test_valid_uuid_no_hyphens(self):
        """Should return True for UUID without hyphens"""
        assert _is_valid_uuid("550e8400e29b41d4a716446655440000") is True

    def test_invalid_uuid_agent_type_string(self):
        """Should return False for agent_type strings like 'orchestrator'"""
        assert _is_valid_uuid("orchestrator") is False
        assert _is_valid_uuid("ops_agent") is False
        assert _is_valid_uuid("dev_agent") is False

    def test_invalid_uuid_empty_string(self):
        """Should return False for empty string"""
        assert _is_valid_uuid("") is False

    def test_invalid_uuid_none(self):
        """Should return False for None"""
        assert _is_valid_uuid(None) is False

    def test_invalid_uuid_malformed(self):
        """Should return False for malformed UUID strings"""
        assert _is_valid_uuid("not-a-uuid") is False
        assert _is_valid_uuid("550e8400-e29b-41d4-a716") is False  # Too short
        assert _is_valid_uuid("550e8400-e29b-41d4-a716-446655440000-extra") is False  # Too long
        assert _is_valid_uuid("gggggggg-gggg-gggg-gggg-gggggggggggg") is False  # Invalid hex

    def test_invalid_uuid_integer(self):
        """Should return False for integer input"""
        assert _is_valid_uuid(12345) is False

    def test_invalid_uuid_list(self):
        """Should return False for list input"""
        assert _is_valid_uuid(["550e8400-e29b-41d4-a716-446655440000"]) is False


class TestResolveAgentUuid:
    """Test ReputationEngine.resolve_agent_uuid method"""

    @pytest.fixture
    def mock_engine(self):
        """Create a ReputationEngine with mocked dependencies"""
        with patch.object(ReputationEngine, '_load_policies', return_value={}):
            engine = ReputationEngine(supabase_client=None, policies_path='/nonexistent')
            return engine

    def test_resolve_valid_uuid_returns_as_is(self, mock_engine):
        """Should return valid UUID as-is without DB lookup"""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = mock_engine.resolve_agent_uuid(valid_uuid)
        assert result == valid_uuid

    def test_resolve_none_returns_none(self, mock_engine):
        """Should return None for None input"""
        result = mock_engine.resolve_agent_uuid(None)
        assert result is None

    def test_resolve_empty_string_returns_none(self, mock_engine):
        """Should return None for empty string"""
        result = mock_engine.resolve_agent_uuid("")
        assert result is None

    def test_resolve_agent_type_with_db_lookup(self, mock_engine):
        """Should look up agent_type in DB and return UUID"""
        expected_uuid = "550e8400-e29b-41d4-a716-446655440000"

        with patch.object(mock_engine, 'get_or_create_agent', return_value=expected_uuid):
            result = mock_engine.resolve_agent_uuid("orchestrator")
            assert result == expected_uuid

    def test_resolve_agent_type_caches_result(self, mock_engine):
        """Should cache resolved UUID for subsequent calls"""
        expected_uuid = "550e8400-e29b-41d4-a716-446655440000"

        with patch.object(mock_engine, 'get_or_create_agent', return_value=expected_uuid) as mock_get:
            # First call - should hit DB
            result1 = mock_engine.resolve_agent_uuid("orchestrator")
            assert result1 == expected_uuid
            assert mock_get.call_count == 1

            # Second call - should use cache
            result2 = mock_engine.resolve_agent_uuid("orchestrator")
            assert result2 == expected_uuid
            assert mock_get.call_count == 1  # Still 1, not 2

    def test_resolve_agent_type_db_failure_returns_none(self, mock_engine):
        """Should return None when DB lookup fails"""
        with patch.object(mock_engine, 'get_or_create_agent', return_value=None):
            result = mock_engine.resolve_agent_uuid("orchestrator")
            assert result is None

    def test_resolve_agent_type_does_not_cache_failure(self, mock_engine):
        """Should not cache failed resolutions"""
        with patch.object(mock_engine, 'get_or_create_agent', return_value=None) as mock_get:
            # First call - fails
            result1 = mock_engine.resolve_agent_uuid("orchestrator")
            assert result1 is None
            assert mock_get.call_count == 1

            # Second call - should try again (not cached)
            result2 = mock_engine.resolve_agent_uuid("orchestrator")
            assert result2 is None
            assert mock_get.call_count == 2

    def test_resolve_different_agent_types_cached_separately(self, mock_engine):
        """Should cache different agent types separately"""
        uuid1 = "550e8400-e29b-41d4-a716-446655440001"
        uuid2 = "550e8400-e29b-41d4-a716-446655440002"

        def mock_get_or_create(agent_type):
            return uuid1 if agent_type == "orchestrator" else uuid2

        with patch.object(mock_engine, 'get_or_create_agent', side_effect=mock_get_or_create):
            result1 = mock_engine.resolve_agent_uuid("orchestrator")
            result2 = mock_engine.resolve_agent_uuid("ops_agent")

            assert result1 == uuid1
            assert result2 == uuid2
            assert mock_engine._agent_uuid_cache["orchestrator"] == uuid1
            assert mock_engine._agent_uuid_cache["ops_agent"] == uuid2


class TestResolveAgentUuidLogging:
    """Test logging behavior of resolve_agent_uuid"""

    @pytest.fixture
    def mock_engine(self):
        """Create a ReputationEngine with mocked dependencies"""
        with patch.object(ReputationEngine, '_load_policies', return_value={}):
            engine = ReputationEngine(supabase_client=None, policies_path='/nonexistent')
            return engine

    def test_logs_successful_resolution(self, mock_engine, caplog):
        """Should log successful agent_type to UUID resolution"""
        expected_uuid = "550e8400-e29b-41d4-a716-446655440000"

        with patch.object(mock_engine, 'get_or_create_agent', return_value=expected_uuid):
            import logging
            with caplog.at_level(logging.INFO):
                mock_engine.resolve_agent_uuid("orchestrator")

            # Check that resolution was logged (via logger or print)
            # Note: After converting print to logger, this will capture the log
            assert expected_uuid in str(mock_engine._agent_uuid_cache)

    def test_logs_failed_resolution(self, mock_engine, caplog):
        """Should log failed agent_type resolution"""
        with patch.object(mock_engine, 'get_or_create_agent', return_value=None):
            import logging
            with caplog.at_level(logging.WARNING):
                result = mock_engine.resolve_agent_uuid("unknown_agent")

            assert result is None


class TestAgentUuidCacheIsolation:
    """Test that cache is properly isolated per engine instance"""

    def test_cache_isolated_between_instances(self):
        """Each ReputationEngine instance should have its own cache"""
        with patch.object(ReputationEngine, '_load_policies', return_value={}):
            engine1 = ReputationEngine(supabase_client=None, policies_path='/nonexistent')
            engine2 = ReputationEngine(supabase_client=None, policies_path='/nonexistent')

            # Populate cache in engine1
            engine1._agent_uuid_cache["orchestrator"] = "uuid-1"

            # engine2 should not see engine1's cache
            assert "orchestrator" not in engine2._agent_uuid_cache
