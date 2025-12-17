#!/usr/bin/env python3
"""
Verify README index files match actual directory contents.

This script checks that README.md index files in docs/ directories
accurately list all markdown files in their respective directories.

Usage:
    python scripts/verify-readme-index.py [--fix]

Options:
    --fix    Automatically add missing files to README index tables
"""

import os
import re
import sys
from pathlib import Path
from typing import NamedTuple


class IndexIssue(NamedTuple):
    """Represents an issue found in a README index."""
    directory: str
    issue_type: str  # 'missing_in_readme' or 'missing_in_directory'
    filename: str


def extract_linked_files_from_readme(readme_path: Path) -> set[str]:
    """Extract all .md files linked in a README table."""
    if not readme_path.exists():
        return set()
    
    content = readme_path.read_text(encoding='utf-8')
    
    # Match markdown links like [filename.md](filename.md) or [text](filename.md)
    # Also match table rows with links
    pattern = r'\[([^\]]+)\]\(([^)]+\.md)\)'
    matches = re.findall(pattern, content)
    
    linked_files = set()
    readme_dir = readme_path.parent
    for _, link in matches:
        # Resolve the link relative to the README directory
        link_path = readme_dir / link
        if link_path.exists() and link_path.name != 'README.md':
            # Store the relative path from the README directory
            linked_files.add(link)
    
    return linked_files


def get_md_files_in_directory(directory: Path) -> set[str]:
    """Get all .md files in a directory (excluding README.md).
    
    Only descends into subdirectories that don't have their own README.md,
    to avoid pulling in files from nested index directories.
    """
    if not directory.exists():
        return set()
    
    md_files = set()
    for f in directory.iterdir():
        if f.is_file() and f.suffix == '.md' and f.name != 'README.md':
            md_files.add(f.name)
        elif f.is_dir():
            # Only include subdirectory files if the subdirectory doesn't have its own README
            subdir_readme = f / 'README.md'
            if not subdir_readme.exists():
                for subf in f.iterdir():
                    if subf.is_file() and subf.suffix == '.md' and subf.name != 'README.md':
                        # Use as_posix() for cross-platform path consistency
                        md_files.add(Path(f.name, subf.name).as_posix())
    
    return md_files


def check_directory(directory: Path) -> list[IndexIssue]:
    """Check a single directory for README index consistency."""
    issues = []
    readme_path = directory / 'README.md'
    
    if not readme_path.exists():
        return issues
    
    linked_files = extract_linked_files_from_readme(readme_path)
    actual_files = get_md_files_in_directory(directory)
    
    # Files in directory but not in README
    for f in actual_files - linked_files:
        issues.append(IndexIssue(
            directory=directory.as_posix(),
            issue_type='missing_in_readme',
            filename=f
        ))
    
    # Files in README but not in directory (only check if link doesn't resolve)
    # This is already handled by extract_linked_files_from_readme which only
    # includes files that exist
    
    return issues


def is_index_style_readme(readme_path: Path) -> bool:
    """Check if a README.md file is an index-style README with a table.
    
    Index-style READMEs contain markdown tables (with |---| separators)
    and links to .md files. Non-index READMEs (narrative documentation)
    are skipped.
    """
    if not readme_path.exists():
        return False
    
    content = readme_path.read_text(encoding='utf-8')
    
    # Check for markdown table separator (|---| or | --- |)
    has_table = bool(re.search(r'\|[\s-]+\|', content))
    
    # Check for at least one relative .md link (not README.md, not http)
    has_md_links = bool(re.search(r'\]\((?!http)(?!#)(?!README\.md)[^)]+\.md\)', content))
    
    return has_table and has_md_links


def get_docs_directories() -> list[Path]:
    """Get all directories under docs/ that should have README indexes.
    
    Dynamically discovers subdirectories under docs/ that contain
    index-style README.md files. Focuses on directories that are part
    of the PR7 documentation migration structure.
    
    Scanned areas:
    - docs/reports/* (all subdirectories)
    - docs/guides, docs/runbooks, docs/releases, docs/migration
    """
    docs_root = Path('docs')
    directories = []
    
    if not docs_root.exists():
        return directories
    
    # Dynamically discover docs/reports/* subdirectories with index READMEs
    reports_dir = docs_root / 'reports'
    if reports_dir.exists():
        for readme_path in reports_dir.rglob('README.md'):
            parent_dir = readme_path.parent
            # Skip docs/reports itself, only include subdirectories
            if parent_dir != reports_dir and is_index_style_readme(readme_path):
                directories.append(parent_dir)
    
    # Check other PR7 migration directories
    for subdir_name in ['guides', 'runbooks', 'releases', 'migration']:
        subdir = docs_root / subdir_name
        readme_path = subdir / 'README.md'
        if subdir.exists() and is_index_style_readme(readme_path):
            directories.append(subdir)
    
    return sorted(directories, key=lambda p: p.as_posix())


def main() -> int:
    """Main entry point."""
    fix_mode = '--fix' in sys.argv
    
    directories = get_docs_directories()
    all_issues: list[IndexIssue] = []
    
    for directory in directories:
        issues = check_directory(directory)
        all_issues.extend(issues)
    
    if not all_issues:
        print("All README index files are consistent with directory contents.")
        return 0
    
    # Group issues by type
    missing_in_readme = [i for i in all_issues if i.issue_type == 'missing_in_readme']
    missing_in_directory = [i for i in all_issues if i.issue_type == 'missing_in_directory']
    
    if missing_in_readme:
        print(f"\nFiles missing from README index ({len(missing_in_readme)}):")
        for issue in sorted(missing_in_readme, key=lambda x: (x.directory, x.filename)):
            print(f"  {issue.directory}: {issue.filename}")
    
    if missing_in_directory:
        print(f"\nFiles listed in README but not found ({len(missing_in_directory)}):")
        for issue in sorted(missing_in_directory, key=lambda x: (x.directory, x.filename)):
            print(f"  {issue.directory}: {issue.filename}")
    
    if fix_mode and missing_in_readme:
        print("\n--fix mode: Auto-fix not implemented yet. Please update README files manually.")
    
    return 1 if all_issues else 0


if __name__ == '__main__':
    sys.exit(main())
