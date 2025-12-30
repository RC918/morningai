"""
Schema/Prompt Drift Detection Tests - D-1.3

Issue #3214: Automated Schema/Prompt Drift Detection
Issue #3249: Refactor schema drift tests with helper abstractions
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

Helper functions are provided in schema_drift_helpers.py to reduce
test/design over-binding and provide a single point of change when
prompt structure changes.
"""
import dataclasses
import json

from coder.simple_coder import (
    CoderOutput,
    CoderStatus,
    CODER_OUTPUT_SCHEMA_VERSION,
    CODER_PROMPT_TEMPLATE,
    CODER_SYSTEM_PROMPT,
    CODER_LLM_RESPONSE_FIELDS,
    CODER_SYSTEM_ADDED_FIELDS,
)
from coder.tests.schema_drift_helpers import (
    extract_prompt_schema_section,
    get_expected_output_keys,
    validate_field_not_in_schema,
    PROMPT_JSON_SCHEMA_ANCHOR,
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
        assert '"status"' in CODER_SYSTEM_PROMPT, (
            'CODER_SYSTEM_PROMPT must contain "status" field definition'
        )
        assert '"skipped"' in CODER_SYSTEM_PROMPT or "'skipped'" in CODER_SYSTEM_PROMPT, (
            'CODER_SYSTEM_PROMPT must document "skipped" as a valid status value'
        )
        assert '"patch"' in CODER_SYSTEM_PROMPT or "'patch'" in CODER_SYSTEM_PROMPT, (
            'CODER_SYSTEM_PROMPT must document "patch" as a valid status value'
        )

    def test_prompt_contains_reason_field(self):
        """Verify prompt documents the reason field."""
        assert '"reason"' in CODER_SYSTEM_PROMPT, (
            'CODER_SYSTEM_PROMPT must contain "reason" field definition'
        )

    def test_prompt_contains_patch_field(self):
        """Verify prompt documents the patch field."""
        assert '"patch"' in CODER_SYSTEM_PROMPT, (
            'CODER_SYSTEM_PROMPT must contain "patch" field definition'
        )

    def test_prompt_specifies_json_format(self):
        """Verify prompt requires JSON output."""
        prompt_lower = CODER_SYSTEM_PROMPT.lower()
        assert "json" in prompt_lower, (
            'CODER_SYSTEM_PROMPT must specify JSON output format. '
            f'Got prompt (first 200 chars): {CODER_SYSTEM_PROMPT[:200]}...'
        )

    def test_prompt_schema_matches_coder_status_enum(self):
        """Verify prompt status values match CoderStatus enum."""
        prompt_lower = CODER_SYSTEM_PROMPT.lower()
        for status in CoderStatus:
            assert status.value in prompt_lower, (
                f'CoderStatus.{status.name} value "{status.value}" not found in '
                f'CODER_SYSTEM_PROMPT. All CoderStatus values must be documented.'
            )

    def test_prompt_does_not_mention_system_fields(self):
        """Verify prompt does NOT ask LLM to output system-added fields.

        The LLM should only output {status, reason, patch}.
        System-added fields (schema_version, file_path, syntax_valid)
        should NOT be in the prompt's JSON schema.

        Uses helper functions for anchor-based extraction to find the
        JSON schema section in the prompt, which is more robust than
        regex matching braces.
        """
        json_section = extract_prompt_schema_section(CODER_SYSTEM_PROMPT)
        assert json_section is not None, (
            f"Anchor text '{PROMPT_JSON_SCHEMA_ANCHOR}' not found in CODER_SYSTEM_PROMPT. "
            "Update PROMPT_JSON_SCHEMA_ANCHOR in schema_drift_helpers.py if the prompt structure changed."
        )

        system_fields = get_expected_output_keys("system_added")
        for field in system_fields:
            assert validate_field_not_in_schema(field, json_section), (
                f"CODER_SYSTEM_PROMPT should not ask LLM to output {field}"
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

        skipped_dict = output_skipped.to_dict()
        patch_dict = output_patch.to_dict()

        assert "schema_version" in skipped_dict, (
            f'"schema_version" missing from skipped output. Got keys: {list(skipped_dict.keys())}'
        )
        assert "schema_version" in patch_dict, (
            f'"schema_version" missing from patch output. Got keys: {list(patch_dict.keys())}'
        )

    def test_schema_version_is_integer(self):
        """Verify schema_version is an integer."""
        output = CoderOutput.create_skipped("test")
        schema_version = output.to_dict()["schema_version"]

        assert isinstance(schema_version, int), (
            f'schema_version must be int, got {type(schema_version).__name__}: {schema_version}'
        )
        assert schema_version == CODER_OUTPUT_SCHEMA_VERSION, (
            f'schema_version mismatch. Expected: {CODER_OUTPUT_SCHEMA_VERSION}, got: {schema_version}'
        )

    def test_schema_version_matches_constant(self):
        """Verify to_dict() uses CODER_OUTPUT_SCHEMA_VERSION constant."""
        output = CoderOutput.create_patch("test patch")
        actual = output.to_dict()["schema_version"]
        assert actual == CODER_OUTPUT_SCHEMA_VERSION, (
            f'to_dict() schema_version mismatch. '
            f'Expected CODER_OUTPUT_SCHEMA_VERSION={CODER_OUTPUT_SCHEMA_VERSION}, got: {actual}'
        )

    def test_skipped_output_has_required_fields(self):
        """Verify skipped output has status and reason."""
        output = CoderOutput.create_skipped("test reason", file_path="test.py")
        result = output.to_dict()

        assert "status" in result, (
            f'Required field "status" missing from skipped output. Got keys: {list(result.keys())}'
        )
        assert result["status"] == "skipped", (
            f'Expected status="skipped", got: "{result["status"]}"'
        )
        assert "reason" in result, (
            f'Required field "reason" missing from skipped output. Got keys: {list(result.keys())}'
        )
        assert result["reason"] == "test reason", (
            f'Expected reason="test reason", got: "{result["reason"]}"'
        )
        assert "patch" not in result, (
            f'Skipped output should not contain "patch" field. Got: {result}'
        )

    def test_patch_output_has_required_fields(self):
        """Verify patch output has status and patch."""
        output = CoderOutput.create_patch(
            "fixed code",
            file_path="test.py",
            syntax_valid=True
        )
        result = output.to_dict()

        assert "status" in result, (
            f'Required field "status" missing from patch output. Got keys: {list(result.keys())}'
        )
        assert result["status"] == "patch", (
            f'Expected status="patch", got: "{result["status"]}"'
        )
        assert "patch" in result, (
            f'Required field "patch" missing from patch output. Got keys: {list(result.keys())}'
        )
        assert result["patch"] == "fixed code", (
            f'Expected patch="fixed code", got: "{result["patch"]}"'
        )
        assert "reason" not in result, (
            f'Patch output should not contain "reason" field. Got: {result}'
        )

    def test_file_path_included_when_provided(self):
        """Verify file_path is included when provided."""
        output = CoderOutput.create_skipped("test", file_path="src/utils.py")
        result = output.to_dict()

        assert "file_path" in result, (
            f'Field "file_path" missing when provided. Got keys: {list(result.keys())}'
        )
        assert result["file_path"] == "src/utils.py", (
            f'Expected file_path="src/utils.py", got: "{result["file_path"]}"'
        )

    def test_syntax_valid_included_when_provided(self):
        """Verify syntax_valid is included when provided."""
        output = CoderOutput.create_patch("code", syntax_valid=True)
        result = output.to_dict()

        assert result["syntax_valid"] is True, (
            f'Expected syntax_valid=True, got: {result.get("syntax_valid")}'
        )

    def test_optional_fields_excluded_when_none(self):
        """Verify optional fields are excluded when None."""
        output = CoderOutput(status=CoderStatus.SKIPPED, reason="test")
        result = output.to_dict()

        assert "file_path" not in result, (
            f'"file_path" should be excluded when None. Got keys: {list(result.keys())}'
        )
        assert "syntax_valid" not in result, (
            f'"syntax_valid" should be excluded when None. Got keys: {list(result.keys())}'
        )
        assert "patch" not in result, (
            f'"patch" should be excluded for skipped status. Got keys: {list(result.keys())}'
        )

    def test_to_dict_output_is_json_serializable(self):
        """Verify to_dict() output can be serialized to JSON."""
        output = CoderOutput.create_patch(
            "def foo(): pass",
            file_path="test.py",
            syntax_valid=True
        )

        json_str = json.dumps(output.to_dict())
        parsed = json.loads(json_str)

        assert "schema_version" in parsed, (
            f'JSON parsed output missing "schema_version". Got keys: {list(parsed.keys())}'
        )
        assert parsed["schema_version"] == CODER_OUTPUT_SCHEMA_VERSION, (
            f'JSON parsed schema_version mismatch. '
            f'Expected: {CODER_OUTPUT_SCHEMA_VERSION}, got: {parsed["schema_version"]}'
        )
        assert "status" in parsed, (
            f'JSON parsed output missing "status". Got keys: {list(parsed.keys())}'
        )
        assert parsed["status"] == "patch", (
            f'JSON parsed status mismatch. Expected: "patch", got: "{parsed["status"]}"'
        )


class TestSchemaVersionEvolution:
    """Verify schema versioning is properly implemented."""

    def test_schema_version_constant_exists(self):
        """Verify CODER_OUTPUT_SCHEMA_VERSION constant is defined."""
        assert CODER_OUTPUT_SCHEMA_VERSION is not None, (
            'CODER_OUTPUT_SCHEMA_VERSION constant must be defined (got None)'
        )
        assert isinstance(CODER_OUTPUT_SCHEMA_VERSION, int), (
            f'CODER_OUTPUT_SCHEMA_VERSION must be int, '
            f'got {type(CODER_OUTPUT_SCHEMA_VERSION).__name__}: {CODER_OUTPUT_SCHEMA_VERSION}'
        )

    def test_schema_version_is_positive(self):
        """Verify schema version is a positive integer."""
        assert CODER_OUTPUT_SCHEMA_VERSION > 0, (
            f'CODER_OUTPUT_SCHEMA_VERSION must be positive, got: {CODER_OUTPUT_SCHEMA_VERSION}'
        )

    def test_schema_version_in_module_docstring(self):
        """Verify schema_version is documented in module docstring."""
        import coder.simple_coder as module
        docstring = module.__doc__ or ""

        assert "schema_version" in docstring.lower(), (
            'Module docstring must mention "schema_version". '
            f'Got docstring (first 200 chars): {docstring[:200]}...'
        )


class TestDocstringSchemaAlignment:
    """Verify docstrings accurately describe the schemas."""

    def test_coder_output_docstring_mentions_llm_schema(self):
        """Verify CoderOutput docstring mentions LLM schema."""
        docstring = CoderOutput.__doc__ or ""
        docstring_lower = docstring.lower()

        assert "status" in docstring_lower, (
            f'CoderOutput docstring must mention "status". '
            f'Got docstring (first 200 chars): {docstring[:200]}...'
        )
        assert "reason" in docstring_lower, (
            f'CoderOutput docstring must mention "reason". '
            f'Got docstring (first 200 chars): {docstring[:200]}...'
        )
        assert "patch" in docstring_lower, (
            f'CoderOutput docstring must mention "patch". '
            f'Got docstring (first 200 chars): {docstring[:200]}...'
        )

    def test_coder_output_docstring_mentions_system_fields(self):
        """Verify CoderOutput docstring mentions system-added fields."""
        docstring = CoderOutput.__doc__ or ""
        docstring_lower = docstring.lower()

        assert "file_path" in docstring_lower, (
            f'CoderOutput docstring must mention "file_path". '
            f'Got docstring (first 200 chars): {docstring[:200]}...'
        )
        assert "syntax_valid" in docstring_lower, (
            f'CoderOutput docstring must mention "syntax_valid". '
            f'Got docstring (first 200 chars): {docstring[:200]}...'
        )

    def test_to_dict_docstring_mentions_schema_version(self):
        """Verify to_dict() docstring mentions schema_version."""
        docstring = CoderOutput.to_dict.__doc__ or ""
        docstring_lower = docstring.lower()

        assert "schema_version" in docstring_lower or "schema" in docstring_lower, (
            f'to_dict() docstring must mention "schema_version" or "schema". '
            f'Got docstring: {docstring}'
        )


class TestSchemaFieldCompleteness:
    """Verify all documented fields are actually implemented.

    Field definitions are imported from simple_coder.py (Single Source of Truth)
    to prevent drift between implementation and tests.

    Note: test_all_llm_fields_are_coder_output_attributes and
    test_all_system_fields_in_to_dict were removed as they are now covered
    by TestSchemaFieldConstantsConsistency with more robust implementations.
    """

    def test_no_undocumented_fields_in_to_dict(self):
        """Verify to_dict() doesn't add undocumented fields.

        Uses get_expected_output_keys helper to get all documented fields.
        """
        output = CoderOutput.create_patch(
            "code",
            file_path="test.py",
            syntax_valid=True
        )
        result = output.to_dict()

        all_documented = get_expected_output_keys("all")
        for field in result.keys():
            assert field in all_documented, (
                f'to_dict() contains undocumented field "{field}". '
                f'Documented fields: {all_documented}, got keys: {list(result.keys())}'
            )


class TestSchemaFieldConstantsConsistency:
    """Verify CODER_LLM_RESPONSE_FIELDS and CODER_SYSTEM_ADDED_FIELDS match CoderOutput.

    These tests ensure the field constants (Single Source of Truth) stay in sync
    with the actual CoderOutput dataclass implementation.
    """

    def test_llm_fields_are_subset_of_coder_output_attributes(self):
        """Verify all LLM response fields exist as CoderOutput attributes."""
        coder_output_fields = {f.name for f in dataclasses.fields(CoderOutput)}

        for field in CODER_LLM_RESPONSE_FIELDS:
            assert field in coder_output_fields, (
                f'CODER_LLM_RESPONSE_FIELDS contains "{field}" but CoderOutput '
                f'has no such attribute. CoderOutput fields: {coder_output_fields}'
            )

    def test_system_fields_match_to_dict_output(self):
        """Verify system fields can all appear in to_dict() output."""
        output = CoderOutput.create_patch(
            "code",
            file_path="test.py",
            syntax_valid=True
        )
        result = output.to_dict()

        for field in CODER_SYSTEM_ADDED_FIELDS:
            assert field in result, (
                f'CODER_SYSTEM_ADDED_FIELDS contains "{field}" but to_dict() '
                f'does not include it. to_dict() keys: {list(result.keys())}'
            )

    def test_field_sets_are_disjoint(self):
        """Verify LLM and system field sets don't overlap."""
        overlap = CODER_LLM_RESPONSE_FIELDS & CODER_SYSTEM_ADDED_FIELDS
        assert len(overlap) == 0, (
            f'CODER_LLM_RESPONSE_FIELDS and CODER_SYSTEM_ADDED_FIELDS overlap: {overlap}. '
            'Each field should belong to exactly one set.'
        )

    def test_field_sets_are_immutable(self):
        """Verify field sets are frozensets (immutable)."""
        assert isinstance(CODER_LLM_RESPONSE_FIELDS, frozenset), (
            f'CODER_LLM_RESPONSE_FIELDS should be frozenset, got {type(CODER_LLM_RESPONSE_FIELDS)}'
        )
        assert isinstance(CODER_SYSTEM_ADDED_FIELDS, frozenset), (
            f'CODER_SYSTEM_ADDED_FIELDS should be frozenset, got {type(CODER_SYSTEM_ADDED_FIELDS)}'
        )


class TestPromptTemplateConsistency:
    """Verify CODER_PROMPT_TEMPLATE is consistent with schema."""

    def test_prompt_template_exists(self):
        """Verify CODER_PROMPT_TEMPLATE is defined."""
        assert CODER_PROMPT_TEMPLATE is not None, (
            'CODER_PROMPT_TEMPLATE must be defined (got None)'
        )
        assert len(CODER_PROMPT_TEMPLATE) > 0, (
            'CODER_PROMPT_TEMPLATE must not be empty'
        )

    def test_prompt_template_has_placeholders(self):
        """Verify prompt template has required placeholders."""
        assert "{file_path}" in CODER_PROMPT_TEMPLATE, (
            'CODER_PROMPT_TEMPLATE must contain "{file_path}" placeholder'
        )
        assert "{file_content}" in CODER_PROMPT_TEMPLATE, (
            'CODER_PROMPT_TEMPLATE must contain "{file_content}" placeholder'
        )
        assert "{review_comment}" in CODER_PROMPT_TEMPLATE, (
            'CODER_PROMPT_TEMPLATE must contain "{review_comment}" placeholder'
        )
        assert "{severity}" in CODER_PROMPT_TEMPLATE, (
            'CODER_PROMPT_TEMPLATE must contain "{severity}" placeholder'
        )

    def test_prompt_template_mentions_status_values(self):
        """Verify prompt template mentions valid status values."""
        template_lower = CODER_PROMPT_TEMPLATE.lower()
        assert "skipped" in template_lower, (
            'CODER_PROMPT_TEMPLATE must mention "skipped" status value'
        )
        assert "patch" in template_lower, (
            'CODER_PROMPT_TEMPLATE must mention "patch" status value'
        )
