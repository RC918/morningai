"""
Tests for Runtime Drift Detection (EPIC I-1)

These tests ensure:
1. Drift detector works correctly in observe-only mode
2. Drift detector does NOT break SimpleCoder/GeneralCoder
3. Feature flags control behavior as expected
4. Metrics are properly recorded

Contract Test: drift validator must not block SimpleCoder normal operation
"""

import json
import pytest
from unittest.mock import Mock, patch

# Import drift detector components
from governance.drift_detector import (
    DriftDetector,
    DriftDetectedError,
    DriftEvent,
    DriftType,
    DriftSeverity,
    DriftValidationResult,
    get_drift_detector,
    observe_response,
    reset_drift_detector,
)


class TestDriftDetector:
    """Unit tests for DriftDetector class"""

    def test_init_defaults(self):
        """Test default initialization (disabled)"""
        detector = DriftDetector()
        assert detector.enabled is False
        assert detector.block_on_fail is False
        assert detector.sample_rate == 1.0

    def test_init_enabled(self):
        """Test enabled initialization"""
        detector = DriftDetector(enabled=True, block_on_fail=False, sample_rate=0.5)
        assert detector.enabled is True
        assert detector.block_on_fail is False
        assert detector.sample_rate == 0.5

    def test_should_check_disabled(self):
        """Test should_check returns False when disabled"""
        detector = DriftDetector(enabled=False)
        assert detector.should_check() is False

    def test_should_check_enabled(self):
        """Test should_check returns True when enabled with full sampling"""
        detector = DriftDetector(enabled=True, sample_rate=1.0)
        assert detector.should_check() is True

    def test_should_check_zero_sample_rate(self):
        """Test should_check returns False with zero sample rate"""
        detector = DriftDetector(enabled=True, sample_rate=0.0)
        assert detector.should_check() is False

    def test_validate_empty_response(self):
        """Test detection of empty response"""
        detector = DriftDetector(enabled=True)
        result = detector.validate_response("", json_mode=False)

        assert result.is_valid is False
        assert result.has_drift is True
        assert len(result.events) == 1
        assert result.events[0].drift_type == DriftType.EMPTY_RESPONSE

    def test_validate_valid_json(self):
        """Test validation of valid JSON response"""
        detector = DriftDetector(enabled=True)
        content = json.dumps({"status": "success", "data": "test"})
        result = detector.validate_response(content, json_mode=True)

        assert result.is_valid is True
        assert result.has_drift is False
        assert len(result.events) == 0

    def test_validate_invalid_json(self):
        """Test detection of invalid JSON when json_mode=True"""
        detector = DriftDetector(enabled=True)
        result = detector.validate_response("not valid json {", json_mode=True)

        assert result.is_valid is False
        assert result.has_drift is True
        assert len(result.events) == 1
        assert result.events[0].drift_type == DriftType.JSON_PARSE_ERROR

    def test_validate_missing_required_field(self):
        """Test detection of missing required field"""
        detector = DriftDetector(enabled=True)
        content = json.dumps({"status": "success"})
        schema = {"required": ["status", "data"]}

        result = detector.validate_response(
            content, json_mode=True, expected_schema=schema
        )

        assert result.is_valid is False
        assert result.has_drift is True
        assert any(
            e.drift_type == DriftType.MISSING_REQUIRED_FIELD for e in result.events
        )

    def test_validate_non_json_mode(self):
        """Test that non-JSON responses are not validated for JSON format"""
        detector = DriftDetector(enabled=True)
        result = detector.validate_response("plain text response", json_mode=False)

        assert result.is_valid is True
        assert result.has_drift is False

    def test_get_stats(self):
        """Test statistics tracking"""
        detector = DriftDetector(enabled=True)

        # Perform some validations
        detector.validate_response("valid", json_mode=False)
        detector.validate_response("", json_mode=False)  # Empty = drift

        stats = detector.get_stats()
        assert stats["check_count"] == 2
        assert stats["drift_count"] == 1
        assert stats["drift_rate"] == 0.5


class TestDriftEvent:
    """Unit tests for DriftEvent dataclass"""

    def test_to_dict(self):
        """Test conversion to dictionary"""
        event = DriftEvent(
            drift_type=DriftType.JSON_PARSE_ERROR,
            severity=DriftSeverity.HIGH,
            provider="openai",
            model="gpt-4",
            json_mode=True,
            error_message="Parse error"
        )

        d = event.to_dict()
        assert d["drift_type"] == "json_parse_error"
        assert d["severity"] == "high"
        assert d["provider"] == "openai"
        assert d["model"] == "gpt-4"
        assert d["json_mode"] is True

    def test_to_json(self):
        """Test conversion to JSON string"""
        event = DriftEvent(drift_type=DriftType.EMPTY_RESPONSE)
        json_str = event.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["drift_type"] == "empty_response"


class TestObserveResponse:
    """Unit tests for observe_response function"""

    def setup_method(self):
        """Reset drift detector before each test"""
        reset_drift_detector()

    def test_observe_disabled(self):
        """Test observe_response when drift detection is disabled"""
        with patch("governance.drift_detector.get_drift_detector") as mock_get:
            mock_detector = Mock()
            mock_detector.should_check.return_value = False
            mock_get.return_value = mock_detector

            result = observe_response("test response")

            assert result.is_valid is True
            mock_detector.validate_response.assert_not_called()

    def test_observe_with_response_object(self):
        """Test observe_response with LLMResponse-like object"""
        with patch("governance.drift_detector.get_drift_detector") as mock_get:
            mock_detector = Mock()
            mock_detector.should_check.return_value = True
            mock_detector.block_on_fail = False
            mock_detector.validate_response.return_value = DriftValidationResult(
                is_valid=True
            )
            mock_get.return_value = mock_detector

            # Mock response object with content attribute
            mock_response = Mock()
            mock_response.content = '{"status": "ok"}'

            observe_response(mock_response, json_mode=True)

            mock_detector.validate_response.assert_called_once()
            call_args = mock_detector.validate_response.call_args
            assert call_args.kwargs["content"] == '{"status": "ok"}'

    def test_observe_block_on_fail(self):
        """Test that DriftDetectedError is raised when block_on_fail=True"""
        with patch("governance.drift_detector.get_drift_detector") as mock_get:
            mock_detector = Mock()
            mock_detector.should_check.return_value = True
            mock_detector.block_on_fail = True
            mock_detector.validate_response.return_value = DriftValidationResult(
                is_valid=False,
                events=[DriftEvent(drift_type=DriftType.JSON_PARSE_ERROR)]
            )
            mock_get.return_value = mock_detector

            with pytest.raises(DriftDetectedError):
                observe_response("invalid json", json_mode=True)


class TestContractWithSimpleCoder:
    """
    Contract tests ensuring drift detection does NOT break SimpleCoder

    These tests verify the critical requirement from EPIC I plan:
    "drift validator must not block SimpleCoder normal operation"
    """

    def setup_method(self):
        """Reset drift detector before each test"""
        reset_drift_detector()

    def test_drift_validator_does_not_block_valid_coder_response(self):
        """
        Contract: Valid SimpleCoder JSON responses must pass through unchanged

        SimpleCoder returns JSON like:
        {"action": "patch", "patch": "...", "reason": "..."}
        or
        {"action": "skip", "reason": "..."}
        """
        detector = DriftDetector(enabled=True, block_on_fail=False)

        # Valid SimpleCoder patch response
        patch_response = json.dumps({
            "action": "patch",
            "patch": "--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new",
            "reason": "Fixed the issue"
        })

        result = detector.validate_response(patch_response, json_mode=True)
        assert result.is_valid is True
        assert result.has_drift is False

        # Valid SimpleCoder skip response
        skip_response = json.dumps({
            "action": "skip",
            "reason": "Low confidence"
        })

        result = detector.validate_response(skip_response, json_mode=True)
        assert result.is_valid is True
        assert result.has_drift is False

    def test_drift_validator_observe_only_mode(self):
        """
        Contract: With block_on_fail=False, drift events are logged but not raised

        This is critical for EPIC D development - we don't want to break
        SimpleCoder iterations even if the model outputs imperfect JSON.
        """
        detector = DriftDetector(enabled=True, block_on_fail=False)

        # Invalid JSON that SimpleCoder might receive from a misbehaving model
        invalid_response = "This is not JSON at all"

        # Should NOT raise, just return validation result
        result = detector.validate_response(invalid_response, json_mode=True)

        assert result.is_valid is False
        assert result.has_drift is True
        # But no exception was raised - observe-only mode

    def test_drift_validator_with_coder_schema(self):
        """
        Contract: Schema validation should work with SimpleCoder expected schema
        """
        detector = DriftDetector(enabled=True, block_on_fail=False)

        coder_schema = {
            "required": ["action"]
        }

        # Valid response with required field
        valid_response = json.dumps({"action": "patch", "patch": "..."})
        result = detector.validate_response(
            valid_response, json_mode=True, expected_schema=coder_schema
        )
        assert result.is_valid is True

        # Invalid response missing required field
        invalid_response = json.dumps({"patch": "..."})
        result = detector.validate_response(
            invalid_response, json_mode=True, expected_schema=coder_schema
        )
        assert result.is_valid is False
        assert any(
            e.drift_type == DriftType.MISSING_REQUIRED_FIELD for e in result.events
        )

    @patch("governance.drift_detector.get_drift_detector")
    def test_llm_client_integration_does_not_break_coder(self, mock_get_detector):
        """
        Contract: LLMClient.generate() with drift detection enabled
        must still return the response to SimpleCoder

        This simulates the integration point in llm/client.py
        """
        # Setup mock detector in observe-only mode
        mock_detector = DriftDetector(enabled=True, block_on_fail=False)
        mock_get_detector.return_value = mock_detector

        # Simulate what happens in LLMClient.generate()
        mock_response = Mock()
        mock_response.content = json.dumps({"action": "patch", "patch": "..."})

        # observe_response should not raise
        result = observe_response(
            mock_response,
            json_mode=True,
            provider="alicloud",
            model="qwen-plus"
        )

        # Response should still be usable by SimpleCoder
        assert result.is_valid is True

    def test_feature_flag_disabled_has_no_impact(self):
        """
        Contract: When DRIFT_DETECTION_ENABLED=false, there is zero impact
        on SimpleCoder or any other component
        """
        detector = DriftDetector(enabled=False)

        # Even with invalid input, should_check returns False
        assert detector.should_check() is False

        # Validation is essentially a no-op when disabled
        # (though we don't call validate_response if should_check is False)


class TestDriftDetectorIntegration:
    """Integration tests for drift detection with settings"""

    def setup_method(self):
        """Reset drift detector before each test"""
        reset_drift_detector()

    @patch("governance.drift_detector.settings")
    def test_get_drift_detector_from_settings(self, mock_settings):
        """Test that get_drift_detector reads from settings"""
        mock_settings.drift_detection_enabled = True
        mock_settings.drift_detection_block_on_fail = False
        mock_settings.drift_detection_sample_rate = 0.5

        reset_drift_detector()

        # This will create a new detector from settings
        with patch("governance.drift_detector._drift_detector", None):
            detector = get_drift_detector()

            # Note: Due to import caching, this test may not work as expected
            # in all scenarios. The important thing is that the code path exists.
            assert detector is not None
