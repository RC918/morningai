"""
Review Context Module - EPIC B Phase 7-8 and B-13 Implementation

This module provides enhanced review capabilities for the MorningAI Reviewer Agent:

- B-9: Multi-Specialist Review (Parallel Collaboration)
- B-9.6: Comment Validator (False Positive Detection)
- B-11: Test Coverage Flagging
- B-12: Dependency Analysis
- B-13: Real-time Feedback Loop (Memory v2 Integration)

All capabilities respect the Blueprint Agent Separation Principle (Section 3.3):
- Reviewer Agent can FLAG issues and SUGGEST actions
- Reviewer Agent CANNOT generate code or apply fixes
"""

from review_context.multi_specialist_reviewer import (
    MultiSpecialistReviewer,
    ReviewSpecialist,
    SpecialistFindings,
    generate_multi_specialist_review,
    review_with_specialists,
)
from review_context.comment_validator import (
    CommentValidator,
    ValidationResult,
    ValidationStats,
    validate_review_comments,
)
from review_context.test_coverage_analyzer import (
    TestCoverageAnalyzer,
    CoverageGap,
    TestCoverageAnalysis,
    analyze_test_coverage,
)
from review_context.dependency_analyzer import (
    DependencyAnalyzer,
    DependencyIssue,
    DependencyIssueType,
    DependencyAnalysis,
    analyze_dependencies,
)
from review_context.review_feedback_loop import (
    ReviewFeedbackLoop,
    ReviewPattern,
    FeedbackLoopStats,
    get_feedback_loop,
)

__all__ = [
    # B-9: Multi-Specialist Review
    "MultiSpecialistReviewer",
    "ReviewSpecialist",
    "SpecialistFindings",
    "generate_multi_specialist_review",
    "review_with_specialists",
    # B-9.6: Comment Validator
    "CommentValidator",
    "ValidationResult",
    "ValidationStats",
    "validate_review_comments",
    # B-11: Test Coverage Flagging
    "TestCoverageAnalyzer",
    "CoverageGap",
    "TestCoverageAnalysis",
    "analyze_test_coverage",
    # B-12: Dependency Analysis
    "DependencyAnalyzer",
    "DependencyIssue",
    "DependencyIssueType",
    "DependencyAnalysis",
    "analyze_dependencies",
    # B-13: Real-time Feedback Loop
    "ReviewFeedbackLoop",
    "ReviewPattern",
    "FeedbackLoopStats",
    "get_feedback_loop",
]
