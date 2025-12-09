#!/usr/bin/env python3
"""
Generate documentation changelog sections from a single YAML source.

This script reads docs/pr-changelog.yaml and generates formatted changelog
sections for multiple documentation files:
- docs/ONBOARDING_GUIDE.md
- docs/PROJECT_STRUCTURE_REPORT.md
- docs/ENVIRONMENTS.md
- docs/deployment/troubleshooting-monitoring.md

Usage:
    python scripts/generate-docs-changelog.py [--dry-run] [--period PERIOD]

Options:
    --dry-run       Preview changes without modifying files
    --period PERIOD Only generate for a specific period (e.g., "Dec 7 - Dec 9, 2025")
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


def load_changelog(changelog_path: Path) -> dict[str, Any]:
    """Load the PR changelog YAML file."""
    with open(changelog_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_onboarding_guide_section(period_data: dict[str, Any]) -> str:
    """Generate changelog section for ONBOARDING_GUIDE.md format.

    Format:
    **Recent Improvements (Dec 7 - Dec 9, 2025)**:

    *Category Name:*
    - **PR #123**: title
      - Path: `path/to/file`
      - Impact: description
      - Merged: 2025-12-07
    """
    lines = [f"**Recent Improvements ({period_data['period']})**:", ""]

    for category in period_data["categories"]:
        lines.append(f"*{category['name']}:*")
        for pr in category["prs"]:
            lines.append(f"- **PR #{pr['number']}**: {pr['title']}")
            if pr.get("path"):
                lines.append(f"  - Path: `{pr['path']}`")
            lines.append(f"  - Impact: {pr['impact']}")
            lines.append(f"  - Merged: {pr['merged']}")
        lines.append("")

    return "\n".join(lines)


def generate_project_structure_section(period_data: dict[str, Any]) -> str:
    """Generate changelog section for PROJECT_STRUCTURE_REPORT.md format.

    Format:
    **Recent PRs (Dec 8 - Dec 9, 2025)**:

    *Category Name:*
    - **PR #123** (Merged): title
      - Path: `path/to/file` (note)
    """
    lines = [f"**Recent PRs ({period_data['period']})**:", ""]

    for category in period_data["categories"]:
        lines.append(f"*{category['name']}:*")
        for pr in category["prs"]:
            lines.append(f"- **PR #{pr['number']}** (Merged): {pr['title']}")
            if pr.get("path"):
                path_str = f"  - Path: `{pr['path']}`"
                if pr.get("path_note"):
                    path_str += f" ({pr['path_note']})"
                lines.append(path_str)
        lines.append("")

    return "\n".join(lines)


def generate_environments_section(period_data: dict[str, Any]) -> str:
    """Generate changelog section for ENVIRONMENTS.md format (Chinese).

    Format:
    **近期重要更新** (2025-12-07 至 2025-12-09):

    *Category Name (Chinese):*
    - **PR #123**: title
      - Path: `path/to/file`
      - 影響：impact (Chinese)
    """
    lines = [f"**近期重要更新** ({period_data['period_zh']}):", ""]

    for category in period_data["categories"]:
        lines.append(f"*{category.get('name_zh', category['name'])}:*")
        for pr in category["prs"]:
            lines.append(f"- **PR #{pr['number']}**: {pr['title']}")
            if pr.get("path"):
                lines.append(f"  - Path: `{pr['path']}`")
            impact_zh = pr.get("impact_zh", pr["impact"])
            lines.append(f"  - 影響：{impact_zh}")
        lines.append("")

    return "\n".join(lines)


def generate_troubleshooting_section(period_data: dict[str, Any]) -> str:
    """Generate changelog section for troubleshooting-monitoring.md format.

    Format:
    ## Recent Updates (Dec 8 - Dec 9, 2025)

    ### Category Name

    #### PR #123: Short title
    - **Path**: `path/to/file`
    - **Change**: description
    - **Impact**: impact
    """
    lines = [f"## Recent Updates ({period_data['period']})", ""]

    for category in period_data["categories"]:
        # Only include relevant categories for troubleshooting docs
        relevant_keywords = [
            "Backend",
            "Infrastructure",
            "Monitoring",
            "Phase 7",
            "Rollout",
            "Multi-Signal",
        ]
        if not any(kw in category["name"] for kw in relevant_keywords):
            continue

        lines.append(f"### {category['name']}")
        lines.append("")

        for pr in category["prs"]:
            # Extract short title from full title
            short_title = pr["title"].split(": ", 1)[-1] if ": " in pr["title"] else pr["title"]
            lines.append(f"#### PR #{pr['number']}: {short_title}")
            if pr.get("path"):
                lines.append(f"- **Path**: `{pr['path']}`")
            lines.append(f"- **Change**: {pr['impact']}")
            lines.append(f"- **Impact**: {pr['impact']}")
            lines.append("")

    return "\n".join(lines)


def find_insertion_point(content: str, doc_type: str) -> tuple[int, int]:
    """Find the insertion point for new changelog section.

    Returns (start_index, end_index) where the new section should be inserted.
    If end_index > start_index, the content between them should be replaced.
    """
    if doc_type == "onboarding":
        # Insert after "### Current Status" section, before existing "Recent Improvements"
        pattern = r"\*\*Recent Improvements \(Dec \d+ - Dec \d+, 2025\)\*\*:"
        match = re.search(pattern, content)
        if match:
            return match.start(), match.start()
        # Fallback: after Current Status section
        pattern = r"### Current Status.*?\n\n"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.end(), match.end()

    elif doc_type == "project_structure":
        # Insert before existing "Recent PRs" section
        pattern = r"\*\*Recent PRs \(Dec \d+ - Dec \d+, 2025\)\*\*:"
        match = re.search(pattern, content)
        if match:
            return match.start(), match.start()

    elif doc_type == "environments":
        # Insert before existing "近期重要更新" section
        pattern = r"\*\*近期重要更新\*\* \(2025-\d+-\d+ 至 2025-\d+-\d+\):"
        match = re.search(pattern, content)
        if match:
            return match.start(), match.start()

    elif doc_type == "troubleshooting":
        # Insert before existing "## Recent Updates" section
        pattern = r"## Recent Updates \(Dec \d+ - Dec \d+, 2025\)"
        match = re.search(pattern, content)
        if match:
            return match.start(), match.start()

    return -1, -1


def update_document(
    doc_path: Path,
    new_section: str,
    doc_type: str,
    dry_run: bool = False,
) -> bool:
    """Update a documentation file with the new changelog section.

    Returns True if the document was updated (or would be updated in dry-run mode).
    """
    if not doc_path.exists():
        print(f"Warning: {doc_path} does not exist, skipping")
        return False

    content = doc_path.read_text(encoding="utf-8")
    start_idx, end_idx = find_insertion_point(content, doc_type)

    if start_idx == -1:
        print(f"Warning: Could not find insertion point in {doc_path}")
        return False

    # Check if section already exists (avoid duplicates)
    if new_section.split("\n")[0] in content:
        print(f"Info: Section already exists in {doc_path}, skipping")
        return False

    # Insert the new section
    new_content = content[:start_idx] + new_section + "\n" + content[end_idx:]

    if dry_run:
        print(f"\n{'='*60}")
        print(f"DRY RUN: Would update {doc_path}")
        print(f"{'='*60}")
        print(f"New section to insert:\n{new_section[:500]}...")
        return True

    doc_path.write_text(new_content, encoding="utf-8")
    print(f"Updated: {doc_path}")
    return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate documentation changelog sections from YAML source"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--period",
        type=str,
        help="Only generate for a specific period (e.g., 'Dec 7 - Dec 9, 2025')",
    )
    args = parser.parse_args()

    # Determine repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    # Load changelog
    changelog_path = repo_root / "docs" / "pr-changelog.yaml"
    if not changelog_path.exists():
        print(f"Error: {changelog_path} not found")
        return 1

    changelog = load_changelog(changelog_path)

    # Filter periods if specified
    periods = changelog.get("changelog", [])
    if args.period:
        periods = [p for p in periods if p["period"] == args.period]
        if not periods:
            print(f"Error: Period '{args.period}' not found in changelog")
            return 1

    # Document configurations
    docs_config = [
        {
            "path": repo_root / "docs" / "ONBOARDING_GUIDE.md",
            "type": "onboarding",
            "generator": generate_onboarding_guide_section,
        },
        {
            "path": repo_root / "docs" / "PROJECT_STRUCTURE_REPORT.md",
            "type": "project_structure",
            "generator": generate_project_structure_section,
        },
        {
            "path": repo_root / "docs" / "ENVIRONMENTS.md",
            "type": "environments",
            "generator": generate_environments_section,
        },
        {
            "path": repo_root / "docs" / "deployment" / "troubleshooting-monitoring.md",
            "type": "troubleshooting",
            "generator": generate_troubleshooting_section,
        },
    ]

    updated_count = 0
    for period_data in periods:
        print(f"\nProcessing period: {period_data['period']}")

        for doc_config in docs_config:
            section = doc_config["generator"](period_data)
            if update_document(
                doc_config["path"],
                section,
                doc_config["type"],
                dry_run=args.dry_run,
            ):
                updated_count += 1

    print(f"\n{'='*60}")
    if args.dry_run:
        print(f"DRY RUN complete. {updated_count} files would be updated.")
    else:
        print(f"Complete. {updated_count} files updated.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
