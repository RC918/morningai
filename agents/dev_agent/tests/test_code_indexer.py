"""
Tests for Code Indexer
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock
from agents.dev_agent.knowledge.code_indexer import CodeIndexer


@pytest.fixture
def mock_kg():
    """Mock Knowledge Graph Manager."""
    kg = Mock()
    kg.add_entity = Mock(return_value=1)
    kg.add_relationship = Mock(return_value=1)
    kg.get_entity_by_name = Mock(return_value=None)
    return kg


@pytest.fixture
def code_indexer(mock_kg):
    """Code Indexer instance."""
    return CodeIndexer(mock_kg)


@pytest.fixture
def temp_python_file():
    """Create a temporary Python file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
import os
from typing import List

class TestClass:
    def __init__(self):
        self.value = 0
    
    def method(self, x: int) -> int:
        return x * 2

def test_function(name: str) -> str:
    return f"Hello, {name}"

def another_function():
    result = test_function("World")
    return result
""")
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)


def test_should_ignore(code_indexer):
    """Test ignore pattern matching."""
    assert code_indexer.should_ignore(Path("__pycache__/test.py"))
    assert code_indexer.should_ignore(Path(".git/config"))
    assert code_indexer.should_ignore(Path("node_modules/package.json"))
    assert not code_indexer.should_ignore(Path("src/main.py"))


def test_index_python_file(code_indexer, temp_python_file, mock_kg):
    """Test indexing a Python file."""
    with open(temp_python_file, 'r') as f:
        source_code = f.read()
    
    result = code_indexer.index_python_file(
        file_path=temp_python_file,
        source_code=source_code,
        session_id="test-session",
        file_entity_id=1
    )
    
    assert result["entities_created"] > 0
    assert result["relationships_created"] > 0
    
    assert mock_kg.add_entity.called
    assert mock_kg.add_relationship.called


def test_index_file(code_indexer, temp_python_file):
    """Test indexing a single file."""
    result = code_indexer.index_file(temp_python_file, "test-session")
    
    assert result["entities_created"] >= 1
    assert result["relationships_created"] >= 0


def test_scan_directory(code_indexer):
    """Test scanning a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def hello(): pass")
        
        stats = code_indexer.scan_directory(
            directory=tmpdir,
            session_id="test-session",
            max_files=10
        )
        
        assert stats["files_scanned"] >= 1
        assert stats["files_indexed"] >= 0


def test_scan_directory_with_ignore(code_indexer):
    """Test directory scanning respects ignore patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "__pycache__").mkdir()
        (Path(tmpdir) / "__pycache__" / "test.py").write_text("ignored")
        (Path(tmpdir) / "valid.py").write_text("def hello(): pass")
        
        stats = code_indexer.scan_directory(
            directory=tmpdir,
            session_id="test-session"
        )
        
        assert stats["files_scanned"] == 1


def test_extract_entities_from_python(code_indexer, mock_kg):
    """Test extracting specific entity types."""
    source_code = """
class MyClass:
    def __init__(self):
        pass
    
    def my_method(self):
        pass

def my_function():
    pass
"""
    
    code_indexer.index_python_file(
        file_path="/test/file.py",
        source_code=source_code,
        session_id="test-session",
        file_entity_id=1
    )
    
    class_calls = [
        call for call in mock_kg.add_entity.call_args_list
        if call[1].get("entity_type") == "class"
    ]
    func_calls = [
        call for call in mock_kg.add_entity.call_args_list
        if call[1].get("entity_type") == "function"
    ]
    
    assert len(class_calls) >= 1
    assert len(func_calls) >= 2


def test_get_file_structure(code_indexer, mock_kg):
    """Test getting file structure."""
    mock_kg.db_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [
        ("/test/file.py", "function", "test_func", 1, 5, {"test": True}),
        ("/test/file.py", "class", "TestClass", 10, 20, {})
    ]
    mock_kg.db_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_kg.connect = Mock()
    
    structure = code_indexer.get_file_structure("test-session")
    
    assert "/test/file.py" in structure
    assert len(structure["/test/file.py"]["entities"]) == 2


def test_handle_syntax_error(code_indexer):
    """Test handling files with syntax errors."""
    invalid_code = "def broken( syntax error"
    
    result = code_indexer.index_python_file(
        file_path="/test/broken.py",
        source_code=invalid_code,
        session_id="test-session",
        file_entity_id=1
    )
    
    assert result["entities_created"] == 0
    assert result["relationships_created"] == 0


def test_max_file_size_limit(code_indexer):
    """Test max file size limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        large_file = Path(tmpdir) / "large.py"
        large_file.write_text("x" * 200000)
        
        stats = code_indexer.scan_directory(
            directory=tmpdir,
            session_id="test-session",
            max_file_size=100000
        )
        
        assert stats["files_scanned"] == 1
        assert stats["files_indexed"] == 0
        assert len(stats["errors"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
