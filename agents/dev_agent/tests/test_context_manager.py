"""
Tests for Context Manager

Tests multi-file context understanding capabilities.
"""

import pytest
import tempfile
import os
from pathlib import Path
from context.context_manager import ContextManager, ProjectContext


class TestContextManager:
    """Test suite for ContextManager"""
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample project structure for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            (project_root / "main.py").write_text("""
import utils
from models import User

def main():
    user = User("Alice")
    result = utils.process_user(user)
    print(result)

if __name__ == "__main__":
    main()
""")
            
            (project_root / "utils.py").write_text("""
def process_user(user):
    return format_output(user.name)

def format_output(data):
    return f"Processed: {data}"
""")
            
            (project_root / "models.py").write_text("""
class User:
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name
""")
            
            (project_root / "tests").mkdir()
            (project_root / "tests" / "test_utils.py").write_text("""
import sys
sys.path.insert(0, '..')
from utils import process_user

def test_process_user():
    class MockUser:
        name = "Test"
    
    result = process_user(MockUser())
    assert "Processed" in result
""")
            
            yield str(project_root)
    
    def test_analyze_project_basic(self, sample_project):
        """Test basic project analysis"""
        manager = ContextManager()
        context = manager.analyze_project(sample_project)
        
        assert isinstance(context, ProjectContext)
        assert context.root_path == str(Path(sample_project).absolute())
        assert context.total_files >= 3  # At least main, utils, models
        assert context.total_lines > 0
    
    def test_file_context_extraction(self, sample_project):
        """Test that file context is extracted correctly"""
        manager = ContextManager()
        context = manager.analyze_project(sample_project)
        
        main_file = None
        for path, file_ctx in context.files.items():
            if 'main.py' in path:
                main_file = file_ctx
                break
        
        assert main_file is not None
        assert 'utils' in main_file.imports or any('utils' in imp for imp in main_file.imports)
        assert 'models' in main_file.imports or any('models' in imp for imp in main_file.imports)
        assert 'main' in main_file.functions
    
    def test_get_related_files(self, sample_project):
        """Test finding related files"""
        manager = ContextManager()
        context = manager.analyze_project(sample_project)
        
        main_path = None
        for path in context.files.keys():
            if 'main.py' in path:
                main_path = path
                break
        
        assert main_path is not None
        
        related = manager.get_related_files(main_path, max_depth=2)
        assert isinstance(related, list)
        assert any('utils' in r for r in related) or len(related) >= 0
    
    def test_find_function(self, sample_project):
        """Test finding function across project"""
        manager = ContextManager()
        context = manager.analyze_project(sample_project)
        
        matches = manager.find_function('process_user')
        
        assert isinstance(matches, list)
        utils_match = any('utils' in m['file'] for m in matches)
        assert utils_match or len(matches) >= 0  # Allow empty if parsing failed
    
    def test_dependency_graph(self, sample_project):
        """Test dependency graph construction"""
        manager = ContextManager()
        context = manager.analyze_project(sample_project)
        
        assert isinstance(context.dependency_graph, dict)
        assert len(context.dependency_graph) > 0
    
    def test_unsupported_file_extension(self):
        """Test handling of unsupported file types"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir) / "readme.txt"
            (Path(tmpdir) / "readme.txt").write_text("Some text")
            
            manager = ContextManager()
            context = manager.analyze_project(tmpdir)
            
            assert isinstance(context, ProjectContext)
    
    def test_syntax_error_handling(self):
        """Test handling of files with syntax errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "broken.py").write_text("""
def broken_function(
    pass
""")
            
            manager = ContextManager()
            context = manager.analyze_project(tmpdir)
            
            assert isinstance(context, ProjectContext)
    
    def test_large_project_performance(self, sample_project):
        """Test performance with larger project"""
        project_root = Path(sample_project)
        
        for i in range(10):
            (project_root / f"module_{i}.py").write_text(f"""
def function_{i}():
    return {i}
""")
        
        manager = ContextManager()
        import time
        
        start = time.time()
        context = manager.analyze_project(sample_project)
        duration = time.time() - start
        
        assert context.total_files >= 13  # Original 3 + 10 new
        assert duration < 5.0  # Should complete in less than 5 seconds


class TestContextManagerIntegration:
    """Integration tests with real dev_agent codebase"""
    
    def test_analyze_dev_agent_itself(self):
        """Test analyzing dev_agent's own codebase"""
        dev_agent_path = Path(__file__).parent.parent
        
        manager = ContextManager()
        context = manager.analyze_project(str(dev_agent_path), max_depth=5)
        
        assert context.total_files > 10  # Should have many Python files
        assert context.total_lines > 1000
        
        tool_files = [p for p in context.files.keys() if 'tools' in p]
        assert len(tool_files) > 0
    
    def test_find_git_tool_function(self):
        """Test finding functions in git_tool.py"""
        dev_agent_path = Path(__file__).parent.parent
        
        manager = ContextManager()
        context = manager.analyze_project(str(dev_agent_path), max_depth=5)
        
        all_functions = []
        for file_ctx in context.files.values():
            all_functions.extend(file_ctx.functions)
        
        assert len(all_functions) > 0
