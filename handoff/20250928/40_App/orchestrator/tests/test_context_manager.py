#!/usr/bin/env python3
"""
Unit tests for Context Manager - Phase 1 (B) Supplemental Implementation
"""
import os
import tempfile
from unittest.mock import patch
from context_manager import (
    tokenize_text,
    calculate_file_score,
    extract_python_signatures,
    find_relevant_files,
    build_context_string,
    get_code_context
)


class TestContextManager:
    """Test suite for Context Manager"""

    def test_tokenize_text(self):
        """Test text tokenization"""
        text = "Fix the bug in the authentication module"
        keywords = tokenize_text(text)

        assert "fix" in keywords
        assert "bug" in keywords
        assert "authentication" in keywords
        assert "module" in keywords
        assert "the" not in keywords
        assert "in" not in keywords

    def test_tokenize_text_empty(self):
        """Test tokenization with empty text"""
        keywords = tokenize_text("")
        assert keywords == []

    def test_calculate_file_score(self):
        """Test file score calculation"""
        goal_keywords = ["authentication", "login", "user"]
        file_path = "agents/auth/login.py"
        file_content = "def authenticate_user(username, password):\n    pass"

        score = calculate_file_score(goal_keywords, file_path, file_content)

        assert 0.0 <= score <= 1.0
        assert score > 0.0

    def test_calculate_file_score_no_match(self):
        """Test file score with no keyword matches"""
        goal_keywords = ["database", "sql", "query"]
        file_path = "agents/ui/button.py"
        file_content = "def render_button():\n    pass"

        score = calculate_file_score(goal_keywords, file_path, file_content)

        assert 0.0 <= score <= 1.0

    def test_extract_python_signatures(self):
        """Test Python signature extraction"""
        code = """
def authenticate_user(username, password):
    pass

class UserManager:
    def __init__(self):
        pass

    def create_user(self, username, email):
        pass
"""
        signatures = extract_python_signatures("test.py", code)

        assert "def authenticate_user(username, password)" in signatures
        assert "class UserManager" in signatures
        assert "def __init__(self)" in signatures
        assert "def create_user(self, username, email)" in signatures

    def test_extract_python_signatures_syntax_error(self):
        """Test signature extraction with syntax error"""
        code = "def broken_function(\n    pass"
        signatures = extract_python_signatures("test.py", code)

        assert signatures == []

    def test_extract_python_signatures_empty(self):
        """Test signature extraction with empty code"""
        signatures = extract_python_signatures("test.py", "")
        assert signatures == []

    def test_find_relevant_files_no_repo(self):
        """Test finding files when repo doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = find_relevant_files(tmpdir, "test goal", max_files=5)
            assert files == []

    def test_build_context_string_empty(self):
        """Test building context with no files"""
        context = build_context_string("/tmp", [], max_tokens=2000)
        assert context == ""

    def test_build_context_string_token_limit(self):
        """Test context string respects token limit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def test():\n    pass\n" * 1000)

            relevant_files = [("test.py", 1.0)]
            context = build_context_string(tmpdir, relevant_files, max_tokens=500)

            estimated_tokens = len(context) // 4
            assert estimated_tokens <= 500

    def test_get_code_context_repo_not_found(self):
        """Test get_code_context when repo not found"""
        with patch('context_manager.os.path.exists', return_value=False):
            context = get_code_context("RC918/morningai", "test goal")

            assert "Repository not found locally" in context
            assert "RC918/morningai" in context

    def test_get_code_context_no_relevant_files(self):
        """Test get_code_context when no relevant files found"""
        with patch('context_manager.os.path.exists', return_value=True):
            with patch('context_manager.find_relevant_files', return_value=[]):
                context = get_code_context("RC918/morningai", "test goal")

                assert "No relevant files found" in context
                assert "RC918/morningai" in context

    def test_get_code_context_with_files(self):
        """Test get_code_context with relevant files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = os.path.join(tmpdir, "agents")
            os.makedirs(agents_dir)

            test_file = os.path.join(agents_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def authenticate_user(username, password):\n    pass\n")

            repo_path = os.path.join(tmpdir, "repos", "morningai")
            os.makedirs(repo_path, exist_ok=True)
            agents_dir_in_repo = os.path.join(repo_path, "agents")
            os.makedirs(agents_dir_in_repo)

            test_file_in_repo = os.path.join(agents_dir_in_repo, "test.py")
            with open(test_file_in_repo, 'w') as f:
                f.write("def authenticate_user(username, password):\n    pass\n")

            with patch('context_manager.os.path.expanduser', return_value=tmpdir):
                context = get_code_context("RC918/morningai", "authentication user login")

                assert "RC918/morningai" in context
                assert "Relevant Files:" in context

    def test_get_code_context_token_limit_enforced(self):
        """Test that get_code_context enforces token limit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = os.path.join(tmpdir, "repos", "morningai")
            os.makedirs(repo_path, exist_ok=True)
            agents_dir = os.path.join(repo_path, "agents")
            os.makedirs(agents_dir)

            test_file = os.path.join(agents_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("def test():\n    pass\n" * 10000)

            with patch('context_manager.os.path.expanduser', return_value=tmpdir):
                context = get_code_context("RC918/morningai", "test", max_tokens=500)

                estimated_tokens = len(context) // 4
                assert estimated_tokens <= 600
