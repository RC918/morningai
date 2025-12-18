"""Unit tests for verify_architecture_manifest.py exclusion patterns.

This module tests the link security check exclusion patterns to ensure
legitimate HTTP URLs in code examples, internal services, and formatting
examples are correctly excluded from the insecure link detection.

Issue #2667: Add unit tests for exclusion patterns
Related: PR #2664, Epic #2465
"""

import re
import sys
from pathlib import Path

import pytest

# Add parent directory to path for importing the module under test
sys.path.insert(0, str(Path(__file__).parent.parent))
from verify_architecture_manifest import ManifestVerifier  # noqa: E402


class TestLinkSecurityExclusionPatterns:
    """Tests for the exclusion patterns in check_link_security method."""

    @pytest.fixture
    def verifier(self, tmp_path: Path) -> ManifestVerifier:
        """Create a ManifestVerifier instance with a temporary repo root."""
        return ManifestVerifier(tmp_path, verbose=False)

    @pytest.fixture
    def docs_dir(self, tmp_path: Path) -> Path:
        """Create a docs directory for testing."""
        docs = tmp_path / "docs"
        docs.mkdir()
        return docs

    def create_doc_file(self, docs_dir: Path, filename: str, content: str) -> Path:
        """Helper to create a documentation file with given content."""
        file_path = docs_dir / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path

    # ========== Tests for http://example.com exclusion ==========

    def test_excludes_example_com_basic(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://example.com is excluded from insecure link detection."""
        self.create_doc_file(docs_dir, "test.md", "Visit http://example.com for more info.")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_excludes_example_com_with_path(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://example.com/path is excluded."""
        self.create_doc_file(docs_dir, "test.md", "API endpoint: http://example.com/api/v1/users")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_excludes_example_com_with_query(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://example.com with query params is excluded."""
        self.create_doc_file(docs_dir, "test.md", "URL: http://example.com?foo=bar&baz=qux")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_does_not_exclude_example_org(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://example.org is NOT excluded (only example.com)."""
        self.create_doc_file(docs_dir, "test.md", "Visit http://example.org for more info.")
        verifier.check_link_security({})
        assert len(verifier.errors) == 1
        assert "example.org" in verifier.errors[0]

    # ========== Tests for http://mcp-server exclusion ==========

    def test_excludes_mcp_server_basic(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://mcp-server is excluded (internal service)."""
        self.create_doc_file(docs_dir, "test.md", "Connect to http://mcp-server:8080")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_excludes_mcp_server_with_path(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://mcp-server with path is excluded."""
        self.create_doc_file(docs_dir, "test.md", "Endpoint: http://mcp-server:8080/api/health")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_excludes_mcp_server_no_port(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://mcp-server without port is excluded."""
        self.create_doc_file(docs_dir, "test.md", "Server: http://mcp-server/status")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_does_not_exclude_similar_server_names(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that similar but different server names are NOT excluded."""
        self.create_doc_file(docs_dir, "test.md", "Connect to http://other-server:8080")
        verifier.check_link_security({})
        assert len(verifier.errors) == 1
        assert "other-server" in verifier.errors[0]

    # ========== Tests for http://` (backtick) exclusion ==========

    def test_excludes_backtick_format_example(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://` formatting example is excluded."""
        self.create_doc_file(docs_dir, "test.md", "Protocol mismatch: http://`")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_excludes_backtick_in_code_block(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://` in code context is excluded."""
        content = """
```
# Example of protocol mismatch
url = "http://`"
```
"""
        self.create_doc_file(docs_dir, "test.md", content)
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    # ========== Tests for http://$ (variable) exclusion ==========

    def test_excludes_variable_url_basic(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://$ variable URL is excluded."""
        self.create_doc_file(docs_dir, "test.md", "URL: http://$HOST:$PORT")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_excludes_variable_url_with_braces(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://${VAR} style URLs are excluded."""
        self.create_doc_file(docs_dir, "test.md", "Connect to http://${SERVER_HOST}:${SERVER_PORT}")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    # ========== Tests for localhost/IP exclusions (built-in) ==========

    def test_excludes_localhost(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://localhost is excluded (built-in exclusion)."""
        self.create_doc_file(docs_dir, "test.md", "Dev server: http://localhost:3000")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_excludes_127_0_0_1(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://127.0.0.1 is excluded (built-in exclusion)."""
        self.create_doc_file(docs_dir, "test.md", "Local: http://127.0.0.1:8080")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_excludes_0_0_0_0(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that http://0.0.0.0 is excluded (built-in exclusion)."""
        self.create_doc_file(docs_dir, "test.md", "Bind: http://0.0.0.0:5000")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    # ========== Tests for real insecure links (should be detected) ==========

    def test_detects_real_insecure_link(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that real insecure HTTP links are detected."""
        self.create_doc_file(docs_dir, "test.md", "Visit http://insecure-site.com for info.")
        verifier.check_link_security({})
        assert len(verifier.errors) == 1
        assert "insecure-site.com" in verifier.errors[0]

    def test_detects_multiple_insecure_links(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that multiple insecure links are all detected."""
        content = """
Link 1: http://site1.com
Link 2: http://site2.org/path
Link 3: http://site3.net:8080
"""
        self.create_doc_file(docs_dir, "test.md", content)
        verifier.check_link_security({})
        assert len(verifier.errors) == 3

    def test_https_links_are_not_flagged(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that HTTPS links are not flagged as insecure."""
        self.create_doc_file(docs_dir, "test.md", "Secure: https://secure-site.com")
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    # ========== Edge case tests ==========

    def test_mixed_excluded_and_insecure_links(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test file with both excluded and insecure links."""
        content = """
# Documentation

Example: http://example.com/api
Internal: http://mcp-server:8080
Insecure: http://real-site.com
Local: http://localhost:3000
"""
        self.create_doc_file(docs_dir, "test.md", content)
        verifier.check_link_security({})
        # Only http://real-site.com should be flagged
        assert len(verifier.errors) == 1
        assert "real-site.com" in verifier.errors[0]

    def test_empty_docs_directory(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test with empty docs directory."""
        verifier.check_link_security({})
        assert len(verifier.errors) == 0

    def test_no_docs_directory(self, verifier: ManifestVerifier) -> None:
        """Test when docs directory doesn't exist."""
        verifier.check_link_security({})
        # Should log a warning, not an error
        assert len(verifier.errors) == 0
        assert len(verifier.warnings) == 1
        assert "docs/ directory not found" in verifier.warnings[0]

    def test_multiple_files_with_links(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test scanning multiple documentation files."""
        self.create_doc_file(docs_dir, "file1.md", "Safe: http://example.com")
        self.create_doc_file(docs_dir, "file2.md", "Insecure: http://bad-site.com")
        self.create_doc_file(docs_dir, "file3.md", "Local: http://localhost:3000")

        verifier.check_link_security({})
        # Only file2.md should have an error
        assert len(verifier.errors) == 1
        assert "bad-site.com" in verifier.errors[0]

    def test_nested_docs_directory(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test scanning nested documentation directories."""
        subdir = docs_dir / "subdir"
        subdir.mkdir()
        self.create_doc_file(subdir, "nested.md", "Insecure: http://nested-insecure.com")

        verifier.check_link_security({})
        assert len(verifier.errors) == 1
        assert "nested-insecure.com" in verifier.errors[0]

    def test_non_md_files_ignored(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test that non-markdown files are ignored."""
        # Create a .txt file with insecure link
        txt_file = docs_dir / "readme.txt"
        txt_file.write_text("Insecure: http://should-be-ignored.com", encoding='utf-8')

        verifier.check_link_security({})
        # Should not detect the link in .txt file
        assert len(verifier.errors) == 0

    def test_special_characters_in_url(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test URLs with special characters."""
        content = """
URL with params: http://site.com/path?query=value&other=123
URL with fragment: http://site.com/page#section
URL with encoded: http://site.com/path%20with%20spaces
"""
        self.create_doc_file(docs_dir, "test.md", content)
        verifier.check_link_security({})
        # All should be detected as insecure
        assert len(verifier.errors) == 3

    def test_url_at_end_of_line(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test URL detection at end of line."""
        self.create_doc_file(docs_dir, "test.md", "Visit http://end-of-line.com")
        verifier.check_link_security({})
        assert len(verifier.errors) == 1

    def test_url_in_markdown_link(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test URL in markdown link syntax."""
        self.create_doc_file(docs_dir, "test.md", "[Click here](http://markdown-link.com)")
        verifier.check_link_security({})
        assert len(verifier.errors) == 1
        assert "markdown-link.com" in verifier.errors[0]

    def test_url_in_angle_brackets(self, verifier: ManifestVerifier, docs_dir: Path) -> None:
        """Test URL in angle brackets."""
        self.create_doc_file(docs_dir, "test.md", "Link: <http://angle-brackets.com>")
        verifier.check_link_security({})
        assert len(verifier.errors) == 1


class TestExclusionPatternRegex:
    """Direct tests for the exclusion pattern regex compilation."""

    def test_excluded_patterns_compile(self) -> None:
        """Test that all exclusion patterns compile correctly."""
        excluded_patterns = [
            r'http://example\.com',
            r'http://mcp-server',
            r'http://`',
            r'http://\$',
        ]
        # Should not raise
        excluded_regex = re.compile('|'.join(excluded_patterns))
        assert excluded_regex is not None

    def test_excluded_regex_matches_example_com(self) -> None:
        """Test regex matches http://example.com."""
        excluded_patterns = [
            r'http://example\.com',
            r'http://mcp-server',
            r'http://`',
            r'http://\$',
        ]
        excluded_regex = re.compile('|'.join(excluded_patterns))

        assert excluded_regex.search("http://example.com")
        assert excluded_regex.search("http://example.com/path")
        assert not excluded_regex.search("http://example.org")

    def test_excluded_regex_matches_mcp_server(self) -> None:
        """Test regex matches http://mcp-server."""
        excluded_patterns = [
            r'http://example\.com',
            r'http://mcp-server',
            r'http://`',
            r'http://\$',
        ]
        excluded_regex = re.compile('|'.join(excluded_patterns))

        assert excluded_regex.search("http://mcp-server")
        assert excluded_regex.search("http://mcp-server:8080")
        assert not excluded_regex.search("http://other-server")

    def test_excluded_regex_matches_backtick(self) -> None:
        """Test regex matches http://`."""
        excluded_patterns = [
            r'http://example\.com',
            r'http://mcp-server',
            r'http://`',
            r'http://\$',
        ]
        excluded_regex = re.compile('|'.join(excluded_patterns))

        assert excluded_regex.search("http://`")

    def test_excluded_regex_matches_variable(self) -> None:
        """Test regex matches http://$."""
        excluded_patterns = [
            r'http://example\.com',
            r'http://mcp-server',
            r'http://`',
            r'http://\$',
        ]
        excluded_regex = re.compile('|'.join(excluded_patterns))

        assert excluded_regex.search("http://$HOST")
        assert excluded_regex.search("http://${SERVER}")


class TestHttpPatternRegex:
    """Tests for the main HTTP pattern regex."""

    def test_http_pattern_matches_basic_url(self) -> None:
        """Test HTTP pattern matches basic URLs."""
        http_pattern = re.compile(r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^\s\)>\]]+')

        matches = http_pattern.findall("Visit http://example.com for info")
        assert len(matches) == 1
        assert "example.com" in matches[0]

    def test_http_pattern_excludes_localhost(self) -> None:
        """Test HTTP pattern excludes localhost."""
        http_pattern = re.compile(r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^\s\)>\]]+')

        matches = http_pattern.findall("Local: http://localhost:3000")
        assert len(matches) == 0

    def test_http_pattern_excludes_127_0_0_1(self) -> None:
        """Test HTTP pattern excludes 127.0.0.1."""
        http_pattern = re.compile(r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^\s\)>\]]+')

        matches = http_pattern.findall("Local: http://127.0.0.1:8080")
        assert len(matches) == 0

    def test_http_pattern_excludes_0_0_0_0(self) -> None:
        """Test HTTP pattern excludes 0.0.0.0."""
        http_pattern = re.compile(r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^\s\)>\]]+')

        matches = http_pattern.findall("Bind: http://0.0.0.0:5000")
        assert len(matches) == 0

    def test_http_pattern_stops_at_whitespace(self) -> None:
        """Test HTTP pattern stops at whitespace."""
        http_pattern = re.compile(r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^\s\)>\]]+')

        matches = http_pattern.findall("URL: http://site.com more text")
        assert len(matches) == 1
        # The regex captures the full URL including http://
        assert matches[0] == "http://site.com"
        assert "more text" not in matches[0]

    def test_http_pattern_stops_at_parenthesis(self) -> None:
        """Test HTTP pattern stops at closing parenthesis."""
        http_pattern = re.compile(r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^\s\)>\]]+')

        matches = http_pattern.findall("[Link](http://site.com)")
        assert len(matches) == 1
        # The regex captures the full URL including http://
        assert matches[0] == "http://site.com"

    def test_http_pattern_stops_at_angle_bracket(self) -> None:
        """Test HTTP pattern stops at closing angle bracket."""
        http_pattern = re.compile(r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^\s\)>\]]+')

        matches = http_pattern.findall("<http://site.com>")
        assert len(matches) == 1
        # The regex captures the full URL including http://
        assert matches[0] == "http://site.com"
