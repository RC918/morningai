"""
Tests for File Reference Resolver module.

Issue #3223: Enhance Diff-Aware Context Gathering with cross-file reference resolution.
"""

import pytest
from unittest.mock import Mock, MagicMock

from tools.file_reference_resolver import (
    Language,
    FileReference,
    ReferenceContext,
    ResolverResult,
    detect_language,
    sanitize_path,
    extract_python_imports,
    extract_typescript_imports,
    extract_references_from_diff,
    resolve_import_path,
    fetch_file_content,
    resolve_file_references,
    format_reference_context_for_prompt,
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_LINES_PER_FILE,
    ALLOWED_EXTENSIONS,
)


class TestLanguageDetection:
    """Tests for language detection from filename."""

    def test_detect_python(self):
        assert detect_language("src/utils.py") == Language.PYTHON
        assert detect_language("test_file.py") == Language.PYTHON

    def test_detect_typescript(self):
        assert detect_language("src/App.ts") == Language.TYPESCRIPT
        assert detect_language("components/Button.tsx") == Language.TYPESCRIPT

    def test_detect_javascript(self):
        assert detect_language("src/index.js") == Language.JAVASCRIPT
        assert detect_language("components/Modal.jsx") == Language.JAVASCRIPT
        assert detect_language("utils.mjs") == Language.JAVASCRIPT
        assert detect_language("config.cjs") == Language.JAVASCRIPT

    def test_detect_unknown(self):
        assert detect_language("README.md") == Language.UNKNOWN
        assert detect_language("Dockerfile") == Language.UNKNOWN
        assert detect_language("config.yaml") == Language.UNKNOWN


class TestPythonImportExtraction:
    """Tests for Python import extraction."""

    def test_from_import(self):
        content = """
+from utils.helpers import format_date
+from models import User, Post
"""
        refs = extract_python_imports(content, "src/main.py")

        assert len(refs) == 2
        assert refs[0].import_path == "utils.helpers"
        assert refs[0].language == Language.PYTHON
        assert refs[1].import_path == "models"

    def test_import_statement(self):
        content = """
+import os
+import sys, json
+import pandas as pd
"""
        refs = extract_python_imports(content, "src/main.py")

        assert len(refs) == 4
        assert refs[0].import_path == "os"
        assert refs[1].import_path == "sys"
        assert refs[2].import_path == "json"
        assert refs[3].import_path == "pandas"

    def test_relative_import(self):
        content = """
+from .utils import helper
+from ..models import User
+from ...core import base
"""
        refs = extract_python_imports(content, "src/views/main.py")

        assert len(refs) == 3
        assert refs[0].import_path == ".utils"
        assert refs[0].is_relative is True
        assert refs[1].import_path == "..models"
        assert refs[1].is_relative is True
        assert refs[2].import_path == "...core"
        assert refs[2].is_relative is True

    def test_skip_removed_lines(self):
        content = """
-from old_module import deprecated
+from new_module import updated
"""
        refs = extract_python_imports(content, "src/main.py")

        assert len(refs) == 1
        assert refs[0].import_path == "new_module"


class TestTypeScriptImportExtraction:
    """Tests for TypeScript/JavaScript import extraction."""

    def test_es6_import(self):
        content = """
+import React from 'react'
+import { useState, useEffect } from 'react'
+import * as utils from './utils'
"""
        refs = extract_typescript_imports(content, "src/App.tsx")

        assert len(refs) == 3
        assert refs[0].import_path == "react"
        assert refs[0].is_relative is False
        assert refs[1].import_path == "react"
        assert refs[2].import_path == "./utils"
        assert refs[2].is_relative is True

    def test_require_import(self):
        content = """
+const fs = require('fs')
+const path = require("path")
+const utils = require('./utils')
"""
        refs = extract_typescript_imports(content, "src/index.js")

        assert len(refs) == 3
        assert refs[0].import_path == "fs"
        assert refs[1].import_path == "path"
        assert refs[2].import_path == "./utils"

    def test_side_effect_import(self):
        content = """
+import './styles.css'
+import 'polyfill'
"""
        refs = extract_typescript_imports(content, "src/App.tsx")

        assert len(refs) == 2
        assert refs[0].import_path == "./styles.css"
        assert refs[1].import_path == "polyfill"

    def test_skip_removed_lines(self):
        content = """
-import { oldUtil } from './old'
+import { newUtil } from './new'
"""
        refs = extract_typescript_imports(content, "src/App.tsx")

        assert len(refs) == 1
        assert refs[0].import_path == "./new"


class TestDiffExtraction:
    """Tests for extracting references from unified diff."""

    def test_extract_from_python_diff(self):
        diff = """--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,6 @@
+from utils.helpers import format_date
 import os

 def main():
     pass
"""
        refs = extract_references_from_diff(diff)

        assert len(refs) >= 1
        python_refs = [r for r in refs if r.language == Language.PYTHON]
        assert any(r.import_path == "utils.helpers" for r in python_refs)

    def test_extract_from_typescript_diff(self):
        diff = """--- a/src/App.tsx
+++ b/src/App.tsx
@@ -1,5 +1,6 @@
+import { Button } from './components/Button'
 import React from 'react'

 export const App = () => <div>Hello</div>
"""
        refs = extract_references_from_diff(diff)

        assert len(refs) >= 1
        ts_refs = [r for r in refs if r.language == Language.TYPESCRIPT]
        assert any(r.import_path == "./components/Button" for r in ts_refs)

    def test_extract_from_multiple_files(self):
        diff = """--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+from utils import helper
 def main():
     pass
--- a/src/App.tsx
+++ b/src/App.tsx
@@ -1,3 +1,4 @@
+import { util } from './util'
 export const App = () => null
"""
        refs = extract_references_from_diff(diff)

        assert len(refs) >= 2
        assert any(r.import_path == "utils" for r in refs)
        assert any(r.import_path == "./util" for r in refs)


class TestImportPathResolution:
    """Tests for resolving import paths to file paths."""

    def test_resolve_python_absolute_import(self):
        resolved = resolve_import_path(
            "utils.helpers",
            "src/main.py",
            Language.PYTHON,
        )
        assert resolved == "utils/helpers.py"

    def test_resolve_python_relative_import(self):
        resolved = resolve_import_path(
            ".utils",
            "src/views/main.py",
            Language.PYTHON,
        )
        assert "utils" in resolved

    def test_resolve_typescript_relative_import(self):
        resolved = resolve_import_path(
            "./components/Button",
            "src/App.tsx",
            Language.TYPESCRIPT,
        )
        assert "components/Button" in resolved

    def test_skip_node_modules(self):
        resolved = resolve_import_path(
            "react",
            "src/App.tsx",
            Language.TYPESCRIPT,
        )
        assert resolved is None

    def test_skip_node_modules_scoped(self):
        resolved = resolve_import_path(
            "@types/node",
            "src/index.ts",
            Language.TYPESCRIPT,
        )
        assert resolved is None


class TestFetchFileContent:
    """Tests for fetching file content from repository."""

    def test_fetch_success(self):
        mock_repo = Mock()
        mock_file = Mock()
        mock_file.decoded_content = b"line1\nline2\nline3"
        mock_repo.get_contents.return_value = mock_file

        result = fetch_file_content(mock_repo, "src/utils.py", "abc123", max_lines=100)

        assert result.file_path == "src/utils.py"
        assert result.content == "line1\nline2\nline3"
        assert result.line_count == 3
        assert result.truncated is False
        assert result.error is None

    def test_fetch_with_truncation(self):
        mock_repo = Mock()
        mock_file = Mock()
        mock_file.decoded_content = b"line1\nline2\nline3\nline4\nline5"
        mock_repo.get_contents.return_value = mock_file

        result = fetch_file_content(mock_repo, "src/utils.py", "abc123", max_lines=2)

        assert result.truncated is True
        assert result.line_count == 3  # 2 lines + truncation message
        assert "truncated" in result.content

    def test_fetch_error(self):
        mock_repo = Mock()
        mock_repo.get_contents.side_effect = Exception("File not found")

        result = fetch_file_content(mock_repo, "src/missing.py", "abc123")

        assert result.error == "File not found"
        assert result.content == ""


class TestResolveFileReferences:
    """Tests for the main resolve_file_references function."""

    def test_resolve_with_valid_diff(self):
        mock_repo = Mock()
        mock_file = Mock()
        mock_file.decoded_content = b"def helper():\n    pass"
        mock_repo.get_contents.return_value = mock_file

        diff = """--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+from utils import helper
 def main():
     pass
"""
        result = resolve_file_references(
            repo=mock_repo,
            diff_content=diff,
            head_sha="abc123",
            trace_id="test-trace",
        )

        assert result.total_references_found >= 1
        assert result.error is None

    def test_resolve_empty_diff(self):
        mock_repo = Mock()

        result = resolve_file_references(
            repo=mock_repo,
            diff_content="",
            head_sha="abc123",
        )

        assert result.total_references_found == 0
        assert result.total_contexts_fetched == 0

    def test_resolve_with_max_files_limit(self):
        mock_repo = Mock()
        mock_file = Mock()
        mock_file.decoded_content = b"content"
        mock_repo.get_contents.return_value = mock_file

        diff = """--- a/src/main.py
+++ b/src/main.py
@@ -1,10 +1,16 @@
+from utils1 import a
+from utils2 import b
+from utils3 import c
+from utils4 import d
+from utils5 import e
+from utils6 import f
 def main():
     pass
"""
        result = resolve_file_references(
            repo=mock_repo,
            diff_content=diff,
            head_sha="abc123",
            max_files=3,
        )

        assert result.total_contexts_fetched <= 3


class TestFormatReferenceContext:
    """Tests for formatting reference context for LLM prompt."""

    def test_format_with_contexts(self):
        result = ResolverResult(
            contexts=[
                ReferenceContext(
                    file_path="src/utils.py",
                    content="def helper():\n    pass",
                    line_count=2,
                    truncated=False,
                ),
            ],
            total_contexts_fetched=1,
        )

        formatted = format_reference_context_for_prompt(result)

        assert "## Referenced Files" in formatted
        assert "src/utils.py" in formatted
        assert "def helper():" in formatted

    def test_format_with_truncation_note(self):
        result = ResolverResult(
            contexts=[
                ReferenceContext(
                    file_path="src/utils.py",
                    content="content",
                    line_count=100,
                    truncated=True,
                ),
            ],
            truncated=True,
        )

        formatted = format_reference_context_for_prompt(result)

        assert "truncated" in formatted.lower()

    def test_format_empty_contexts(self):
        result = ResolverResult()

        formatted = format_reference_context_for_prompt(result)

        assert formatted == ""


class TestFileReferenceDataclasses:
    """Tests for dataclass serialization."""

    def test_file_reference_to_dict(self):
        ref = FileReference(
            import_path="utils.helpers",
            source_file="src/main.py",
            language=Language.PYTHON,
            line_number=10,
            is_relative=False,
        )

        d = ref.to_dict()

        assert d["import_path"] == "utils.helpers"
        assert d["source_file"] == "src/main.py"
        assert d["language"] == "python"
        assert d["line_number"] == 10
        assert d["is_relative"] is False

    def test_reference_context_to_dict(self):
        ctx = ReferenceContext(
            file_path="src/utils.py",
            content="def helper(): pass",
            line_count=1,
            truncated=False,
        )

        d = ctx.to_dict()

        assert d["file_path"] == "src/utils.py"
        assert d["content"] == "def helper(): pass"
        assert d["line_count"] == 1
        assert d["truncated"] is False

    def test_resolver_result_to_dict(self):
        result = ResolverResult(
            references=[
                FileReference(
                    import_path="utils",
                    source_file="main.py",
                    language=Language.PYTHON,
                )
            ],
            contexts=[
                ReferenceContext(
                    file_path="utils.py",
                    content="content",
                    line_count=1,
                )
            ],
            total_references_found=1,
            total_contexts_fetched=1,
            total_bytes=100,
        )

        d = result.to_dict()

        assert len(d["references"]) == 1
        assert len(d["contexts"]) == 1
        assert d["total_references_found"] == 1
        assert d["total_contexts_fetched"] == 1
        assert d["total_bytes"] == 100


class TestPathSanitization:
    """Tests for path sanitization security measures."""

    def test_valid_python_path(self):
        """Valid Python file paths should pass."""
        assert sanitize_path("src/utils.py") == "src/utils.py"
        assert sanitize_path("tests/test_main.py") == "tests/test_main.py"
        assert sanitize_path("module/__init__.py") == "module/__init__.py"

    def test_valid_typescript_path(self):
        """Valid TypeScript/JavaScript file paths should pass."""
        assert sanitize_path("src/App.tsx") == "src/App.tsx"
        assert sanitize_path("components/Button.ts") == "components/Button.ts"
        assert sanitize_path("utils/helpers.js") == "utils/helpers.js"

    def test_reject_null_bytes(self):
        """Paths with null bytes should be rejected (security)."""
        assert sanitize_path("src/utils\x00.py") is None
        assert sanitize_path("src\x00/utils.py") is None

    def test_reject_backslashes(self):
        """Paths with backslashes should be rejected (Windows-style bypass)."""
        assert sanitize_path("src\\utils.py") is None
        assert sanitize_path("..\\..\\etc\\passwd") is None

    def test_reject_absolute_paths(self):
        """Absolute paths should be rejected."""
        assert sanitize_path("/etc/passwd") is None
        assert sanitize_path("/home/user/.ssh/id_rsa") is None
        assert sanitize_path("/src/utils.py") is None

    def test_reject_path_traversal(self):
        """Paths with .. traversal should be rejected."""
        assert sanitize_path("../utils.py") is None
        assert sanitize_path("../../etc/passwd") is None
        assert sanitize_path("src/../../../etc/passwd") is None
        assert sanitize_path("..") is None

    def test_reject_hidden_files(self):
        """Hidden files/directories should be rejected (except allowlisted)."""
        assert sanitize_path(".env") is None
        assert sanitize_path(".secrets/api_key") is None
        assert sanitize_path("src/.hidden/file.py") is None

    def test_allow_github_directory(self):
        """Allow .github directory (common config)."""
        assert sanitize_path(".github/workflows/ci.yml") == ".github/workflows/ci.yml"

    def test_reject_disallowed_extensions(self):
        """Files with disallowed extensions should be rejected."""
        assert sanitize_path("secrets.key") is None
        assert sanitize_path("database.sqlite") is None
        assert sanitize_path("image.png") is None
        assert sanitize_path("archive.zip") is None

    def test_allowed_extensions_comprehensive(self):
        """Verify all allowed extensions work."""
        allowed_samples = [
            "file.py", "file.pyi", "file.ts", "file.tsx",
            "file.js", "file.jsx", "file.mjs", "file.cjs",
            "file.json", "file.yaml", "file.yml", "file.toml",
            "file.md", "file.txt", "file.rst",
            "file.html", "file.css", "file.scss", "file.less",
            "file.go", "file.rs", "file.java", "file.kt", "file.swift",
            "file.c", "file.cpp", "file.h", "file.hpp",
            "file.rb", "file.php", "file.sh", "file.bash",
        ]
        for path in allowed_samples:
            result = sanitize_path(path)
            assert result == path, f"Expected {path} to be allowed, got {result}"

    def test_empty_path(self):
        """Empty paths should be rejected."""
        assert sanitize_path("") is None
        assert sanitize_path(None) is None

    def test_whitespace_handling(self):
        """Whitespace should be stripped."""
        assert sanitize_path("  src/utils.py  ") == "src/utils.py"


class TestPathSanitizationIntegration:
    """Tests for path sanitization integration in resolve_file_references."""

    def test_unsafe_import_path_rejected(self):
        """Unsafe import paths should be rejected during resolution."""
        mock_repo = Mock()
        mock_repo.get_contents.return_value = Mock(
            decoded_content=b"# content"
        )

        # Diff with a malicious import trying path traversal
        diff_content = '''diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+from ....secrets import api_key
 def main():
     pass
'''

        result = resolve_file_references(
            repo=mock_repo,
            diff_content=diff_content,
            head_sha="abc123",
        )

        # The malicious import should be extracted but not fetched
        # (sanitization should reject it)
        assert result.total_contexts_fetched == 0

    def test_safe_import_path_allowed(self):
        """Safe import paths should be allowed during resolution."""
        mock_repo = Mock()
        mock_file = Mock()
        mock_file.decoded_content = b"# Safe content\ndef helper():\n    pass"
        mock_repo.get_contents.return_value = mock_file

        diff_content = '''diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+from utils.helpers import helper
 def main():
     pass
'''

        result = resolve_file_references(
            repo=mock_repo,
            diff_content=diff_content,
            head_sha="abc123",
        )

        # The safe import should be fetched
        assert result.total_references_found == 1


class TestReferenceContextFromDict:
    """Tests for ReferenceContext.from_dict - Issue #4079, #4080."""

    def test_from_dict_valid(self):
        """Test creating ReferenceContext from valid dict."""
        data = {
            "file_path": "src/utils.py",
            "content": "def helper(): pass",
            "line_count": 1,
            "truncated": False,
            "error": None,
        }

        ctx = ReferenceContext.from_dict(data)

        assert ctx.file_path == "src/utils.py"
        assert ctx.content == "def helper(): pass"
        assert ctx.line_count == 1
        assert ctx.truncated is False
        assert ctx.error is None

    def test_from_dict_with_defaults(self):
        """Test creating ReferenceContext with optional fields defaulted."""
        data = {
            "file_path": "src/utils.py",
            "content": "content",
            "line_count": 5,
        }

        ctx = ReferenceContext.from_dict(data)

        assert ctx.truncated is False  # Default
        assert ctx.error is None  # Default

    def test_from_dict_missing_required_field(self):
        """Test that missing required fields raise ValueError."""
        data = {
            "file_path": "src/utils.py",
            # Missing "content" and "line_count"
        }

        with pytest.raises(ValueError) as exc_info:
            ReferenceContext.from_dict(data)

        assert "Missing required field" in str(exc_info.value)

    def test_from_dict_invalid_type(self):
        """Test that invalid types raise ValueError."""
        data = {
            "file_path": 123,  # Should be str
            "content": "content",
            "line_count": 1,
        }

        with pytest.raises(ValueError) as exc_info:
            ReferenceContext.from_dict(data)

        assert "file_path must be str" in str(exc_info.value)

    def test_from_dict_not_a_dict(self):
        """Test that non-dict input raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReferenceContext.from_dict("not a dict")

        assert "Expected dict" in str(exc_info.value)

    def test_roundtrip_to_dict_from_dict(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = ReferenceContext(
            file_path="src/utils.py",
            content="def helper(): pass",
            line_count=1,
            truncated=True,
            error="Some error",
        )

        data = original.to_dict()
        restored = ReferenceContext.from_dict(data)

        assert restored.file_path == original.file_path
        assert restored.content == original.content
        assert restored.line_count == original.line_count
        assert restored.truncated == original.truncated
        assert restored.error == original.error


class TestResolverResultFromDict:
    """Tests for ResolverResult.from_dict - Issue #4079, #4080."""

    def test_from_dict_valid(self):
        """Test creating ResolverResult from valid dict."""
        data = {
            "contexts": [
                {
                    "file_path": "src/utils.py",
                    "content": "def helper(): pass",
                    "line_count": 1,
                    "truncated": False,
                }
            ],
            "total_references_found": 2,
            "total_contexts_fetched": 1,
            "total_bytes": 100,
            "truncated": False,
        }

        result = ResolverResult.from_dict(data)

        assert len(result.contexts) == 1
        assert result.contexts[0].file_path == "src/utils.py"
        assert result.total_references_found == 2
        assert result.total_contexts_fetched == 1
        assert result.total_bytes == 100
        assert result.truncated is False

    def test_from_dict_empty_contexts(self):
        """Test creating ResolverResult with empty contexts."""
        data = {
            "contexts": [],
            "total_references_found": 0,
            "total_contexts_fetched": 0,
            "total_bytes": 0,
        }

        result = ResolverResult.from_dict(data)

        assert len(result.contexts) == 0
        assert result.total_references_found == 0

    def test_from_dict_with_defaults(self):
        """Test creating ResolverResult with optional fields defaulted."""
        data = {}  # All fields have defaults

        result = ResolverResult.from_dict(data)

        assert len(result.contexts) == 0
        assert result.total_references_found == 0
        assert result.truncated is False

    def test_from_dict_invalid_context(self):
        """Test that invalid context data raises ValueError."""
        data = {
            "contexts": [
                {"file_path": "valid.py", "content": "x", "line_count": 1},
                {"invalid": "context"},  # Missing required fields
            ],
        }

        with pytest.raises(ValueError) as exc_info:
            ResolverResult.from_dict(data)

        assert "Invalid context at index 1" in str(exc_info.value)

    def test_from_dict_invalid_contexts_type(self):
        """Test that non-list contexts raises ValueError."""
        data = {
            "contexts": "not a list",
        }

        with pytest.raises(ValueError) as exc_info:
            ResolverResult.from_dict(data)

        assert "contexts must be list" in str(exc_info.value)

    def test_from_dict_invalid_numeric_type(self):
        """Test that invalid numeric types raise ValueError."""
        data = {
            "contexts": [],
            "total_references_found": "not an int",
        }

        with pytest.raises(ValueError) as exc_info:
            ResolverResult.from_dict(data)

        assert "total_references_found must be int" in str(exc_info.value)

    def test_roundtrip_to_dict_from_dict(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = ResolverResult(
            references=[],  # References are not serialized
            contexts=[
                ReferenceContext(
                    file_path="src/utils.py",
                    content="content",
                    line_count=5,
                    truncated=True,
                )
            ],
            total_references_found=3,
            total_contexts_fetched=1,
            total_bytes=500,
            truncated=True,
            error="Some error",
        )

        data = original.to_dict()
        restored = ResolverResult.from_dict(data)

        assert len(restored.contexts) == len(original.contexts)
        assert restored.contexts[0].file_path == original.contexts[0].file_path
        assert restored.total_references_found == original.total_references_found
        assert restored.total_contexts_fetched == original.total_contexts_fetched
        assert restored.total_bytes == original.total_bytes
        assert restored.truncated == original.truncated
        assert restored.error == original.error
