"""
Safety and Compliance Simulation Scenarios

Blueprint Section 5.3: Safety/compliance testing

Scenarios for testing safety scanning and compliance checks.
"""

import logging
from typing import Any, Dict, List, Optional

from simulation.scenario import SafetyComplianceScenario

# Type aliases used in this module
_ScanResult = Dict[str, Any]  # noqa: F841

logger = logging.getLogger(__name__)


class ContentSafetyScenario(SafetyComplianceScenario):
    """
    Test content safety scanning.

    Verifies that:
    - Harmful content is detected and blocked
    - Safe content passes through
    - Risk levels are correctly assessed
    """

    name = "Content Safety Scan"
    description = "Test content safety scanner detects harmful content"
    tags = ["safety", "content", "scan"]

    def __init__(
        self,
        test_input: str,
        expected_blocked: bool = False,
        expected_risk_level: Optional[str] = None,
    ):
        super().__init__(test_input, expected_blocked)
        self.expected_risk_level = expected_risk_level
        self.actual_blocked: bool = False
        self.actual_risk_level: Optional[str] = None
        self.scan_result: Optional[Dict[str, Any]] = None

    def setup(self) -> None:
        """Initialize safety scanner."""
        super().setup()
        if self.expected_risk_level:
            self.add_metadata("expected_risk_level", self.expected_risk_level)

    def execute(self) -> None:
        """Execute safety scan."""
        # In real implementation, would call content_safety_scanner.scan()
        # For now, simulate based on keywords
        harmful_keywords = ["hack", "exploit", "malware", "attack"]

        input_lower = self.test_input.lower()
        has_harmful = any(kw in input_lower for kw in harmful_keywords)

        if has_harmful:
            self.actual_blocked = True
            self.actual_risk_level = "high"
        else:
            self.actual_blocked = False
            self.actual_risk_level = "low"

        self.scan_result = {
            "blocked": self.actual_blocked,
            "risk_level": self.actual_risk_level,
            "input_length": len(self.test_input),
        }

        logger.info(
            f"[ContentSafetyScenario] Scan result: blocked={self.actual_blocked}, "
            f"risk={self.actual_risk_level}",
            extra={"operation": "simulation.scenario"}
        )

    def validate(self) -> List[tuple]:
        """Validate safety scan results."""
        assertions = []

        # Check scan completed
        assertions.append((
            "Scan result is not None",
            self.scan_result is not None
        ))

        # Check blocked status matches expectation
        assertions.append((
            f"Blocked status is {self.expected_blocked}",
            self.actual_blocked == self.expected_blocked
        ))

        # Check risk level if specified
        if self.expected_risk_level:
            assertions.append((
                f"Risk level is {self.expected_risk_level}",
                self.actual_risk_level == self.expected_risk_level
            ))

        return assertions


class PIIScannerScenario(SafetyComplianceScenario):
    """
    Test PII (Personally Identifiable Information) scanning.

    Verifies that:
    - PII is detected in content
    - PII types are correctly identified
    - Redaction works correctly
    """

    name = "PII Scanner"
    description = "Test PII detection and redaction"
    tags = ["safety", "compliance", "pii"]

    def __init__(
        self,
        test_input: str,
        expected_pii_types: Optional[List[str]] = None,
        expected_pii_count: int = 0,
    ):
        super().__init__(test_input, expected_blocked=expected_pii_count > 0)
        self.expected_pii_types = expected_pii_types or []
        self.expected_pii_count = expected_pii_count
        self.detected_pii: List[Dict[str, Any]] = []
        self.redacted_text: Optional[str] = None

    def setup(self) -> None:
        """Initialize PII scanner."""
        super().setup()
        self.add_metadata("expected_pii_count", self.expected_pii_count)
        if self.expected_pii_types:
            self.add_metadata("expected_pii_types", self.expected_pii_types)

    def execute(self) -> None:
        """Execute PII scan."""
        # In real implementation, would call pii_scanner.scan()
        # For now, simulate basic PII detection
        import re

        pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        }

        self.detected_pii = []
        self.redacted_text = self.test_input

        for pii_type, pattern in pii_patterns.items():
            matches = re.findall(pattern, self.test_input)
            for match in matches:
                self.detected_pii.append({
                    "type": pii_type,
                    "value": match,
                })
                # Redact the PII
                self.redacted_text = self.redacted_text.replace(
                    match, f"[REDACTED_{pii_type.upper()}]"
                )

        logger.info(
            f"[PIIScannerScenario] Detected {len(self.detected_pii)} PII items",
            extra={"operation": "simulation.scenario"}
        )

    def validate(self) -> List[tuple]:
        """Validate PII scan results."""
        assertions = []

        # Check PII count
        assertions.append((
            f"Detected {self.expected_pii_count} PII items",
            len(self.detected_pii) == self.expected_pii_count
        ))

        # Check PII types if specified
        if self.expected_pii_types:
            detected_types = {p["type"] for p in self.detected_pii}
            for pii_type in self.expected_pii_types:
                assertions.append((
                    f"Detected PII type: {pii_type}",
                    pii_type in detected_types
                ))

        # Check redaction worked
        if self.expected_pii_count > 0:
            assertions.append((
                "Redacted text differs from original",
                self.redacted_text != self.test_input
            ))
            assertions.append((
                "Redacted text contains [REDACTED_",
                "[REDACTED_" in (self.redacted_text or "")
            ))

        return assertions
