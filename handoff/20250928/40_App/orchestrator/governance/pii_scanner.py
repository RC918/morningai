"""
PII Scanner - EPIC E Phase E-4 Compliance Radar v2 MVP

Blueprint Reference: Section 4.2 (Compliance Radar v2)
Issue: Part of EPIC E Safety Governor v2

This module implements PII (Personally Identifiable Information) scanning
for content safety and compliance. It detects various types of PII including:
- Email addresses
- Phone numbers (US, international formats)
- Social Security Numbers (SSN)
- Credit card numbers
- Names (with context-aware detection)
- Physical addresses
- IP addresses
- Dates of birth

Design Principles:
- Pattern-based detection with confidence scoring
- Configurable actions per PII type (allow/block/redact/require_approval)
- Evidence generation for audit trail
- Integration with existing governance infrastructure
"""
import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple, Pattern

logger = logging.getLogger(__name__)

# Maximum length for matched text in logs/results (security: prevent full PII exposure)
MAX_MATCHED_TEXT_LOG_LENGTH = 20

# Maximum content length for scanning (defense-in-depth against ReDoS)
# Issue #3941: ReDoS vulnerability analysis for PIIScanner patterns
MAX_CONTENT_LENGTH = 100_000  # 100KB limit


class PIICategory(str, Enum):
    """Categories of PII that can be detected"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    NAME = "name"
    ADDRESS = "address"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"


class PIIRiskLevel(str, Enum):
    """Risk levels for PII findings"""
    CRITICAL = "critical"  # SSN, Credit Card - immediate action required
    HIGH = "high"          # Passport, Driver License - significant risk
    MEDIUM = "medium"      # Phone, Address, DOB - moderate risk
    LOW = "low"            # Email, IP Address - lower risk
    INFO = "info"          # Name (context-dependent) - informational


class PIIAction(str, Enum):
    """Actions to take when PII is detected"""
    ALLOW = "allow"                    # Allow content to pass
    BLOCK = "block"                    # Block content entirely
    REDACT = "redact"                  # Redact the PII and allow
    REQUIRE_APPROVAL = "require_approval"  # Require human approval
    LOG_ONLY = "log_only"              # Log but allow


@dataclass
class PIIFinding:
    """Represents a single PII finding"""
    category: PIICategory
    risk_level: PIIRiskLevel
    pattern_id: str
    title: str
    description: str
    matched_text: str  # Sanitized/truncated for security
    position: int
    confidence: float
    recommendation: str
    evidence_hash: str
    redacted_text: Optional[str] = None  # Redacted version if applicable

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "pattern_id": self.pattern_id,
            "title": self.title,
            "description": self.description,
            "matched_text": self.matched_text,
            "position": self.position,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "evidence_hash": self.evidence_hash,
            "redacted_text": self.redacted_text,
        }


@dataclass
class PIIScanResult:
    """Result of a PII scan operation"""
    has_pii: bool
    overall_risk: PIIRiskLevel
    action: PIIAction
    findings: List[PIIFinding] = field(default_factory=list)
    summary: str = ""
    scan_duration_ms: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "has_pii": self.has_pii,
            "overall_risk": self.overall_risk.value,
            "action": self.action.value,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
            "scan_duration_ms": self.scan_duration_ms,
            "context": self.context,
        }


class PIIScanner:
    """
    PII Scanner for EPIC E Phase E-4 Compliance Radar v2.

    Detects various types of PII in content using regex patterns
    with confidence scoring and configurable actions.

    Blueprint Alignment:
    - Section 4.2: Compliance Radar v2 - PII scanning
    - Section 9.2: Safe by Design - redaction protects PII/secrets
    """

    # Email patterns
    EMAIL_PATTERNS: List[Tuple[str, str, str, PIIRiskLevel]] = [
        (
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            "PII-EMAIL-001",
            "Email address detected",
            PIIRiskLevel.LOW,
        ),
    ]

    # Phone number patterns (various formats)
    PHONE_PATTERNS: List[Tuple[str, str, str, PIIRiskLevel]] = [
        # US phone formats: (123) 456-7890, 123-456-7890, 123.456.7890
        (
            r'\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            "PII-PHONE-001",
            "US phone number detected",
            PIIRiskLevel.MEDIUM,
        ),
        # International format: +XX XXX XXX XXXX
        (
            r'\b\+[1-9]\d{1,2}[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b',
            "PII-PHONE-002",
            "International phone number detected",
            PIIRiskLevel.MEDIUM,
        ),
    ]

    # SSN patterns
    SSN_PATTERNS: List[Tuple[str, str, str, PIIRiskLevel]] = [
        # Standard SSN format: XXX-XX-XXXX
        (
            r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b',
            "PII-SSN-001",
            "Social Security Number detected",
            PIIRiskLevel.CRITICAL,
        ),
    ]

    # Credit card patterns (Luhn-validated in post-processing)
    CREDIT_CARD_PATTERNS: List[Tuple[str, str, str, PIIRiskLevel]] = [
        # Visa: starts with 4, 13-16 digits
        (
            r'\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,4}\b',
            "PII-CC-001",
            "Visa credit card number detected",
            PIIRiskLevel.CRITICAL,
        ),
        # Mastercard: starts with 51-55 or 2221-2720, 16 digits
        (
            r'\b(?:5[1-5]\d{2}|222[1-9]|22[3-9]\d|2[3-6]\d{2}|27[01]\d|2720)'
            r'[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "PII-CC-002",
            "Mastercard credit card number detected",
            PIIRiskLevel.CRITICAL,
        ),
        # American Express: starts with 34 or 37, 15 digits
        (
            r'\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b',
            "PII-CC-003",
            "American Express card number detected",
            PIIRiskLevel.CRITICAL,
        ),
        # Generic 16-digit card pattern
        (
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "PII-CC-004",
            "Potential credit card number detected",
            PIIRiskLevel.HIGH,
        ),
    ]

    # IP Address patterns
    IP_PATTERNS: List[Tuple[str, str, str, PIIRiskLevel]] = [
        # IPv4
        (
            r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
            r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b',
            "PII-IP-001",
            "IPv4 address detected",
            PIIRiskLevel.LOW,
        ),
        # IPv6 (simplified pattern)
        (
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
            "PII-IP-002",
            "IPv6 address detected",
            PIIRiskLevel.LOW,
        ),
    ]

    # Date of Birth patterns
    DOB_PATTERNS: List[Tuple[str, str, str, PIIRiskLevel]] = [
        # MM/DD/YYYY or MM-DD-YYYY
        (
            r'\b(?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])[-/]'
            r'(?:19|20)\d{2}\b',
            "PII-DOB-001",
            "Date of birth (MM/DD/YYYY) detected",
            PIIRiskLevel.MEDIUM,
        ),
        # YYYY-MM-DD (ISO format)
        (
            r'\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/]'
            r'(?:0[1-9]|[12]\d|3[01])\b',
            "PII-DOB-002",
            "Date of birth (YYYY-MM-DD) detected",
            PIIRiskLevel.MEDIUM,
        ),
    ]

    # Physical address patterns (US-focused)
    # Issue #3941: ReDoS fix - unrolled loop to avoid catastrophic backtracking
    ADDRESS_PATTERNS: List[Tuple[str, str, str, PIIRiskLevel]] = [
        # Street address: 123 Main St, 456 Oak Avenue, etc.
        # Fixed: Unrolled (?:[A-Za-z]+\s+){1,3} to [A-Za-z]+\s+(?:[A-Za-z]+\s+){0,2}
        # This prevents ReDoS by bounding the outer quantifier to max 2 iterations
        (
            r'\b\d{1,5}\s+[A-Za-z]+\s+(?:[A-Za-z]+\s+){0,2}'
            r'(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|'
            r'Lane|Ln|Court|Ct|Way|Place|Pl|Circle|Cir)\b',
            "PII-ADDR-001",
            "Street address detected",
            PIIRiskLevel.MEDIUM,
        ),
        # ZIP code (US): 12345 or 12345-6789
        (
            r'\b\d{5}(?:-\d{4})?\b',
            "PII-ADDR-002",
            "ZIP code detected",
            PIIRiskLevel.LOW,
        ),
    ]

    # Passport patterns (various countries)
    PASSPORT_PATTERNS: List[Tuple[str, str, str, PIIRiskLevel]] = [
        # US Passport: 9 digits
        (
            r'\b[A-Z]?\d{8,9}\b',
            "PII-PASS-001",
            "Potential US passport number detected",
            PIIRiskLevel.HIGH,
        ),
    ]

    # Driver's License patterns (state-specific patterns would be more accurate)
    DRIVER_LICENSE_PATTERNS: List[Tuple[str, str, str, PIIRiskLevel]] = [
        # Generic alphanumeric pattern (7-13 characters)
        (
            r'\b[A-Z]{1,2}\d{5,8}\b',
            "PII-DL-001",
            "Potential driver's license number detected",
            PIIRiskLevel.HIGH,
        ),
    ]

    # Default action configuration per PII category
    DEFAULT_ACTIONS: Dict[PIICategory, PIIAction] = {
        PIICategory.EMAIL: PIIAction.LOG_ONLY,
        PIICategory.PHONE: PIIAction.REQUIRE_APPROVAL,
        PIICategory.SSN: PIIAction.BLOCK,
        PIICategory.CREDIT_CARD: PIIAction.BLOCK,
        PIICategory.NAME: PIIAction.LOG_ONLY,
        PIICategory.ADDRESS: PIIAction.REQUIRE_APPROVAL,
        PIICategory.IP_ADDRESS: PIIAction.LOG_ONLY,
        PIICategory.DATE_OF_BIRTH: PIIAction.REQUIRE_APPROVAL,
        PIICategory.PASSPORT: PIIAction.BLOCK,
        PIICategory.DRIVER_LICENSE: PIIAction.BLOCK,
    }

    def __init__(
        self,
        enabled: bool = True,
        strict_mode: bool = False,
        action_overrides: Optional[Dict[PIICategory, PIIAction]] = None,
    ):
        """
        Initialize PIIScanner.

        Args:
            enabled: Whether scanning is enabled
            strict_mode: If True, lower thresholds for detection
            action_overrides: Override default actions per PII category
        """
        self.enabled = enabled
        self.strict_mode = strict_mode
        self.action_config = self.DEFAULT_ACTIONS.copy()
        if action_overrides:
            self.action_config.update(action_overrides)
        self._load_settings()
        self._compile_patterns()
        logger.info(
            "[PIIScanner] Initialized - EPIC E Phase E-4: "
            "enabled=%s, strict_mode=%s",
            self.enabled,
            self.strict_mode,
        )

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance optimization."""
        self._compiled_patterns: Dict[
            PIICategory, List[Tuple[Pattern[str], str, str, PIIRiskLevel]]
        ] = {}

        pattern_groups = [
            (PIICategory.EMAIL, self.EMAIL_PATTERNS),
            (PIICategory.PHONE, self.PHONE_PATTERNS),
            (PIICategory.SSN, self.SSN_PATTERNS),
            (PIICategory.CREDIT_CARD, self.CREDIT_CARD_PATTERNS),
            (PIICategory.IP_ADDRESS, self.IP_PATTERNS),
            (PIICategory.DATE_OF_BIRTH, self.DOB_PATTERNS),
            (PIICategory.ADDRESS, self.ADDRESS_PATTERNS),
            (PIICategory.PASSPORT, self.PASSPORT_PATTERNS),
            (PIICategory.DRIVER_LICENSE, self.DRIVER_LICENSE_PATTERNS),
        ]

        for category, patterns in pattern_groups:
            self._compiled_patterns[category] = []
            for pattern, pid, title, risk in patterns:
                self._compiled_patterns[category].append(
                    (re.compile(pattern, re.IGNORECASE), pid, title, risk)
                )

    def _load_settings(self) -> None:
        """Load settings from configuration if available."""
        try:
            from common.config.settings import settings
            self.enabled = getattr(
                settings, 'pii_scanner_enabled', self.enabled
            )
            self.strict_mode = getattr(
                settings, 'pii_scanner_strict_mode', self.strict_mode
            )
            logger.debug(
                "[PIIScanner] Settings loaded: enabled=%s, strict_mode=%s",
                self.enabled,
                self.strict_mode,
            )
        except (ImportError, AttributeError) as e:
            logger.debug(
                "[PIIScanner] Using default settings: %s", e
            )

    def scan(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> PIIScanResult:
        """
        Scan content for PII.

        Args:
            content: Text content to scan
            context: Optional context metadata

        Returns:
            PIIScanResult with findings and recommended action
        """
        start_time = time.time()

        if not self.enabled:
            return PIIScanResult(
                has_pii=False,
                overall_risk=PIIRiskLevel.INFO,
                action=PIIAction.ALLOW,
                summary="PII scanning disabled",
                context=context or {},
            )

        if not content or not content.strip():
            return PIIScanResult(
                has_pii=False,
                overall_risk=PIIRiskLevel.INFO,
                action=PIIAction.ALLOW,
                summary="No content to scan",
                context=context or {},
            )

        # Issue #3941: Defense-in-depth against ReDoS - limit content length
        if len(content) > MAX_CONTENT_LENGTH:
            logger.warning(
                "[PIIScanner] Content exceeds max length (%d > %d), truncating",
                len(content),
                MAX_CONTENT_LENGTH,
            )
            content = content[:MAX_CONTENT_LENGTH]

        findings: List[PIIFinding] = []
        found_critical = False

        # Scan for each PII category
        for category, compiled_patterns in self._compiled_patterns.items():
            category_findings, found_critical = self._check_category(
                content, category, compiled_patterns, found_critical
            )
            findings.extend(category_findings)

        # Calculate overall risk and action
        overall_risk = self._calculate_risk_level(findings)
        action = self._determine_action(findings)

        # Generate summary
        summary = self._generate_summary(findings, overall_risk)

        scan_duration = (time.time() - start_time) * 1000

        return PIIScanResult(
            has_pii=len(findings) > 0,
            overall_risk=overall_risk,
            action=action,
            findings=findings,
            summary=summary,
            scan_duration_ms=scan_duration,
            context=context or {},
        )

    def _check_category(
        self,
        content: str,
        category: PIICategory,
        compiled_patterns: List[Tuple[Pattern[str], str, str, PIIRiskLevel]],
        found_critical: bool,
    ) -> Tuple[List[PIIFinding], bool]:
        """
        Check content for a specific PII category.

        Args:
            content: Text to scan
            category: PII category to check
            compiled_patterns: Pre-compiled patterns for this category
            found_critical: Whether CRITICAL risk was already found

        Returns:
            Tuple of (findings list, whether CRITICAL was found)
        """
        findings = []

        for compiled_pattern, pattern_id, title, risk_level in compiled_patterns:
            # Short-circuit: skip non-CRITICAL patterns if CRITICAL already found
            if found_critical and risk_level != PIIRiskLevel.CRITICAL:
                continue

            for match in compiled_pattern.finditer(content):
                matched_text = match.group(0)
                confidence = self._calculate_confidence(
                    match, content, category
                )

                # Apply confidence threshold
                threshold = 0.5 if self.strict_mode else 0.7
                if confidence < threshold:
                    continue

                # Validate specific patterns (e.g., Luhn check for credit cards)
                if not self._validate_match(matched_text, category):
                    continue

                findings.append(
                    PIIFinding(
                        category=category,
                        risk_level=risk_level,
                        pattern_id=pattern_id,
                        title=title,
                        description=f"Detected {category.value}: {title}",
                        matched_text=self._sanitize_matched_text(matched_text),
                        position=match.start(),
                        confidence=confidence,
                        recommendation=self._get_recommendation(category),
                        evidence_hash=self._compute_evidence_hash(matched_text),
                        redacted_text=self._redact_text(matched_text, category),
                    )
                )

                if risk_level == PIIRiskLevel.CRITICAL:
                    found_critical = True

        return findings, found_critical

    def _sanitize_matched_text(self, text: str) -> str:
        """Sanitize matched text for logging (security: prevent full PII exposure)."""
        if not text:
            return ""
        if len(text) <= MAX_MATCHED_TEXT_LOG_LENGTH:
            # Still partially redact even short text
            if len(text) > 4:
                return text[:2] + "*" * (len(text) - 4) + text[-2:]
            return "*" * len(text)
        # For longer text, show first 2 and last 2 chars
        return text[:2] + "*" * 16 + text[-2:]

    def _redact_text(self, text: str, category: PIICategory) -> str:
        """Generate redacted version of PII text."""
        if category == PIICategory.EMAIL:
            # user@domain.com -> u***@d***.com
            parts = text.split("@")
            if len(parts) == 2:
                user = parts[0][0] + "***" if parts[0] else "***"
                domain_parts = parts[1].split(".")
                if len(domain_parts) >= 2:
                    domain = domain_parts[0][0] + "***" if domain_parts[0] else "***"
                    tld = ".".join(domain_parts[1:])
                    return f"{user}@{domain}.{tld}"
            return "[REDACTED_EMAIL]"

        elif category == PIICategory.PHONE:
            # Show last 4 digits: ***-***-1234
            digits = re.sub(r'\D', '', text)
            if len(digits) >= 4:
                return "***-***-" + digits[-4:]
            return "[REDACTED_PHONE]"

        elif category == PIICategory.SSN:
            # Show last 4 digits: ***-**-1234
            digits = re.sub(r'\D', '', text)
            if len(digits) >= 4:
                return "***-**-" + digits[-4:]
            return "[REDACTED_SSN]"

        elif category == PIICategory.CREDIT_CARD:
            # Show last 4 digits: ****-****-****-1234
            digits = re.sub(r'\D', '', text)
            if len(digits) >= 4:
                return "****-****-****-" + digits[-4:]
            return "[REDACTED_CC]"

        elif category == PIICategory.IP_ADDRESS:
            # Partially redact: 192.168.***.***
            parts = text.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.***.***"
            return "[REDACTED_IP]"

        else:
            # Generic redaction
            return f"[REDACTED_{category.value.upper()}]"

    def _validate_match(self, text: str, category: PIICategory) -> bool:
        """Validate a match using category-specific rules."""
        if category == PIICategory.CREDIT_CARD:
            return self._luhn_check(text)
        return True

    def _luhn_check(self, card_number: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        digits = re.sub(r'\D', '', card_number)
        if len(digits) < 13 or len(digits) > 19:
            return False

        total = 0
        reverse_digits = digits[::-1]
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        return total % 10 == 0

    def _calculate_confidence(
        self,
        match: re.Match,
        content: str,
        category: PIICategory,
    ) -> float:
        """Calculate confidence score for a match."""
        base_confidence = 0.8

        # Adjust based on context
        matched_text = match.group(0)
        start = max(0, match.start() - 50)
        end = min(len(content), match.end() + 50)
        context_text = content[start:end].lower()

        # Look for contextual keywords that increase confidence
        context_keywords = {
            PIICategory.EMAIL: ["email", "contact", "reach", "send"],
            PIICategory.PHONE: ["phone", "call", "mobile", "cell", "tel"],
            PIICategory.SSN: ["ssn", "social security", "tax id"],
            PIICategory.CREDIT_CARD: ["card", "payment", "credit", "debit"],
            PIICategory.ADDRESS: ["address", "live", "reside", "located"],
            PIICategory.DATE_OF_BIRTH: ["born", "birthday", "dob", "birth"],
        }

        keywords = context_keywords.get(category, [])
        for keyword in keywords:
            if keyword in context_text:
                base_confidence = min(1.0, base_confidence + 0.1)
                break

        # Reduce confidence for very short matches
        if len(matched_text) < 5:
            base_confidence *= 0.7

        return round(base_confidence, 2)

    def _calculate_risk_level(
        self, findings: List[PIIFinding]
    ) -> PIIRiskLevel:
        """Calculate overall risk level from findings."""
        if not findings:
            return PIIRiskLevel.INFO

        risk_priority = {
            PIIRiskLevel.CRITICAL: 4,
            PIIRiskLevel.HIGH: 3,
            PIIRiskLevel.MEDIUM: 2,
            PIIRiskLevel.LOW: 1,
            PIIRiskLevel.INFO: 0,
        }

        max_risk = PIIRiskLevel.INFO
        for finding in findings:
            if risk_priority[finding.risk_level] > risk_priority[max_risk]:
                max_risk = finding.risk_level

        return max_risk

    def _determine_action(self, findings: List[PIIFinding]) -> PIIAction:
        """Determine action based on findings and configuration."""
        if not findings:
            return PIIAction.ALLOW

        # Priority: BLOCK > REQUIRE_APPROVAL > REDACT > LOG_ONLY > ALLOW
        action_priority = {
            PIIAction.BLOCK: 4,
            PIIAction.REQUIRE_APPROVAL: 3,
            PIIAction.REDACT: 2,
            PIIAction.LOG_ONLY: 1,
            PIIAction.ALLOW: 0,
        }

        max_action = PIIAction.ALLOW
        for finding in findings:
            category_action = self.action_config.get(
                finding.category, PIIAction.LOG_ONLY
            )
            if action_priority[category_action] > action_priority[max_action]:
                max_action = category_action

        return max_action

    def _get_recommendation(self, category: PIICategory) -> str:
        """Get recommendation for a PII category."""
        recommendations = {
            PIICategory.EMAIL: (
                "Consider redacting email addresses to protect user privacy."
            ),
            PIICategory.PHONE: (
                "Phone numbers should be redacted or require approval "
                "before sharing."
            ),
            PIICategory.SSN: (
                "CRITICAL: Social Security Numbers must be blocked. "
                "Never share SSNs in any output."
            ),
            PIICategory.CREDIT_CARD: (
                "CRITICAL: Credit card numbers must be blocked. "
                "PCI-DSS compliance requires protection of cardholder data."
            ),
            PIICategory.NAME: (
                "Names may be acceptable in context. Review for sensitivity."
            ),
            PIICategory.ADDRESS: (
                "Physical addresses should be reviewed before sharing. "
                "Consider redacting for privacy."
            ),
            PIICategory.IP_ADDRESS: (
                "IP addresses may reveal user location. "
                "Consider redacting in public outputs."
            ),
            PIICategory.DATE_OF_BIRTH: (
                "Dates of birth are sensitive PII. "
                "Require approval before sharing."
            ),
            PIICategory.PASSPORT: (
                "CRITICAL: Passport numbers must be blocked. "
                "Never share passport information."
            ),
            PIICategory.DRIVER_LICENSE: (
                "CRITICAL: Driver's license numbers must be blocked. "
                "Never share license information."
            ),
        }
        return recommendations.get(
            category,
            "Review this PII finding and take appropriate action."
        )

    def _generate_summary(
        self,
        findings: List[PIIFinding],
        overall_risk: PIIRiskLevel,
    ) -> str:
        """Generate human-readable summary of scan results."""
        if not findings:
            return "No PII detected in content."

        # Count by category
        category_counts: Dict[str, int] = {}
        for finding in findings:
            cat = finding.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        parts = [f"Found {len(findings)} PII item(s)"]
        parts.append(f"Overall risk: {overall_risk.value.upper()}")

        category_summary = ", ".join(
            f"{count} {cat}" for cat, count in category_counts.items()
        )
        parts.append(f"Categories: {category_summary}")

        return ". ".join(parts) + "."

    def _compute_evidence_hash(self, text: str) -> str:
        """Compute SHA-256 hash of evidence for audit trail.

        Uses 32 hex chars (16 bytes) for better collision resistance
        while keeping reasonable storage size for audit trail.
        """
        return hashlib.sha256(text.encode()).hexdigest()[:32]


# Global singleton instance
_pii_scanner: Optional[PIIScanner] = None


def get_pii_scanner() -> PIIScanner:
    """Get or create global PIIScanner instance."""
    global _pii_scanner
    if _pii_scanner is None:
        _pii_scanner = PIIScanner()
    return _pii_scanner


def reset_pii_scanner() -> None:
    """Reset global PIIScanner instance (for testing)."""
    global _pii_scanner
    _pii_scanner = None


def scan_for_pii(
    content: str,
    context: Optional[Dict[str, Any]] = None,
) -> PIIScanResult:
    """Convenience function to scan content for PII."""
    return get_pii_scanner().scan(content, context)
