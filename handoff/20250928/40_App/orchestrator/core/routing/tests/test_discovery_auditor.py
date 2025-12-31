"""
Tests for DiscoveryAuditor - Reviewer Agent capability for test discovery audit.

Issue #3310: Discovery 全鏈路治理 - Layer 2 (Reviewer Agent Auditor)
"""

import pytest

from core.routing.discovery_auditor import (
    AuditResult,
    AuditStatus,
    DiscoveryAuditor,
    create_discovery_auditor,
)


class TestDiscoveryAuditor:
    """Tests for DiscoveryAuditor class."""

    @pytest.fixture
    def auditor(self) -> DiscoveryAuditor:
        """Create a DiscoveryAuditor instance for testing."""
        return DiscoveryAuditor()

    def test_audit_no_test_files_in_diff(self, auditor: DiscoveryAuditor):
        """Test audit when PR diff contains no test files."""
        pr_diff = """
diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+# New comment
 def main():
     pass
"""
        ci_logs = "collected 100 tests"

        result = auditor.audit_test_execution(pr_diff, ci_logs)

        assert result.status == AuditStatus.SKIPPED
        assert "No test files found" in result.message
        assert result.missing_tests == []

    def test_audit_all_tests_executed(self, auditor: DiscoveryAuditor):
        """Test audit when all test files in diff are executed in CI."""
        pr_diff = """
diff --git a/tests/test_feature.py b/tests/test_feature.py
--- /dev/null
+++ b/tests/test_feature.py
@@ -0,0 +1,10 @@
+def test_new_feature():
+    pass
"""
        ci_logs = """
collecting ...
<Module tests/test_feature.py>
  <Function test_new_feature>
collected 1 item

tests/test_feature.py::test_new_feature PASSED
"""

        result = auditor.audit_test_execution(pr_diff, ci_logs, base_path="")

        assert result.status == AuditStatus.APPROVED
        assert "1 test file(s) in diff were executed" in result.message
        assert result.missing_tests == []
        assert "tests/test_feature.py" in result.new_test_files

    def test_audit_missing_test_execution(self, auditor: DiscoveryAuditor):
        """Test audit when test files in diff are NOT executed in CI."""
        pr_diff = """
diff --git a/new_module/tests/test_new.py b/new_module/tests/test_new.py
--- /dev/null
+++ b/new_module/tests/test_new.py
@@ -0,0 +1,5 @@
+def test_something():
+    pass
"""
        ci_logs = """
collecting ...
<Module tests/test_existing.py>
collected 50 items

tests/test_existing.py::test_old PASSED
"""

        result = auditor.audit_test_execution(pr_diff, ci_logs, base_path="")

        assert result.status == AuditStatus.REQUEST_CHANGES
        assert "Silent failure detected" in result.message
        assert "new_module/tests/test_new.py" in result.missing_tests

    def test_audit_partial_execution(self, auditor: DiscoveryAuditor):
        """Test audit when some test files are executed and some are not."""
        pr_diff = """
diff --git a/tests/test_a.py b/tests/test_a.py
--- /dev/null
+++ b/tests/test_a.py
@@ -0,0 +1,3 @@
+def test_a():
+    pass

diff --git a/other/tests/test_b.py b/other/tests/test_b.py
--- /dev/null
+++ b/other/tests/test_b.py
@@ -0,0 +1,3 @@
+def test_b():
+    pass
"""
        ci_logs = """
<Module tests/test_a.py>
tests/test_a.py::test_a PASSED
"""

        result = auditor.audit_test_execution(pr_diff, ci_logs, base_path="")

        assert result.status == AuditStatus.REQUEST_CHANGES
        assert len(result.missing_tests) == 1
        assert "other/tests/test_b.py" in result.missing_tests
        assert "tests/test_a.py" in result.new_test_files

    def test_audit_with_base_path_stripping(self, auditor: DiscoveryAuditor):
        """Test that base_path is correctly stripped for path matching."""
        pr_diff = """
diff --git a/handoff/20250928/40_App/orchestrator/tests/test_new.py b/handoff/20250928/40_App/orchestrator/tests/test_new.py
--- /dev/null
+++ b/handoff/20250928/40_App/orchestrator/tests/test_new.py
@@ -0,0 +1,3 @@
+def test_new():
+    pass
"""
        ci_logs = """
<Module tests/test_new.py>
tests/test_new.py::test_new PASSED
"""

        result = auditor.audit_test_execution(
            pr_diff,
            ci_logs,
            base_path="handoff/20250928/40_App/orchestrator/"
        )

        assert result.status == AuditStatus.APPROVED
        assert result.missing_tests == []

    def test_extract_test_files_from_diff_new_file(self, auditor: DiscoveryAuditor):
        """Test extraction of new test files from diff."""
        pr_diff = """
diff --git a/tests/test_new.py b/tests/test_new.py
--- /dev/null
+++ b/tests/test_new.py
@@ -0,0 +1,5 @@
+def test_something():
+    pass
"""

        test_files = auditor._extract_test_files_from_diff(pr_diff)

        assert "tests/test_new.py" in test_files

    def test_extract_test_files_from_diff_modified_file(self, auditor: DiscoveryAuditor):
        """Test extraction of modified test files from diff."""
        pr_diff = """
diff --git a/tests/test_existing.py b/tests/test_existing.py
--- a/tests/test_existing.py
+++ b/tests/test_existing.py
@@ -1,3 +1,5 @@
 def test_old():
     pass
+def test_new():
+    pass
"""

        test_files = auditor._extract_test_files_from_diff(pr_diff)

        assert "tests/test_existing.py" in test_files

    def test_extract_test_files_ignores_non_test_files(self, auditor: DiscoveryAuditor):
        """Test that non-test files are ignored."""
        pr_diff = """
diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+# comment
 def main():
     pass

diff --git a/tests/conftest.py b/tests/conftest.py
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -1,3 +1,4 @@
+# fixture
 import pytest
"""

        test_files = auditor._extract_test_files_from_diff(pr_diff)

        assert len(test_files) == 0

    def test_extract_test_files_ignores_deleted_files(self, auditor: DiscoveryAuditor):
        """Test that deleted test files are correctly ignored.

        This is a critical test case from Gemini Code Assist:
        Deleted files have --- a/path and +++ /dev/null, so they should NOT
        be flagged as "silent failures" since they no longer exist.
        """
        pr_diff = """
diff --git a/tests/test_to_be_deleted.py b/tests/test_to_be_deleted.py
deleted file mode 100644
--- a/tests/test_to_be_deleted.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def test_old():
-    pass
-
"""

        test_files = auditor._extract_test_files_from_diff(pr_diff)

        # Deleted files should NOT be extracted (they have +++ /dev/null, not +++ b/path)
        assert len(test_files) == 0

    def test_extract_executed_tests_collection_format(self, auditor: DiscoveryAuditor):
        """Test extraction from pytest collection output."""
        ci_logs = """
collecting ...
<Module tests/test_a.py>
  <Class TestA>
    <Function test_method>
<Module tests/test_b.py>
  <Function test_func>
collected 2 items
"""

        executed = auditor._extract_executed_tests_from_logs(ci_logs)

        assert "tests/test_a.py" in executed
        assert "tests/test_b.py" in executed

    def test_extract_executed_tests_execution_format(self, auditor: DiscoveryAuditor):
        """Test extraction from pytest execution output."""
        ci_logs = """
tests/test_a.py::TestA::test_method PASSED
tests/test_b.py::test_func FAILED
"""

        executed = auditor._extract_executed_tests_from_logs(ci_logs)

        assert "tests/test_a.py" in executed
        assert "tests/test_b.py" in executed

    def test_extract_executed_tests_result_format(self, auditor: DiscoveryAuditor):
        """Test extraction from pytest result summary."""
        ci_logs = """
=== FAILURES ===
FAILED tests/test_fail.py::test_bad
=== short test summary info ===
PASSED tests/test_pass.py::test_good
ERROR tests/test_error.py::test_broken
SKIPPED tests/test_skip.py::test_skipped
"""

        executed = auditor._extract_executed_tests_from_logs(ci_logs)

        assert "tests/test_fail.py" in executed
        assert "tests/test_pass.py" in executed
        assert "tests/test_error.py" in executed
        assert "tests/test_skip.py" in executed


class TestAuditResult:
    """Tests for AuditResult dataclass."""

    def test_to_review_comment_approved(self):
        """Test that APPROVED status returns None for comment."""
        result = AuditResult(
            status=AuditStatus.APPROVED,
            message="All tests executed",
            new_test_files=["tests/test_a.py"],
            executed_tests=["tests/test_a.py"]
        )

        assert result.to_review_comment() is None

    def test_to_review_comment_skipped(self):
        """Test that SKIPPED status returns None for comment."""
        result = AuditResult(
            status=AuditStatus.SKIPPED,
            message="No test files"
        )

        assert result.to_review_comment() is None

    def test_to_review_comment_request_changes(self):
        """Test that REQUEST_CHANGES generates proper comment."""
        result = AuditResult(
            status=AuditStatus.REQUEST_CHANGES,
            message="Silent failure detected",
            missing_tests=["new_module/tests/test_new.py", "other/tests/test_other.py"]
        )

        comment = result.to_review_comment()

        assert comment is not None
        assert "Silent Failure Detected" in comment
        assert "new_module/tests/test_new.py" in comment
        assert "other/tests/test_other.py" in comment
        assert "pytest.ini" in comment
        assert "3310" in comment  # Issue number in URL


class TestCreateDiscoveryAuditor:
    """Tests for factory function."""

    def test_create_discovery_auditor(self):
        """Test factory function creates valid instance."""
        auditor = create_discovery_auditor()

        assert isinstance(auditor, DiscoveryAuditor)
