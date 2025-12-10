"""Unit tests for generate-docs-changelog.py script."""

import tempfile
from pathlib import Path

import pytest
import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib import import_module

# Import functions from the script
generate_docs_changelog = import_module("generate-docs-changelog")


@pytest.fixture
def sample_period_data():
    """Sample period data for testing."""
    return {
        "period": "Dec 7 - Dec 9, 2025",
        "period_zh": "2025-12-07 至 2025-12-09",
        "categories": [
            {
                "name": "Test Category",
                "name_zh": "測試類別",
                "prs": [
                    {
                        "number": 1234,
                        "title": "feat(test): add test feature",
                        "path": "src/test/file.py",
                        "path_note": "new file",
                        "impact": "Added test feature",
                        "impact_zh": "新增測試功能",
                        "merged": "2025-12-07",
                    },
                    {
                        "number": 1235,
                        "title": "fix(test): fix test bug",
                        "path": "src/test/other.py",
                        "impact": "Fixed test bug",
                        "impact_zh": "修復測試錯誤",
                        "merged": "2025-12-08",
                    },
                ],
            },
            {
                "name": "Backend & Infrastructure",
                "name_zh": "Backend 與基礎設施",
                "prs": [
                    {
                        "number": 1236,
                        "title": "feat(backend): add backend feature",
                        "path": "src/backend/api.py",
                        "impact": "Added backend feature",
                        "impact_zh": "新增後端功能",
                        "merged": "2025-12-09",
                    },
                ],
            },
        ],
    }


class TestGenerateOnboardingGuideSection:
    """Tests for generate_onboarding_guide_section function."""

    def test_generates_correct_format(self, sample_period_data):
        """Test that the function generates the correct format."""
        result = generate_docs_changelog.generate_onboarding_guide_section(sample_period_data)

        assert "**Recent Improvements (Dec 7 - Dec 9, 2025)**:" in result
        assert "*Test Category:*" in result
        assert "- **PR #1234**: feat(test): add test feature" in result
        assert "  - Path: `src/test/file.py`" in result
        assert "  - Impact: Added test feature" in result
        assert "  - Merged: 2025-12-07" in result

    def test_includes_all_prs(self, sample_period_data):
        """Test that all PRs are included."""
        result = generate_docs_changelog.generate_onboarding_guide_section(sample_period_data)

        assert "PR #1234" in result
        assert "PR #1235" in result
        assert "PR #1236" in result

    def test_includes_all_categories(self, sample_period_data):
        """Test that all categories are included."""
        result = generate_docs_changelog.generate_onboarding_guide_section(sample_period_data)

        assert "*Test Category:*" in result
        assert "*Backend & Infrastructure:*" in result


class TestGenerateProjectStructureSection:
    """Tests for generate_project_structure_section function."""

    def test_generates_correct_format(self, sample_period_data):
        """Test that the function generates the correct format."""
        result = generate_docs_changelog.generate_project_structure_section(sample_period_data)

        assert "**Recent PRs (Dec 7 - Dec 9, 2025)**:" in result
        assert "- **PR #1234** (Merged): feat(test): add test feature" in result
        assert "  - Path: `src/test/file.py` (new file)" in result

    def test_includes_path_note(self, sample_period_data):
        """Test that path notes are included."""
        result = generate_docs_changelog.generate_project_structure_section(sample_period_data)

        # PR #1234 has path_note "new file"
        assert "(new file)" in result


class TestGenerateEnvironmentsSection:
    """Tests for generate_environments_section function."""

    def test_generates_chinese_format(self, sample_period_data):
        """Test that the function generates Chinese format."""
        result = generate_docs_changelog.generate_environments_section(sample_period_data)

        assert "**近期重要更新** (2025-12-07 至 2025-12-09):" in result
        assert "*測試類別:*" in result
        assert "  - 影響：新增測試功能" in result

    def test_falls_back_to_english(self, sample_period_data):
        """Test fallback to English when Chinese not available."""
        # Remove Chinese translations
        sample_period_data["categories"][0]["prs"][0].pop("impact_zh")

        result = generate_docs_changelog.generate_environments_section(sample_period_data)

        # Should fall back to English impact
        assert "  - 影響：Added test feature" in result


class TestGenerateTroubleshootingSection:
    """Tests for generate_troubleshooting_section function."""

    def test_generates_correct_format(self, sample_period_data):
        """Test that the function generates the correct format."""
        result = generate_docs_changelog.generate_troubleshooting_section(sample_period_data)

        assert "## Recent Updates (Dec 7 - Dec 9, 2025)" in result

    def test_filters_relevant_categories(self, sample_period_data):
        """Test that only relevant categories are included."""
        result = generate_docs_changelog.generate_troubleshooting_section(sample_period_data)

        # "Test Category" should NOT be included (not relevant)
        assert "### Test Category" not in result
        # "Backend & Infrastructure" SHOULD be included
        assert "### Backend & Infrastructure" in result

    def test_uses_change_field_when_available(self, sample_period_data):
        """Test that 'change' field is used when available."""
        # Add a 'change' field to one PR
        sample_period_data["categories"][1]["prs"][0]["change"] = "Refactored backend API"

        result = generate_docs_changelog.generate_troubleshooting_section(sample_period_data)

        # Should use 'change' field for Change line
        assert "- **Change**: Refactored backend API" in result
        # Should still use 'impact' field for Impact line
        assert "- **Impact**: Added backend feature" in result

    def test_falls_back_to_impact_when_no_change(self, sample_period_data):
        """Test that 'impact' is used when 'change' is not available."""
        result = generate_docs_changelog.generate_troubleshooting_section(sample_period_data)

        # Should use 'impact' for both Change and Impact when no 'change' field
        assert "- **Change**: Added backend feature" in result
        assert "- **Impact**: Added backend feature" in result

    def test_custom_relevant_keywords(self, sample_period_data):
        """Test that custom relevant_keywords parameter works."""
        # Use custom keywords that include "Test"
        result = generate_docs_changelog.generate_troubleshooting_section(
            sample_period_data,
            relevant_keywords=["Test"],
        )

        # "Test Category" SHOULD now be included
        assert "### Test Category" in result
        # "Backend & Infrastructure" should NOT be included (no matching keyword)
        assert "### Backend & Infrastructure" not in result


class TestLoadChangelog:
    """Tests for load_changelog function."""

    def test_loads_valid_yaml(self):
        """Test loading a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"changelog": [{"period": "Test"}]}, f)
            f.flush()

            result = generate_docs_changelog.load_changelog(Path(f.name))

            assert "changelog" in result
            assert result["changelog"][0]["period"] == "Test"


class TestFindInsertionPoint:
    """Tests for find_insertion_point function."""

    def test_finds_onboarding_insertion_point(self):
        """Test finding insertion point in onboarding guide."""
        content = """
### Current Status

Some content here.

**Recent Improvements (Dec 1 - Dec 3, 2025)**:

Old content.
"""
        start, end = generate_docs_changelog.find_insertion_point(content, "onboarding")

        assert start > 0
        assert content[start:].startswith("**Recent Improvements")

    def test_finds_project_structure_insertion_point(self):
        """Test finding insertion point in project structure report."""
        content = """
Some header.

**Recent PRs (Dec 1 - Dec 3, 2025)**:

Old content.
"""
        start, end = generate_docs_changelog.find_insertion_point(content, "project_structure")

        assert start > 0
        assert content[start:].startswith("**Recent PRs")

    def test_returns_negative_when_not_found(self):
        """Test that -1 is returned when pattern not found."""
        content = "No matching pattern here."

        start, end = generate_docs_changelog.find_insertion_point(content, "onboarding")

        assert start == -1
        assert end == -1

    def test_html_comment_marker_takes_priority(self):
        """Test that HTML comment marker is used when present."""
        content = """
Some header.

<!-- CHANGELOG_INSERT_POINT:onboarding -->

**Recent Improvements (Dec 1 - Dec 3, 2025)**:

Old content.
"""
        start, end = generate_docs_changelog.find_insertion_point(content, "onboarding")

        assert start > 0
        # Should insert after the marker, not at the regex match
        assert "<!-- CHANGELOG_INSERT_POINT:onboarding -->" in content[:start]

    def test_year_agnostic_regex_patterns(self):
        """Test that regex patterns work across different years."""
        # Test with 2026 date
        content = """
Some header.

**Recent PRs (Jan 1 - Jan 5, 2026)**:

Old content.
"""
        start, end = generate_docs_changelog.find_insertion_point(content, "project_structure")

        assert start > 0
        assert content[start:].startswith("**Recent PRs")

    def test_environments_year_agnostic(self):
        """Test that environments pattern works across years."""
        content = """
Some header.

**近期重要更新** (2026-01-01 至 2026-01-05):

Old content.
"""
        start, end = generate_docs_changelog.find_insertion_point(content, "environments")

        assert start > 0
        assert content[start:].startswith("**近期重要更新")


class TestUpdateDocument:
    """Tests for update_document function."""

    def test_dry_run_does_not_modify_file(self, sample_period_data):
        """Test that dry run mode doesn't modify files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            original_content = """
### Current Status

Content.

**Recent Improvements (Dec 1 - Dec 3, 2025)**:

Old.
"""
            f.write(original_content)
            f.flush()

            section = generate_docs_changelog.generate_onboarding_guide_section(sample_period_data)
            result = generate_docs_changelog.update_document(
                Path(f.name),
                section,
                "onboarding",
                dry_run=True,
            )

            # Should return True (would update)
            assert result is True

            # File should not be modified
            with open(f.name) as check:
                assert check.read() == original_content

    def test_skips_if_section_exists(self, sample_period_data):
        """Test that existing sections are not duplicated."""
        section = generate_docs_changelog.generate_onboarding_guide_section(sample_period_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            # Write content that already contains the section
            f.write(section)
            f.flush()

            result = generate_docs_changelog.update_document(
                Path(f.name),
                section,
                "onboarding",
                dry_run=False,
            )

            # Should return False (section already exists)
            assert result is False
