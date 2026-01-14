#!/usr/bin/env python3
"""
Content Safety Scanner - EPIC E Phase E-3

Heuristic-based content safety scanner for detecting:
- Prompt Injection attacks
- Jailbreak attempts
- Harmful content

Design Principles:
- Pattern-based detection with confidence scoring
- Evidence generation for audit trail
- Configurable thresholds via feature flags
- Integration with existing governance modules

Blueprint Reference: Section 4.1 Safety Governor v2
"""
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple, Pattern

logger = logging.getLogger(__name__)

# Maximum length for matched text in logs/results (security: prevent PII exposure)
MAX_MATCHED_TEXT_LOG_LENGTH = 50


class ContentSafetyCategory(Enum):
    """Content safety violation categories"""
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    HARMFUL_CONTENT = "harmful_content"
    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    INSTRUCTION_OVERRIDE = "instruction_override"


class ContentRiskLevel(Enum):
    """Risk levels for content safety findings"""
    CRITICAL = "critical"  # Immediate block required
    HIGH = "high"          # Should block, requires review
    MEDIUM = "medium"      # Advisory, may require approval
    LOW = "low"            # Informational
    NONE = "none"          # No risk detected


class ContentSafetyAction(Enum):
    """Actions to take based on content safety scan"""
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    REDACT = "redact"
    LOG_ONLY = "log_only"


@dataclass
class ContentSafetyFinding:
    """Represents a content safety finding"""
    category: ContentSafetyCategory
    risk_level: ContentRiskLevel
    pattern_id: str
    title: str
    description: str
    matched_text: Optional[str] = None
    position: Optional[int] = None
    confidence: float = 1.0
    recommendation: Optional[str] = None
    evidence_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "pattern_id": self.pattern_id,
            "title": self.title,
            "description": self.description,
            "matched_text": self.matched_text[:100] if self.matched_text else None,
            "position": self.position,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "evidence_hash": self.evidence_hash,
        }


@dataclass
class ContentSafetyScanResult:
    """Result of content safety scan"""
    is_safe: bool
    risk_level: ContentRiskLevel
    action: ContentSafetyAction
    findings: List[ContentSafetyFinding] = field(default_factory=list)
    summary: str = ""
    scanner_id: str = "content_safety_v1"
    scan_duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "is_safe": self.is_safe,
            "risk_level": self.risk_level.value,
            "action": self.action.value,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
            "scanner_id": self.scanner_id,
            "scan_duration_ms": self.scan_duration_ms,
            "metadata": self.metadata,
        }


class ContentSafetyScanner:
    """
    Heuristic-based content safety scanner for EPIC E Phase E-3.

    Detects:
    - Prompt Injection: System prompt exfiltration, instruction override
    - Jailbreak: Role-play attacks, DAN-style prompts, character personas
    - Harmful Content: Violence, hate speech, illegal activities

    Blueprint Reference: Section 4.1 Safety Governor v2
    """

    # Prompt Injection Patterns (CWE-94 equivalent for LLMs)
    PROMPT_INJECTION_PATTERNS: List[Tuple[str, str, str, ContentRiskLevel]] = [
        # System prompt exfiltration attempts
        (
            r"(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above|earlier)\s+"
            r"(instructions?|prompts?|rules?|guidelines?)",
            "PI-001",
            "Instruction override attempt",
            ContentRiskLevel.CRITICAL,
        ),
        (
            r"(?i)(what|tell\s+me|reveal|show|display|print|output)\s+"
            r"(is\s+)?(your|the)\s+(system\s+)?(prompt|instructions?|rules?)",
            "PI-002",
            "System prompt exfiltration attempt",
            ContentRiskLevel.HIGH,
        ),
        (
            r"(?i)repeat\s+(back\s+)?(your|the)\s+"
            r"(initial|original|first|system|above|previous)\s+"
            r"(system\s+)?(prompt|instructions?|message|rules?)",
            "PI-003",
            "System prompt extraction via repetition",
            ContentRiskLevel.HIGH,
        ),
        # Delimiter injection
        (
            r"(?i)(```|<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>)",
            "PI-004",
            "Chat template delimiter injection",
            ContentRiskLevel.CRITICAL,
        ),
        # Role confusion attacks
        (
            r"(?i)(you\s+are\s+now|from\s+now\s+on\s+you\s+are|"
            r"act\s+as\s+if\s+you\s+are|pretend\s+to\s+be)\s+"
            r"(a\s+)?(different|new|another)\s+(ai|assistant|model)",
            "PI-005",
            "Role confusion attack",
            ContentRiskLevel.HIGH,
        ),
        # Instruction injection via formatting
        (
            r"(?i)(new\s+instruction|updated\s+instruction|override\s+instruction):",
            "PI-006",
            "Explicit instruction injection",
            ContentRiskLevel.CRITICAL,
        ),
        # Context manipulation
        (
            r"(?i)(the\s+following\s+is\s+your\s+new|"
            r"your\s+new\s+instructions?\s+are|"
            r"system:\s*you\s+are)",
            "PI-007",
            "Context manipulation attempt",
            ContentRiskLevel.HIGH,
        ),
    ]

    # Jailbreak Patterns
    JAILBREAK_PATTERNS: List[Tuple[str, str, str, ContentRiskLevel]] = [
        # DAN (Do Anything Now) style prompts
        (
            r"(?i)(enable\s+)?DAN(\s+mode)?|do\s+anything\s+now",
            "JB-001",
            "DAN-style jailbreak attempt",
            ContentRiskLevel.CRITICAL,
        ),
        # Developer/Debug mode exploitation
        (
            r"(?i)(developer|debug|admin|root|sudo|maintenance)\s+"
            r"(mode|access|override|privileges?)",
            "JB-002",
            "Privilege escalation attempt",
            ContentRiskLevel.HIGH,
        ),
        # Character/Persona roleplay jailbreaks
        (
            r"(?i)(you\s+are|act\s+as|pretend\s+to\s+be|roleplay\s+as)\s+"
            r"(an?\s+)?(evil|malicious|unethical|unrestricted|uncensored)\s+"
            r"(ai|assistant|version|model)",
            "JB-003",
            "Malicious persona roleplay",
            ContentRiskLevel.CRITICAL,
        ),
        # Hypothetical scenario exploitation
        (
            r"(?i)(hypothetically|theoretically|in\s+a\s+fictional\s+world|"
            r"for\s+educational\s+purposes|for\s+a\s+story|in\s+a\s+movie)"
            r"[,\s]+.{0,100}(how\s+to|explain|describe|tell\s+me|hack|make|create)",
            "JB-004",
            "Hypothetical scenario jailbreak",
            ContentRiskLevel.MEDIUM,
        ),
        # Opposite day / Inversion attacks
        (
            r"(?i)(opposite\s+day|opposite\s+mode|reverse\s+mode|"
            r"do\s+the\s+opposite|say\s+the\s+opposite)",
            "JB-005",
            "Inversion attack attempt",
            ContentRiskLevel.HIGH,
        ),
        # Token smuggling / Encoding bypass
        (
            r"(?i)(base64|rot13|hex|unicode|encode|decode)\s+"
            r"(this|the\s+following|my\s+message)",
            "JB-006",
            "Encoding bypass attempt",
            ContentRiskLevel.MEDIUM,
        ),
        # Grandma exploit / Emotional manipulation
        (
            r"(?i)(my\s+(grandmother|grandma|mom|mother|dad|father)\s+"
            r"(used\s+to|would)\s+(tell|read|say)|"
            r"please\s+i\s+(really\s+)?need\s+this|"
            r"i('ll|will)\s+(die|be\s+fired|lose\s+my\s+job)\s+if)",
            "JB-007",
            "Emotional manipulation attempt",
            ContentRiskLevel.MEDIUM,
        ),
        # Continuation attack
        (
            r"(?i)(continue\s+from|finish\s+this|complete\s+this)\s*:\s*"
            r"[\"']?(how\s+to\s+(make|create|build)|step\s+\d+)",
            "JB-008",
            "Continuation attack",
            ContentRiskLevel.HIGH,
        ),
    ]

    # Harmful Content Patterns
    HARMFUL_CONTENT_PATTERNS: List[Tuple[str, str, str, ContentRiskLevel]] = [
        # Violence and weapons
        (
            r"(?i)(how\s+to\s+(make|build|create|assemble)|"
            r"instructions?\s+for\s+(making|building|creating))\s+"
            r"(a\s+)?(bomb|explosive|weapon|gun|firearm)",
            "HC-001",
            "Weapon/explosive creation request",
            ContentRiskLevel.CRITICAL,
        ),
        # Illegal activities
        (
            r"(?i)(how\s+to\s+(hack\s+into|hack|break\s+into|bypass|crack|get\s+into)|"
            r"exploit\s+(for|to)|vulnerability\s+in)\s+"
            r"(a\s+)?(bank|account|system|network|password|computer|server|website)",
            "HC-002",
            "Hacking/illegal access request",
            ContentRiskLevel.CRITICAL,
        ),
        # Drug synthesis
        (
            r"(?i)(how\s+to\s+(make|synthesize|produce|manufacture)|"
            r"recipe\s+for|synthesis\s+of)\s+"
            r"(meth|cocaine|heroin|fentanyl|lsd|mdma|drugs?)",
            "HC-003",
            "Drug synthesis request",
            ContentRiskLevel.CRITICAL,
        ),
        # Self-harm content
        (
            r"(?i)(how\s+to\s+(kill|harm|hurt)\s+(myself|yourself)|"
            r"methods?\s+(of|for)\s+suicide|"
            r"best\s+way\s+to\s+(die|end\s+it))",
            "HC-004",
            "Self-harm content",
            ContentRiskLevel.CRITICAL,
        ),
        # Hate speech indicators
        (
            r"(?i)(all\s+\w+\s+should\s+(die|be\s+killed)|"
            r"(kill|eliminate|exterminate)\s+all\s+\w+|"
            r"\w+\s+are\s+(subhuman|inferior|vermin))",
            "HC-005",
            "Hate speech indicator",
            ContentRiskLevel.CRITICAL,
        ),
        # Child safety
        (
            r"(?i)(child|minor|underage|kid)\s+"
            r"(porn|explicit|nude|naked|sexual)",
            "HC-006",
            "Child safety violation",
            ContentRiskLevel.CRITICAL,
        ),
        # Fraud and scam
        (
            r"(?i)(how\s+to\s+(scam|defraud|trick|create\s+a\s+phishing)|"
            r"(create|make|write)\s+(a\s+)?phishing\s*(email|page|site)?|"
            r"phishing\s+(email|page|site|attack)|"
            r"fake\s+(identity|id|passport|document))",
            "HC-007",
            "Fraud/scam content",
            ContentRiskLevel.HIGH,
        ),
    ]

    def __init__(
        self,
        enabled: bool = True,
        strict_mode: bool = False,
        block_on_critical: bool = True,
        require_approval_on_high: bool = True,
    ):
        """
        Initialize ContentSafetyScanner.

        Args:
            enabled: Whether scanning is enabled
            strict_mode: If True, lower thresholds for detection
            block_on_critical: If True, block on CRITICAL findings
            require_approval_on_high: If True, require approval on HIGH findings
        """
        self.enabled = enabled
        self.strict_mode = strict_mode
        self.block_on_critical = block_on_critical
        self.require_approval_on_high = require_approval_on_high
        self._load_settings()
        self._compile_patterns()
        logger.info(
            "[ContentSafetyScanner] Initialized - EPIC E Phase E-3: "
            "enabled=%s, strict_mode=%s",
            self.enabled,
            self.strict_mode,
        )

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance optimization."""
        self._compiled_pi_patterns: List[
            Tuple[Pattern[str], str, str, ContentRiskLevel]
        ] = []
        self._compiled_jb_patterns: List[
            Tuple[Pattern[str], str, str, ContentRiskLevel]
        ] = []
        self._compiled_hc_patterns: List[
            Tuple[Pattern[str], str, str, ContentRiskLevel]
        ] = []

        for pattern, pid, title, risk in self.PROMPT_INJECTION_PATTERNS:
            self._compiled_pi_patterns.append(
                (re.compile(pattern, re.IGNORECASE), pid, title, risk)
            )

        for pattern, pid, title, risk in self.JAILBREAK_PATTERNS:
            self._compiled_jb_patterns.append(
                (re.compile(pattern, re.IGNORECASE), pid, title, risk)
            )

        for pattern, pid, title, risk in self.HARMFUL_CONTENT_PATTERNS:
            self._compiled_hc_patterns.append(
                (re.compile(pattern, re.IGNORECASE), pid, title, risk)
            )

    def _load_settings(self) -> None:
        """Load settings from environment/config"""
        try:
            from common.config.settings import settings
            self.enabled = getattr(
                settings, "content_safety_scanner_enabled", self.enabled
            )
            self.strict_mode = getattr(
                settings, "content_safety_strict_mode", self.strict_mode
            )
            self.block_on_critical = getattr(
                settings, "content_safety_block_on_critical", self.block_on_critical
            )
            self.require_approval_on_high = getattr(
                settings,
                "content_safety_require_approval_on_high",
                self.require_approval_on_high,
            )
            logger.debug(
                "[ContentSafetyScanner] Settings loaded from config"
            )
        except (ImportError, AttributeError) as e:
            logger.debug(
                "[ContentSafetyScanner] Using default settings: %s", e
            )

    def scan(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ContentSafetyScanResult:
        """
        Scan content for safety issues.

        Args:
            content: Text content to scan
            context: Optional context (e.g., source, user_id, task_type)

        Returns:
            ContentSafetyScanResult with findings and recommended action
        """
        import time
        start_time = time.time()

        if not self.enabled:
            return ContentSafetyScanResult(
                is_safe=True,
                risk_level=ContentRiskLevel.NONE,
                action=ContentSafetyAction.ALLOW,
                summary="Content safety scanning disabled",
            )

        if not content or not content.strip():
            return ContentSafetyScanResult(
                is_safe=True,
                risk_level=ContentRiskLevel.NONE,
                action=ContentSafetyAction.ALLOW,
                summary="Empty content",
            )

        findings: List[ContentSafetyFinding] = []
        found_critical = False

        # Check for prompt injection (with short-circuit optimization)
        pi_findings, found_critical = self._check_prompt_injection(
            content, found_critical
        )
        findings.extend(pi_findings)

        # Check for jailbreak attempts (with short-circuit optimization)
        jb_findings, found_critical = self._check_jailbreak(
            content, found_critical
        )
        findings.extend(jb_findings)

        # Check for harmful content (with short-circuit optimization)
        hc_findings, found_critical = self._check_harmful_content(
            content, found_critical
        )
        findings.extend(hc_findings)

        # Calculate overall risk level
        risk_level = self._calculate_risk_level(findings)

        # Determine action based on risk level
        action = self._determine_action(risk_level)

        # Generate summary
        summary = self._generate_summary(findings, risk_level)

        # Calculate scan duration
        scan_duration_ms = (time.time() - start_time) * 1000

        is_safe = risk_level in (ContentRiskLevel.NONE, ContentRiskLevel.LOW)

        result = ContentSafetyScanResult(
            is_safe=is_safe,
            risk_level=risk_level,
            action=action,
            findings=findings,
            summary=summary,
            scanner_id="content_safety_v1",
            scan_duration_ms=scan_duration_ms,
            metadata={
                "content_length": len(content),
                "findings_count": len(findings),
                "context": context or {},
            },
        )

        logger.info(
            "[ContentSafetyScanner] Scan complete: risk=%s, action=%s, "
            "findings=%d, duration=%.2fms",
            risk_level.value,
            action.value,
            len(findings),
            scan_duration_ms,
        )

        return result

    def _sanitize_matched_text(self, text: str) -> str:
        """Sanitize matched text for logging (security: prevent PII exposure)."""
        if not text:
            return ""
        if len(text) <= MAX_MATCHED_TEXT_LOG_LENGTH:
            return text
        return text[:MAX_MATCHED_TEXT_LOG_LENGTH] + "..."

    def _check_prompt_injection(
        self, content: str, found_critical: bool = False
    ) -> Tuple[List[ContentSafetyFinding], bool]:
        """
        Check for prompt injection patterns.

        Args:
            content: Text to scan
            found_critical: Whether CRITICAL risk was already found (for short-circuit)

        Returns:
            Tuple of (findings list, whether CRITICAL was found)
        """
        findings = []

        for compiled_pattern, pattern_id, title, risk_level in self._compiled_pi_patterns:
            # Short-circuit: skip non-CRITICAL patterns if CRITICAL already found
            if found_critical and risk_level != ContentRiskLevel.CRITICAL:
                continue

            for match in compiled_pattern.finditer(content):
                confidence = self._calculate_confidence(match, content)

                if self.strict_mode or confidence >= 0.7:
                    matched_text = match.group(0)
                    findings.append(
                        ContentSafetyFinding(
                            category=ContentSafetyCategory.PROMPT_INJECTION,
                            risk_level=risk_level,
                            pattern_id=pattern_id,
                            title=title,
                            description=(
                                f"Detected potential prompt injection: {title}"
                            ),
                            matched_text=self._sanitize_matched_text(matched_text),
                            position=match.start(),
                            confidence=confidence,
                            recommendation=(
                                "Review input for malicious intent. "
                                "Consider blocking or requiring human approval."
                            ),
                            evidence_hash=self._compute_evidence_hash(matched_text),
                        )
                    )
                    if risk_level == ContentRiskLevel.CRITICAL:
                        found_critical = True

        return findings, found_critical

    def _check_jailbreak(
        self, content: str, found_critical: bool = False
    ) -> Tuple[List[ContentSafetyFinding], bool]:
        """
        Check for jailbreak attempt patterns.

        Args:
            content: Text to scan
            found_critical: Whether CRITICAL risk was already found (for short-circuit)

        Returns:
            Tuple of (findings list, whether CRITICAL was found)
        """
        findings = []

        for compiled_pattern, pattern_id, title, risk_level in self._compiled_jb_patterns:
            # Short-circuit: skip non-CRITICAL patterns if CRITICAL already found
            if found_critical and risk_level != ContentRiskLevel.CRITICAL:
                continue

            for match in compiled_pattern.finditer(content):
                confidence = self._calculate_confidence(match, content)

                if self.strict_mode or confidence >= 0.6:
                    matched_text = match.group(0)
                    findings.append(
                        ContentSafetyFinding(
                            category=ContentSafetyCategory.JAILBREAK,
                            risk_level=risk_level,
                            pattern_id=pattern_id,
                            title=title,
                            description=(
                                f"Detected potential jailbreak attempt: {title}"
                            ),
                            matched_text=self._sanitize_matched_text(matched_text),
                            position=match.start(),
                            confidence=confidence,
                            recommendation=(
                                "This appears to be an attempt to bypass "
                                "safety guidelines. Consider blocking."
                            ),
                            evidence_hash=self._compute_evidence_hash(matched_text),
                        )
                    )
                    if risk_level == ContentRiskLevel.CRITICAL:
                        found_critical = True

        return findings, found_critical

    def _check_harmful_content(
        self, content: str, found_critical: bool = False
    ) -> Tuple[List[ContentSafetyFinding], bool]:
        """
        Check for harmful content patterns.

        Args:
            content: Text to scan
            found_critical: Whether CRITICAL risk was already found (for short-circuit)

        Returns:
            Tuple of (findings list, whether CRITICAL was found)
        """
        findings = []

        for compiled_pattern, pattern_id, title, risk_level in self._compiled_hc_patterns:
            # Short-circuit: skip non-CRITICAL patterns if CRITICAL already found
            if found_critical and risk_level != ContentRiskLevel.CRITICAL:
                continue

            for match in compiled_pattern.finditer(content):
                confidence = self._calculate_confidence(match, content)

                # Harmful content has higher confidence threshold to reduce FP
                if self.strict_mode or confidence >= 0.8:
                    matched_text = match.group(0)
                    findings.append(
                        ContentSafetyFinding(
                            category=ContentSafetyCategory.HARMFUL_CONTENT,
                            risk_level=risk_level,
                            pattern_id=pattern_id,
                            title=title,
                            description=(
                                f"Detected potentially harmful content: {title}"
                            ),
                            matched_text=self._sanitize_matched_text(matched_text),
                            position=match.start(),
                            confidence=confidence,
                            recommendation=(
                                "This content may violate safety policies. "
                                "Blocking is recommended."
                            ),
                            evidence_hash=self._compute_evidence_hash(matched_text),
                        )
                    )
                    if risk_level == ContentRiskLevel.CRITICAL:
                        found_critical = True

        return findings, found_critical

    def _calculate_confidence(
        self, match: re.Match, content: str
    ) -> float:
        """
        Calculate confidence score for a pattern match.

        Factors:
        - Match length relative to content
        - Surrounding context
        - Pattern specificity
        """
        matched_text = match.group(0)
        match_len = len(matched_text)

        # Base confidence from match length
        if match_len < 10:
            base_confidence = 0.5
        elif match_len < 30:
            base_confidence = 0.7
        else:
            base_confidence = 0.9

        # Adjust based on content length ratio
        content_len = len(content)
        if content_len > 0:
            ratio = match_len / content_len
            if ratio > 0.5:
                # Match is majority of content - likely intentional
                base_confidence = min(1.0, base_confidence + 0.2)
            elif ratio < 0.01:
                # Match is tiny part of content - might be coincidental
                base_confidence = max(0.3, base_confidence - 0.2)

        return round(base_confidence, 2)

    def _calculate_risk_level(
        self, findings: List[ContentSafetyFinding]
    ) -> ContentRiskLevel:
        """Calculate overall risk level from findings"""
        if not findings:
            return ContentRiskLevel.NONE

        # Get highest risk level from findings
        risk_priority = {
            ContentRiskLevel.CRITICAL: 4,
            ContentRiskLevel.HIGH: 3,
            ContentRiskLevel.MEDIUM: 2,
            ContentRiskLevel.LOW: 1,
            ContentRiskLevel.NONE: 0,
        }

        max_risk = ContentRiskLevel.NONE
        for finding in findings:
            if risk_priority[finding.risk_level] > risk_priority[max_risk]:
                max_risk = finding.risk_level

        return max_risk

    def _determine_action(
        self, risk_level: ContentRiskLevel
    ) -> ContentSafetyAction:
        """Determine action based on risk level and configuration"""
        if risk_level == ContentRiskLevel.CRITICAL:
            if self.block_on_critical:
                return ContentSafetyAction.BLOCK
            return ContentSafetyAction.REQUIRE_APPROVAL

        if risk_level == ContentRiskLevel.HIGH:
            if self.require_approval_on_high:
                return ContentSafetyAction.REQUIRE_APPROVAL
            return ContentSafetyAction.LOG_ONLY

        if risk_level == ContentRiskLevel.MEDIUM:
            return ContentSafetyAction.LOG_ONLY

        return ContentSafetyAction.ALLOW

    def _generate_summary(
        self,
        findings: List[ContentSafetyFinding],
        risk_level: ContentRiskLevel,
    ) -> str:
        """Generate human-readable summary of scan results"""
        if not findings:
            return "No content safety issues detected"

        category_counts: Dict[str, int] = {}
        for finding in findings:
            cat = finding.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        parts = []
        for cat, count in category_counts.items():
            parts.append(f"{count} {cat}")

        return (
            f"Detected {len(findings)} issue(s): {', '.join(parts)}. "
            f"Overall risk: {risk_level.value}"
        )

    def _compute_evidence_hash(self, text: str) -> str:
        """Compute hash for evidence tracking"""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()[:16]


# Singleton instance
_content_safety_scanner: Optional[ContentSafetyScanner] = None


def get_content_safety_scanner() -> ContentSafetyScanner:
    """Get or create singleton ContentSafetyScanner instance"""
    global _content_safety_scanner
    if _content_safety_scanner is None:
        _content_safety_scanner = ContentSafetyScanner()
    return _content_safety_scanner


def reset_content_safety_scanner() -> None:
    """Reset singleton instance (for testing)"""
    global _content_safety_scanner
    _content_safety_scanner = None


def scan_content(
    content: str,
    context: Optional[Dict[str, Any]] = None,
) -> ContentSafetyScanResult:
    """Convenience function to scan content"""
    return get_content_safety_scanner().scan(content, context)
