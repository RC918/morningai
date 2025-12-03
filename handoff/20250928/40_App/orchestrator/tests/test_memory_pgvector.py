"""
Tests for PGVector Memory Store

Phase 0-Lite: Targeted tests for AI-critical orchestrator modules
"""
import pytest
from unittest.mock import Mock, patch

from orchestrator.memory.pgvector_store import (
    get_client,
    embed,
    save_text,
    recall_top,
    recall_recent,
    search_similar,
    search_by_key_prefix,
    delete_by_key,
    get_memory_stats,
)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    client = Mock()

    # Mock table operations
    table_mock = Mock()
    table_mock.insert = Mock(return_value=Mock(execute=Mock()))
    table_mock.select = Mock(return_value=table_mock)
    table_mock.order = Mock(return_value=table_mock)
    table_mock.limit = Mock(return_value=table_mock)
    table_mock.execute = Mock(return_value=Mock(data=[
        {"id": 1, "key": "test1", "text": "Test memory 1"},
        {"id": 2, "key": "test2", "text": "Test memory 2"}
    ]))

    client.table = Mock(return_value=table_mock)

    return client


class TestGetClient:
    """Test get_client function"""

    @patch('orchestrator.memory.pgvector_store.SUPABASE_SERVICE_ROLE_KEY', "test-key")
    @patch('orchestrator.memory.pgvector_store.SUPABASE_URL', "https://test.supabase.co")
    @patch('orchestrator.memory.pgvector_store.create_client')
    def test_get_client_with_credentials(self, mock_create_client, mock_supabase_client):
        """Test get_client returns client when credentials available"""
        mock_create_client.return_value = mock_supabase_client

        client = get_client()

        assert client is not None
        mock_create_client.assert_called_once_with(
            "https://test.supabase.co",
            "test-key"
        )

    @patch('orchestrator.memory.pgvector_store.SUPABASE_SERVICE_ROLE_KEY', None)
    @patch('orchestrator.memory.pgvector_store.SUPABASE_URL', None)
    @patch('orchestrator.memory.pgvector_store.create_client')
    def test_get_client_without_credentials(self, mock_create_client):
        """Test get_client returns None when credentials missing"""
        client = get_client()

        assert client is None
        mock_create_client.assert_not_called()

    @patch('orchestrator.memory.pgvector_store.SUPABASE_SERVICE_ROLE_KEY', "test-key")
    @patch('orchestrator.memory.pgvector_store.SUPABASE_URL', "https://test.supabase.co")
    @patch('orchestrator.memory.pgvector_store.create_client')
    def test_get_client_handles_exception(self, mock_create_client):
        """Test get_client handles Supabase client creation failure"""
        mock_create_client.side_effect = Exception("Connection failed")

        client = get_client()

        assert client is None


class TestEmbed:
    """Test embed function using EmbeddingClient abstraction"""

    @patch('orchestrator.memory.pgvector_store.get_embedding_client')
    def test_embed_with_api_key(self, mock_get_embedding_client):
        """Test embed delegates to EmbeddingClient"""
        mock_client = Mock()
        mock_client.embed.return_value = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        mock_get_embedding_client.return_value = mock_client

        embedding = embed("Test text for embedding")

        assert embedding is not None
        assert len(embedding) == 1536
        mock_client.embed.assert_called_once_with("Test text for embedding")

    @patch('orchestrator.memory.pgvector_store.get_embedding_client')
    def test_embed_without_api_key(self, mock_get_embedding_client):
        """Test embed returns None when EmbeddingClient is unavailable"""
        mock_client = Mock()
        mock_client.embed.return_value = None
        mock_get_embedding_client.return_value = mock_client

        embedding = embed("Test text")

        assert embedding is None

    @patch('orchestrator.memory.pgvector_store.get_embedding_client')
    def test_embed_handles_exception(self, mock_get_embedding_client):
        """Test embed propagates None when EmbeddingClient fails"""
        mock_client = Mock()
        mock_client.embed.return_value = None  # EmbeddingClient handles exceptions internally
        mock_get_embedding_client.return_value = mock_client

        embedding = embed("Test text")

        assert embedding is None
        mock_client.embed.assert_called_once_with("Test text")


class TestSaveText:
    """Test save_text function"""

    @patch('orchestrator.memory.pgvector_store.embed')
    @patch('orchestrator.memory.pgvector_store.get_client')
    @patch('orchestrator.memory.pgvector_store.settings')
    def test_save_text_success(self, mock_settings, mock_get_client, mock_embed, mock_supabase_client):
        """Test save_text successfully saves text with embedding"""
        mock_settings.memory_table = "memory"
        mock_get_client.return_value = mock_supabase_client
        mock_embed.return_value = [0.1, 0.2, 0.3] * 512

        save_text("test-key", "Test memory text")

        # Verify embed was called
        mock_embed.assert_called_once_with("Test memory text")

        # Verify Supabase insert was called
        mock_supabase_client.table.assert_called_once_with("memory")
        table_mock = mock_supabase_client.table.return_value
        table_mock.insert.assert_called_once()

        # Verify insert data
        insert_data = table_mock.insert.call_args[0][0]
        assert insert_data["key"] == "test-key"
        assert insert_data["text"] == "Test memory text"
        assert len(insert_data["embedding"]) == 1536

    @patch('orchestrator.memory.pgvector_store.embed')
    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_save_text_without_client(self, mock_get_client, mock_embed):
        """Test save_text handles missing Supabase client"""
        mock_get_client.return_value = None
        mock_embed.return_value = [0.1, 0.2, 0.3]

        # Should not raise exception
        save_text("test-key", "Test text")

        mock_embed.assert_not_called()

    @patch('orchestrator.memory.pgvector_store.embed')
    @patch('orchestrator.memory.pgvector_store.get_client')
    @patch('orchestrator.memory.pgvector_store.settings')
    def test_save_text_with_embedding_failure(self, mock_settings, mock_get_client, mock_embed, mock_supabase_client):
        """Test save_text handles embedding failure gracefully by storing NULL"""
        mock_settings.memory_table = "memory"
        mock_get_client.return_value = mock_supabase_client
        mock_embed.return_value = None  # Embedding failed

        result = save_text("test-key", "Test text")

        assert result is True
        table_mock = mock_supabase_client.table.return_value
        table_mock.insert.assert_called_once()
        insert_data = table_mock.insert.call_args[0][0]
        assert insert_data["embedding"] is None

    @patch('orchestrator.memory.pgvector_store.embed')
    @patch('orchestrator.memory.pgvector_store.get_client')
    @patch('orchestrator.memory.pgvector_store.settings')
    def test_save_text_handles_insert_exception(self, mock_settings, mock_get_client, mock_embed, mock_supabase_client):
        """Test save_text handles Supabase insert failure"""
        mock_settings.memory_table = "memory"
        mock_get_client.return_value = mock_supabase_client
        mock_embed.return_value = [0.1, 0.2, 0.3]

        # Make insert raise exception
        table_mock = mock_supabase_client.table.return_value
        table_mock.insert.side_effect = Exception("Insert failed")

        # Should not raise exception
        save_text("test-key", "Test text")


class TestRecallTop:
    """Test recall_top function"""

    @patch('orchestrator.memory.pgvector_store.get_client')
    @patch('orchestrator.memory.pgvector_store.settings')
    def test_recall_top_success(self, mock_settings, mock_get_client, mock_supabase_client):
        """Test recall_top retrieves recent memories"""
        mock_settings.memory_table = "memory"
        mock_get_client.return_value = mock_supabase_client

        memories = recall_top("test keywords", limit=5)

        assert len(memories) == 2
        assert memories[0]["key"] == "test1"
        assert memories[1]["key"] == "test2"

        # Verify query was constructed correctly
        mock_supabase_client.table.assert_called_once_with("memory")
        table_mock = mock_supabase_client.table.return_value
        table_mock.select.assert_called_once_with("*")
        table_mock.order.assert_called_once_with("id", desc=True)
        table_mock.limit.assert_called_once_with(5)
        table_mock.execute.assert_called_once()

    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_recall_top_without_client(self, mock_get_client):
        """Test recall_top handles missing Supabase client"""
        mock_get_client.return_value = None

        memories = recall_top("test keywords")

        assert memories == []

    @patch('orchestrator.memory.pgvector_store.get_client')
    @patch('orchestrator.memory.pgvector_store.settings')
    def test_recall_top_with_empty_result(self, mock_settings, mock_get_client, mock_supabase_client):
        """Test recall_top handles empty result"""
        mock_settings.memory_table = "memory"
        mock_get_client.return_value = mock_supabase_client

        # Mock empty result
        table_mock = mock_supabase_client.table.return_value
        table_mock.execute = Mock(return_value=Mock(data=None))

        memories = recall_top("test keywords")

        assert memories == []

    @patch('orchestrator.memory.pgvector_store.get_client')
    @patch('orchestrator.memory.pgvector_store.settings')
    def test_recall_top_handles_exception(self, mock_settings, mock_get_client, mock_supabase_client):
        """Test recall_top handles query exception"""
        mock_settings.memory_table = "memory"
        mock_get_client.return_value = mock_supabase_client

        # Make query raise exception
        table_mock = mock_supabase_client.table.return_value
        table_mock.select.side_effect = Exception("Query failed")

        memories = recall_top("test keywords")

        assert memories == []

    @patch('orchestrator.memory.pgvector_store.get_client')
    @patch('orchestrator.memory.pgvector_store.settings')
    def test_recall_top_custom_limit(self, mock_settings, mock_get_client, mock_supabase_client):
        """Test recall_top respects custom limit parameter"""
        mock_settings.memory_table = "memory"
        mock_get_client.return_value = mock_supabase_client

        recall_top("test keywords", limit=10)

        table_mock = mock_supabase_client.table.return_value
        table_mock.limit.assert_called_once_with(10)


class TestSearchSimilar:
    """Test search_similar function (Phase 2 vector search)"""

    @patch('orchestrator.memory.pgvector_store.embed')
    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_search_similar_success(self, mock_get_client, mock_embed, mock_supabase_client):
        """Test search_similar uses vector similarity search"""
        mock_get_client.return_value = mock_supabase_client
        mock_embed.return_value = [0.1, 0.2, 0.3] * 512

        rpc_mock = Mock()
        rpc_mock.execute = Mock(return_value=Mock(data=[
            {"id": 1, "key": "test1", "text": "Similar memory", "similarity": 0.95}
        ]))
        mock_supabase_client.rpc = Mock(return_value=rpc_mock)

        memories = search_similar("test query", limit=5, threshold=0.7)

        assert len(memories) == 1
        assert memories[0]["similarity"] == 0.95
        mock_supabase_client.rpc.assert_called_once()

    @patch('orchestrator.memory.pgvector_store.embed')
    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_search_similar_fallback_on_no_embedding(self, mock_get_client, mock_embed, mock_supabase_client):
        """Test search_similar falls back to recent when embedding fails"""
        mock_get_client.return_value = mock_supabase_client
        mock_embed.return_value = None

        memories = search_similar("test query")

        assert len(memories) == 2

    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_search_similar_no_client(self, mock_get_client):
        """Test search_similar handles missing client"""
        mock_get_client.return_value = None

        memories = search_similar("test query")

        assert memories == []


class TestRecallRecent:
    """Test recall_recent function"""

    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_recall_recent_success(self, mock_get_client, mock_supabase_client):
        """Test recall_recent retrieves recent memories"""
        mock_get_client.return_value = mock_supabase_client

        memories = recall_recent(limit=5)

        assert len(memories) == 2
        mock_supabase_client.table.assert_called_once()

    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_recall_recent_no_client(self, mock_get_client):
        """Test recall_recent handles missing client"""
        mock_get_client.return_value = None

        memories = recall_recent()

        assert memories == []


class TestSearchByKeyPrefix:
    """Test search_by_key_prefix function"""

    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_search_by_key_prefix_success(self, mock_get_client, mock_supabase_client):
        """Test search_by_key_prefix filters by prefix"""
        mock_get_client.return_value = mock_supabase_client

        table_mock = mock_supabase_client.table.return_value
        table_mock.like = Mock(return_value=table_mock)

        memories = search_by_key_prefix("test", limit=10)

        assert len(memories) == 2
        table_mock.like.assert_called_once_with("key", "test%")

    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_search_by_key_prefix_no_client(self, mock_get_client):
        """Test search_by_key_prefix handles missing client"""
        mock_get_client.return_value = None

        memories = search_by_key_prefix("test")

        assert memories == []


class TestDeleteByKey:
    """Test delete_by_key function"""

    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_delete_by_key_success(self, mock_get_client, mock_supabase_client):
        """Test delete_by_key deletes memory entry"""
        mock_get_client.return_value = mock_supabase_client

        table_mock = mock_supabase_client.table.return_value
        table_mock.delete = Mock(return_value=table_mock)
        table_mock.eq = Mock(return_value=table_mock)

        result = delete_by_key("test-key")

        assert result is True
        table_mock.delete.assert_called_once()
        table_mock.eq.assert_called_once_with("key", "test-key")

    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_delete_by_key_no_client(self, mock_get_client):
        """Test delete_by_key handles missing client"""
        mock_get_client.return_value = None

        result = delete_by_key("test-key")

        assert result is False


class TestGetMemoryStats:
    """Test get_memory_stats function"""

    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_get_memory_stats_success(self, mock_get_client, mock_supabase_client):
        """Test get_memory_stats returns statistics"""
        mock_get_client.return_value = mock_supabase_client

        table_mock = mock_supabase_client.table.return_value
        table_mock.not_ = Mock(return_value=table_mock)
        table_mock.is_ = Mock(return_value=table_mock)

        stats = get_memory_stats()

        assert stats["enabled"] is True
        assert "total_records" in stats

    @patch('orchestrator.memory.pgvector_store.get_client')
    def test_get_memory_stats_no_client(self, mock_get_client):
        """Test get_memory_stats handles missing client"""
        mock_get_client.return_value = None

        stats = get_memory_stats()

        assert stats["enabled"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
