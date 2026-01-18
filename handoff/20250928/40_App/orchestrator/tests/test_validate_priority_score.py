"""
Test for validate_priority_score function.

H-2 Verification: This test will FAIL because validate_priority_score
has an intentional bug (missing upper bound check).

This test is placed in the tests/ directory to ensure pytest discovers it.
The PR also contains code changes in regression.py to bypass smart filtering.
"""

from simulation.regression import validate_priority_score


class TestValidatePriorityScore:
    """Tests for the validate_priority_score function."""

    def test_valid_score_zero(self):
        """Test that 0.0 is a valid score."""
        assert validate_priority_score(0.0) is True

    def test_valid_score_one(self):
        """Test that 1.0 is a valid score."""
        assert validate_priority_score(1.0) is True

    def test_valid_score_middle(self):
        """Test that 0.5 is a valid score."""
        assert validate_priority_score(0.5) is True

    def test_invalid_score_negative(self):
        """Test that negative scores are invalid."""
        assert validate_priority_score(-0.1) is False
        assert validate_priority_score(-1.0) is False

    def test_invalid_score_above_one(self):
        """
        Test that scores above 1.0 are invalid.

        H-2 Verification: This test will FAIL because validate_priority_score
        has an intentional bug - it doesn't check for score > 1.0.

        Expected: validate_priority_score(1.5) returns False
        Actual (buggy): validate_priority_score(1.5) returns True
        """
        # This assertion will FAIL due to the intentional bug
        assert validate_priority_score(1.5) is False, (
            "Score 1.5 should be invalid (above 1.0 range). "
            "This failure is intentional to test the H-2 Regression Pipeline."
        )
        assert validate_priority_score(2.0) is False, (
            "Score 2.0 should be invalid (above 1.0 range). "
            "This failure is intentional to test the H-2 Regression Pipeline."
        )
