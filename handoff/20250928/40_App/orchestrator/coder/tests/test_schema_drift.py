"""
Schema/Prompt Drift Detection Tests - D-1.3

Issue #3214: Automated Schema/Prompt Drift Detection
Parent Issue #2760: D-1 General Coder Agent MVP
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family

This module implements automated CI checks to prevent drift between:
1. CODER_SYSTEM_PROMPT (LLM schema definition)
2. Module docstrings (schema documentation)
3. CoderOutput class (implementation)

The tests verify:
- Prompt schema matches documented LLM Response Schema
- to_dict() output matches documented Final CoderOutput Schema
- schema_version is present and valid in all outputs
"""
import json

from typing import Set

from coder.simple_coder import (
    CoderOutput,
    CoderStatus,
    CODER_OUTPUT_SCHEMA_VERSION,
    CODER_PROMPT_TEMPLATE,
    CODER_SYSTEM_PROMPT,
)


class TestLLMResponseSchemaConsistency:
    """Verify CODER_SYSTEM_PROMPT matches documented LLM Response Schema.

    LLM Response Schema (from docstring):
    {
        "status": "skipped" | "patch",
        "reason": "string (required if skipped)",
        "patch": "string (required if patch)"
    }
    """

    def test_prompt_contains_status_field(self):
        """Verify prompt documents the status field."""
        assert '"status"' in CODER_SYSTEM_PROMPT
        assert '"skipped"' in CODER_SYSTEM_PROMPT or "'skipped'" in CODER_SYSTEM_PROMPT
        assert '"patch"' in CODER_SYSTEM_PROMPT or "'patch'" in CODER_SYSTEM_PROMPT

    def test_prompt_contains_reason_field(self):
        """Verify prompt documents the reason field."""
        assert '"reason"' in CODER_SYSTEM_PROMPT

    def test_prompt_contains_patch_field(self):
        """Verify prompt documents the patch field."""
        assert '"patch"' in CODER_SYSTEM_PROMPT

    def test_prompt_specifies_json_format(self):
        """Verify prompt requires JSON output."""
        prompt_lower = CODER_SYSTEM_PROMPT.lower()
        assert "json" in prompt_lower

    def test_prompt_schema_matches_coder_status_enum(self):
        """Verify prompt status values match CoderStatus enum."""
        for status in CoderStatus:
            assert status.value in CODER_SYSTEM_PROMPT.lower()

    def test_prompt_does_not_mention_system_fields(self):
        """Verify prompt does NOT ask LLM to output system-added fields.

        The LLM should only output {status, reason, patch}.
        System-added fields (schema_version, file_path, syntax_valid)
        should NOT be in the prompt's JSON schema.

        Uses anchor-based extraction to find the JSON schema section
        in the prompt, which is more robust than regex matching braces.
        """
        anchor = "You MUST respond with ONLY a JSON object"
        anchor_pos = CODER_SYSTEM_PROMPT.find(anchor)
        assert anchor_pos != -1, (
            f"Anchor text '{anchor}' not found in CODER_SYSTEM_PROMPT. "
            "Update this test if the prompt structure changed."
        )
        json_section = CODER_SYSTEM_PROMPT[anchor_pos:]
        assert "schema_version" not in json_section, (
            "CODER_SYSTEM_PROMPT should not ask LLM to output schema_version"
        )
        assert "file_path" not in json_section, (
            "CODER_SYSTEM_PROMPT should not ask LLM to output file_path"
        )
        assert "syntax_valid" not in json_section, (
            "CODER_SYSTEM_PROMPT should not ask LLM to output syntax_valid"
        )


class TestFinalOutputSchemaConsistency:
    """Verify CoderOutput.to_dict() matches documented Final CoderOutput Schema.

    Final CoderOutput Schema (from docstring):
    {
        "schema_version": 1,
        "status": "skipped" | "patch",
        "reason": "string (present if skipped)",
        "patch": "string (present if patch)",
        "file_path": "string (system-added)",
        "syntax_valid": bool | null (system-added, Python files only)
    }
    """

    def test_schema_version_always_present(self):
        """Verify schema_version is always in to_dict() output."""
        output_skipped = CoderOutput.create_skipped("test reason")
        output_patch = CoderOutput.create_patch("test patch")

        assert "schema_version" in output_skipped.to_dict()
        assert "schema_version" in output_patch.to_dict()

    def test_schema_version_is_integer(self):
        """Verify schema_version is an integer."""
        output = CoderOutput.create_skipped("test")
        schema_version = output.to_dict()["schema_version"]

        assert isinstance(schema_version, int)
        assert schema_version == CODER_OUTPUT_SCHEMA_VERSION

    def test_schema_version_matches_constant(self):
        """Verify to_dict() uses CODER_OUTPUT_SCHEMA_VERSION constant."""
        output = CoderOutput.create_patch("test patch")
        assert output.to_dict()["schema_version"] == CODER_OUTPUT_SCHEMA_VERSION

    def test_skipped_output_has_required_fields(self):
        """Verify skipped output has status and reason."""
        output = CoderOutput.create_skipped("test reason", file_path="test.py")
        result = output.to_dict()

        assert result["status"] == "skipped"
        assert result["reason"] == "test reason"
        assert "patch" not in result

    def test_patch_output_has_required_fields(self):
        """Verify patch output has status and patch."""
        output = CoderOutput.create_patch(
            "fixed code",
            file_path="test.py",
            syntax_valid=True
        )
        result = output.to_dict()

        assert result["status"] == "patch"
        assert result["patch"] == "fixed code"
        assert "reason" not in result

    def test_file_path_included_when_provided(self):
        """Verify file_path is included when provided."""
        output = CoderOutput.create_skipped("test", file_path="src/utils.py")
        result = output.to_dict()

        assert result["file_path"] == "src/utils.py"

    def test_syntax_valid_included_when_provided(self):
        """Verify syntax_valid is included when provided."""
        output = CoderOutput.create_patch("code", syntax_valid=True)
        result = output.to_dict()

        assert result["syntax_valid"] is True

    def test_optional_fields_excluded_when_none(self):
        """Verify optional fields are excluded when None."""
        output = CoderOutput(status=CoderStatus.SKIPPED, reason="test")
        result = output.to_dict()

        assert "file_path" not in result
        assert "syntax_valid" not in result
        assert "patch" not in result

    def test_to_dict_output_is_json_serializable(self):
        """Verify to_dict() output can be serialized to JSON."""
        output = CoderOutput.create_patch(
            "def foo(): pass",
            file_path="test.py",
            syntax_valid=True
        )

        json_str = json.dumps(output.to_dict())
        parsed = json.loads(json_str)

        assert parsed["schema_version"] == CODER_OUTPUT_SCHEMA_VERSION
        assert parsed["status"] == "patch"


class TestSchemaVersionEvolution:
    """Verify schema versioning is properly implemented."""

    def test_schema_version_constant_exists(self):
        """Verify CODER_OUTPUT_SCHEMA_VERSION constant is defined."""
        assert CODER_OUTPUT_SCHEMA_VERSION is not None
        assert isinstance(CODER_OUTPUT_SCHEMA_VERSION, int)

    def test_schema_version_is_positive(self):
        """Verify schema version is a positive integer."""
        assert CODER_OUTPUT_SCHEMA_VERSION > 0

    def test_schema_version_in_module_docstring(self):
        """Verify schema_version is documented in module docstring."""
        import coder.simple_coder as module
        docstring = module.__doc__ or ""

        assert "schema_version" in docstring.lower()


class TestDocstringSchemaAlignment:
    """Verify docstrings accurately describe the schemas."""

    def test_coder_output_docstring_mentions_llm_schema(self):
        """Verify CoderOutput docstring mentions LLM schema."""
        docstring = CoderOutput.__doc__ or ""

        assert "status" in docstring.lower()
        assert "reason" in docstring.lower()
        assert "patch" in docstring.lower()

    def test_coder_output_docstring_mentions_system_fields(self):
        """Verify CoderOutput docstring mentions system-added fields."""
        docstring = CoderOutput.__doc__ or ""

        assert "file_path" in docstring.lower()
        assert "syntax_valid" in docstring.lower()

    def test_to_dict_docstring_mentions_schema_version(self):
        """Verify to_dict() docstring mentions schema_version."""
        docstring = CoderOutput.to_dict.__doc__ or ""

        assert "schema_version" in docstring.lower() or "schema" in docstring.lower()


class TestSchemaFieldCompleteness:
    """Verify all documented fields are actually implemented."""

    DOCUMENTED_LLM_FIELDS: Set[str] = {"status", "reason", "patch"}
    DOCUMENTED_SYSTEM_FIELDS: Set[str] = {"schema_version", "file_path", "syntax_valid"}

    def test_all_llm_fields_are_coder_output_attributes(self):
        """Verify all LLM response fields map to CoderOutput attributes."""
        output = CoderOutput(
            status=CoderStatus.PATCH,
            reason="test",
            patch="code"
        )

        for field in self.DOCUMENTED_LLM_FIELDS:
            assert hasattr(output, field), f"Missing attribute: {field}"

    def test_all_system_fields_in_to_dict(self):
        """Verify all system fields can appear in to_dict() output."""
        output = CoderOutput.create_patch(
            "code",
            file_path="test.py",
            syntax_valid=True
        )
        result = output.to_dict()

        for field in self.DOCUMENTED_SYSTEM_FIELDS:
            assert field in result, f"Missing field in to_dict(): {field}"

    def test_no_undocumented_fields_in_to_dict(self):
        """Verify to_dict() doesn't add undocumented fields."""
        output = CoderOutput.create_patch(
            "code",
            file_path="test.py",
            syntax_valid=True
        )
        result = output.to_dict()

        all_documented = self.DOCUMENTED_LLM_FIELDS | self.DOCUMENTED_SYSTEM_FIELDS
        for field in result.keys():
            assert field in all_documented, f"Undocumented field: {field}"


class TestPromptTemplateConsistency:
    """Verify CODER_PROMPT_TEMPLATE is consistent with schema."""

    def test_prompt_template_exists(self):
        """Verify CODER_PROMPT_TEMPLATE is defined."""
        assert CODER_PROMPT_TEMPLATE is not None
        assert len(CODER_PROMPT_TEMPLATE) > 0

    def test_prompt_template_has_placeholders(self):
        """Verify prompt template has required placeholders."""
        assert "{file_path}" in CODER_PROMPT_TEMPLATE
        assert "{file_content}" in CODER_PROMPT_TEMPLATE
        assert "{review_comment}" in CODER_PROMPT_TEMPLATE
        assert "{severity}" in CODER_PROMPT_TEMPLATE

    def test_prompt_template_mentions_status_values(self):
        """Verify prompt template mentions valid status values."""
        template_lower = CODER_PROMPT_TEMPLATE.lower()
        assert "skipped" in template_lower
        assert "patch" in template_lower
