"""Unit tests for capture-merged-pr.py script."""

import tempfile
from pathlib import Path

import pytest
import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from importlib import import_module

# Import functions from the script
capture_merged_pr = import_module("capture-merged-pr")


class TestParseConventionalCommit:
    """Tests for _parse_conventional_commit function."""

    def test_parses_type_and_scope(self):
        """Test parsing type and scope from conventional commit."""
        pr_type, scope = capture_merged_pr._parse_conventional_commit(
            "feat(owner-console): add feature"
        )
        assert pr_type == "feat"
        assert scope == "owner-console"

    def test_parses_type_only(self):
        """Test parsing type when no scope is present."""
        pr_type, scope = capture_merged_pr._parse_conventional_commit(
            "docs: update readme"
        )
        assert pr_type == "docs"
        assert scope is None

    def test_returns_none_for_non_conventional(self):
        """Test that None is returned for non-conventional titles."""
        pr_type, scope = capture_merged_pr._parse_conventional_commit(
            "Update something"
        )
        assert pr_type is None
        assert scope is None


class TestGetPrimaryPath:
    """Tests for _get_primary_path function."""

    def test_returns_most_common_parent(self):
        """Test that most common parent directory is returned."""
        paths = [
            "src/components/Button.tsx",
            "src/components/Input.tsx",
            "src/utils/helpers.ts",
        ]
        result = capture_merged_pr._get_primary_path(paths)
        assert result == "src/components"

    def test_returns_empty_for_empty_list(self):
        """Test that empty string is returned for empty list."""
        result = capture_merged_pr._get_primary_path([])
        assert result == ""

    def test_handles_single_file(self):
        """Test handling of single file."""
        result = capture_merged_pr._get_primary_path(["src/index.ts"])
        assert result == "src"


class TestExtractCategoryFromTitle:
    """Tests for extract_category_from_title function."""

    def test_extracts_scope_from_conventional_commit(self):
        """Test extraction of scope from conventional commit format."""
        assert capture_merged_pr.extract_category_from_title(
            "feat(owner-console): add new feature"
        ) == "owner-console"

    def test_extracts_scope_with_hyphen(self):
        """Test extraction of scope with hyphen."""
        assert capture_merged_pr.extract_category_from_title(
            "fix(api-backend): fix bug"
        ) == "api-backend"

    def test_returns_type_when_no_scope(self):
        """Test that type is returned when no scope is present."""
        assert capture_merged_pr.extract_category_from_title(
            "docs: update readme"
        ) == "docs"

    def test_returns_uncategorized_for_non_conventional(self):
        """Test that uncategorized is returned for non-conventional titles."""
        assert capture_merged_pr.extract_category_from_title(
            "Update something"
        ) == "uncategorized"


class TestExtractPrType:
    """Tests for extract_pr_type function."""

    def test_extracts_feat_type(self):
        """Test extraction of feat type."""
        assert capture_merged_pr.extract_pr_type(
            "feat(owner-console): add feature"
        ) == "feat"

    def test_extracts_fix_type(self):
        """Test extraction of fix type."""
        assert capture_merged_pr.extract_pr_type(
            "fix(orchestrator): fix bug"
        ) == "fix"

    def test_extracts_refactor_type(self):
        """Test extraction of refactor type."""
        assert capture_merged_pr.extract_pr_type(
            "refactor: clean up code"
        ) == "refactor"

    def test_returns_other_for_non_conventional(self):
        """Test that other is returned for non-conventional titles."""
        assert capture_merged_pr.extract_pr_type(
            "Update something"
        ) == "other"


class TestLoadRawFeed:
    """Tests for load_raw_feed function."""

    def test_creates_new_structure_when_file_missing(self):
        """Test that new structure is created when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.yaml"
            result = capture_merged_pr.load_raw_feed(path)

            assert "raw_feed" in result
            assert "metadata" in result
            assert result["raw_feed"] == []

    def test_loads_existing_file(self):
        """Test loading an existing raw feed file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "raw_feed": [{"number": 123, "title": "Test"}],
                "metadata": {"last_updated": "2025-01-01"}
            }, f)
            f.flush()

            result = capture_merged_pr.load_raw_feed(Path(f.name))

            assert len(result["raw_feed"]) == 1
            assert result["raw_feed"][0]["number"] == 123


class TestPrExistsInFeed:
    """Tests for pr_exists_in_feed function."""

    def test_returns_true_when_pr_exists(self):
        """Test that True is returned when PR exists."""
        feed = {"raw_feed": [{"number": 123}, {"number": 456}]}
        assert capture_merged_pr.pr_exists_in_feed(feed, 123) is True

    def test_returns_false_when_pr_not_exists(self):
        """Test that False is returned when PR doesn't exist."""
        feed = {"raw_feed": [{"number": 123}, {"number": 456}]}
        assert capture_merged_pr.pr_exists_in_feed(feed, 789) is False

    def test_returns_false_for_empty_feed(self):
        """Test that False is returned for empty feed."""
        feed = {"raw_feed": []}
        assert capture_merged_pr.pr_exists_in_feed(feed, 123) is False


class TestCreateRawEntry:
    """Tests for create_raw_entry function."""

    def test_creates_entry_with_all_fields(self):
        """Test that entry is created with all required fields."""
        pr_data = {
            "number": 1234,
            "title": "feat(owner-console): add new feature",
            "labels": [{"name": "enhancement"}, {"name": "frontend"}],
            "changed_files": 5,
            "merged_at": "2025-12-10T00:00:00Z",
            "merged_by": {"login": "reviewer"},
            "user": {"login": "author"},
            "html_url": "https://github.com/org/repo/pull/1234",
            "body": "This is the PR description",
        }
        changed_paths = ["src/components/Feature.tsx", "src/components/Feature.test.tsx"]

        entry = capture_merged_pr.create_raw_entry(pr_data, changed_paths)

        assert entry["number"] == 1234
        assert entry["title"] == "feat(owner-console): add new feature"
        assert entry["type"] == "feat"
        assert entry["scope"] == "owner-console"
        assert entry["labels"] == ["enhancement", "frontend"]
        assert entry["primary_path"] == "src/components"
        assert entry["changed_files_count"] == 5
        assert entry["merged_at"] == "2025-12-10T00:00:00Z"
        assert entry["merged_by"] == "reviewer"
        assert entry["author"] == "author"
        assert entry["curated"] is False

    def test_handles_missing_optional_fields(self):
        """Test that entry handles missing optional fields gracefully."""
        pr_data = {
            "number": 1234,
            "title": "Update something",
            "labels": [],
        }
        changed_paths = []

        entry = capture_merged_pr.create_raw_entry(pr_data, changed_paths)

        assert entry["number"] == 1234
        assert entry["type"] == "other"
        assert entry["scope"] == "uncategorized"
        assert entry["labels"] == []
        assert entry["primary_path"] == ""
        assert entry["curated"] is False


class TestSaveRawFeed:
    """Tests for save_raw_feed function."""

    def test_saves_and_updates_timestamp(self):
        """Test that feed is saved and timestamp is updated."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            path = Path(f.name)

        data = {
            "raw_feed": [{"number": 123}],
            "metadata": {"last_updated": None}
        }

        capture_merged_pr.save_raw_feed(path, data)

        # Read back and verify
        with open(path) as f:
            saved = yaml.safe_load(f)

        assert saved["metadata"]["last_updated"] is not None
        assert saved["raw_feed"][0]["number"] == 123
