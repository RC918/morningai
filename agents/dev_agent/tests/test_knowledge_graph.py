"""
Tests for Knowledge Graph Manager
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from agents.dev_agent.knowledge.knowledge_graph import KnowledgeGraphManager


@pytest.fixture
def mock_db_config():
    """Mock database configuration."""
    return {
        "host": "localhost",
        "port": "5432",
        "database": "test_db",
        "user": "test_user",
        "password": "test_pass"
    }


@pytest.fixture
def kg_manager_no_vector(mock_db_config):
    """KnowledgeGraphManager without vector search."""
    with patch('agents.dev_agent.knowledge.knowledge_graph.psycopg2'):
        kg = KnowledgeGraphManager(
            db_config=mock_db_config,
            enable_vector_search=False
        )
        kg.db_conn = Mock()
        kg.db_conn.closed = False
        return kg


def test_initialize_schema_without_vector(kg_manager_no_vector):
    """Test schema initialization without pgvector."""
    mock_cursor = Mock()
    kg_manager_no_vector.db_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    kg_manager_no_vector.initialize_schema()
    
    assert mock_cursor.execute.called
    assert kg_manager_no_vector.db_conn.commit.called


def test_add_entity_without_embedding(kg_manager_no_vector):
    """Test adding entity without embedding."""
    mock_cursor = Mock()
    mock_cursor.fetchone.return_value = [1]
    kg_manager_no_vector.db_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    entity_id = kg_manager_no_vector.add_entity(
        session_id="test-session",
        entity_type="function",
        entity_name="test_function",
        file_path="/test/file.py",
        line_start=1,
        line_end=10,
        source_code="def test_function(): pass",
        metadata={"test": True}
    )
    
    assert entity_id == 1
    assert mock_cursor.execute.called
    assert kg_manager_no_vector.db_conn.commit.called


def test_keyword_search(kg_manager_no_vector):
    """Test keyword-based search."""
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [
        {
            "id": 1,
            "entity_type": "function",
            "entity_name": "test_func",
            "file_path": "/test.py",
            "line_start": 1,
            "line_end": 5,
            "source_code": "def test_func(): pass",
            "metadata": {}
        }
    ]
    kg_manager_no_vector.db_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    results = kg_manager_no_vector.keyword_search("test_func", top_k=10)
    
    assert len(results) == 1
    assert results[0]["entity_name"] == "test_func"
    assert mock_cursor.execute.called


def test_add_relationship(kg_manager_no_vector):
    """Test adding relationship between entities."""
    mock_cursor = Mock()
    mock_cursor.fetchone.return_value = [1]
    kg_manager_no_vector.db_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    rel_id = kg_manager_no_vector.add_relationship(
        from_entity_id=1,
        to_entity_id=2,
        relationship_type="calls",
        weight=1.0
    )
    
    assert rel_id == 1
    assert mock_cursor.execute.called


def test_get_session_stats(kg_manager_no_vector):
    """Test getting session statistics."""
    mock_cursor = Mock()
    mock_cursor.fetchone.side_effect = [
        {
            "total_entities": 10,
            "entity_types": 3,
            "files_indexed": 5,
            "last_updated": None
        },
        {"total_relationships": 15}
    ]
    mock_cursor.fetchall.return_value = [
        {"entity_type": "function", "count": 5},
        {"entity_type": "class", "count": 3},
        {"entity_type": "file", "count": 2}
    ]
    kg_manager_no_vector.db_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    stats = kg_manager_no_vector.get_session_stats("test-session")
    
    assert stats["total_entities"] == 10
    assert stats["entity_types"] == 3
    assert stats["total_relationships"] == 15
    assert len(stats["entities_by_type"]) == 3


def test_find_related_entities(kg_manager_no_vector):
    """Test finding related entities."""
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [
        {
            "id": 2,
            "entity_type": "function",
            "entity_name": "called_func",
            "file_path": "/test.py",
            "line_start": 10,
            "line_end": 15,
            "source_code": "def called_func(): pass",
            "metadata": {},
            "depth": 1,
            "path": [1, 2],
            "relationship_path": ["calls"]
        }
    ]
    kg_manager_no_vector.db_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    results = kg_manager_no_vector.find_related_entities(
        entity_id=1,
        depth=2,
        max_results=50
    )
    
    assert len(results) == 1
    assert results[0]["entity_name"] == "called_func"
    assert results[0]["depth"] == 1


def test_clear_session(kg_manager_no_vector):
    """Test clearing session data."""
    mock_cursor = Mock()
    kg_manager_no_vector.db_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    kg_manager_no_vector.clear_session("test-session")
    
    assert mock_cursor.execute.called
    assert kg_manager_no_vector.db_conn.commit.called


def test_context_manager(mock_db_config):
    """Test context manager usage."""
    with patch('agents.dev_agent.knowledge.knowledge_graph.psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_conn.closed = False
        mock_connect.return_value = mock_conn
        
        with KnowledgeGraphManager(db_config=mock_db_config, enable_vector_search=False) as kg:
            assert kg.db_conn is not None
        
        assert mock_conn.close.called


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Requires OPENAI_API_KEY and RUN_INTEGRATION_TESTS=1"
)
def test_generate_embedding_integration():
    """Integration test for embedding generation (requires OpenAI API key)."""
    kg = KnowledgeGraphManager(enable_vector_search=True)
    
    embedding = kg.generate_embedding("def hello(): return 'world'")
    
    assert embedding is not None
    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
