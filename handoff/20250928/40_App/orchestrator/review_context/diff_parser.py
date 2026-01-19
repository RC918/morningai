"""
Unified Diff Parser Module

Issue #4215: Refactor diff parsing logic to separate module
Issue #4214: Handle quoted file paths with spaces

This module provides a clean, reusable API for parsing unified diffs.
It extracts file paths and addition line numbers from git diff output.

Blueprint Alignment:
- Section 3.3 (Separation of Concerns): Separating diff parsing from prompt construction
- Improves testability and reusability

Usage:
    from review_context.diff_parser import DiffParser

    parser = DiffParser(diff_content)
    files = parser.extract_files()
    addition_lines = parser.extract_addition_lines()
"""

import re
from collections import defaultdict
from typing import Dict, List, Optional


# Pre-compiled regex patterns for diff parsing
# Pattern to match hunk headers: @@ -old_start,old_count +new_start,new_count @@
HUNK_HEADER_PATTERN = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@')

# Pattern to match diff --git headers: diff --git a/path b/path
# Issue #4214: Handle quoted file paths with spaces
# Git quotes paths containing spaces: diff --git "a/path with spaces" "b/path with spaces"
# Note: We use separate simple patterns instead of a complex combined pattern
# to avoid ReDoS vulnerabilities from nested quantifiers and backreferences.

# Simpler pattern for unquoted paths (most common case)
DIFF_GIT_HEADER_SIMPLE = re.compile(r'^diff --git a/(.+?) b/\1$')

# Pattern for quoted paths with spaces
DIFF_GIT_HEADER_QUOTED = re.compile(r'^diff --git "a/(.+?)" "b/\1"$')

# Pattern for +++ headers (fallback)
# Issue #4214: Handle quoted paths: +++ "b/path with spaces"
# Note: We use separate simple patterns instead of a complex combined pattern
# to avoid ReDoS vulnerabilities from nested quantifiers and backreferences.
PLUS_HEADER_SIMPLE = re.compile(r'^\+\+\+ b/(.+)$')
PLUS_HEADER_QUOTED = re.compile(r'^\+\+\+ "b/(.+)"$')


class DiffParser:
    """
    Parser for unified diff format.

    This class provides methods to extract file paths and addition line numbers
    from git diff output. It handles edge cases like:
    - Quoted file paths with spaces (Issue #4214)
    - Deleted files (/dev/null)
    - C++ pre-increment lines (+++counter;)

    Attributes:
        diff_content: The raw unified diff content
    """

    def __init__(self, diff_content: str):
        """
        Initialize the DiffParser with diff content.

        Args:
            diff_content: The unified diff content to parse
        """
        self.diff_content = diff_content
        self._files_cache: Optional[List[str]] = None
        self._addition_lines_cache: Optional[Dict[str, List[int]]] = None

    def extract_files(self) -> List[str]:
        """
        Extract file paths from the unified diff.

        Issue #4199: Prevent specialist file path hallucination by providing
        an explicit list of valid files to the LLM.

        Issue #4214: Handle quoted file paths with spaces.

        Returns:
            List of file paths that appear in the diff
        """
        if self._files_cache is not None:
            return self._files_cache

        files: List[str] = []

        for line in self.diff_content.split('\n'):
            file_path = self._extract_file_from_header(line)
            if file_path and file_path not in files:
                files.append(file_path)

        self._files_cache = files
        return files

    def _extract_file_from_header(self, line: str) -> Optional[str]:
        """
        Extract file path from a diff header line.

        Handles both diff --git headers and +++ headers.
        Supports quoted paths with spaces (Issue #4214).

        Args:
            line: A single line from the diff

        Returns:
            The file path if found, None otherwise
        """
        # Try diff --git header first (more reliable)
        if line.startswith('diff --git '):
            # Try simple unquoted pattern first (most common)
            match = DIFF_GIT_HEADER_SIMPLE.match(line)
            if match:
                return match.group(1)

            # Try quoted pattern for paths with spaces
            match = DIFF_GIT_HEADER_QUOTED.match(line)
            if match:
                return match.group(1)

        # Try +++ header (fallback)
        if line.startswith('+++ '):
            # Skip deleted files
            if line == '+++ /dev/null':
                return None

            # Try simple unquoted pattern first
            match = PLUS_HEADER_SIMPLE.match(line)
            if match:
                return match.group(1)

            # Try quoted pattern for paths with spaces
            match = PLUS_HEADER_QUOTED.match(line)
            if match:
                return match.group(1)

        return None

    def extract_addition_lines(self) -> Dict[str, List[int]]:
        """
        Extract valid addition line numbers from the unified diff.

        P0 Enhancement: Provide explicit list of valid addition lines to LLM
        to solve the problem of LLM not reliably following "addition-lines-only"
        constraint. This gives the LLM a concrete list of line numbers it can
        use for inline comments.

        Returns:
            Dict mapping file_path -> list of valid line numbers (addition lines only)
        """
        if self._addition_lines_cache is not None:
            return self._addition_lines_cache

        addition_lines: Dict[str, List[int]] = defaultdict(list)
        current_file: Optional[str] = None
        current_line_num: int = 0

        for line in self.diff_content.split('\n'):
            # Check for new file header
            if line.startswith('diff --git '):
                file_path = self._extract_file_from_header(line)
                if file_path:
                    current_file = file_path
                continue

            # Check for +++ header (fallback for file path)
            if line.startswith('+++ '):
                # Skip deleted files
                if line == '+++ /dev/null':
                    continue
                file_path = self._extract_file_from_header(line)
                if file_path:
                    current_file = file_path
                continue

            # Check for hunk header
            hunk_match = HUNK_HEADER_PATTERN.match(line)
            if hunk_match:
                # new_start is the starting line number in the new file
                current_line_num = int(hunk_match.group(1))
                continue

            # Skip if we don't have a current file
            if current_file is None:
                continue

            # Process diff lines within a hunk
            # Check for exact '+' prefix, not just startswith('+')
            # This correctly handles C++ pre-increment lines like '+++counter;'
            if line.startswith('+') and line != '+++' and not line.startswith('+++ '):
                # Addition line - this is a valid line for inline comments
                addition_lines[current_file].append(current_line_num)
                current_line_num += 1
            elif line.startswith('-') and line != '---' and not line.startswith('--- '):
                # Deletion line - does NOT increment new file line counter
                pass
            elif line.startswith(' ') or line == '':
                # Context line or empty line - increments new file line counter
                current_line_num += 1

        # Remove files with no addition lines and convert to regular dict
        result = {f: lines for f, lines in addition_lines.items() if lines}
        self._addition_lines_cache = result
        return result

    def format_line_ranges(self, lines: List[int]) -> str:
        """
        Format a list of line numbers into compact ranges.

        Example: [1, 2, 3, 5, 7, 8, 9] -> "1-3, 5, 7-9"

        Args:
            lines: List of line numbers (must be sorted)

        Returns:
            Formatted string with compact ranges
        """
        if not lines:
            return ""

        # Remove duplicates and sort
        sorted_lines = sorted(set(lines))
        ranges: List[str] = []
        range_start = sorted_lines[0]
        range_end = sorted_lines[0]

        for line in sorted_lines[1:]:
            if line == range_end + 1:
                # Continue the current range
                range_end = line
            else:
                # End current range and start new one
                if range_start == range_end:
                    ranges.append(str(range_start))
                else:
                    ranges.append(f"{range_start}-{range_end}")
                range_start = line
                range_end = line

        # Add the last range
        if range_start == range_end:
            ranges.append(str(range_start))
        else:
            ranges.append(f"{range_start}-{range_end}")

        return ", ".join(ranges)


def extract_files_from_diff(diff_content: str) -> List[str]:
    """
    Convenience function to extract files from a diff.

    Args:
        diff_content: The unified diff content

    Returns:
        List of file paths that appear in the diff
    """
    return DiffParser(diff_content).extract_files()


def extract_addition_lines_from_diff(diff_content: str) -> Dict[str, List[int]]:
    """
    Convenience function to extract addition lines from a diff.

    Args:
        diff_content: The unified diff content

    Returns:
        Dict mapping file_path -> list of valid line numbers
    """
    return DiffParser(diff_content).extract_addition_lines()
