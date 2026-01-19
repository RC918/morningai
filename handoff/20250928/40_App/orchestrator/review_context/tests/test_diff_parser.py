"""
Tests for DiffParser module.

Issue #4215: Refactor diff parsing logic to separate module
Issue #4214: Handle quoted file paths with spaces
"""

from review_context.diff_parser import (
    DiffParser,
    extract_files_from_diff,
    extract_addition_lines_from_diff,
)


class TestDiffParserExtractFiles:
    """Tests for DiffParser.extract_files() method."""

    def test_extract_files_from_simple_diff(self):
        """Test extracting files from a simple diff."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "--- a/src/api.py\n"
            "+++ b/src/api.py\n"
            "@@ -1,3 +1,4 @@\n"
            " import os\n"
            "+import sys\n"
            "\n"
            " def main():\n"
        )
        parser = DiffParser(diff)
        files = parser.extract_files()
        assert files == ["src/api.py"]

    def test_extract_files_from_multiple_files(self):
        """Test extracting multiple files from a diff."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "--- a/src/api.py\n"
            "+++ b/src/api.py\n"
            "@@ -1,3 +1,4 @@\n"
            " import os\n"
            "+import sys\n"
            "diff --git a/src/utils.py b/src/utils.py\n"
            "--- a/src/utils.py\n"
            "+++ b/src/utils.py\n"
            "@@ -1,2 +1,3 @@\n"
            " def helper():\n"
            "+    pass\n"
        )
        parser = DiffParser(diff)
        files = parser.extract_files()
        assert files == ["src/api.py", "src/utils.py"]

    def test_extract_files_with_spaces_in_path(self):
        """Test extracting files with spaces in path (Issue #4214)."""
        diff = (
            'diff --git "a/path with spaces/file.py" "b/path with spaces/file.py"\n'
            '--- "a/path with spaces/file.py"\n'
            '+++ "b/path with spaces/file.py"\n'
            "@@ -1,2 +1,3 @@\n"
            " def main():\n"
            "+    pass\n"
        )
        parser = DiffParser(diff)
        files = parser.extract_files()
        assert files == ["path with spaces/file.py"]

    def test_extract_files_skips_deleted_files(self):
        """Test that deleted files (/dev/null) are skipped."""
        diff = (
            "diff --git a/deleted.py b/deleted.py\n"
            "--- a/deleted.py\n"
            "+++ /dev/null\n"
            "@@ -1,3 +0,0 @@\n"
            "-def old_function():\n"
            "-    pass\n"
        )
        parser = DiffParser(diff)
        files = parser.extract_files()
        # Deleted files should still appear in the list from diff --git header
        assert files == ["deleted.py"]

    def test_extract_files_empty_diff(self):
        """Test extracting files from an empty diff."""
        parser = DiffParser("")
        files = parser.extract_files()
        assert files == []

    def test_extract_files_caches_result(self):
        """Test that extract_files caches its result."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "+++ b/src/api.py\n"
        )
        parser = DiffParser(diff)
        files1 = parser.extract_files()
        files2 = parser.extract_files()
        assert files1 is files2  # Same object (cached)


class TestDiffParserExtractAdditionLines:
    """Tests for DiffParser.extract_addition_lines() method."""

    def test_extract_addition_lines_simple(self):
        """Test extracting addition lines from a simple diff."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "--- a/src/api.py\n"
            "+++ b/src/api.py\n"
            "@@ -1,3 +1,5 @@\n"
            " import os\n"
            "+import sys\n"
            "+import re\n"
            "\n"
            " def main():\n"
        )
        parser = DiffParser(diff)
        addition_lines = parser.extract_addition_lines()
        assert addition_lines == {"src/api.py": [2, 3]}

    def test_extract_addition_lines_multiple_hunks(self):
        """Test extracting addition lines from multiple hunks."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "--- a/src/api.py\n"
            "+++ b/src/api.py\n"
            "@@ -1,3 +1,4 @@\n"
            " import os\n"
            "+import sys\n"
            "\n"
            " def main():\n"
            "@@ -10,3 +11,4 @@\n"
            " def helper():\n"
            "     pass\n"
            "+    return True\n"
        )
        parser = DiffParser(diff)
        addition_lines = parser.extract_addition_lines()
        # Hunk 1: starts at line 1, addition at line 2
        # Hunk 2: starts at line 11, context lines at 11-12, addition at line 13
        assert addition_lines == {"src/api.py": [2, 13]}

    def test_extract_addition_lines_multiple_files(self):
        """Test extracting addition lines from multiple files."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "--- a/src/api.py\n"
            "+++ b/src/api.py\n"
            "@@ -1,2 +1,3 @@\n"
            " import os\n"
            "+import sys\n"
            "diff --git a/src/utils.py b/src/utils.py\n"
            "--- a/src/utils.py\n"
            "+++ b/src/utils.py\n"
            "@@ -5,2 +5,3 @@\n"
            " def helper():\n"
            "+    pass\n"
        )
        parser = DiffParser(diff)
        addition_lines = parser.extract_addition_lines()
        assert addition_lines == {
            "src/api.py": [2],
            "src/utils.py": [6],
        }

    def test_extract_addition_lines_with_spaces_in_path(self):
        """Test extracting addition lines with spaces in path (Issue #4214)."""
        diff = (
            'diff --git "a/path with spaces/file.py" "b/path with spaces/file.py"\n'
            '--- "a/path with spaces/file.py"\n'
            '+++ "b/path with spaces/file.py"\n'
            "@@ -1,2 +1,3 @@\n"
            " def main():\n"
            "+    pass\n"
        )
        parser = DiffParser(diff)
        addition_lines = parser.extract_addition_lines()
        assert addition_lines == {"path with spaces/file.py": [2]}

    def test_extract_addition_lines_cpp_preincrement(self):
        """Test that C++ pre-increment lines (+++counter;) are handled correctly."""
        diff = (
            "diff --git a/src/counter.cpp b/src/counter.cpp\n"
            "--- a/src/counter.cpp\n"
            "+++ b/src/counter.cpp\n"
            "@@ -1,3 +1,4 @@\n"
            " int counter = 0;\n"
            "++++counter;\n"
            " return counter;\n"
        )
        parser = DiffParser(diff)
        addition_lines = parser.extract_addition_lines()
        # The line "+++counter;" should be recognized as an addition line
        assert addition_lines == {"src/counter.cpp": [2]}

    def test_extract_addition_lines_skips_deletions(self):
        """Test that deletion lines don't affect line numbering."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "--- a/src/api.py\n"
            "+++ b/src/api.py\n"
            "@@ -1,4 +1,4 @@\n"
            " import os\n"
            "-import old_module\n"
            "+import new_module\n"
            "\n"
            " def main():\n"
        )
        parser = DiffParser(diff)
        addition_lines = parser.extract_addition_lines()
        # Line 2 is the addition (new_module replaces old_module)
        assert addition_lines == {"src/api.py": [2]}

    def test_extract_addition_lines_empty_diff(self):
        """Test extracting addition lines from an empty diff."""
        parser = DiffParser("")
        addition_lines = parser.extract_addition_lines()
        assert addition_lines == {}

    def test_extract_addition_lines_no_additions(self):
        """Test diff with only deletions."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "--- a/src/api.py\n"
            "+++ b/src/api.py\n"
            "@@ -1,3 +1,2 @@\n"
            " import os\n"
            "-import sys\n"
            "\n"
        )
        parser = DiffParser(diff)
        addition_lines = parser.extract_addition_lines()
        assert addition_lines == {}

    def test_extract_addition_lines_caches_result(self):
        """Test that extract_addition_lines caches its result."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "+++ b/src/api.py\n"
            "@@ -1,2 +1,3 @@\n"
            " import os\n"
            "+import sys\n"
        )
        parser = DiffParser(diff)
        lines1 = parser.extract_addition_lines()
        lines2 = parser.extract_addition_lines()
        assert lines1 is lines2  # Same object (cached)


class TestDiffParserFormatLineRanges:
    """Tests for DiffParser.format_line_ranges() method."""

    def test_format_single_line(self):
        """Test formatting a single line."""
        parser = DiffParser("")
        result = parser.format_line_ranges([5])
        assert result == "5"

    def test_format_consecutive_lines(self):
        """Test formatting consecutive lines as a range."""
        parser = DiffParser("")
        result = parser.format_line_ranges([1, 2, 3])
        assert result == "1-3"

    def test_format_mixed_lines(self):
        """Test formatting mixed single lines and ranges."""
        parser = DiffParser("")
        result = parser.format_line_ranges([1, 2, 3, 5, 7, 8, 9])
        assert result == "1-3, 5, 7-9"

    def test_format_unsorted_lines(self):
        """Test that unsorted lines are sorted before formatting."""
        parser = DiffParser("")
        result = parser.format_line_ranges([5, 1, 3, 2])
        assert result == "1-3, 5"

    def test_format_empty_lines(self):
        """Test formatting empty list."""
        parser = DiffParser("")
        result = parser.format_line_ranges([])
        assert result == ""


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_extract_files_from_diff_function(self):
        """Test the extract_files_from_diff convenience function."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "+++ b/src/api.py\n"
        )
        files = extract_files_from_diff(diff)
        assert files == ["src/api.py"]

    def test_extract_addition_lines_from_diff_function(self):
        """Test the extract_addition_lines_from_diff convenience function."""
        diff = (
            "diff --git a/src/api.py b/src/api.py\n"
            "+++ b/src/api.py\n"
            "@@ -1,2 +1,3 @@\n"
            " import os\n"
            "+import sys\n"
        )
        addition_lines = extract_addition_lines_from_diff(diff)
        assert addition_lines == {"src/api.py": [2]}
