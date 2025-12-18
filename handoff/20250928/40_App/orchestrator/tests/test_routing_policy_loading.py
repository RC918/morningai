"""
Unit tests for routing_policy.json loading and error handling

Issue #2672 - EPIC #2594: Qwen3 Provider Integration

Tests cover:
- JSON file parsing and validation
- Error handling when JSON is malformed
- Fallback behavior when JSON sections are missing
- Configuration precedence (JSON vs Python defaults)
"""
import json
import logging
import pytest  # noqa: F401 - pytest fixtures (tmp_path, caplog) are used implicitly
from pathlib import Path
from unittest.mock import patch

from core.routing import RoutingEngine, Tier, TaskType
from core.routing.engine import DEFAULT_TASK_ROUTING


class TestPolicyFileNotFound:
    """Tests for policy file not found scenarios"""

    def test_load_policy_file_not_found_uses_defaults(self):
        """Should use defaults when policy file doesn't exist"""
        engine = RoutingEngine(
            policy_path=Path("/nonexistent/path/routing_policy.json"),
            available_providers=["alicloud"]
        )
        # Should still work with defaults
        assert engine._task_routing is not None
        assert len(engine._task_routing) > 0

    def test_load_policy_nonexistent_directory(self):
        """Should use defaults when directory doesn't exist"""
        engine = RoutingEngine(
            policy_path=Path("/this/path/does/not/exist/policy.json"),
            available_providers=["alicloud"]
        )
        # Should fall back to defaults
        model_info = engine.select_model(TaskType.PLANNING)
        assert model_info.model_name == "qwen-max"

    def test_load_policy_none_uses_default_location(self):
        """Should try default location when policy_path is None"""
        engine = RoutingEngine(
            policy_path=None,
            available_providers=["alicloud"]
        )
        # Should work with default policy file or defaults
        assert engine._task_routing is not None


class TestPolicyMalformedJSON:
    """Tests for malformed JSON handling"""

    def test_load_policy_malformed_json_uses_defaults(self, tmp_path):
        """Should use defaults when JSON is malformed"""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{ invalid json }")

        engine = RoutingEngine(
            policy_path=bad_json,
            available_providers=["alicloud"]
        )
        # Should fall back to defaults
        assert engine._task_routing == DEFAULT_TASK_ROUTING

    def test_load_policy_empty_file_uses_defaults(self, tmp_path):
        """Should use defaults when JSON file is empty"""
        empty_json = tmp_path / "empty.json"
        empty_json.write_text("")

        engine = RoutingEngine(
            policy_path=empty_json,
            available_providers=["alicloud"]
        )
        # Should fall back to defaults
        assert engine._task_routing == DEFAULT_TASK_ROUTING

    def test_load_policy_truncated_json_uses_defaults(self, tmp_path):
        """Should use defaults when JSON is truncated"""
        truncated_json = tmp_path / "truncated.json"
        truncated_json.write_text('{"task_types": {"planning": {"tier": 0')

        engine = RoutingEngine(
            policy_path=truncated_json,
            available_providers=["alicloud"]
        )
        # Should fall back to defaults
        assert engine._task_routing == DEFAULT_TASK_ROUTING

    def test_load_policy_invalid_json_syntax_uses_defaults(self, tmp_path):
        """Should use defaults when JSON has syntax errors"""
        invalid_json = tmp_path / "invalid.json"
        # Missing comma between properties
        invalid_json.write_text('{"task_types": {} "tier_models": {}}')

        engine = RoutingEngine(
            policy_path=invalid_json,
            available_providers=["alicloud"]
        )
        # Should fall back to defaults
        assert engine._task_routing == DEFAULT_TASK_ROUTING


class TestPolicyPartialJSON:
    """Tests for partial JSON (some sections present, others missing)"""

    def test_load_policy_missing_task_types_uses_defaults(self, tmp_path):
        """Should use defaults when task_types section is missing"""
        partial_json = tmp_path / "partial.json"
        partial_json.write_text(json.dumps({
            "version": "1.0",
            "tier_models": {}
        }))

        engine = RoutingEngine(
            policy_path=partial_json,
            available_providers=["alicloud"]
        )
        # Should fall back to defaults for task_types
        assert engine._task_routing == DEFAULT_TASK_ROUTING

    def test_load_policy_empty_task_types_uses_empty(self, tmp_path):
        """Should use empty task_types when section is empty dict.

        Design intent: Empty task_types dict is valid and intentional.
        select_model() will safely fallback to tier 2 via .get() default.
        """
        partial_json = tmp_path / "empty_tasks.json"
        partial_json.write_text(json.dumps({
            "version": "1.0",
            "task_types": {}
        }))

        engine = RoutingEngine(
            policy_path=partial_json,
            available_providers=["alicloud"]
        )
        # Empty task_types is valid - select_model() uses .get() with default tier 2
        assert engine._task_routing == {}

    def test_load_policy_only_version_uses_defaults(self, tmp_path):
        """Should use defaults when only version is present"""
        version_only = tmp_path / "version_only.json"
        version_only.write_text(json.dumps({
            "version": "1.0"
        }))

        engine = RoutingEngine(
            policy_path=version_only,
            available_providers=["alicloud"]
        )
        # Should fall back to defaults
        assert engine._task_routing == DEFAULT_TASK_ROUTING


class TestPolicyCustomTaskTypes:
    """Tests for custom task_types from JSON"""

    def test_load_policy_custom_task_types(self, tmp_path):
        """Should use custom task_types from JSON"""
        custom_json = tmp_path / "custom.json"
        custom_json.write_text(json.dumps({
            "task_types": {
                "planning": {"tier": 1, "fallback": 2},
                "custom_task": {"tier": 2, "fallback": 3}
            }
        }))

        engine = RoutingEngine(
            policy_path=custom_json,
            available_providers=["alicloud"]
        )
        # Should use custom task_types
        assert engine._task_routing["planning"]["tier"] == 1
        assert engine._task_routing["planning"]["fallback"] == 2
        assert "custom_task" in engine._task_routing

    def test_load_policy_overrides_default_tier(self, tmp_path):
        """Should override default tier with JSON value"""
        override_json = tmp_path / "override.json"
        # Planning is normally tier 0, override to tier 2
        override_json.write_text(json.dumps({
            "task_types": {
                "planning": {"tier": 2, "fallback": 3}
            }
        }))

        engine = RoutingEngine(
            policy_path=override_json,
            available_providers=["alicloud"]
        )
        # Should use overridden tier
        assert engine._task_routing["planning"]["tier"] == 2

    def test_load_policy_adds_new_task_type(self, tmp_path):
        """Should add new task types from JSON"""
        new_task_json = tmp_path / "new_task.json"
        new_task_json.write_text(json.dumps({
            "task_types": {
                "my_custom_task": {"tier": 1, "fallback": 2}
            }
        }))

        engine = RoutingEngine(
            policy_path=new_task_json,
            available_providers=["alicloud"]
        )
        # Should have the new task type
        assert "my_custom_task" in engine._task_routing
        assert engine._task_routing["my_custom_task"]["tier"] == 1


class TestPolicyFilePermissions:
    """Tests for file permission issues"""

    def test_load_policy_permission_denied_uses_defaults(self, tmp_path):
        """Should use defaults when file permission is denied"""
        # Use mock to simulate PermissionError for cross-platform stability
        # (chmod-based tests can be flaky on CI runners with root or special FS)
        policy_path = tmp_path / "restricted.json"

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', side_effect=PermissionError("Permission denied")):
                engine = RoutingEngine(
                    policy_path=policy_path,
                    available_providers=["alicloud"]
                )
                # Should fall back to defaults due to PermissionError
                assert engine._task_routing == DEFAULT_TASK_ROUTING


class TestPolicyValidJSON:
    """Tests for valid JSON loading"""

    def test_load_policy_valid_json_success(self, tmp_path):
        """Should successfully load valid JSON policy"""
        valid_json = tmp_path / "valid.json"
        valid_json.write_text(json.dumps({
            "version": "1.1",
            "task_types": {
                "planning": {"tier": 0, "fallback": 1},
                "coding": {"tier": 1, "fallback": 2}
            }
        }))

        engine = RoutingEngine(
            policy_path=valid_json,
            available_providers=["alicloud"]
        )
        # Should load task_types from JSON
        assert engine._task_routing["planning"]["tier"] == 0
        assert engine._task_routing["coding"]["tier"] == 1

    def test_load_policy_from_default_location(self):
        """Should load policy from default location if it exists"""
        # This tests the actual default policy file
        engine = RoutingEngine(available_providers=["alicloud"])

        # Should have loaded task_types (either from file or defaults)
        assert "planning" in engine._task_routing
        assert "coding" in engine._task_routing

    def test_load_policy_preserves_all_task_types(self, tmp_path):
        """Should preserve all task types from JSON"""
        full_json = tmp_path / "full.json"
        full_json.write_text(json.dumps({
            "task_types": {
                "planning": {"tier": 0, "fallback": 1},
                "coding": {"tier": 1, "fallback": 2},
                "review": {"tier": 1, "fallback": 2},
                "ux_copy": {"tier": 3, "fallback": 2},
                "translation": {"tier": 2, "fallback": 3},
                "summarization": {"tier": 2, "fallback": 3},
                "analysis": {"tier": 1, "fallback": 2},
                "chat": {"tier": 2, "fallback": 3}
            }
        }))

        engine = RoutingEngine(
            policy_path=full_json,
            available_providers=["alicloud"]
        )
        # Should have all 8 task types
        assert len(engine._task_routing) == 8


class TestPolicyInvalidValues:
    """Tests for invalid values in JSON"""

    def test_load_policy_invalid_tier_number_handled(self, tmp_path):
        """Should handle invalid tier numbers gracefully"""
        invalid_tier_json = tmp_path / "invalid_tier.json"
        invalid_tier_json.write_text(json.dumps({
            "task_types": {
                "planning": {"tier": 99, "fallback": 1}
            }
        }))

        engine = RoutingEngine(
            policy_path=invalid_tier_json,
            available_providers=["alicloud"]
        )
        # Should load the JSON (validation happens at select_model time)
        assert engine._task_routing["planning"]["tier"] == 99

    def test_load_policy_negative_tier_handled(self, tmp_path):
        """Should handle negative tier numbers"""
        negative_tier_json = tmp_path / "negative_tier.json"
        negative_tier_json.write_text(json.dumps({
            "task_types": {
                "planning": {"tier": -1, "fallback": 0}
            }
        }))

        engine = RoutingEngine(
            policy_path=negative_tier_json,
            available_providers=["alicloud"]
        )
        # Should load the JSON
        assert engine._task_routing["planning"]["tier"] == -1

    def test_load_policy_string_tier_handled(self, tmp_path):
        """Should handle string tier values (type coercion)"""
        string_tier_json = tmp_path / "string_tier.json"
        string_tier_json.write_text(json.dumps({
            "task_types": {
                "planning": {"tier": "0", "fallback": "1"}
            }
        }))

        engine = RoutingEngine(
            policy_path=string_tier_json,
            available_providers=["alicloud"]
        )
        # Should load the JSON (tier is string "0")
        assert engine._task_routing["planning"]["tier"] == "0"


class TestPolicyLogging:
    """Tests for logging during policy loading"""

    def test_load_policy_logs_success(self, tmp_path, caplog):
        """Should log success message when policy loads"""
        valid_json = tmp_path / "valid.json"
        valid_json.write_text(json.dumps({"task_types": {}}))

        with caplog.at_level(logging.INFO):
            RoutingEngine(
                policy_path=valid_json,
                available_providers=["alicloud"]
            )

        assert "Loaded policy from" in caplog.text

    def test_load_policy_logs_warning_on_error(self, tmp_path, caplog):
        """Should log warning when policy fails to load"""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{ invalid }")

        with caplog.at_level(logging.WARNING):
            RoutingEngine(
                policy_path=bad_json,
                available_providers=["alicloud"]
            )

        assert "Failed to load policy" in caplog.text

    def test_load_policy_logs_info_when_no_file(self, caplog):
        """Should log info when no policy file found"""
        with caplog.at_level(logging.INFO):
            # Use a path that definitely doesn't exist
            with patch.object(Path, 'exists', return_value=False):
                RoutingEngine(
                    policy_path=None,
                    available_providers=["alicloud"]
                )

        # Should log that no policy file was found
        assert "No policy file found" in caplog.text or "Initialized" in caplog.text


class TestPolicyIntegrationWithSelectModel:
    """Integration tests for policy loading with select_model"""

    def test_custom_policy_affects_model_selection(self, tmp_path):
        """Custom policy should affect model selection"""
        # Make planning use tier 3 instead of tier 0
        custom_json = tmp_path / "custom.json"
        custom_json.write_text(json.dumps({
            "task_types": {
                "planning": {"tier": 3, "fallback": 2}
            }
        }))

        engine = RoutingEngine(
            policy_path=custom_json,
            available_providers=["siliconflow"]
        )

        model_info = engine.select_model(TaskType.PLANNING)
        # Should get tier 3 model due to custom policy
        assert model_info.tier == Tier.TIER_3

    def test_default_policy_used_when_json_missing_task(self, tmp_path):
        """Should use default routing when task not in JSON"""
        partial_json = tmp_path / "partial.json"
        partial_json.write_text(json.dumps({
            "task_types": {
                "planning": {"tier": 0, "fallback": 1}
            }
        }))

        engine = RoutingEngine(
            policy_path=partial_json,
            available_providers=["alicloud"]
        )

        # Coding is not in the JSON, should use default from select_model
        model_info = engine.select_model(TaskType.CODING)
        # Should fall back to default tier 2 (from select_model's default)
        assert model_info is not None
