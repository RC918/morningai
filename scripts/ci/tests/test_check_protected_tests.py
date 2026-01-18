"""
Tests for check_protected_tests.py

H-4 CI Enforcement (Blueprint Section 5.4)
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_protected_tests import (  # noqa: E402
    PROTECTION_MARKER,
    REGRESSION_TEST_DIR,
    is_protected_test,
    is_regression_test_file,
)


class TestIsRegressionTestFile:
    """Tests for is_regression_test_file function."""

    def test_file_in_regression_dir(self):
        """Test that files in regression dir are detected."""
        assert is_regression_test_file("tests/regression/test_foo.py") is True
        assert is_regression_test_file("tests/regression/subdir/test_bar.py") is True

    def test_file_not_in_regression_dir(self):
        """Test that files outside regression dir are not detected."""
        assert is_regression_test_file("tests/test_foo.py") is False
        assert is_regression_test_file("src/regression/test_foo.py") is False

    def test_similar_directory_names(self):
        """Test that similar directory names don't match."""
        # Should NOT match tests/regression_backup
        assert is_regression_test_file("tests/regression_backup/test_foo.py") is False
        assert is_regression_test_file("tests/regression2/test_foo.py") is False

    def test_exact_directory_match(self):
        """Test exact directory path."""
        assert is_regression_test_file("tests/regression") is True

    def test_custom_regression_dir(self):
        """Test with custom regression directory."""
        assert is_regression_test_file(
            "custom/regression/test_foo.py",
            regression_dir="custom/regression"
        ) is True
        assert is_regression_test_file(
            "tests/regression/test_foo.py",
            regression_dir="custom/regression"
        ) is False


class TestIsProtectedTest:
    """Tests for is_protected_test function."""

    def test_protected_test_detected(self):
        """Test that protected tests are detected."""
        content = '''
"""Test module."""
import pytest

REGRESSION_METADATA = {
    "candidate_id": "abc12345",
    "protected": True,
}

def test_something():
    pass
'''
        assert is_protected_test(content) is True

    def test_unprotected_test_not_detected(self):
        """Test that unprotected tests are not detected."""
        content = '''
"""Test module."""
import pytest

def test_something():
    pass
'''
        assert is_protected_test(content) is False

    def test_partial_marker_not_detected(self):
        """Test that partial marker names don't match.
        
        Uses word boundary matching to avoid false positives with similar markers
        like REGRESSION_METADATA_EXTRA.
        """
        content = '''
# This is not REGRESSION_METADATA_EXTRA
SOME_OTHER_METADATA = {}
'''
        # Should NOT match because we use word boundary regex
        # REGRESSION_METADATA_EXTRA is a different marker than REGRESSION_METADATA
        assert is_protected_test(content) is False

    def test_marker_in_comment(self):
        """Test that marker in comment is detected."""
        content = '''
# Contains REGRESSION_METADATA marker
def test_something():
    pass
'''
        assert is_protected_test(content) is True


class TestProtectionMarker:
    """Tests for protection marker constant."""

    def test_marker_value(self):
        """Test that marker has expected value."""
        assert PROTECTION_MARKER == "REGRESSION_METADATA"

    def test_default_regression_dir(self):
        """Test default regression directory."""
        assert REGRESSION_TEST_DIR == "tests/regression"
