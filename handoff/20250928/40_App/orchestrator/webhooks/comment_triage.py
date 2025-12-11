"""
Comment Triage Agent - AI Reviewer Comment Classification and Risk Assessment

This module provides intelligent triage of AI reviewer comments, classifying them
by type, assessing risk levels, and determining if they should be auto-fixed.

Issue: #2210 - Comment Triage Agent 設計與實作
Milestone: Phase 7 - 生態系閉環 (AI Review Closed Loop)

Flow:
    WebhookEvent (with is_ai_reviewer=True) → CommentTriageAgent → CommentTriageResult
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .bot_protocol import WebhookEvent

logger = logging.getLogger(__name__)


class CommentCategory(Enum):
    """Categories for AI reviewer comments"""
    BUG_FIX = "bug_fix"
    STYLE = "style"
    REFACTOR = "refactor"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """Risk levels for comment-suggested changes"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CommentTriageResult:
    """
    Result of triaging an AI reviewer comment.

    This represents the output of the Comment Triage Agent, providing
    classification, risk assessment, and auto-fix recommendations.

    Issue: #2210 - Comment Triage Agent 設計與實作
    """
    comment_id: str
    source: str  # "codex", "gemini", "coderabbit", etc.
    category: CommentCategory
    risk_level: RiskLevel
    files_affected: List[str] = field(default_factory=list)
    lines_affected: int = 0
    should_auto_fix: bool = False
    confidence: float = 0.0
    reason: str = ""
    keywords_matched: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "comment_id": self.comment_id,
            "source": self.source,
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "files_affected": self.files_affected,
            "lines_affected": self.lines_affected,
            "should_auto_fix": self.should_auto_fix,
            "confidence": self.confidence,
            "reason": self.reason,
            "keywords_matched": self.keywords_matched,
            "metadata": self.metadata,
        }


class CommentTriageAgent:
    """
    Agent for triaging AI reviewer comments.

    This agent analyzes comments from AI reviewers (Codex, Gemini, CodeRabbit, etc.)
    and provides:
    1. Category classification (bug_fix, style, refactor, security, performance)
    2. Risk level assessment (high, medium, low)
    3. File impact analysis
    4. Auto-fix recommendations

    Issue: #2210 - Comment Triage Agent 設計與實作
    """

    # Keywords for category classification
    # Each category has a list of (keyword, weight) tuples
    CATEGORY_KEYWORDS: Dict[CommentCategory, List[Tuple[str, float]]] = {
        CommentCategory.BUG_FIX: [
            ("bug", 1.0),
            ("fix", 0.8),
            ("error", 0.9),
            ("crash", 1.0),
            ("exception", 0.9),
            ("null pointer", 1.0),
            ("undefined", 0.8),
            ("incorrect", 0.7),
            ("wrong", 0.7),
            ("broken", 0.9),
            ("fails", 0.8),
            ("doesn't work", 0.9),
            ("not working", 0.9),
            ("issue", 0.5),
            ("problem", 0.6),
            ("race condition", 1.0),
            ("deadlock", 1.0),
            ("memory leak", 1.0),
            ("off-by-one", 0.9),
            ("boundary", 0.7),
        ],
        CommentCategory.STYLE: [
            ("style", 0.9),
            ("formatting", 0.9),
            ("naming", 0.8),
            ("convention", 0.8),
            ("indentation", 0.9),
            ("whitespace", 0.8),
            ("lint", 0.7),
            ("pep8", 0.9),
            ("eslint", 0.9),
            ("prettier", 0.9),
            ("camelcase", 0.8),
            ("snake_case", 0.8),
            ("consistent", 0.5),
            ("readability", 0.6),
            ("nitpick", 0.9),
            ("nit:", 0.9),
        ],
        CommentCategory.REFACTOR: [
            ("refactor", 1.0),
            ("restructure", 0.9),
            ("simplify", 0.8),
            ("extract", 0.7),
            ("decompose", 0.8),
            ("modularize", 0.8),
            ("abstract", 0.6),
            ("generalize", 0.7),
            ("dry", 0.8),
            ("duplication", 0.8),
            ("duplicate code", 0.9),
            ("code smell", 0.8),
            ("complexity", 0.7),
            ("maintainability", 0.7),
            ("clean up", 0.7),
            ("cleanup", 0.7),
            ("technical debt", 0.8),
        ],
        CommentCategory.SECURITY: [
            ("security", 1.0),
            ("vulnerability", 1.0),
            ("injection", 1.0),
            ("sql injection", 1.0),
            ("xss", 1.0),
            ("cross-site", 1.0),
            ("csrf", 1.0),
            ("authentication", 0.8),
            ("authorization", 0.8),
            ("permission", 0.7),
            ("access control", 0.9),
            ("sensitive", 0.7),
            ("credential", 0.9),
            ("password", 0.8),
            ("secret", 0.9),
            ("token", 0.6),
            ("encryption", 0.8),
            ("sanitize", 0.9),
            ("escape", 0.7),
            ("validate input", 0.9),
            ("untrusted", 0.9),
            ("unsafe", 0.9),
        ],
        CommentCategory.PERFORMANCE: [
            ("performance", 1.0),
            ("optimize", 0.9),
            ("optimization", 0.9),
            ("slow", 0.8),
            ("fast", 0.5),
            ("efficient", 0.7),
            ("inefficient", 0.9),
            ("memory", 0.6),
            ("cpu", 0.7),
            ("latency", 0.8),
            ("throughput", 0.8),
            ("cache", 0.6),
            ("caching", 0.7),
            ("n+1", 0.9),
            ("query", 0.5),
            ("index", 0.5),
            ("bottleneck", 0.9),
            ("scalability", 0.8),
            ("complexity", 0.5),
            ("o(n)", 0.7),
            ("time complexity", 0.9),
            ("space complexity", 0.9),
        ],
        CommentCategory.DOCUMENTATION: [
            ("documentation", 1.0),
            ("document", 0.7),
            ("comment", 0.6),
            ("docstring", 0.9),
            ("jsdoc", 0.9),
            ("readme", 0.9),
            ("explain", 0.5),
            ("clarify", 0.6),
            ("describe", 0.5),
            ("missing doc", 0.9),
            ("undocumented", 0.9),
            ("type hint", 0.7),
            ("annotation", 0.6),
        ],
    }

    # Keywords that indicate high risk
    HIGH_RISK_KEYWORDS = [
        "security", "vulnerability", "injection", "authentication",
        "authorization", "credential", "password", "secret", "token",
        "production", "database", "migration", "delete", "drop",
        "critical", "urgent", "breaking change", "api change",
    ]

    # Keywords that indicate low risk
    LOW_RISK_KEYWORDS = [
        "style", "formatting", "naming", "whitespace", "indentation",
        "nitpick", "nit:", "minor", "cosmetic", "typo", "spelling",
        "comment", "documentation", "docstring",
    ]

    # File patterns that indicate higher risk
    HIGH_RISK_FILE_PATTERNS = [
        r"auth", r"security", r"credential", r"password", r"secret",
        r"config", r"settings", r"env", r"migration", r"schema",
        r"database", r"db", r"model", r"api", r"route",
    ]

    # File patterns that indicate lower risk
    LOW_RISK_FILE_PATTERNS = [
        r"test", r"spec", r"mock", r"fixture", r"readme",
        r"\.md$", r"\.txt$", r"\.json$", r"\.yaml$", r"\.yml$",
    ]

    def __init__(self):
        """Initialize the Comment Triage Agent"""
        logger.info("[CommentTriageAgent] Initialized")

    def triage(self, event: WebhookEvent) -> Optional[CommentTriageResult]:
        """
        Triage an AI reviewer comment event.

        Args:
            event: WebhookEvent with is_ai_reviewer=True in metadata

        Returns:
            CommentTriageResult with classification and recommendations,
            or None if the event is not from an AI reviewer
        """
        # Verify this is an AI reviewer event
        if not event.metadata.get("is_ai_reviewer"):
            logger.debug(
                "[CommentTriageAgent] Event %s is not from AI reviewer, skipping",
                event.event_id,
            )
            return None

        # Extract comment text
        comment_text = self._extract_comment_text(event)
        if not comment_text:
            logger.warning(
                "[CommentTriageAgent] No comment text found in event %s",
                event.event_id,
            )
            return None

        # Get review source
        source = event.metadata.get("review_source", "unknown")

        # Classify the comment
        category, category_confidence, matched_keywords = self._classify_comment(
            comment_text
        )

        # Extract affected files
        files_affected = self._extract_affected_files(event, comment_text)

        # Estimate lines affected
        lines_affected = self._estimate_lines_affected(event, comment_text)

        # Assess risk level
        risk_level = self._assess_risk(
            comment_text, category, files_affected
        )

        # Determine if auto-fix is appropriate
        should_auto_fix, auto_fix_reason = self._should_auto_fix(
            category, risk_level, files_affected, lines_affected, category_confidence
        )

        # Calculate overall confidence
        confidence = self._calculate_confidence(
            category_confidence, len(matched_keywords), len(files_affected)
        )

        # Generate reason
        reason = self._generate_reason(
            category, risk_level, should_auto_fix, auto_fix_reason, matched_keywords
        )

        # Extract repo and PR info for observability
        repo = f"{event.repo_owner}/{event.repo_name}" if event.repo_owner and event.repo_name else "unknown"
        pr_number = event.resource_id or "unknown"

        # Create result
        result = CommentTriageResult(
            comment_id=event.event_id,
            source=source,
            category=category,
            risk_level=risk_level,
            files_affected=files_affected,
            lines_affected=lines_affected,
            should_auto_fix=should_auto_fix,
            confidence=confidence,
            reason=reason,
            keywords_matched=matched_keywords,
            metadata={
                "event_type": event.event_type.value,
                "actor": event.actor_name,
                "url": event.url,
            },
        )

        # Issue: #2248 - Structured logging for comment triage category distribution
        # Log triage results for category distribution monitoring and weight adjustment
        logger.info(
            "[CommentTriageAgent] Comment triage completed",
            extra={
                "operation": "comment_triage_result",
                "comment_id": event.event_id,
                "bot_name": source,
                "repo": repo,
                "pr_number": pr_number,
                "category": category.value,
                "risk_level": risk_level.value,
                "confidence": round(confidence, 3),
                "should_auto_fix": should_auto_fix,
                "keywords_matched": matched_keywords,
                "files_affected_count": len(files_affected),
                "lines_affected": lines_affected,
            }
        )

        return result

    def _extract_comment_text(self, event: WebhookEvent) -> str:
        """Extract the comment text from the event"""
        # Try description first (usually contains the comment body)
        if event.description:
            return event.description

        # Try title as fallback
        if event.title:
            return event.title

        # Try raw payload for comment body
        raw = event.raw_payload
        if "comment" in raw and "body" in raw["comment"]:
            return raw["comment"]["body"]
        if "review" in raw and "body" in raw["review"]:
            return raw["review"]["body"]

        return ""

    def _classify_comment(
        self, text: str
    ) -> Tuple[CommentCategory, float, List[str]]:
        """
        Classify the comment into a category.

        Returns:
            Tuple of (category, confidence, matched_keywords)
        """
        text_lower = text.lower()
        category_scores: Dict[CommentCategory, float] = {}
        category_keywords: Dict[CommentCategory, List[str]] = {}

        # Calculate scores for each category
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0.0
            matched = []
            for keyword, weight in keywords:
                if keyword in text_lower:
                    score += weight
                    matched.append(keyword)
            category_scores[category] = score
            category_keywords[category] = matched

        # Find the category with highest score
        if not category_scores or max(category_scores.values()) == 0:
            return CommentCategory.UNKNOWN, 0.0, []

        best_category = max(category_scores, key=lambda k: category_scores[k])
        best_score = category_scores[best_category]
        matched_keywords = category_keywords[best_category]

        # Calculate confidence based on score and number of matches
        # Normalize score to 0-1 range (assuming max reasonable score is ~5)
        confidence = min(best_score / 5.0, 1.0)

        return best_category, confidence, matched_keywords

    def _extract_affected_files(
        self, event: WebhookEvent, comment_text: str
    ) -> List[str]:
        """Extract files that might be affected by the comment"""
        files = []

        # Check raw payload for file information
        raw = event.raw_payload

        # GitHub PR review comment includes path
        if "comment" in raw and "path" in raw["comment"]:
            files.append(raw["comment"]["path"])

        # GitHub PR review includes changed files
        if "pull_request" in raw:
            pr = raw["pull_request"]
            if "changed_files" in pr:
                # This is just a count, not actual files
                pass

        # Extract file paths mentioned in comment text
        # Look for common file path patterns
        file_patterns = [
            r'`([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)`',  # `path/to/file.ext`
            r'"([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)"',  # "path/to/file.ext"
            r"'([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)'",  # 'path/to/file.ext'
            r'\b([a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)\b',  # path/file.ext
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, comment_text)
            files.extend(matches)

        # Deduplicate while preserving order (using dict.fromkeys for efficiency)
        return list(dict.fromkeys(files))

    def _estimate_lines_affected(
        self, event: WebhookEvent, comment_text: str
    ) -> int:
        """Estimate the number of lines affected by the suggested change"""
        # Check raw payload for line information
        raw = event.raw_payload

        # GitHub PR review comment includes line numbers
        if "comment" in raw:
            comment = raw["comment"]
            if "line" in comment:
                # Single line comment
                return 1
            if "start_line" in comment and "line" in comment:
                # Multi-line comment
                start = comment.get("start_line", 0)
                end = comment.get("line", 0)
                if start and end:
                    return max(1, end - start + 1)

        # Estimate based on comment content
        # Look for line number mentions
        line_mentions = re.findall(r'line[s]?\s*(\d+)(?:\s*-\s*(\d+))?', comment_text.lower())
        if line_mentions:
            total_lines = 0
            for match in line_mentions:
                start = int(match[0])
                end = int(match[1]) if match[1] else start
                total_lines += max(1, end - start + 1)
            return total_lines

        # Default estimate based on category
        # Style/formatting changes typically affect few lines
        # Refactoring might affect more
        return 5  # Default estimate

    def _assess_risk(
        self,
        comment_text: str,
        category: CommentCategory,
        files_affected: List[str],
    ) -> RiskLevel:
        """Assess the risk level of implementing the suggested change"""
        text_lower = comment_text.lower()

        # Check for high-risk keywords
        high_risk_score = sum(
            1 for keyword in self.HIGH_RISK_KEYWORDS
            if keyword in text_lower
        )

        # Check for low-risk keywords
        low_risk_score = sum(
            1 for keyword in self.LOW_RISK_KEYWORDS
            if keyword in text_lower
        )

        # Check file patterns for risk
        for file_path in files_affected:
            file_lower = file_path.lower()
            for pattern in self.HIGH_RISK_FILE_PATTERNS:
                if re.search(pattern, file_lower):
                    high_risk_score += 1
            for pattern in self.LOW_RISK_FILE_PATTERNS:
                if re.search(pattern, file_lower):
                    low_risk_score += 1

        # Category-based risk adjustment
        if category == CommentCategory.SECURITY:
            high_risk_score += 2
        elif category == CommentCategory.BUG_FIX:
            high_risk_score += 1
        elif category == CommentCategory.STYLE:
            low_risk_score += 2
        elif category == CommentCategory.DOCUMENTATION:
            low_risk_score += 2

        # Determine risk level
        if high_risk_score >= 2:
            return RiskLevel.HIGH
        elif low_risk_score >= 2 and high_risk_score == 0:
            return RiskLevel.LOW
        else:
            return RiskLevel.MEDIUM

    def _should_auto_fix(
        self,
        category: CommentCategory,
        risk_level: RiskLevel,
        files_affected: List[str],
        lines_affected: int,
        confidence: float,
    ) -> Tuple[bool, str]:
        """
        Determine if the suggested change should be auto-fixed.

        Returns:
            Tuple of (should_auto_fix, reason)
        """
        # Never auto-fix high-risk changes
        if risk_level == RiskLevel.HIGH:
            return False, "High risk changes require human review"

        # Never auto-fix security issues
        if category == CommentCategory.SECURITY:
            return False, "Security changes require human review"

        # Auto-fix style issues with high confidence
        if category == CommentCategory.STYLE and confidence >= 0.7:
            if lines_affected <= 10:
                return True, "Low-risk style fix with high confidence"
            return False, "Style fix affects too many lines"

        # Auto-fix documentation with high confidence
        if category == CommentCategory.DOCUMENTATION and confidence >= 0.7:
            return True, "Documentation update with high confidence"

        # Auto-fix low-risk bug fixes with very high confidence
        if category == CommentCategory.BUG_FIX:
            if risk_level == RiskLevel.LOW and confidence >= 0.85:
                if lines_affected <= 5:
                    return True, "Clear bug fix with limited scope"
            return False, "Bug fixes require careful review"

        # Auto-fix simple refactoring with high confidence
        if category == CommentCategory.REFACTOR:
            if risk_level == RiskLevel.LOW and confidence >= 0.8:
                if lines_affected <= 5 and len(files_affected) <= 1:
                    return True, "Simple refactoring with limited scope"
            return False, "Refactoring requires careful review"

        # Default: don't auto-fix
        return False, "Requires human review"

    def _calculate_confidence(
        self,
        category_confidence: float,
        num_keywords: int,
        num_files: int,
    ) -> float:
        """Calculate overall confidence score"""
        # Start with category confidence
        confidence = category_confidence

        # Boost confidence if multiple keywords matched
        if num_keywords >= 3:
            confidence = min(confidence + 0.1, 1.0)
        elif num_keywords >= 2:
            confidence = min(confidence + 0.05, 1.0)

        # Reduce confidence if no files identified
        if num_files == 0:
            confidence *= 0.9

        # Ensure confidence is in valid range
        return max(0.0, min(1.0, confidence))

    def _generate_reason(
        self,
        category: CommentCategory,
        risk_level: RiskLevel,
        should_auto_fix: bool,
        auto_fix_reason: str,
        keywords_matched: List[str],
    ) -> str:
        """Generate a human-readable reason for the triage result"""
        parts = []

        # Category description
        category_desc = {
            CommentCategory.BUG_FIX: "Bug fix suggestion",
            CommentCategory.STYLE: "Code style improvement",
            CommentCategory.REFACTOR: "Refactoring suggestion",
            CommentCategory.SECURITY: "Security concern",
            CommentCategory.PERFORMANCE: "Performance optimization",
            CommentCategory.DOCUMENTATION: "Documentation update",
            CommentCategory.UNKNOWN: "General comment",
        }
        parts.append(category_desc.get(category, "Comment"))

        # Risk level
        parts.append(f"with {risk_level.value} risk")

        # Keywords
        if keywords_matched:
            keywords_str = ", ".join(keywords_matched[:3])
            if len(keywords_matched) > 3:
                keywords_str += f" (+{len(keywords_matched) - 3} more)"
            parts.append(f"(keywords: {keywords_str})")

        # Auto-fix decision
        parts.append(f"- {auto_fix_reason}")

        return " ".join(parts)

    def batch_triage(
        self, events: List[WebhookEvent]
    ) -> List[CommentTriageResult]:
        """
        Triage multiple AI reviewer comment events.

        Args:
            events: List of WebhookEvents

        Returns:
            List of CommentTriageResults for AI reviewer events
        """
        results = []
        for event in events:
            result = self.triage(event)
            if result:
                results.append(result)

        logger.info(
            "[CommentTriageAgent] Batch triaged %d events, produced %d results",
            len(events),
            len(results),
        )

        return results
