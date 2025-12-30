"""
Tests for GeneralCoder Agent - D-1b Multi-file Extension

Issue #2760: D-1b Multi-file GeneralCoder (<=5 files)
"""
import json
import pytest
from unittest.mock import patch

from coder.general_coder import (
    GeneralCoder,
    MultiFileCoderOutput,
    FilePatch,
    CoderStatus,
    CODER_OUTPUT_SCHEMA_VERSION,
    MAX_FILES_PER_OPERATION,
    parse_python_imports,
    resolve_local_import,
    get_general_coder,
    MULTI_FILE_LLM_RESPONSE_FIELDS,
    MULTI_FILE_SYSTEM_ADDED_FIELDS,
    FILE_PATCH_LLM_FIELDS,
    FILE_PATCH_SYSTEM_FIELDS,
)
from core.agents import AgentInput


class TestFilePatch:
    """Tests for FilePatch dataclass."""

    def test_create_file_patch(self):
        """Test creating a FilePatch."""
        patch = FilePatch(
            file_path="src/utils.py",
            patch="def foo(): pass",
            syntax_valid=True
        )
        assert patch.file_path == "src/utils.py"
        assert patch.patch == "def foo(): pass"
        assert patch.syntax_valid is True

    def test_to_dict(self):
        """Test FilePatch to_dict."""
        patch = FilePatch(
            file_path="test.py",
            patch="code",
            syntax_valid=True
        )
        d = patch.to_dict()
        assert d["file_path"] == "test.py"
        assert d["patch"] == "code"
        assert d["syntax_valid"] is True

    def test_to_dict_no_syntax_valid(self):
        """Test FilePatch to_dict without syntax_valid."""
        patch = FilePatch(
            file_path="test.js",
            patch="code"
        )
        d = patch.to_dict()
        assert d["file_path"] == "test.js"
        assert d["patch"] == "code"
        assert "syntax_valid" not in d


class TestMultiFileCoderOutput:
    """Tests for MultiFileCoderOutput dataclass."""

    def test_create_skipped(self):
        """Test creating a skipped output."""
        output = MultiFileCoderOutput.create_skipped("Not confident")
        assert output.status == CoderStatus.SKIPPED
        assert output.reason == "Not confident"
        assert output.patches == []
        assert output.files_affected == 0

    def test_create_patch(self):
        """Test creating a patch output."""
        patches = [
            FilePatch("file1.py", "code1", True),
            FilePatch("file2.py", "code2", True),
        ]
        output = MultiFileCoderOutput.create_patch(patches)
        assert output.status == CoderStatus.PATCH
        assert output.reason is None
        assert len(output.patches) == 2
        assert output.files_affected == 2

    def test_to_dict_skipped(self):
        """Test to_dict for skipped output."""
        output = MultiFileCoderOutput.create_skipped("Reason")
        d = output.to_dict()
        assert d["schema_version"] == CODER_OUTPUT_SCHEMA_VERSION
        assert d["status"] == "skipped"
        assert d["reason"] == "Reason"
        assert d["files_affected"] == 0
        assert "patches" not in d

    def test_to_dict_patch(self):
        """Test to_dict for patch output."""
        patches = [FilePatch("test.py", "code", True)]
        output = MultiFileCoderOutput.create_patch(patches)
        d = output.to_dict()
        assert d["schema_version"] == CODER_OUTPUT_SCHEMA_VERSION
        assert d["status"] == "patch"
        assert d["files_affected"] == 1
        assert len(d["patches"]) == 1
        assert d["patches"][0]["file_path"] == "test.py"

    def test_to_json(self):
        """Test to_json serialization."""
        output = MultiFileCoderOutput.create_skipped("Reason")
        j = output.to_json()
        parsed = json.loads(j)
        assert parsed["schema_version"] == CODER_OUTPUT_SCHEMA_VERSION
        assert parsed["status"] == "skipped"


class TestParsePythonImports:
    """Tests for parse_python_imports function."""

    def test_simple_imports(self):
        """Test parsing simple imports."""
        code = """
import os
import sys
from typing import List
"""
        imports = parse_python_imports(code)
        assert "os" in imports
        assert "sys" in imports
        assert "typing" in imports

    def test_from_imports(self):
        """Test parsing from imports."""
        code = """
from utils import helper
from core.agents import BaseAgent
"""
        imports = parse_python_imports(code)
        assert "utils" in imports
        assert "core.agents" in imports

    def test_invalid_syntax(self):
        """Test parsing code with syntax errors."""
        code = "def foo(\n    x = 1"
        imports = parse_python_imports(code)
        assert imports == []

    def test_empty_code(self):
        """Test parsing empty code."""
        imports = parse_python_imports("")
        assert imports == []


class TestResolveLocalImport:
    """Tests for resolve_local_import function."""

    def test_resolve_simple_import(self):
        """Test resolving a simple import."""
        available = ["utils.py", "main.py"]
        result = resolve_local_import("utils", "main.py", available)
        assert result == "utils.py"

    def test_resolve_package_import(self):
        """Test resolving a package import."""
        available = ["core/__init__.py", "core/agents.py"]
        result = resolve_local_import("core", "main.py", available)
        assert result == "core/__init__.py"

    def test_resolve_not_found(self):
        """Test resolving an import that doesn't exist."""
        available = ["utils.py"]
        result = resolve_local_import("nonexistent", "main.py", available)
        assert result is None


class TestGeneralCoder:
    """Tests for GeneralCoder class."""

    @pytest.fixture
    def coder(self):
        """Create a GeneralCoder instance."""
        return GeneralCoder()

    def test_init(self, coder):
        """Test GeneralCoder initialization."""
        assert coder.agent_id == "general_coder"

    @patch.object(GeneralCoder, 'call_llm')
    def test_generate_multi_file_fix_skipped(self, mock_call_llm, coder):
        """Test generate_multi_file_fix when LLM returns skipped."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "skipped",
                "reason": "Complex refactoring required"
            })
        }

        files = [
            {"path": "file1.py", "content": "def foo(): pass"},
            {"path": "file2.py", "content": "from file1 import foo"},
        ]

        result = coder.generate_multi_file_fix(
            files=files,
            review_comment="Refactor these functions",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "Complex refactoring" in result.reason

    @patch.object(GeneralCoder, 'call_llm')
    def test_generate_multi_file_fix_patch_valid(self, mock_call_llm, coder):
        """Test generate_multi_file_fix with valid patches."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patches": [
                    {"file_path": "file1.py", "patch": "def foo():\n    '''Docstring.'''\n    pass"},
                    {"file_path": "file2.py", "patch": "from file1 import foo\n\nfoo()"},
                ]
            })
        }

        files = [
            {"path": "file1.py", "content": "def foo(): pass"},
            {"path": "file2.py", "content": "from file1 import foo"},
        ]

        result = coder.generate_multi_file_fix(
            files=files,
            review_comment="Add docstrings",
            severity="low"
        )

        assert result.status == CoderStatus.PATCH
        assert len(result.patches) == 2
        assert result.files_affected == 2

    @patch.object(GeneralCoder, 'call_llm')
    def test_generate_multi_file_fix_invalid_syntax(self, mock_call_llm, coder):
        """Test generate_multi_file_fix with invalid syntax in patch."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patches": [
                    {"file_path": "file1.py", "patch": "def foo(\n    pass"},  # Invalid
                ]
            })
        }

        files = [{"path": "file1.py", "content": "def foo(): pass"}]

        result = coder.generate_multi_file_fix(
            files=files,
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "Syntax check failed" in result.reason

    @patch.object(GeneralCoder, 'call_llm')
    def test_generate_multi_file_fix_too_many_patches(self, mock_call_llm, coder):
        """Test generate_multi_file_fix with too many patches."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patches": [
                    {"file_path": f"file{i}.py", "patch": "pass"}
                    for i in range(6)  # 6 > MAX_FILES_PER_OPERATION
                ]
            })
        }

        files = [{"path": "file1.py", "content": "pass"}]

        result = coder.generate_multi_file_fix(
            files=files,
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "Too many patches" in result.reason

    @patch.object(GeneralCoder, 'call_llm')
    def test_generate_multi_file_fix_invalid_path(self, mock_call_llm, coder):
        """Test generate_multi_file_fix with path traversal attempt."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patches": [
                    {"file_path": "../../../etc/passwd", "patch": "malicious"},
                ]
            })
        }

        files = [{"path": "file1.py", "content": "pass"}]

        result = coder.generate_multi_file_fix(
            files=files,
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "Invalid file path" in result.reason

    @patch.object(GeneralCoder, 'call_llm')
    def test_generate_multi_file_fix_whitespace_only(self, mock_call_llm, coder):
        """Test generate_multi_file_fix rejects whitespace-only patches (Issue #3288)."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patches": [
                    {"file_path": "file1.py", "patch": "   \n\t  \n  "},
                ]
            })
        }

        files = [{"path": "file1.py", "content": "pass"}]

        result = coder.generate_multi_file_fix(
            files=files,
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "Whitespace-only" in result.reason

    @patch.object(GeneralCoder, 'call_llm')
    def test_generate_multi_file_fix_invalid_json(self, mock_call_llm, coder):
        """Test generate_multi_file_fix with invalid JSON response."""
        mock_call_llm.return_value = {
            "content": "This is not JSON"
        }

        files = [{"path": "file1.py", "content": "pass"}]

        result = coder.generate_multi_file_fix(
            files=files,
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "JSON" in result.reason

    @patch.object(GeneralCoder, 'call_llm')
    def test_generate_multi_file_fix_llm_error(self, mock_call_llm, coder):
        """Test generate_multi_file_fix when LLM call fails."""
        mock_call_llm.side_effect = Exception("API Error")

        files = [{"path": "file1.py", "content": "pass"}]

        result = coder.generate_multi_file_fix(
            files=files,
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "LLM call failed" in result.reason

    @patch.object(GeneralCoder, 'call_llm')
    def test_execute_success(self, mock_call_llm, coder):
        """Test execute method with successful patches."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patches": [
                    {"file_path": "file1.py", "patch": "def foo():\n    pass"},
                ]
            })
        }

        input = AgentInput(
            task_id="test-001",
            prompt="Fix the code",
            context={
                "files": [{"path": "file1.py", "content": "def foo(): pass"}],
                "review_comment": "Add newline",
                "severity": "low"
            }
        )

        output = coder.execute(input)

        assert output.success is True
        assert output.data["status"] == "patch"
        assert output.data["files_affected"] == 1

    def test_execute_missing_files(self, coder):
        """Test execute method with missing files."""
        input = AgentInput(
            task_id="test-001",
            prompt="Fix the code",
            context={}
        )

        output = coder.execute(input)

        assert output.success is False
        assert "Missing" in output.error or "no files" in output.error.lower()

    def test_execute_too_many_files(self, coder):
        """Test execute method with too many files."""
        input = AgentInput(
            task_id="test-001",
            prompt="Fix the code",
            context={
                "files": [{"path": f"file{i}.py", "content": "pass"} for i in range(6)],
                "review_comment": "Fix it",
                "severity": "low"
            }
        )

        output = coder.execute(input)

        assert output.success is False
        assert "Too many files" in output.error


class TestGetGeneralCoder:
    """Tests for get_general_coder factory function."""

    def test_returns_general_coder(self):
        """Factory should return GeneralCoder instance."""
        coder = get_general_coder()
        assert isinstance(coder, GeneralCoder)

    def test_returns_cached_instance(self):
        """Factory should return cached instance."""
        coder1 = get_general_coder()
        coder2 = get_general_coder()
        assert coder1 is coder2


class TestSchemaFieldDefinitions:
    """Tests for schema field definitions (drift detection)."""

    def test_multi_file_llm_response_fields(self):
        """Test LLM response fields are defined correctly."""
        assert MULTI_FILE_LLM_RESPONSE_FIELDS == frozenset({"status", "reason", "patches"})

    def test_multi_file_system_added_fields(self):
        """Test system-added fields are defined correctly."""
        assert MULTI_FILE_SYSTEM_ADDED_FIELDS == frozenset({"schema_version", "files_affected"})

    def test_file_patch_llm_fields(self):
        """Test FilePatch LLM fields are defined correctly."""
        assert FILE_PATCH_LLM_FIELDS == frozenset({"file_path", "patch"})

    def test_file_patch_system_fields(self):
        """Test FilePatch system fields are defined correctly."""
        assert FILE_PATCH_SYSTEM_FIELDS == frozenset({"syntax_valid"})

    def test_max_files_per_operation(self):
        """Test max files constant is set correctly."""
        assert MAX_FILES_PER_OPERATION == 5
