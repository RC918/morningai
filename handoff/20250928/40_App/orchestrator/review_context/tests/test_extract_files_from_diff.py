"""
Tests for _extract_files_from_diff function in MultiSpecialistReviewer.

Issue #4199: Prevent specialist file path hallucination by providing
an explicit list of valid files to the LLM.
"""

from review_context.multi_specialist_reviewer import MultiSpecialistReviewer


class TestExtractFilesFromDiff:
    """Tests for _extract_files_from_diff method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reviewer = MultiSpecialistReviewer(trace_id="test-trace-id")

    def test_extract_files_from_git_diff_headers(self):
        """Test extraction from standard git diff headers."""
        diff_content = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+import os
 def main():
     pass

diff --git a/src/utils.py b/src/utils.py
index 1234567..abcdefg 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,3 +1,4 @@
+import sys
 def util():
     pass
"""
        files = self.reviewer._extract_files_from_diff(diff_content)
        assert files == ["src/main.py", "src/utils.py"]

    def test_extract_files_from_plus_headers_fallback(self):
        """Test fallback to +++ headers when diff --git not present."""
        diff_content = """--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+import os
 def main():
     pass
"""
        files = self.reviewer._extract_files_from_diff(diff_content)
        assert files == ["src/main.py"]

    def test_extract_files_excludes_dev_null(self):
        """Test that /dev/null is excluded (new file creation)."""
        diff_content = """--- /dev/null
+++ b/src/new_file.py
@@ -0,0 +1,3 @@
+def new_func():
+    pass
"""
        files = self.reviewer._extract_files_from_diff(diff_content)
        assert files == ["src/new_file.py"]

    def test_extract_files_no_duplicates(self):
        """Test that duplicate file paths are not included."""
        diff_content = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+import os

diff --git a/src/main.py b/src/main.py
index abcdefg..1234567 100644
--- a/src/main.py
+++ b/src/main.py
@@ -5,3 +6,4 @@
+import sys
"""
        files = self.reviewer._extract_files_from_diff(diff_content)
        # Should only have one entry for src/main.py
        assert files == ["src/main.py"]

    def test_extract_files_empty_diff(self):
        """Test handling of empty diff content."""
        files = self.reviewer._extract_files_from_diff("")
        assert files == []

    def test_extract_files_no_valid_headers(self):
        """Test handling of diff without valid file headers."""
        diff_content = """Some random text
that doesn't contain
any valid diff headers
"""
        files = self.reviewer._extract_files_from_diff(diff_content)
        assert files == []

    def test_extract_files_complex_paths(self):
        """Test extraction of complex file paths with special characters."""
        diff_content = """diff --git a/handoff/20250928/40_App/orchestrator/debugger_agent/debugger_agent_v2.py b/handoff/20250928/40_App/orchestrator/debugger_agent/debugger_agent_v2.py
index 1234567..abcdefg 100644
--- a/handoff/20250928/40_App/orchestrator/debugger_agent/debugger_agent_v2.py
+++ b/handoff/20250928/40_App/orchestrator/debugger_agent/debugger_agent_v2.py
@@ -1,3 +1,4 @@
+import os
"""
        files = self.reviewer._extract_files_from_diff(diff_content)
        assert files == ["handoff/20250928/40_App/orchestrator/debugger_agent/debugger_agent_v2.py"]

    def test_extract_files_handles_renamed_files(self):
        """Test that renamed files are correctly extracted via fallback.

        When a file is renamed, the diff --git header has different paths
        (a/old.py b/new.py), so the primary regex won't match. The function
        should fall back to +++ b/ parsing and extract the new file path.
        """
        diff_content = """diff --git a/src/old.py b/src/new.py
similarity index 90%
rename from src/old.py
rename to src/new.py
index 1234567..abcdefg 100644
--- a/src/old.py
+++ b/src/new.py
@@ -1,3 +1,3 @@
-def old_function():
+def new_function():
     pass
"""
        files = self.reviewer._extract_files_from_diff(diff_content)
        # Should extract the new file path via +++ fallback
        assert files == ["src/new.py"]


class TestBuildUserPromptWithFileList:
    """Tests for _build_user_prompt with file list inclusion."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reviewer = MultiSpecialistReviewer(trace_id="test-trace-id")

    def test_prompt_includes_file_list(self):
        """Test that the prompt includes the list of valid files."""
        from governance.types import SpecialistType

        diff_content = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+import os
"""
        pr_context = {
            "pr_number": 123,
            "goal": "Add feature",
            "repo": "test/repo",
        }

        prompt = self.reviewer._build_user_prompt(
            diff_content, pr_context, SpecialistType.SECURITY
        )

        # Check that the prompt contains the file list section
        assert "VALID FILES IN THIS PR" in prompt
        assert "- src/main.py" in prompt
        assert "CRITICAL: Only comment on the files listed above" in prompt

    def test_prompt_handles_empty_file_list(self):
        """Test that the prompt handles empty file list gracefully."""
        from governance.types import SpecialistType

        diff_content = "no valid diff content"
        pr_context = {
            "pr_number": 123,
            "goal": "Add feature",
            "repo": "test/repo",
        }

        prompt = self.reviewer._build_user_prompt(
            diff_content, pr_context, SpecialistType.SECURITY
        )

        # Check that the prompt indicates no files detected
        assert "VALID FILES IN THIS PR" in prompt
        assert "(no files detected)" in prompt
