"""
Changeset Significance Score (Value Gate) for Publisher Node

Blueprint Alignment:
- Flow Controller v3: This is a core governance gate in the Publisher Node
- Safety Governor v2: Prevents low-value PRs from being created
- Planner v3: Can be called by Flow Controller for pre-PR validation

Purpose:
Calculate the "significance" of a changeset to determine if it warrants a PR.
Low-significance changes (e.g., formatting-only, trivial whitespace) are
automatically downgraded to log-only mode instead of creating a PR.

Feature Flags:
- ENABLE_VALUE_GATE: Master switch (default: True)
- VALUE_GATE_MIN_SCORE: Minimum score to create PR (default: 30)
- VALUE_GATE_DRY_RUN: Log-only mode for testing (default: True)

Scoring Dimensions:
1. Semantic Impact: Does the change affect logic/behavior?
2. Scope: How many files/lines are affected?
3. Risk Level: Does the change touch critical paths?
4. Novelty: Is this a new feature vs. maintenance?

Issue: Publisher Node Value Gate (垃圾PR Prevention)
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Classification of change types by significance"""
    FORMATTING = "formatting"           # Whitespace, indentation, line breaks
    COMMENT = "comment"                 # Comment additions/modifications
    IMPORT = "import"                   # Import statement changes
    REFACTOR = "refactor"               # Code restructuring without behavior change
    BUGFIX = "bugfix"                   # Bug fixes
    FEATURE = "feature"                 # New functionality
    CONFIG = "config"                   # Configuration changes
    DOCS = "docs"                       # Documentation changes
    TEST = "test"                       # Test additions/modifications
    DEPENDENCY = "dependency"           # Dependency updates
    SECURITY = "security"               # Security-related changes
    UNKNOWN = "unknown"                 # Cannot classify


# Significance weights for each change type (0-100)
CHANGE_TYPE_WEIGHTS = {
    ChangeType.FORMATTING: 5,
    ChangeType.COMMENT: 10,
    ChangeType.IMPORT: 15,
    ChangeType.DOCS: 20,
    ChangeType.REFACTOR: 30,
    ChangeType.CONFIG: 35,
    ChangeType.TEST: 40,
    ChangeType.DEPENDENCY: 45,
    ChangeType.BUGFIX: 60,
    ChangeType.FEATURE: 80,
    ChangeType.SECURITY: 90,
    ChangeType.UNKNOWN: 25,
}

# File patterns that indicate higher significance
HIGH_SIGNIFICANCE_PATTERNS = [
    r"\.py$",           # Python source files
    r"\.ts$",           # TypeScript source files
    r"\.tsx$",          # React TypeScript files
    r"\.js$",           # JavaScript files
    r"\.jsx$",          # React JavaScript files
    r"\.go$",           # Go source files
    r"\.rs$",           # Rust source files
    r"\.java$",         # Java source files
    r"\.sql$",          # SQL files (database changes)
    r"\.yaml$",         # YAML config (often CI/CD)
    r"\.yml$",          # YAML config
    r"Dockerfile",      # Container definitions
    r"docker-compose",  # Container orchestration
]

# File patterns that indicate lower significance
LOW_SIGNIFICANCE_PATTERNS = [
    r"\.md$",           # Markdown documentation
    r"\.txt$",          # Text files
    r"\.json$",         # JSON (often config/data)
    r"\.lock$",         # Lock files
    r"\.log$",          # Log files
    r"\.gitignore$",    # Git ignore
    r"LICENSE",         # License files
    r"README",          # README files
    r"CHANGELOG",       # Changelog files
]

# Patterns that indicate formatting-only changes
FORMATTING_PATTERNS = [
    r"^\s*$",                           # Empty lines
    r"^\s+",                            # Leading whitespace only
    r"\s+$",                            # Trailing whitespace only
    r"^[-+]\s*#",                       # Comment lines
    r"^[-+]\s*//",                      # Comment lines (JS/TS)
    r"^[-+]\s*/\*",                     # Block comment start
    r"^[-+]\s*\*/",                     # Block comment end
]


@dataclass
class SignificanceResult:
    """Result of changeset significance analysis"""
    score: int                          # 0-100 significance score
    should_create_pr: bool              # Whether to create PR
    primary_change_type: ChangeType     # Dominant change type
    change_type_breakdown: Dict[ChangeType, int] = field(default_factory=dict)
    files_analyzed: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    high_significance_files: List[str] = field(default_factory=list)
    low_significance_files: List[str] = field(default_factory=list)
    reasoning: str = ""
    downgrade_reason: Optional[str] = None


@dataclass
class ChangesetAnalysis:
    """Intermediate analysis of a changeset"""
    files: List[str] = field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0
    change_types: Dict[ChangeType, int] = field(default_factory=dict)
    high_significance_files: List[str] = field(default_factory=list)
    low_significance_files: List[str] = field(default_factory=list)


def _classify_line_change(line: str) -> ChangeType:
    """
    Classify a single line change by its content.
    
    Args:
        line: A diff line (starting with + or -)
        
    Returns:
        ChangeType classification
    """
    content = line[1:].strip() if line.startswith(('+', '-')) else line.strip()
    
    # Empty or whitespace-only
    if not content:
        return ChangeType.FORMATTING
    
    # Comments
    if content.startswith('#') or content.startswith('//'):
        return ChangeType.COMMENT
    if content.startswith('/*') or content.startswith('*') or content.endswith('*/'):
        return ChangeType.COMMENT
    if content.startswith('"""') or content.startswith("'''"):
        return ChangeType.COMMENT
    
    # Imports
    if content.startswith('import ') or content.startswith('from '):
        return ChangeType.IMPORT
    if re.match(r'^(const|let|var)\s+\w+\s*=\s*require\(', content):
        return ChangeType.IMPORT
    
    # Security-related keywords
    security_keywords = ['password', 'secret', 'token', 'api_key', 'auth', 'credential']
    if any(kw in content.lower() for kw in security_keywords):
        return ChangeType.SECURITY
    
    # Test-related
    if 'test' in content.lower() or 'assert' in content.lower():
        return ChangeType.TEST
    
    # Default to unknown (will be refined by context)
    return ChangeType.UNKNOWN


def _classify_file(file_path: str) -> Tuple[bool, bool]:
    """
    Classify a file by its path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (is_high_significance, is_low_significance)
    """
    is_high = any(re.search(p, file_path) for p in HIGH_SIGNIFICANCE_PATTERNS)
    is_low = any(re.search(p, file_path) for p in LOW_SIGNIFICANCE_PATTERNS)
    
    # Test files are medium significance
    if '/test' in file_path or '_test.' in file_path or '.test.' in file_path:
        return False, False
    
    return is_high, is_low


def analyze_diff(diff_content: str) -> ChangesetAnalysis:
    """
    Analyze a unified diff to extract changeset information.
    
    Args:
        diff_content: Unified diff string
        
    Returns:
        ChangesetAnalysis with extracted information
    """
    analysis = ChangesetAnalysis()
    
    current_file = None
    
    for line in diff_content.split('\n'):
        # File header
        if line.startswith('diff --git'):
            match = re.search(r'b/(.+)$', line)
            if match:
                current_file = match.group(1)
                analysis.files.append(current_file)
                
                is_high, is_low = _classify_file(current_file)
                if is_high:
                    analysis.high_significance_files.append(current_file)
                elif is_low:
                    analysis.low_significance_files.append(current_file)
        
        # Added lines
        elif line.startswith('+') and not line.startswith('+++'):
            analysis.lines_added += 1
            change_type = _classify_line_change(line)
            analysis.change_types[change_type] = analysis.change_types.get(change_type, 0) + 1
        
        # Removed lines
        elif line.startswith('-') and not line.startswith('---'):
            analysis.lines_removed += 1
            change_type = _classify_line_change(line)
            analysis.change_types[change_type] = analysis.change_types.get(change_type, 0) + 1
    
    return analysis


def calculate_significance_score(
    analysis: ChangesetAnalysis,
    goal: Optional[str] = None
) -> SignificanceResult:
    """
    Calculate the significance score for a changeset.
    
    Blueprint Alignment:
    - This function can be called by Flow Controller v3 for pre-PR validation
    - Integrates with Safety Governor v2 risk assessment
    
    Args:
        analysis: ChangesetAnalysis from analyze_diff()
        goal: Optional goal/task description for context
        
    Returns:
        SignificanceResult with score and recommendation
    """
    if not analysis.files:
        return SignificanceResult(
            score=0,
            should_create_pr=False,
            primary_change_type=ChangeType.UNKNOWN,
            reasoning="No files in changeset",
            downgrade_reason="empty_changeset"
        )
    
    # Calculate weighted score based on change types
    total_changes = sum(analysis.change_types.values())
    if total_changes == 0:
        return SignificanceResult(
            score=0,
            should_create_pr=False,
            primary_change_type=ChangeType.UNKNOWN,
            reasoning="No line changes detected",
            downgrade_reason="no_changes"
        )
    
    # Weighted average of change type scores
    weighted_sum = sum(
        CHANGE_TYPE_WEIGHTS[ct] * count 
        for ct, count in analysis.change_types.items()
    )
    base_score = weighted_sum / total_changes
    
    # Determine primary change type
    primary_type = max(analysis.change_types.keys(), key=lambda ct: analysis.change_types[ct])
    
    # Adjust score based on file significance
    file_multiplier = 1.0
    if analysis.high_significance_files:
        file_multiplier += 0.2 * min(len(analysis.high_significance_files), 5)
    if analysis.low_significance_files and not analysis.high_significance_files:
        file_multiplier -= 0.3
    
    # Adjust score based on scope
    scope_multiplier = 1.0
    total_lines = analysis.lines_added + analysis.lines_removed
    if total_lines < 5:
        scope_multiplier = 0.5  # Very small changes
    elif total_lines < 20:
        scope_multiplier = 0.8  # Small changes
    elif total_lines > 500:
        scope_multiplier = 1.2  # Large changes
    
    # Calculate final score
    final_score = int(base_score * file_multiplier * scope_multiplier)
    final_score = max(0, min(100, final_score))  # Clamp to 0-100
    
    # Determine if PR should be created
    # Default threshold is 30 (configurable via VALUE_GATE_MIN_SCORE)
    try:
        from common.config.settings import settings
        min_score = getattr(settings, 'value_gate_min_score', 30) or 30
    except ImportError:
        min_score = 30
    
    should_create_pr = final_score >= min_score
    
    # Build reasoning
    high_sig_count = len(analysis.high_significance_files)
    low_sig_count = len(analysis.low_significance_files)
    reasoning_parts = [
        f"Primary change type: {primary_type.value} (weight: {CHANGE_TYPE_WEIGHTS[primary_type]})",
        f"Total changes: {total_changes} lines ({analysis.lines_added}+/{analysis.lines_removed}-)",
        f"Files: {len(analysis.files)} ({high_sig_count} high-sig, {low_sig_count} low-sig)",
        f"Base: {base_score:.1f}, File mult: {file_multiplier:.2f}, Scope mult: {scope_multiplier:.2f}",
        f"Final score: {final_score} (threshold: {min_score})"
    ]
    
    downgrade_reason = None
    if not should_create_pr:
        if primary_type == ChangeType.FORMATTING:
            downgrade_reason = "formatting_only"
        elif primary_type == ChangeType.COMMENT:
            downgrade_reason = "comment_only"
        elif total_lines < 5:
            downgrade_reason = "trivial_change"
        else:
            downgrade_reason = "low_significance"
    
    return SignificanceResult(
        score=final_score,
        should_create_pr=should_create_pr,
        primary_change_type=primary_type,
        change_type_breakdown=dict(analysis.change_types),
        files_analyzed=len(analysis.files),
        lines_added=analysis.lines_added,
        lines_removed=analysis.lines_removed,
        high_significance_files=analysis.high_significance_files,
        low_significance_files=analysis.low_significance_files,
        reasoning="; ".join(reasoning_parts),
        downgrade_reason=downgrade_reason
    )


def check_value_gate(
    diff_content: str,
    goal: Optional[str] = None,
    trace_id: Optional[str] = None
) -> SignificanceResult:
    """
    Main entry point for Value Gate check.
    
    Blueprint Alignment:
    - Flow Controller v3: Called before PR creation in Publisher Node
    - Safety Governor v2: Part of the governance layer
    - Telemetry v2: Logs all decisions for traceability
    
    Args:
        diff_content: Unified diff string
        goal: Optional goal/task description
        trace_id: Optional trace ID for logging
        
    Returns:
        SignificanceResult with decision
    """
    # Check if Value Gate is enabled
    try:
        from common.config.settings import settings
        enabled = getattr(settings, 'enable_value_gate', True)
        dry_run = getattr(settings, 'value_gate_dry_run', True)
    except ImportError:
        enabled = True
        dry_run = True
    
    if not enabled:
        logger.info("[ValueGate] Feature disabled, allowing PR creation", extra={
            "operation": "value_gate",
            "trace_id": trace_id,
            "enabled": False
        })
        return SignificanceResult(
            score=100,
            should_create_pr=True,
            primary_change_type=ChangeType.UNKNOWN,
            reasoning="Value Gate disabled"
        )
    
    # Analyze the diff
    analysis = analyze_diff(diff_content)
    result = calculate_significance_score(analysis, goal)
    
    # Log the decision
    log_extra = {
        "operation": "value_gate",
        "trace_id": trace_id,
        "score": result.score,
        "should_create_pr": result.should_create_pr,
        "primary_change_type": result.primary_change_type.value,
        "files_analyzed": result.files_analyzed,
        "lines_added": result.lines_added,
        "lines_removed": result.lines_removed,
        "dry_run": dry_run,
        "downgrade_reason": result.downgrade_reason
    }
    
    if result.should_create_pr:
        logger.info("[ValueGate] PR creation approved", extra=log_extra)
    else:
        if dry_run:
            logger.warning(
                "[ValueGate][DRY-RUN] Would downgrade to log-only",
                extra=log_extra
            )
            # In dry-run mode, still allow PR creation
            result.should_create_pr = True
            result.reasoning += " [DRY-RUN: Would have blocked]"
        else:
            logger.warning(
                "[ValueGate] PR creation blocked - downgrading to log-only",
                extra=log_extra
            )
    
    return result


def get_changeset_hash(diff_content: str) -> str:
    """
    Generate a hash of the changeset for deduplication.
    
    Args:
        diff_content: Unified diff string
        
    Returns:
        MD5 hash of the normalized diff
    """
    # Normalize the diff (remove timestamps, line numbers that might vary)
    normalized = re.sub(r'@@ -\d+,\d+ \+\d+,\d+ @@', '@@', diff_content)
    normalized = re.sub(r'index [a-f0-9]+\.\.[a-f0-9]+', 'index', normalized)
    
    return hashlib.md5(normalized.encode()).hexdigest()
