"""
Unit tests for diagnostic_helper module.

Tests the format_diagnostic function for:
- Valid JSON output
- Fallback mechanism on serialization errors
- Size limits and array sampling
- Special characters handling
"""
import json
from diagnostic_helper import format_diagnostic, _sample_array, MAX_SAMPLE_SIZE


class TestFormatDiagnostic:
    """Tests for format_diagnostic function."""

    def test_basic_output_is_valid_json(self):
        """Test that basic output produces valid JSON after the delimiter."""
        data = {"pr_number": 123, "trace_id": "abc123"}
        result = format_diagnostic(data)

        # Should start with " | "
        assert result.startswith(" | ")

        # JSON part should be parseable
        json_part = result[3:]  # Skip " | "
        parsed = json.loads(json_part)
        assert parsed["pr_number"] == 123
        assert parsed["trace_id"] == "abc123"

    def test_array_sampling_for_large_arrays(self):
        """Test that large arrays are sampled to prevent log truncation."""
        large_array = [{"file": f"file{i}.py", "line": i} for i in range(50)]
        data = {"raw_comment_structures": large_array}
        result = format_diagnostic(data)

        json_part = result[3:]
        parsed = json.loads(json_part)

        # Should have count, sample, and hash
        assert "raw_comment_structures" in parsed
        sampled = parsed["raw_comment_structures"]
        assert sampled["count"] == 50
        assert len(sampled["sample"]) == MAX_SAMPLE_SIZE
        assert sampled["hash"] is not None

    def test_fallback_on_non_serializable_object(self):
        """Test fallback when data contains non-serializable objects."""
        class NonSerializable:
            pass

        data = {"obj": NonSerializable(), "pr_number": 123}
        result = format_diagnostic(data)

        # Should still produce valid JSON
        assert result.startswith(" | ")
        json_part = result[3:]
        parsed = json.loads(json_part)

        # Should contain the serializable fields
        assert "pr_number" in parsed or "_diagnostic_error" in parsed

    def test_special_characters_in_data(self):
        """Test that special characters are properly escaped."""
        data = {
            "file": "path/with\"quotes.py",
            "message": "line with\nnewline",
            "unicode": "中文字符"
        }
        result = format_diagnostic(data)

        json_part = result[3:]
        parsed = json.loads(json_part)
        assert parsed["file"] == "path/with\"quotes.py"
        assert parsed["unicode"] == "中文字符"

    def test_empty_data(self):
        """Test handling of empty data."""
        result = format_diagnostic({})

        json_part = result[3:]
        parsed = json.loads(json_part)
        # Empty data should only contain the version field
        assert "_v" in parsed
        assert len(parsed) == 1  # Only version field

    def test_allowed_lines_sample_limiting(self):
        """Test that allowed_lines_sample is limited."""
        data = {
            "allowed_lines_sample": list(range(100))
        }
        result = format_diagnostic(data)

        json_part = result[3:]
        parsed = json.loads(json_part)
        assert len(parsed["allowed_lines_sample"]) == MAX_SAMPLE_SIZE
        assert parsed["allowed_lines_total"] == 100

    def test_set_conversion(self):
        """Test that sets are converted to sorted lists."""
        data = {"lines": {3, 1, 2}}
        result = format_diagnostic(data)

        json_part = result[3:]
        parsed = json.loads(json_part)
        assert parsed["lines"] == [1, 2, 3]


class TestSampleArray:
    """Tests for _sample_array helper function."""

    def test_small_array_not_sampled(self):
        """Test that small arrays are not sampled."""
        arr = [1, 2, 3]
        result = _sample_array(arr)

        assert result["count"] == 3
        assert result["sample"] == [1, 2, 3]
        assert result["hash"] is not None

    def test_large_array_sampled(self):
        """Test that large arrays are sampled."""
        arr = list(range(100))
        result = _sample_array(arr)

        assert result["count"] == 100
        assert len(result["sample"]) == MAX_SAMPLE_SIZE
        assert result["sample"] == list(range(MAX_SAMPLE_SIZE))

    def test_empty_array(self):
        """Test handling of empty array."""
        result = _sample_array([])

        assert result["count"] == 0
        assert result["sample"] == []
        assert result["hash"] is None

    def test_none_input(self):
        """Test handling of None input."""
        result = _sample_array(None)

        assert result["count"] == 0
        assert result["sample"] == []
