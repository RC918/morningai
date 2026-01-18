"""
Test for validate_priority_score function.

This test is designed to fail intentionally to trigger the D-4 SelfCorrectionLoop
with SimpleCoder. The test expects validate_priority_score to reject scores > 1.0,
but the function has a bug that allows them.
"""

from simulation.regression import validate_priority_score


def test_valid_score_zero():
    """Test that score 0.0 is valid."""
    assert validate_priority_score(0.0) is True


def test_valid_score_one():
    """Test that score 1.0 is valid."""
    assert validate_priority_score(1.0) is True


def test_valid_score_middle():
    """Test that score 0.5 is valid."""
    assert validate_priority_score(0.5) is True


def test_invalid_score_negative():
    """Test that negative scores are rejected."""
    assert validate_priority_score(-0.1) is False
    assert validate_priority_score(-1.0) is False


def test_invalid_score_above_one():
    """
    Test that scores above 1.0 are rejected.

    This test will FAIL due to the intentional bug in validate_priority_score.
    The function should return False for scores > 1.0, but it returns True.

    SelfCorrectionLoop should detect this failure and use SimpleCoder to fix it.
    """
    assert validate_priority_score(1.5) is False, "Score 1.5 should be invalid"
    assert validate_priority_score(2.0) is False, "Score 2.0 should be invalid"
    assert validate_priority_score(100.0) is False, "Score 100.0 should be invalid"
