"""
Review Context Module - EPIC B Phase 7-8 Implementation

This module provides enhanced review capabilities for the MorningAI Reviewer Agent:

- B-9: Multi-Specialist Review (Parallel Collaboration)
- B-11: Test Coverage Flagging
- B-12: Dependency Analysis

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

__all__ = [
    # B-9: Multi-Specialist Review
    "MultiSpecialistReviewer",
    "ReviewSpecialist",
    "SpecialistFindings",
    "generate_multi_specialist_review",
    "review_with_specialists",
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
]
