"""
Tests for Persistence DB Writer Module

Phase 0-Lite Supplement: Targeted tests for agent_tasks persistence
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add orchestrator to path (standard pattern for all orchestrator tests)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persistence.db_writer import (  # noqa: E402
    normalize_and_validate_uuid,
    fetch_user_tenant_id,
    upsert_task_queued,
    upsert_task_running,
    upsert_task_done,
    upsert_task_error
)
from exceptions import (  # noqa: E402
    DatabaseReadError,
    TenantResolutionError
)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    client = Mock()

    # Mock table operations
    table_mock = Mock()
    table_mock.select = Mock(return_value=table_mock)
    table_mock.eq = Mock(return_value=table_mock)
    table_mock.single = Mock(return_value=table_mock)
    table_mock.upsert = Mock(return_value=table_mock)
    table_mock.execute = Mock(return_value=Mock(data={"tenant_id": "test-tenant-123"}))

    client.table = Mock(return_value=table_mock)

    return client


class TestNormalizeAndValidateUuid:
    """Test normalize_and_validate_uuid function"""

    def test_pure_uuid_fast_path(self):
        """Test that pure UUIDs are validated without regex (fast path)"""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = normalize_and_validate_uuid(test_uuid, "test_field")
        assert result == test_uuid

    def test_prefixed_uuid_extraction(self):
        """Test extraction of UUID from prefixed string"""
        prefixed_id = "phase1-stg-test-550e8400-e29b-41d4-a716-446655440000"
        expected_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = normalize_and_validate_uuid(prefixed_id, "task_id")
        assert result == expected_uuid

    def test_multiple_uuids_extracts_first(self):
        """Test that first UUID is extracted when multiple are present"""
        multi_uuid = "prefix-550e8400-e29b-41d4-a716-446655440000-suffix-660e8400-e29b-41d4-a716-446655440001"
        expected_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = normalize_and_validate_uuid(multi_uuid, "test_field")
        assert result == expected_uuid

    def test_uppercase_uuid_normalized(self):
        """Test that uppercase UUIDs are normalized to lowercase"""
        uppercase_uuid = "550E8400-E29B-41D4-A716-446655440000"
        expected_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = normalize_and_validate_uuid(uppercase_uuid, "test_field")
        assert result == expected_uuid

    def test_invalid_uuid_raises_error(self):
        """Test that invalid UUID raises ValueError"""
        invalid_id = "not-a-uuid-at-all"
        with pytest.raises(ValueError, match="No valid UUID found"):
            normalize_and_validate_uuid(invalid_id, "test_field")

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="No valid UUID found"):
            normalize_and_validate_uuid("", "test_field")

    def test_partial_uuid_raises_error(self):
        """Test that partial UUID raises ValueError"""
        partial_uuid = "550e8400-e29b-41d4-a716"
        with pytest.raises(ValueError, match="No valid UUID found"):
            normalize_and_validate_uuid(partial_uuid, "test_field")

    @patch('persistence.db_writer.logger')
    def test_normalization_logs_warning(self, mock_logger):
        """Test that normalization logs warning when prefix is stripped"""
        prefixed_id = "phase1-stg-test-550e8400-e29b-41d4-a716-446655440000"
        normalize_and_validate_uuid(prefixed_id, "task_id")

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "UUID normalization" in call_args[0][0]
        assert "task_id" in call_args[0][0]

    @patch('persistence.db_writer.logger')
    def test_pure_uuid_no_warning(self, mock_logger):
        """Test that pure UUID does not log warning"""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        normalize_and_validate_uuid(test_uuid, "test_field")

        # Verify no warning was logged
        mock_logger.warning.assert_not_called()


class TestFetchUserTenantId:
    """Test fetch_user_tenant_id function"""

    @patch('persistence.db_writer.get_client')
    def test_fetch_user_tenant_id_success(self, mock_get_client, mock_supabase_client):
        """Test successful tenant_id fetch"""
        mock_get_client.return_value = mock_supabase_client

        tenant_id = fetch_user_tenant_id("user-123")

        assert tenant_id == "test-tenant-123"
        mock_supabase_client.table.assert_called_once_with("user_profiles")

    @patch('persistence.db_writer.get_client')
    def test_fetch_user_tenant_id_no_client(self, mock_get_client):
        """Test fetch_user_tenant_id handles missing client"""
        mock_get_client.return_value = None

        # The function raises DatabaseReadError (wrapping DatabaseConnectionError)
        with pytest.raises(DatabaseReadError):
            fetch_user_tenant_id("user-123")

    @patch('persistence.db_writer.get_client')
    def test_fetch_user_tenant_id_no_profile(self, mock_get_client, mock_supabase_client):
        """Test fetch_user_tenant_id handles missing user profile"""
        mock_get_client.return_value = mock_supabase_client

        # Mock empty response - need to rebuild the chain
        table_mock = Mock()
        table_mock.select = Mock(return_value=table_mock)
        table_mock.eq = Mock(return_value=table_mock)
        table_mock.single = Mock(return_value=table_mock)
        table_mock.execute = Mock(return_value=Mock(data=None))

        mock_supabase_client.table = Mock(return_value=table_mock)

        with pytest.raises(TenantResolutionError) as exc_info:
            fetch_user_tenant_id("user-123")

        assert "No user_profile found" in str(exc_info.value)

    @patch('persistence.db_writer.get_client')
    def test_fetch_user_tenant_id_database_error(self, mock_get_client, mock_supabase_client):
        """Test fetch_user_tenant_id handles database errors"""
        mock_get_client.return_value = mock_supabase_client

        # Mock database error - need to rebuild the chain
        table_mock = Mock()
        table_mock.select = Mock(return_value=table_mock)
        table_mock.eq = Mock(return_value=table_mock)
        table_mock.single = Mock(return_value=table_mock)
        table_mock.execute = Mock(side_effect=Exception("Database connection failed"))

        mock_supabase_client.table = Mock(return_value=table_mock)

        with pytest.raises(DatabaseReadError):
            fetch_user_tenant_id("user-123")


class TestUpsertTaskQueued:
    """Test upsert_task_queued function"""

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_queued_success(self, mock_get_client, mock_supabase_client):
        """Test successful task queued upsert"""
        mock_get_client.return_value = mock_supabase_client

        result = upsert_task_queued(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001",
            question="Test question",
            job_id="job-123",
            tenant_id="tenant-123"
        )

        assert result is True
        mock_supabase_client.table.assert_called_once_with("agent_tasks")

        # Verify upsert was called
        table_mock = mock_supabase_client.table.return_value
        table_mock.upsert.assert_called_once()

        # Verify data structure
        upsert_data = table_mock.upsert.call_args[0][0]
        assert upsert_data["task_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert upsert_data["trace_id"] == "660e8400-e29b-41d4-a716-446655440001"
        assert upsert_data["question"] == "Test question"
        assert upsert_data["status"] == "queued"
        assert upsert_data["job_id"] == "job-123"
        assert upsert_data["tenant_id"] == "tenant-123"

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_queued_default_tenant(self, mock_get_client, mock_supabase_client):
        """Test task queued upsert uses default tenant when not provided"""
        mock_get_client.return_value = mock_supabase_client

        result = upsert_task_queued(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001",
            question="Test question"
        )

        assert result is True

        # Verify default tenant_id
        table_mock = mock_supabase_client.table.return_value
        upsert_data = table_mock.upsert.call_args[0][0]
        assert upsert_data["tenant_id"] == "00000000-0000-0000-0000-000000000001"

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_queued_handles_exception(self, mock_get_client, mock_supabase_client):
        """Test task queued upsert handles exceptions gracefully"""
        mock_get_client.return_value = mock_supabase_client

        # Mock upsert failure
        table_mock = mock_supabase_client.table.return_value
        table_mock.upsert.side_effect = Exception("Database write failed")

        result = upsert_task_queued(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001",
            question="Test question"
        )

        assert result is False


class TestUpsertTaskRunning:
    """Test upsert_task_running function"""

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_running_success(self, mock_get_client, mock_supabase_client):
        """Test successful task running upsert"""
        mock_get_client.return_value = mock_supabase_client

        result = upsert_task_running(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001",
            tenant_id="tenant-123"
        )

        assert result is True

        # Verify data structure
        table_mock = mock_supabase_client.table.return_value
        upsert_data = table_mock.upsert.call_args[0][0]
        assert upsert_data["task_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert upsert_data["status"] == "running"
        assert "started_at" in upsert_data
        assert upsert_data["tenant_id"] == "tenant-123"

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_running_default_tenant(self, mock_get_client, mock_supabase_client):
        """Test task running upsert uses default tenant"""
        mock_get_client.return_value = mock_supabase_client

        result = upsert_task_running(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001"
        )

        assert result is True

        table_mock = mock_supabase_client.table.return_value
        upsert_data = table_mock.upsert.call_args[0][0]
        assert upsert_data["tenant_id"] == "00000000-0000-0000-0000-000000000001"

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_running_handles_exception(self, mock_get_client, mock_supabase_client):
        """Test task running upsert handles exceptions"""
        mock_get_client.return_value = mock_supabase_client

        table_mock = mock_supabase_client.table.return_value
        table_mock.upsert.side_effect = Exception("Database error")

        result = upsert_task_running(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001"
        )

        assert result is False


class TestUpsertTaskDone:
    """Test upsert_task_done function"""

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_done_success(self, mock_get_client, mock_supabase_client):
        """Test successful task done upsert"""
        mock_get_client.return_value = mock_supabase_client

        result = upsert_task_done(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001",
            pr_url="https://github.com/test/repo/pull/123",
            tenant_id="tenant-123"
        )

        assert result is True

        # Verify data structure
        table_mock = mock_supabase_client.table.return_value
        upsert_data = table_mock.upsert.call_args[0][0]
        assert upsert_data["task_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert upsert_data["status"] == "done"
        assert upsert_data["pr_url"] == "https://github.com/test/repo/pull/123"
        assert "finished_at" in upsert_data
        assert upsert_data["tenant_id"] == "tenant-123"

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_done_handles_exception(self, mock_get_client, mock_supabase_client):
        """Test task done upsert handles exceptions"""
        mock_get_client.return_value = mock_supabase_client

        table_mock = mock_supabase_client.table.return_value
        table_mock.upsert.side_effect = Exception("Database error")

        result = upsert_task_done(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001",
            pr_url="https://github.com/test/repo/pull/123"
        )

        assert result is False


class TestUpsertTaskError:
    """Test upsert_task_error function"""

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_error_success(self, mock_get_client, mock_supabase_client):
        """Test successful task error upsert"""
        mock_get_client.return_value = mock_supabase_client

        result = upsert_task_error(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001",
            error_msg="Test error message",
            tenant_id="tenant-123"
        )

        assert result is True

        # Verify data structure
        table_mock = mock_supabase_client.table.return_value
        upsert_data = table_mock.upsert.call_args[0][0]
        assert upsert_data["task_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert upsert_data["status"] == "error"
        assert upsert_data["error_msg"] == "Test error message"
        assert "finished_at" in upsert_data
        assert upsert_data["tenant_id"] == "tenant-123"

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_error_truncates_long_message(self, mock_get_client, mock_supabase_client):
        """Test task error upsert truncates long error messages"""
        mock_get_client.return_value = mock_supabase_client

        long_error = "x" * 600  # 600 characters

        result = upsert_task_error(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001",
            error_msg=long_error
        )

        assert result is True

        # Verify error message is truncated to 500 chars
        table_mock = mock_supabase_client.table.return_value
        upsert_data = table_mock.upsert.call_args[0][0]
        assert len(upsert_data["error_msg"]) == 500

    @patch('persistence.db_writer.get_client')
    def test_upsert_task_error_handles_exception(self, mock_get_client, mock_supabase_client):
        """Test task error upsert handles exceptions"""
        mock_get_client.return_value = mock_supabase_client

        table_mock = mock_supabase_client.table.return_value
        table_mock.upsert.side_effect = Exception("Database error")

        result = upsert_task_error(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            trace_id="660e8400-e29b-41d4-a716-446655440001",
            error_msg="Test error"
        )

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
