"""Test file to trigger CI failure and observe GeneralCoder/SimpleCoder auto-fix.

This test intentionally fails to trigger the fixer_node pipeline.
DO NOT manually fix - let GeneralCoder/SimpleCoder handle it.

Test PR for Issue #3360 investigation.
"""
import pytest


class TestAutofixTrigger:
    """Test class with intentional failure to trigger auto-fix."""

    def test_intentional_failure_for_autofix_observation(self):
        """This test intentionally fails to trigger GeneralCoder/SimpleCoder.

        The fix is simple: change `assert False` to `assert True`.
        This allows us to observe if the auto-fix pipeline detects and fixes it.
        """
        # INTENTIONAL FAILURE - DO NOT MANUALLY FIX
        # Let GeneralCoder/SimpleCoder fix this
        assert False, "Intentional failure to trigger auto-fix pipeline"

    def test_passing_test_for_comparison(self):
        """This test passes normally for comparison."""
        assert True
