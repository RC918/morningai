"""
Tests for Error-Fix Pairs Store

Phase 2: Brain Layer - pgvector similarity search for error-fix pairs
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from orchestrator.memory.error_fix_pairs import (
    ErrorFixPair,
    save_error_fix_pair,
    find_similar_errors,
    get_fix_for_error,
    update_pair_feedback,
    get_error_fix_pairs_by_type,
    get_recent_error_fix_pairs,
    get_pair_by_trace_id,
    update_error_fix_pair,
    get_error_fix_pairs_stats,
    _embed,
)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    client = Mock()

    table_mock = Mock()
    table_mock.insert = Mock(return_value=Mock(execute=Mock(return_value=Mock(data=[{"id": 1}]))))
    table_mock.select = Mock(return_value=table_mock)
    table_mock.eq = Mock(return_value=table_mock)
    table_mock.order = Mock(return_value=table_mock)
    table_mock.limit = Mock(return_value=table_mock)
    table_mock.not_ = Mock(return_value=table_mock)
    table_mock.is_ = Mock(return_value=table_mock)
    table_mock.execute = Mock(return_value=Mock(data=[
        {
            "id": 1,
            "error_text": "TypeError: cannot read property",
            "fix_text": "Add null check before accessing property",
            "error_type": "type_error",
            "fix_type": "code_change",
            "confidence_score": 0.8,
            "success_count": 4,
            "failure_count": 1,
            "similarity": 0.92
        }
    ], count=1))

    client.table = Mock(return_value=table_mock)

    rpc_mock = Mock()
    rpc_mock.execute = Mock(return_value=Mock(data=[
        {
            "id": 1,
            "error_text": "TypeError: cannot read property",
            "fix_text": "Add null check before accessing property",
            "error_type": "type_error",
            "fix_type": "code_change",
            "confidence_score": 0.8,
            "success_count": 4,
            "failure_count": 1,
            "similarity": 0.92
        }
    ]))
    client.rpc = Mock(return_value=rpc_mock)

    return client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    client = Mock()

    mock_embedding = Mock()
    mock_embedding.embedding = [0.1, 0.2, 0.3] * 512

    mock_response = Mock()
    mock_response.data = [mock_embedding]

    client.embeddings.create = Mock(return_value=mock_response)

    return client


class TestErrorFixPairDataclass:
    """Test ErrorFixPair dataclass"""

    def test_create_error_fix_pair(self):
        """Test creating an ErrorFixPair"""
        pair = ErrorFixPair(
            error_text="Test error",
            fix_text="Test fix",
            error_type="test_error",
            fix_type="code_change"
        )

        assert pair.error_text == "Test error"
        assert pair.fix_text == "Test fix"
        assert pair.error_type == "test_error"
        assert pair.fix_type == "code_change"
        assert pair.confidence_score == 0.5
        assert pair.success_count == 0
        assert pair.failure_count == 0

    def test_to_dict(self):
        """Test converting ErrorFixPair to dictionary"""
        pair = ErrorFixPair(
            error_text="Test error",
            fix_text="Test fix",
            error_type="test_error"
        )

        data = pair.to_dict()

        assert data["error_text"] == "Test error"
        assert data["fix_text"] == "Test fix"
        assert data["error_type"] == "test_error"
        assert "id" not in data

    def test_from_dict(self):
        """Test creating ErrorFixPair from dictionary"""
        data = {
            "id": 1,
            "error_text": "Test error",
            "fix_text": "Test fix",
            "error_type": "test_error",
            "confidence_score": 0.9,
            "similarity": 0.85
        }

        pair = ErrorFixPair.from_dict(data)

        assert pair.id == 1
        assert pair.error_text == "Test error"
        assert pair.fix_text == "Test fix"
        assert pair.confidence_score == 0.9
        assert pair.similarity == 0.85


class TestSaveErrorFixPair:
    """Test save_error_fix_pair function"""

    @patch('orchestrator.memory.error_fix_pairs._embed')
    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_save_error_fix_pair_success(self, mock_get_client, mock_embed, mock_supabase_client):
        """Test saving an error-fix pair successfully"""
        mock_get_client.return_value = mock_supabase_client
        mock_embed.return_value = [0.1, 0.2, 0.3] * 512

        pair_id = save_error_fix_pair(
            error_text="TypeError: cannot read property",
            fix_text="Add null check",
            error_type="type_error",
            trace_id="trace-123"
        )

        assert pair_id == 1
        mock_supabase_client.table.assert_called_once_with("error_fix_pairs")

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_save_error_fix_pair_no_client(self, mock_get_client):
        """Test save_error_fix_pair handles missing client"""
        mock_get_client.return_value = None

        pair_id = save_error_fix_pair(
            error_text="Test error",
            fix_text="Test fix"
        )

        assert pair_id is None

    @patch('orchestrator.memory.error_fix_pairs._embed')
    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_save_error_fix_pair_handles_exception(self, mock_get_client, mock_embed, mock_supabase_client):
        """Test save_error_fix_pair handles exceptions"""
        mock_get_client.return_value = mock_supabase_client
        mock_embed.return_value = [0.1, 0.2, 0.3]
        mock_supabase_client.table.return_value.insert.side_effect = Exception("Insert failed")

        pair_id = save_error_fix_pair(
            error_text="Test error",
            fix_text="Test fix"
        )

        assert pair_id is None


class TestFindSimilarErrors:
    """Test find_similar_errors function"""

    @patch('orchestrator.memory.error_fix_pairs._embed')
    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_find_similar_errors_success(self, mock_get_client, mock_embed, mock_supabase_client):
        """Test finding similar errors successfully"""
        mock_get_client.return_value = mock_supabase_client
        mock_embed.return_value = [0.1, 0.2, 0.3] * 512

        pairs = find_similar_errors("TypeError: cannot read property")

        assert len(pairs) == 1
        assert pairs[0].error_text == "TypeError: cannot read property"
        assert pairs[0].similarity == 0.92
        mock_supabase_client.rpc.assert_called_once()

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_find_similar_errors_no_client(self, mock_get_client):
        """Test find_similar_errors handles missing client"""
        mock_get_client.return_value = None

        pairs = find_similar_errors("Test error")

        assert pairs == []

    @patch('orchestrator.memory.error_fix_pairs._embed')
    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_find_similar_errors_no_embedding(self, mock_get_client, mock_embed, mock_supabase_client):
        """Test find_similar_errors handles embedding failure"""
        mock_get_client.return_value = mock_supabase_client
        mock_embed.return_value = None

        pairs = find_similar_errors("Test error")

        assert pairs == []


class TestGetFixForError:
    """Test get_fix_for_error function"""

    @patch('orchestrator.memory.error_fix_pairs.find_similar_errors')
    def test_get_fix_for_error_success(self, mock_find_similar):
        """Test getting fix for error successfully"""
        mock_find_similar.return_value = [
            ErrorFixPair(
                id=1,
                error_text="TypeError",
                fix_text="Add null check",
                confidence_score=0.8,
                similarity=0.92
            )
        ]

        fix = get_fix_for_error("TypeError: cannot read property")

        assert fix is not None
        assert fix.fix_text == "Add null check"
        assert fix.confidence_score == 0.8

    @patch('orchestrator.memory.error_fix_pairs.find_similar_errors')
    def test_get_fix_for_error_low_confidence(self, mock_find_similar):
        """Test get_fix_for_error filters by confidence"""
        mock_find_similar.return_value = [
            ErrorFixPair(
                id=1,
                error_text="TypeError",
                fix_text="Add null check",
                confidence_score=0.3,
                similarity=0.92
            )
        ]

        fix = get_fix_for_error("TypeError", min_confidence=0.5)

        assert fix is None

    @patch('orchestrator.memory.error_fix_pairs.find_similar_errors')
    def test_get_fix_for_error_no_matches(self, mock_find_similar):
        """Test get_fix_for_error handles no matches"""
        mock_find_similar.return_value = []

        fix = get_fix_for_error("Unknown error")

        assert fix is None


class TestUpdatePairFeedback:
    """Test update_pair_feedback function"""

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_update_pair_feedback_success(self, mock_get_client, mock_supabase_client):
        """Test updating pair feedback successfully"""
        mock_get_client.return_value = mock_supabase_client
        mock_supabase_client.rpc.return_value.execute.return_value = Mock(data=0.85)

        new_confidence = update_pair_feedback(pair_id=1, was_successful=True)

        assert new_confidence == 0.85
        mock_supabase_client.rpc.assert_called_once_with(
            "update_error_fix_pair_stats",
            {"pair_id": 1, "was_successful": True}
        )

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_update_pair_feedback_no_client(self, mock_get_client):
        """Test update_pair_feedback handles missing client"""
        mock_get_client.return_value = None

        result = update_pair_feedback(pair_id=1, was_successful=True)

        assert result is None


class TestGetErrorFixPairsByType:
    """Test get_error_fix_pairs_by_type function"""

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_pairs_by_type_success(self, mock_get_client, mock_supabase_client):
        """Test getting pairs by type successfully"""
        mock_get_client.return_value = mock_supabase_client

        pairs = get_error_fix_pairs_by_type("type_error")

        assert len(pairs) == 1
        assert pairs[0].error_type == "type_error"

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_pairs_by_type_no_client(self, mock_get_client):
        """Test get_error_fix_pairs_by_type handles missing client"""
        mock_get_client.return_value = None

        pairs = get_error_fix_pairs_by_type("type_error")

        assert pairs == []


class TestGetRecentErrorFixPairs:
    """Test get_recent_error_fix_pairs function"""

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_recent_pairs_success(self, mock_get_client, mock_supabase_client):
        """Test getting recent pairs successfully"""
        mock_get_client.return_value = mock_supabase_client

        pairs = get_recent_error_fix_pairs(limit=10)

        assert len(pairs) == 1

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_recent_pairs_no_client(self, mock_get_client):
        """Test get_recent_error_fix_pairs handles missing client"""
        mock_get_client.return_value = None

        pairs = get_recent_error_fix_pairs()

        assert pairs == []


class TestGetPairByTraceId:
    """Test get_pair_by_trace_id function"""

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_pair_by_trace_id_success(self, mock_get_client):
        """Test getting pair by trace_id successfully"""
        mock_client = Mock()
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[{
            "id": 1,
            "trace_id": "trace-123",
            "error_text": "TypeError: cannot read property",
            "fix_text": "Add null check",
            "error_type": "type_error",
            "fix_type": "code_change",
            "confidence_score": 0.8,
            "success_count": 4,
            "failure_count": 1,
            "error_context": None,
            "fix_metadata": None
        }])
        mock_client.table.return_value = mock_table
        mock_get_client.return_value = mock_client

        pair = get_pair_by_trace_id("trace-123")

        assert pair is not None
        assert pair.id == 1
        assert pair.error_text == "TypeError: cannot read property"
        assert pair.fix_text == "Add null check"
        mock_table.eq.assert_called_once_with("trace_id", "trace-123")

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_pair_by_trace_id_with_json_string_fields(self, mock_get_client):
        """Test get_pair_by_trace_id parses JSON string fields correctly"""
        mock_client = Mock()
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[{
            "id": 2,
            "trace_id": "trace-456",
            "error_text": "ImportError",
            "fix_text": "Install package",
            "error_type": "import_error",
            "fix_type": "dependency",
            "confidence_score": 0.9,
            "success_count": 10,
            "failure_count": 0,
            "error_context": '{"file": "main.py", "line": 42}',
            "fix_metadata": '{"package": "requests", "version": "2.28.0"}'
        }])
        mock_client.table.return_value = mock_table
        mock_get_client.return_value = mock_client

        pair = get_pair_by_trace_id("trace-456")

        assert pair is not None
        assert pair.error_context == {"file": "main.py", "line": 42}
        assert pair.fix_metadata == {"package": "requests", "version": "2.28.0"}

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_pair_by_trace_id_not_found(self, mock_get_client):
        """Test get_pair_by_trace_id returns None when not found"""
        mock_client = Mock()
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[])
        mock_client.table.return_value = mock_table
        mock_get_client.return_value = mock_client

        pair = get_pair_by_trace_id("nonexistent-trace")

        assert pair is None

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_pair_by_trace_id_no_client(self, mock_get_client):
        """Test get_pair_by_trace_id handles missing client"""
        mock_get_client.return_value = None

        pair = get_pair_by_trace_id("trace-123")

        assert pair is None

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_pair_by_trace_id_handles_exception(self, mock_get_client):
        """Test get_pair_by_trace_id handles exceptions gracefully"""
        mock_client = Mock()
        mock_client.table.side_effect = Exception("Database error")
        mock_get_client.return_value = mock_client

        pair = get_pair_by_trace_id("trace-123")

        assert pair is None

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_pair_by_trace_id_invalid_json_fields(self, mock_get_client):
        """Test get_pair_by_trace_id handles invalid JSON in fields"""
        mock_client = Mock()
        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[{
            "id": 3,
            "trace_id": "trace-789",
            "error_text": "SyntaxError",
            "fix_text": "Fix syntax",
            "error_type": "syntax_error",
            "fix_type": "code_change",
            "confidence_score": 0.7,
            "success_count": 2,
            "failure_count": 1,
            "error_context": "invalid json {",
            "fix_metadata": "also invalid {"
        }])
        mock_client.table.return_value = mock_table
        mock_get_client.return_value = mock_client

        pair = get_pair_by_trace_id("trace-789")

        assert pair is not None
        assert pair.error_context is None
        assert pair.fix_metadata is None


class TestUpdateErrorFixPair:
    """Test update_error_fix_pair function (Issue #1838)"""

    @patch('orchestrator.memory.error_fix_pairs._embed')
    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_update_error_fix_pair_success(self, mock_get_client, mock_embed):
        """Test updating an error-fix pair successfully"""
        mock_client = Mock()
        mock_table = Mock()
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[{"id": 1}])
        mock_client.table.return_value = mock_table
        mock_get_client.return_value = mock_client
        test_embedding = [0.1, 0.2, 0.3] * 512
        mock_embed.return_value = test_embedding

        result = update_error_fix_pair(
            pair_id=1,
            fix_text="Updated fix text",
            fix_type="resolved"
        )

        assert result is True
        mock_table.update.assert_called_once_with({
            "fix_text": "Updated fix text",
            "fix_embedding": test_embedding,
            "fix_type": "resolved"
        })
        mock_table.eq.assert_called_once_with("id", 1)
        mock_embed.assert_called_once_with("Updated fix text")

    @patch('orchestrator.memory.error_fix_pairs._embed')
    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_update_error_fix_pair_with_metadata(self, mock_get_client, mock_embed):
        """Test updating an error-fix pair with metadata"""
        import json
        mock_client = Mock()
        mock_table = Mock()
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[{"id": 1}])
        mock_client.table.return_value = mock_table
        mock_get_client.return_value = mock_client
        test_embedding = [0.1, 0.2, 0.3] * 512
        mock_embed.return_value = test_embedding
        test_metadata = {"status": "resolved", "updated_at": 1234567890}

        result = update_error_fix_pair(
            pair_id=1,
            fix_text="Updated fix",
            fix_type="resolved",
            fix_metadata=test_metadata
        )

        assert result is True
        mock_table.update.assert_called_once_with({
            "fix_text": "Updated fix",
            "fix_embedding": test_embedding,
            "fix_type": "resolved",
            "fix_metadata": json.dumps(test_metadata)
        })

    @patch('orchestrator.memory.error_fix_pairs._embed')
    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_update_error_fix_pair_without_embedding(self, mock_get_client, mock_embed):
        """Test updating an error-fix pair without generating embedding"""
        mock_client = Mock()
        mock_table = Mock()
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[{"id": 1}])
        mock_client.table.return_value = mock_table
        mock_get_client.return_value = mock_client

        result = update_error_fix_pair(
            pair_id=1,
            fix_text="Updated fix",
            generate_embedding=False
        )

        assert result is True
        mock_embed.assert_not_called()
        # Verify payload does not contain fix_embedding when generate_embedding=False
        mock_table.update.assert_called_once_with({
            "fix_text": "Updated fix"
        })

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_update_error_fix_pair_no_client(self, mock_get_client):
        """Test update_error_fix_pair handles missing client"""
        mock_get_client.return_value = None

        result = update_error_fix_pair(pair_id=1, fix_text="Updated fix")

        assert result is False

    @patch('orchestrator.memory.error_fix_pairs._embed')
    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_update_error_fix_pair_handles_exception(self, mock_get_client, mock_embed):
        """Test update_error_fix_pair handles exceptions gracefully"""
        mock_client = Mock()
        mock_client.table.side_effect = Exception("Database error")
        mock_get_client.return_value = mock_client
        mock_embed.return_value = [0.1, 0.2, 0.3] * 512

        result = update_error_fix_pair(pair_id=1, fix_text="Updated fix")

        assert result is False


class TestGetErrorFixPairsStats:
    """Test get_error_fix_pairs_stats function"""

    @patch('orchestrator.memory.error_fix_pairs.get_recent_error_fix_pairs')
    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_stats_success(self, mock_get_client, mock_get_recent, mock_supabase_client):
        """Test getting stats successfully"""
        mock_get_client.return_value = mock_supabase_client
        mock_get_recent.return_value = [
            ErrorFixPair(error_text="e1", fix_text="f1", error_type="type_error"),
            ErrorFixPair(error_text="e2", fix_text="f2", error_type="type_error"),
        ]

        stats = get_error_fix_pairs_stats()

        assert stats["enabled"] is True
        assert "total_pairs" in stats

    @patch('orchestrator.memory.error_fix_pairs._get_supabase_client')
    def test_get_stats_no_client(self, mock_get_client):
        """Test get_error_fix_pairs_stats handles missing client"""
        mock_get_client.return_value = None

        stats = get_error_fix_pairs_stats()

        assert stats["enabled"] is False


class TestEmbed:
    """Test _embed function using unified EmbeddingClient"""

    @patch('orchestrator.memory.error_fix_pairs.get_embedding_client')
    def test_embed_success(self, mock_get_client):
        """Test embedding generation success via EmbeddingClient"""
        mock_client = MagicMock()
        mock_client.embed.return_value = [0.1] * 1536
        mock_get_client.return_value = mock_client

        embedding = _embed("Test text")

        assert embedding is not None
        assert len(embedding) == 1536
        mock_client.embed.assert_called_once_with("Test text")

    @patch('orchestrator.memory.error_fix_pairs.get_embedding_client')
    def test_embed_returns_none_on_client_failure(self, mock_get_client):
        """Test _embed handles EmbeddingClient returning None"""
        mock_client = MagicMock()
        mock_client.embed.return_value = None
        mock_get_client.return_value = mock_client

        embedding = _embed("Test text")

        assert embedding is None

    @patch('orchestrator.memory.error_fix_pairs.get_embedding_client')
    def test_embed_handles_exception(self, mock_get_client):
        """Test _embed handles exceptions from EmbeddingClient"""
        mock_get_client.side_effect = Exception("API error")

        embedding = _embed("Test text")

        assert embedding is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
