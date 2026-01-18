"""
H-2 Regression Pipeline Verification Test

This test intentionally fails to verify that:
1. CI failure triggers the Regression Pipeline (H-2.1)
2. Diagnostic Agent analyzes the failure (H-2.2)
3. LLM generates a regression test (H-2.3)
4. Test is written to disk (H-2.4)

After verification, this PR should be closed without merging.
"""

import pytest


def test_intentional_failure_for_h2_verification():
    """
    This test intentionally fails to trigger the H-2 Regression Pipeline.
    
    Expected behavior in Staging:
    - CI fails on this test
    - D-4 triggers fixer_node
    - Diagnostic Agent analyzes the failure
    - RegressionTestGenerator creates a test using LLM
    - Test is written to tests/regression/ directory
    
    Logs to search for:
    - [RegressionPipeline]
    - [FixerNode]
    - Generating regression test using LLM
    - Writing regression test to disk
    """
    # Intentional assertion failure
    expected_value = 42
    actual_value = 0
    
    assert actual_value == expected_value, (
        f"H-2 Verification: Expected {expected_value} but got {actual_value}. "
        "This failure is intentional to test the Regression Pipeline."
    )
