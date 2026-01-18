"""
Shared Types for Governance and Review Context Modules

Issue #4074: Extract shared specialist types to common module

This module provides shared enums and types used across:
- governance/specialist_trust_score.py (SpecialistTrustScoreTracker)
- review_context/multi_specialist_reviewer.py (MultiSpecialistReviewer)

Blueprint Alignment: Section 7 (Adversarial Collaboration)
- Maintains clean architecture for the E+F+I closed-loop system
- Single source of truth for specialist type definitions
"""

from enum import Enum


class SpecialistType(str, Enum):
    """
    Specialist types for multi-specialist review and trust score tracking.

    Each specialist focuses on specific aspects of code review:
    - SECURITY: Vulnerabilities, injection attacks, auth issues
    - PERFORMANCE: Inefficiencies, memory leaks, N+1 queries
    - ARCHITECTURE: Design patterns, SOLID principles, coupling
    - CORRECTNESS: Logic errors, edge cases, return value correctness (B-17)
    - SELF_CRITIQUE: Verifies findings from other specialists (B-16)

    Blueprint Reference: Section 7 (Parallel Collaboration)
    """
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    CORRECTNESS = "correctness"
    SELF_CRITIQUE = "self_critique"


class FeedbackType(str, Enum):
    """
    Types of feedback for specialist suggestions.

    Used by SpecialistTrustScoreTracker to track accuracy.
    """
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIAL = "partial"  # Partially accepted


# Alias for backward compatibility
# review_context uses ReviewSpecialist, governance uses SpecialistType
ReviewSpecialist = SpecialistType


# Core specialists (excluding SELF_CRITIQUE which is a meta-specialist)
# B-17: Added CORRECTNESS specialist for logic error detection
CORE_SPECIALISTS = [
    SpecialistType.SECURITY,
    SpecialistType.PERFORMANCE,
    SpecialistType.ARCHITECTURE,
    SpecialistType.CORRECTNESS,
]
