"""
Intentional test failure to trigger CI failure for SeniorCoder validation.

Purpose: Validate that CI failure triggers SeniorCoder auto-fix flow.
Expected: API Backend Tests should fail, triggering SeniorCoder.

DO NOT MERGE - This is for staging validation only.

Test run 4 - 2026-01-02 06:58 UTC
Testing webhook dedup fix (PR #3485 merged and deployed)
"""
import pytest


class TestCIFailureValidation:
    """Intentional test failures to trigger CI failure."""

    def test_intentional_failure_for_ci_validation(self):
        """This test intentionally fails to trigger CI failure."""
        # This assertion will fail, causing API Backend Tests to fail
        assert False, "Intentional failure to trigger CI failure for SeniorCoder validation"
