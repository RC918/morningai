"""
File Reference Resolver - Cross-file reference extraction and context fetching.

Issue #3223: Enhance Diff-Aware Context Gathering with cross-file reference resolution.

This module provides deterministic file reference extraction from PR diffs,
enabling the Reviewer Agent to understand cross-file dependencies and provide
more contextual code reviews.

Blueprint Alignment:
- Deterministic: Uses regex patterns for import extraction (not LLM-based)
- Modular: Pluggable into reviewer_node via simple function calls

Features:
- Extract Python imports (from X import Y, import X)
- Extract TypeScript/JavaScript imports (import ... from 'X', require('X'))
- Fetch referenced file content with token budget control
- Support for relative and absolute imports
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported languages for import extraction."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    UNKNOWN = "unknown"


@dataclass
class FileReference:
    """Represents a file reference extracted from diff content."""
    import_path: str
    source_file: str
    language: Language
    line_number: Optional[int] = None
    is_relative: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "import_path": self.import_path,
            "source_file": self.source_file,
            "language": self.language.value,
            "line_number": self.line_number,
            "is_relative": self.is_relative,
        }


@dataclass
class ReferenceContext:
    """Context fetched for a file reference."""
    file_path: str
    content: str
    line_count: int
    truncated: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "content": self.content,
            "line_count": self.line_count,
            "truncated": self.truncated,
            "error": self.error,
        }


@dataclass
class ResolverResult:
    """Result of file reference resolution."""
    references: List[FileReference] = field(default_factory=list)
    contexts: List[ReferenceContext] = field(default_factory=list)
    total_references_found: int = 0
    total_contexts_fetched: int = 0
    total_bytes: int = 0
    truncated: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "references": [r.to_dict() for r in self.references],
            "contexts": [c.to_dict() for c in self.contexts],
            "total_references_found": self.total_references_found,
            "total_contexts_fetched": self.total_contexts_fetched,
            "total_bytes": self.total_bytes,
            "truncated": self.truncated,
            "error": self.error,
        }


# Default limits for token budget control
DEFAULT_MAX_FILES = 5
DEFAULT_MAX_LINES_PER_FILE = 100
DEFAULT_MAX_TOTAL_BYTES = 50000  # 50KB total context budget

# Allowed file extensions for fetching (security: limit to source code files)
ALLOWED_EXTENSIONS = {
    '.py', '.pyi',  # Python
    '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs',  # TypeScript/JavaScript
    '.json', '.yaml', '.yml', '.toml',  # Config files
    '.md', '.txt', '.rst',  # Documentation
    '.html', '.css', '.scss', '.less',  # Web
    '.go', '.rs', '.java', '.kt', '.swift',  # Other languages
    '.c', '.cpp', '.h', '.hpp',  # C/C++
    '.rb', '.php', '.sh', '.bash',  # Scripting
}


def sanitize_path(path: str) -> Optional[str]:
    """
    Sanitize a file path to prevent path traversal and unintended file access.

    Security measures:
    - Reject absolute paths
    - Reject paths with .. traversal
    - Reject paths with null bytes or backslashes
    - Normalize path separators
    - Validate file extension is in allowlist

    Args:
        path: File path to sanitize

    Returns:
        Sanitized path or None if path is rejected
    """
    if not path:
        return None

    # Reject null bytes (security)
    if '\x00' in path:
        logger.debug(f"[FileReferenceResolver] Rejected path with null byte: {repr(path)}")
        return None

    # Reject backslashes (Windows-style paths, potential bypass)
    if '\\' in path:
        logger.debug(f"[FileReferenceResolver] Rejected path with backslash: {path}")
        return None

    # Normalize the path
    normalized = path.strip()

    # Reject absolute paths
    if normalized.startswith('/'):
        logger.debug(f"[FileReferenceResolver] Rejected absolute path: {path}")
        return None

    # Reject paths that start with or contain .. traversal
    parts = normalized.split('/')
    if '..' in parts or any(p.startswith('..') for p in parts):
        logger.debug(f"[FileReferenceResolver] Rejected path with traversal: {path}")
        return None

    # Reject hidden files/directories (starting with .)
    if any(p.startswith('.') and p not in ('.', '..') for p in parts):
        # Allow common config files like .github but reject others
        if not any(p in ('.github', '.vscode', '.circleci') for p in parts):
            logger.debug(f"[FileReferenceResolver] Rejected hidden path: {path}")
            return None

    # Validate file extension
    ext = '.' + normalized.rsplit('.', 1)[-1].lower() if '.' in normalized else ''
    if ext and ext not in ALLOWED_EXTENSIONS:
        logger.debug(f"[FileReferenceResolver] Rejected disallowed extension: {path} (ext={ext})")
        return None

    return normalized


def detect_language(filename: str) -> Language:
    """
    Detect programming language from filename extension.

    Args:
        filename: File path or name

    Returns:
        Language enum value
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "py":
        return Language.PYTHON
    elif ext in ("ts", "tsx"):
        return Language.TYPESCRIPT
    elif ext in ("js", "jsx", "mjs", "cjs"):
        return Language.JAVASCRIPT
    else:
        return Language.UNKNOWN


def extract_python_imports(content: str, source_file: str) -> List[FileReference]:
    """
    Extract Python import statements from content.

    Handles:
    - from X import Y
    - from X import Y, Z
    - from .X import Y (relative)
    - import X
    - import X, Y
    - import X as alias

    Args:
        content: Python source code content
        source_file: Path of the source file

    Returns:
        List of FileReference objects
    """
    references = []

    # Pattern for 'from X import Y' style imports
    from_import_pattern = r'^[+]?\s*from\s+(\.{0,3}[\w.]+)\s+import'

    # Pattern for 'import X' style imports
    import_pattern = r'^[+]?\s*import\s+([\w.,\s]+?)(?:\s+as\s+\w+)?$'

    for line_num, line in enumerate(content.split('\n'), 1):
        # Skip removed lines (lines starting with -)
        if line.startswith('-'):
            continue

        # Check for 'from X import' pattern
        from_match = re.match(from_import_pattern, line.strip())
        if from_match:
            import_path = from_match.group(1)
            is_relative = import_path.startswith('.')
            references.append(FileReference(
                import_path=import_path,
                source_file=source_file,
                language=Language.PYTHON,
                line_number=line_num,
                is_relative=is_relative,
            ))
            continue

        # Check for 'import X' pattern
        import_match = re.match(import_pattern, line.strip())
        if import_match:
            imports_str = import_match.group(1)
            # Handle multiple imports: import X, Y, Z
            for imp in imports_str.split(','):
                imp = imp.strip().split()[0]  # Remove 'as alias' part
                if imp:
                    references.append(FileReference(
                        import_path=imp,
                        source_file=source_file,
                        language=Language.PYTHON,
                        line_number=line_num,
                        is_relative=False,
                    ))

    return references


def extract_typescript_imports(content: str, source_file: str) -> List[FileReference]:
    """
    Extract TypeScript/JavaScript import statements from content.

    Handles:
    - import X from 'Y'
    - import { X } from 'Y'
    - import * as X from 'Y'
    - import 'Y' (side-effect import)
    - require('Y')
    - const X = require('Y')

    Args:
        content: TypeScript/JavaScript source code content
        source_file: Path of the source file

    Returns:
        List of FileReference objects
    """
    references = []
    language = Language.TYPESCRIPT if source_file.endswith(('.ts', '.tsx')) else Language.JAVASCRIPT

    # Pattern for ES6 imports: import ... from 'X' or import 'X'
    es6_import_pattern = r'^[+]?\s*import\s+(?:.*?\s+from\s+)?["\']([^"\']+)["\']'

    # Pattern for require: require('X') or require("X")
    require_pattern = r'require\s*\(\s*["\']([^"\']+)["\']\s*\)'

    for line_num, line in enumerate(content.split('\n'), 1):
        # Skip removed lines
        if line.startswith('-'):
            continue

        # Check for ES6 import
        es6_match = re.search(es6_import_pattern, line)
        if es6_match:
            import_path = es6_match.group(1)
            is_relative = import_path.startswith('.') or import_path.startswith('/')
            references.append(FileReference(
                import_path=import_path,
                source_file=source_file,
                language=language,
                line_number=line_num,
                is_relative=is_relative,
            ))
            continue

        # Check for require()
        require_matches = re.findall(require_pattern, line)
        for import_path in require_matches:
            is_relative = import_path.startswith('.') or import_path.startswith('/')
            references.append(FileReference(
                import_path=import_path,
                source_file=source_file,
                language=language,
                line_number=line_num,
                is_relative=is_relative,
            ))

    return references


def extract_references_from_diff(
    diff_content: str,
) -> List[FileReference]:
    """
    Extract file references from unified diff content.

    Parses the diff to identify changed files and extracts import statements
    from added/modified lines.

    Args:
        diff_content: Unified diff content

    Returns:
        List of FileReference objects
    """
    references = []
    current_file = None

    # Pattern to match diff file headers
    file_header_pattern = r'^(?:---|\+\+\+)\s+[ab]/(.+)$'

    lines = diff_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for file header
        header_match = re.match(file_header_pattern, line)
        if header_match:
            current_file = header_match.group(1)
            i += 1
            continue

        # If we have a current file, extract imports from added lines
        if current_file:
            language = detect_language(current_file)

            # Collect the hunk content for this file
            hunk_content = []
            while i < len(lines) and not lines[i].startswith('---'):
                hunk_content.append(lines[i])
                i += 1

            hunk_text = '\n'.join(hunk_content)

            if language == Language.PYTHON:
                refs = extract_python_imports(hunk_text, current_file)
                references.extend(refs)
            elif language in (Language.TYPESCRIPT, Language.JAVASCRIPT):
                refs = extract_typescript_imports(hunk_text, current_file)
                references.extend(refs)

            continue

        i += 1

    return references


def resolve_import_path(
    import_path: str,
    source_file: str,
    language: Language,
    repo_files: Optional[Set[str]] = None,
) -> Optional[str]:
    """
    Resolve an import path to an actual file path in the repository.

    Args:
        import_path: The import path (e.g., 'utils.helpers', './components/Button')
        source_file: The file containing the import
        language: Programming language
        repo_files: Optional set of known files in the repository

    Returns:
        Resolved file path or None if cannot be resolved
    """
    if language == Language.PYTHON:
        # Convert Python module path to file path
        # e.g., 'utils.helpers' -> 'utils/helpers.py'
        if import_path.startswith('.'):
            # Relative import
            source_dir = '/'.join(source_file.split('/')[:-1])
            dots = len(import_path) - len(import_path.lstrip('.'))
            module_part = import_path.lstrip('.')

            # Security: Reject imports that would traverse outside repo root
            # dots-1 is how many directories we go up (1 dot = current dir, 2 dots = parent, etc.)
            source_depth = len(source_dir.split('/')) if source_dir else 0
            traversal_depth = dots - 1
            if traversal_depth > source_depth:
                logger.debug(
                    f"[FileReferenceResolver] Rejected import traversing outside repo: {import_path}",
                    extra={"source_file": source_file, "dots": dots, "source_depth": source_depth}
                )
                return None

            # Go up directories based on number of dots
            parts = source_dir.split('/')
            if dots > 1:
                parts = parts[:-(dots - 1)] if len(parts) >= dots - 1 else []

            if module_part:
                parts.append(module_part.replace('.', '/'))

            base_path = '/'.join(parts)
        else:
            # Absolute import
            base_path = import_path.replace('.', '/')

        # Try different file extensions
        candidates = [
            f"{base_path}.py",
            f"{base_path}/__init__.py",
        ]

        for candidate in candidates:
            if repo_files is None or candidate in repo_files:
                return candidate

        return f"{base_path}.py"  # Default guess

    elif language in (Language.TYPESCRIPT, Language.JAVASCRIPT):
        if import_path.startswith('.') or import_path.startswith('/'):
            # Relative import
            source_dir = '/'.join(source_file.split('/')[:-1])

            if import_path.startswith('./'):
                resolved = f"{source_dir}/{import_path[2:]}"
            elif import_path.startswith('../'):
                parts = source_dir.split('/')
                up_count = import_path.count('../')

                # Security: Reject imports that would traverse outside repo root
                source_depth = len(parts) if source_dir else 0
                if up_count > source_depth:
                    logger.debug(
                        f"[FileReferenceResolver] Rejected import traversing outside repo: {import_path}",
                        extra={"source_file": source_file, "up_count": up_count, "source_depth": source_depth}
                    )
                    return None

                remaining = import_path.replace('../', '')
                parts = parts[:-up_count] if len(parts) >= up_count else []
                resolved = '/'.join(parts + [remaining]) if parts else remaining
            else:
                resolved = import_path.lstrip('/')

            # Try different extensions
            extensions = ['.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.tsx', '/index.js']
            for ext in extensions:
                candidate = resolved + ext if not resolved.endswith(ext.lstrip('/')) else resolved
                if repo_files is None or candidate in repo_files:
                    return candidate

            return resolved  # Return as-is if no extension matches

        else:
            # Node module - skip these as they're external dependencies
            return None

    return None


def fetch_file_content(
    repo,
    file_path: str,
    ref: str,
    max_lines: int = DEFAULT_MAX_LINES_PER_FILE,
) -> ReferenceContext:
    """
    Fetch content of a file from the repository.

    Args:
        repo: GitHub repository object
        file_path: Path to the file
        ref: Git ref (branch, tag, or SHA)
        max_lines: Maximum lines to fetch

    Returns:
        ReferenceContext with file content
    """
    try:
        file_obj = repo.get_contents(file_path, ref=ref)

        if hasattr(file_obj, 'decoded_content'):
            content = file_obj.decoded_content.decode('utf-8')
            lines = content.split('\n')
            num_lines = len(lines)
            truncated = num_lines > max_lines

            if truncated:
                lines = lines[:max_lines]
                lines.append(f"... (truncated {num_lines - max_lines} more lines)")

            return ReferenceContext(
                file_path=file_path,
                content='\n'.join(lines),
                line_count=len(lines),
                truncated=truncated,
            )
        else:
            return ReferenceContext(
                file_path=file_path,
                content="",
                line_count=0,
                error="File is not a text file or is too large",
            )

    except Exception as e:
        return ReferenceContext(
            file_path=file_path,
            content="",
            line_count=0,
            error=str(e),
        )


def resolve_file_references(
    repo,
    diff_content: str,
    head_sha: str,
    max_files: int = DEFAULT_MAX_FILES,
    max_lines_per_file: int = DEFAULT_MAX_LINES_PER_FILE,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    trace_id: Optional[str] = None,
) -> ResolverResult:
    """
    Main entry point: Extract and resolve file references from PR diff.

    This function:
    1. Extracts import statements from the diff
    2. Resolves import paths to actual file paths
    3. Fetches content of referenced files (with token budget control)

    Args:
        repo: GitHub repository object
        diff_content: Unified diff content
        head_sha: PR head commit SHA for fetching files
        max_files: Maximum number of files to fetch
        max_lines_per_file: Maximum lines per file
        max_total_bytes: Maximum total bytes for all contexts
        trace_id: Optional trace ID for logging

    Returns:
        ResolverResult with references and contexts
    """
    result = ResolverResult()

    try:
        # Step 1: Extract references from diff
        references = extract_references_from_diff(diff_content)
        result.references = references
        result.total_references_found = len(references)

        if not references:
            logger.debug(
                "[FileReferenceResolver] No references found in diff",
                extra={"trace_id": trace_id}
            )
            return result

        # Step 2: Deduplicate and resolve import paths
        seen_paths: Set[str] = set()
        resolved_paths: List[str] = []

        # Pre-compute set of changed files for exact match comparison
        # (avoids false positives from substring matching, e.g., a/b.py in x/y/a/b.py)
        changed_files: Set[str] = {ref.source_file for ref in references}

        for ref in references:
            resolved = resolve_import_path(
                ref.import_path,
                ref.source_file,
                ref.language,
            )
            if resolved and resolved not in seen_paths:
                # Security: Sanitize the resolved path before fetching
                sanitized = sanitize_path(resolved)
                if not sanitized:
                    logger.debug(
                        f"[FileReferenceResolver] Skipped unsafe path: {resolved}",
                        extra={
                            "trace_id": trace_id,
                            "import_path": ref.import_path,
                            "source_file": ref.source_file,
                        }
                    )
                    continue

                # Skip if the resolved path is the same as a changed file
                # (we already have that content in the diff)
                if sanitized not in changed_files:
                    seen_paths.add(sanitized)
                    resolved_paths.append(sanitized)

        if not resolved_paths:
            logger.debug(
                "[FileReferenceResolver] No resolvable paths found",
                extra={
                    "trace_id": trace_id,
                    "total_references": len(references)
                }
            )
            return result

        # Step 3: Fetch file contents with budget control
        total_bytes = 0
        contexts = []

        for path in resolved_paths[:max_files]:
            if total_bytes >= max_total_bytes:
                result.truncated = True
                break

            context = fetch_file_content(
                repo=repo,
                file_path=path,
                ref=head_sha,
                max_lines=max_lines_per_file,
            )

            if context.error:
                logger.debug(
                    f"[FileReferenceResolver] Failed to fetch {path}: {context.error}",
                    extra={"trace_id": trace_id, "file_path": path}
                )
                continue

            content_bytes = len(context.content.encode('utf-8'))
            if total_bytes + content_bytes > max_total_bytes:
                result.truncated = True
                break

            contexts.append(context)
            total_bytes += content_bytes

        result.contexts = contexts
        result.total_contexts_fetched = len(contexts)
        result.total_bytes = total_bytes

        if len(resolved_paths) > max_files:
            result.truncated = True

        logger.info(
            f"[FileReferenceResolver] Resolved {len(contexts)} file references",
            extra={
                "trace_id": trace_id,
                "total_references": len(references),
                "resolved_paths": len(resolved_paths),
                "fetched_contexts": len(contexts),
                "total_bytes": total_bytes,
                "truncated": result.truncated,
            }
        )

        return result

    except Exception as e:
        logger.warning(
            f"[FileReferenceResolver] Error resolving references: {e}",
            extra={"trace_id": trace_id, "error": str(e)}
        )
        result.error = str(e)
        return result


def format_reference_context_for_prompt(result: ResolverResult) -> str:
    """
    Format resolved reference contexts for inclusion in LLM prompt.

    Args:
        result: ResolverResult from resolve_file_references

    Returns:
        Formatted string suitable for LLM prompt
    """
    if not result.contexts:
        return ""

    parts = ["## Referenced Files (for context)\n"]

    for ctx in result.contexts:
        if ctx.content:
            parts.append(f"### {ctx.file_path}")
            if ctx.truncated:
                parts.append(f"(truncated to {ctx.line_count} lines)")
            parts.append("```")
            parts.append(ctx.content)
            parts.append("```\n")

    if result.truncated:
        parts.append("*Note: Reference context was truncated to stay within token budget.*\n")

    return '\n'.join(parts)
