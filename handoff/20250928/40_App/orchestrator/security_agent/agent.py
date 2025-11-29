#!/usr/bin/env python3
"""
Security Agent - Phase 4 PR-2

Advisory agent for security analysis in the 5-Agent Advisory Pipeline.
Provides security recommendations for code changes and task execution.

Design Principles:
- Advisory role: Provides recommendations, does not block execution
- Defense in depth: Multiple security checks at different levels
- Configurable: Security policies configurable via environment variables
- Integration: Works with existing governance modules (PolicyGuard, ViolationDetector)
"""
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class SecurityRisk(Enum):
    """Security risk levels"""
    CRITICAL = "critical"  # Immediate action required, should block
    HIGH = "high"          # Significant risk, requires review
    MEDIUM = "medium"      # Moderate risk, advisory
    LOW = "low"            # Minor risk, informational
    INFO = "info"          # No risk, informational only


@dataclass
class SecurityFinding:
    """Represents a security finding"""
    category: str           # e.g., "secrets", "injection", "traversal", "permissions"
    risk_level: SecurityRisk
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID


@dataclass
class SecurityAdvisory:
    """Security advisory result from SecurityAgent analysis"""
    is_safe: bool
    overall_risk: SecurityRisk
    findings: List[SecurityFinding] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "is_safe": self.is_safe,
            "overall_risk": self.overall_risk.value,
            "findings": [
                {
                    "category": f.category,
                    "risk_level": f.risk_level.value,
                    "title": f.title,
                    "description": f.description,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "recommendation": f.recommendation,
                    "cwe_id": f.cwe_id,
                }
                for f in self.findings
            ],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }


class SecurityAgent:
    """
    Security Agent for the 5-Agent Advisory Pipeline.

    Phase 4 PR-2 Features:
    - Code security analysis (secrets, injection, traversal)
    - File permission checks
    - Dependency vulnerability awareness
    - Integration with PolicyGuard and ViolationDetector
    """

    # Patterns for detecting potential security issues
    SECRET_PATTERNS = [
        (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}', "API Key exposure", "CWE-798"),
        (r'(?i)(secret|password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']{8,}', "Password/Secret exposure", "CWE-798"),
        (r'(?i)(token|bearer)\s*[=:]\s*["\']?[a-zA-Z0-9_\-\.]{20,}', "Token exposure", "CWE-798"),
        (r'(?i)(private[_-]?key|ssh[_-]?key)\s*[=:]\s*', "Private key reference", "CWE-321"),
        (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', "Private key content", "CWE-321"),
        (r'(?i)aws[_-]?(access[_-]?key|secret)', "AWS credential reference", "CWE-798"),
        (r'(?i)(github|gitlab|bitbucket)[_-]?token', "Git platform token", "CWE-798"),
    ]

    INJECTION_PATTERNS = [
        (r'(?i)exec\s*\(', "Potential code execution", "CWE-94"),
        (r'(?i)eval\s*\(', "Potential eval injection", "CWE-95"),
        (r'(?i)subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True', "Shell injection risk", "CWE-78"),
        (r'(?i)os\.system\s*\(', "OS command execution", "CWE-78"),
        (r'(?i)__import__\s*\(', "Dynamic import", "CWE-94"),
        (r'(?i)pickle\.(load|loads)\s*\(', "Unsafe deserialization", "CWE-502"),
        (r'(?i)yaml\.(load|unsafe_load)\s*\([^)]*Loader\s*=\s*yaml\.Loader', "Unsafe YAML loading", "CWE-502"),
    ]

    TRAVERSAL_PATTERNS = [
        (r'\.\./', "Path traversal attempt", "CWE-22"),
        (r'\.\.\\', "Path traversal attempt (Windows)", "CWE-22"),
        (r'%2e%2e%2f', "URL-encoded path traversal", "CWE-22"),
        (r'%252e%252e%252f', "Double URL-encoded path traversal", "CWE-22"),
    ]

    SENSITIVE_FILE_PATTERNS = [
        r'\.env$',
        r'\.env\.',
        r'secrets?\.',
        r'credentials?\.',
        r'\.pem$',
        r'\.key$',
        r'\.p12$',
        r'\.pfx$',
        r'id_rsa',
        r'id_dsa',
        r'id_ecdsa',
        r'id_ed25519',
    ]

    def __init__(self):
        """Initialize SecurityAgent with configuration"""
        self._load_settings()
        self._init_governance_integration()
        logger.info("[SecurityAgent] Initialized - Phase 4 PR-2")

    def _load_settings(self):
        """Load settings from environment"""
        try:
            from common.config.settings import settings
            self.enabled = getattr(settings, 'security_agent_enabled', True)
            self.strict_mode = getattr(settings, 'security_agent_strict_mode', False)
            logger.info(f"[SecurityAgent] Settings loaded: enabled={self.enabled}, strict_mode={self.strict_mode}")
        except (ImportError, AttributeError) as e:
            logger.warning(f"[SecurityAgent] Failed to load settings: {e}, using defaults")
            self.enabled = True
            self.strict_mode = False

    def _init_governance_integration(self):
        """Initialize integration with existing governance modules"""
        self.policy_guard = None
        self.violation_detector = None

        try:
            from ..governance.policy_guard import get_policy_guard
            self.policy_guard = get_policy_guard()
            logger.debug("[SecurityAgent] PolicyGuard integration enabled")
        except ImportError as e:
            logger.debug(f"[SecurityAgent] PolicyGuard not available: {e}")

        try:
            from ..governance.violation_detector import get_violation_detector
            self.violation_detector = get_violation_detector()
            logger.debug("[SecurityAgent] ViolationDetector integration enabled")
        except ImportError as e:
            logger.debug(f"[SecurityAgent] ViolationDetector not available: {e}")

    def analyze_code(self, code: str, file_path: Optional[str] = None) -> SecurityAdvisory:
        """
        Analyze code for security issues.

        Args:
            code: Source code to analyze
            file_path: Optional file path for context

        Returns:
            SecurityAdvisory with findings and recommendations
        """
        if not self.enabled:
            return SecurityAdvisory(
                is_safe=True,
                overall_risk=SecurityRisk.INFO,
                summary="Security analysis disabled"
            )

        findings: List[SecurityFinding] = []

        # Check for secrets
        findings.extend(self._check_secrets(code, file_path))

        # Check for injection vulnerabilities
        findings.extend(self._check_injection(code, file_path))

        # Check for path traversal
        findings.extend(self._check_traversal(code, file_path))

        # Determine overall risk
        overall_risk = self._calculate_overall_risk(findings)
        is_safe = overall_risk in (SecurityRisk.LOW, SecurityRisk.INFO)

        # Generate recommendations
        recommendations = self._generate_recommendations(findings)

        # Generate summary
        summary = self._generate_summary(findings, overall_risk)

        advisory = SecurityAdvisory(
            is_safe=is_safe,
            overall_risk=overall_risk,
            findings=findings,
            summary=summary,
            recommendations=recommendations,
            metadata={
                "file_path": file_path,
                "code_length": len(code),
                "findings_count": len(findings),
            }
        )

        logger.info(
            f"[SecurityAgent] Analysis complete: "
            f"risk={overall_risk.value}, findings={len(findings)}, is_safe={is_safe}"
        )

        return advisory

    def analyze_file_paths(self, file_paths: List[str]) -> SecurityAdvisory:
        """
        Analyze file paths for security concerns.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            SecurityAdvisory with findings
        """
        if not self.enabled:
            return SecurityAdvisory(
                is_safe=True,
                overall_risk=SecurityRisk.INFO,
                summary="Security analysis disabled"
            )

        findings: List[SecurityFinding] = []

        for file_path in file_paths:
            # Check for sensitive file patterns
            for pattern in self.SENSITIVE_FILE_PATTERNS:
                if re.search(pattern, file_path, re.IGNORECASE):
                    findings.append(SecurityFinding(
                        category="sensitive_file",
                        risk_level=SecurityRisk.HIGH,
                        title="Sensitive file access",
                        description=f"Attempting to access potentially sensitive file: {file_path}",
                        file_path=file_path,
                        recommendation="Ensure this file access is intentional and authorized",
                        cwe_id="CWE-538"
                    ))
                    break

            # Check for path traversal in file paths
            for pattern, title, cwe_id in self.TRAVERSAL_PATTERNS:
                if re.search(pattern, file_path, re.IGNORECASE):
                    findings.append(SecurityFinding(
                        category="traversal",
                        risk_level=SecurityRisk.CRITICAL,
                        title=title,
                        description=f"Path traversal pattern detected in: {file_path}",
                        file_path=file_path,
                        recommendation="Sanitize file paths and use absolute paths",
                        cwe_id=cwe_id
                    ))

            # Use PolicyGuard if available
            if self.policy_guard:
                try:
                    self.policy_guard.check_file_access(file_path)
                except Exception as e:
                    findings.append(SecurityFinding(
                        category="policy_violation",
                        risk_level=SecurityRisk.HIGH,
                        title="Policy violation",
                        description=str(e),
                        file_path=file_path,
                        recommendation="Review file access policies"
                    ))

        overall_risk = self._calculate_overall_risk(findings)
        is_safe = overall_risk in (SecurityRisk.LOW, SecurityRisk.INFO)

        return SecurityAdvisory(
            is_safe=is_safe,
            overall_risk=overall_risk,
            findings=findings,
            summary=self._generate_summary(findings, overall_risk),
            recommendations=self._generate_recommendations(findings),
            metadata={
                "file_count": len(file_paths),
                "findings_count": len(findings),
            }
        )

    def analyze_command(self, command: str) -> SecurityAdvisory:
        """
        Analyze a shell command for security issues.

        Args:
            command: Shell command to analyze

        Returns:
            SecurityAdvisory with findings
        """
        if not self.enabled:
            return SecurityAdvisory(
                is_safe=True,
                overall_risk=SecurityRisk.INFO,
                summary="Security analysis disabled"
            )

        findings: List[SecurityFinding] = []

        # Check for dangerous commands
        dangerous_patterns = [
            (r'(?i)rm\s+-rf\s+/', "Dangerous recursive delete", SecurityRisk.CRITICAL),
            (r'(?i)chmod\s+777', "Overly permissive file permissions", SecurityRisk.HIGH),
            (r'(?i)curl\s+.*\|\s*(bash|sh)', "Piping remote script to shell", SecurityRisk.CRITICAL),
            (r'(?i)wget\s+.*\|\s*(bash|sh)', "Piping remote script to shell", SecurityRisk.CRITICAL),
            (r'(?i)>\s*/dev/sd[a-z]', "Direct disk write", SecurityRisk.CRITICAL),
            (r'(?i)dd\s+if=.*of=/dev/', "Direct disk write with dd", SecurityRisk.CRITICAL),
            (r'(?i)mkfs[.\s]', "Filesystem creation", SecurityRisk.CRITICAL),
            (r'(?i):(){ :|:& };:', "Fork bomb", SecurityRisk.CRITICAL),
        ]

        for pattern, title, risk_level in dangerous_patterns:
            if re.search(pattern, command):
                findings.append(SecurityFinding(
                    category="dangerous_command",
                    risk_level=risk_level,
                    title=title,
                    description=f"Dangerous command pattern detected: {command[:100]}",
                    recommendation="Review command carefully before execution",
                    cwe_id="CWE-78"
                ))

        # Use ViolationDetector if available
        if self.violation_detector:
            try:
                self.violation_detector.check_dangerous_operations(command)
            except Exception as e:
                findings.append(SecurityFinding(
                    category="violation",
                    risk_level=SecurityRisk.HIGH,
                    title="Violation detected",
                    description=str(e),
                    recommendation="Review command against security policies"
                ))

        overall_risk = self._calculate_overall_risk(findings)
        is_safe = overall_risk in (SecurityRisk.LOW, SecurityRisk.INFO)

        return SecurityAdvisory(
            is_safe=is_safe,
            overall_risk=overall_risk,
            findings=findings,
            summary=self._generate_summary(findings, overall_risk),
            recommendations=self._generate_recommendations(findings),
            metadata={
                "command_length": len(command),
                "findings_count": len(findings),
            }
        )

    def analyze_task(
        self,
        task_type: str,
        repo: str,
        file_paths: Optional[List[str]] = None,
        code_changes: Optional[str] = None
    ) -> SecurityAdvisory:
        """
        Comprehensive security analysis for a task.

        Args:
            task_type: Type of task being executed
            repo: Repository name
            file_paths: Optional list of file paths involved
            code_changes: Optional code changes to analyze

        Returns:
            SecurityAdvisory with comprehensive findings
        """
        if not self.enabled:
            return SecurityAdvisory(
                is_safe=True,
                overall_risk=SecurityRisk.INFO,
                summary="Security analysis disabled"
            )

        all_findings: List[SecurityFinding] = []

        # Analyze file paths if provided
        if file_paths:
            file_advisory = self.analyze_file_paths(file_paths)
            all_findings.extend(file_advisory.findings)

        # Analyze code changes if provided
        if code_changes:
            code_advisory = self.analyze_code(code_changes)
            all_findings.extend(code_advisory.findings)

        # Check task type risk
        high_risk_task_types = [
            "infrastructure_change",
            "security_config",
            "database_migration",
            "deployment",
        ]

        if task_type in high_risk_task_types:
            all_findings.append(SecurityFinding(
                category="task_risk",
                risk_level=SecurityRisk.MEDIUM,
                title="High-risk task type",
                description=f"Task type '{task_type}' is classified as high-risk",
                recommendation="Ensure proper review and approval before execution"
            ))

        overall_risk = self._calculate_overall_risk(all_findings)
        is_safe = overall_risk in (SecurityRisk.LOW, SecurityRisk.INFO)

        return SecurityAdvisory(
            is_safe=is_safe,
            overall_risk=overall_risk,
            findings=all_findings,
            summary=self._generate_summary(all_findings, overall_risk),
            recommendations=self._generate_recommendations(all_findings),
            metadata={
                "task_type": task_type,
                "repo": repo,
                "file_count": len(file_paths) if file_paths else 0,
                "has_code_changes": code_changes is not None,
                "findings_count": len(all_findings),
            }
        )

    def _check_secrets(self, code: str, file_path: Optional[str] = None) -> List[SecurityFinding]:
        """Check code for exposed secrets"""
        findings = []

        for pattern, title, cwe_id in self.SECRET_PATTERNS:
            matches = re.finditer(pattern, code)
            for match in matches:
                # Get line number
                line_number = code[:match.start()].count('\n') + 1

                findings.append(SecurityFinding(
                    category="secrets",
                    risk_level=SecurityRisk.CRITICAL,
                    title=title,
                    description=f"Potential secret exposure detected at line {line_number}",
                    file_path=file_path,
                    line_number=line_number,
                    recommendation="Remove hardcoded secrets and use environment variables or secret management",
                    cwe_id=cwe_id
                ))

        return findings

    def _check_injection(self, code: str, file_path: Optional[str] = None) -> List[SecurityFinding]:
        """Check code for injection vulnerabilities"""
        findings = []

        for pattern, title, cwe_id in self.INJECTION_PATTERNS:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1

                findings.append(SecurityFinding(
                    category="injection",
                    risk_level=SecurityRisk.HIGH,
                    title=title,
                    description=f"Potential injection vulnerability at line {line_number}",
                    file_path=file_path,
                    line_number=line_number,
                    recommendation="Validate and sanitize all inputs, avoid dynamic code execution",
                    cwe_id=cwe_id
                ))

        return findings

    def _check_traversal(self, code: str, file_path: Optional[str] = None) -> List[SecurityFinding]:
        """Check code for path traversal patterns"""
        findings = []

        for pattern, title, cwe_id in self.TRAVERSAL_PATTERNS:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1

                findings.append(SecurityFinding(
                    category="traversal",
                    risk_level=SecurityRisk.HIGH,
                    title=title,
                    description=f"Path traversal pattern detected at line {line_number}",
                    file_path=file_path,
                    line_number=line_number,
                    recommendation="Use path normalization and validate against allowed directories",
                    cwe_id=cwe_id
                ))

        return findings

    def _calculate_overall_risk(self, findings: List[SecurityFinding]) -> SecurityRisk:
        """Calculate overall risk level from findings"""
        if not findings:
            return SecurityRisk.INFO

        # Get the highest risk level
        risk_priority = {
            SecurityRisk.CRITICAL: 4,
            SecurityRisk.HIGH: 3,
            SecurityRisk.MEDIUM: 2,
            SecurityRisk.LOW: 1,
            SecurityRisk.INFO: 0,
        }

        max_risk = max(findings, key=lambda f: risk_priority.get(f.risk_level, 0))
        return max_risk.risk_level

    def _generate_recommendations(self, findings: List[SecurityFinding]) -> List[str]:
        """Generate unique recommendations from findings"""
        recommendations = []
        seen = set()

        for finding in findings:
            if finding.recommendation and finding.recommendation not in seen:
                recommendations.append(finding.recommendation)
                seen.add(finding.recommendation)

        return recommendations

    def _generate_summary(self, findings: List[SecurityFinding], overall_risk: SecurityRisk) -> str:
        """Generate a summary of the security analysis"""
        if not findings:
            return "No security issues detected"

        # Count by category
        categories = {}
        for finding in findings:
            categories[finding.category] = categories.get(finding.category, 0) + 1

        # Count by risk level
        risk_counts = {}
        for finding in findings:
            risk_counts[finding.risk_level.value] = risk_counts.get(finding.risk_level.value, 0) + 1

        summary_parts = [
            f"Found {len(findings)} security issue(s)",
            f"Overall risk: {overall_risk.value}",
        ]

        if risk_counts:
            risk_summary = ", ".join(f"{count} {level}" for level, count in risk_counts.items())
            summary_parts.append(f"Risk breakdown: {risk_summary}")

        return ". ".join(summary_parts)


# Module-level instance (lazy initialization)
_security_agent: Optional[SecurityAgent] = None


def get_security_agent() -> SecurityAgent:
    """Get or create the SecurityAgent instance"""
    global _security_agent
    if _security_agent is None:
        _security_agent = SecurityAgent()
    return _security_agent


def analyze_code(code: str, file_path: Optional[str] = None) -> SecurityAdvisory:
    """Convenience function to analyze code"""
    return get_security_agent().analyze_code(code, file_path)


def analyze_file_paths(file_paths: List[str]) -> SecurityAdvisory:
    """Convenience function to analyze file paths"""
    return get_security_agent().analyze_file_paths(file_paths)


def analyze_command(command: str) -> SecurityAdvisory:
    """Convenience function to analyze a command"""
    return get_security_agent().analyze_command(command)


def analyze_task(
    task_type: str,
    repo: str,
    file_paths: Optional[List[str]] = None,
    code_changes: Optional[str] = None
) -> SecurityAdvisory:
    """Convenience function to analyze a task"""
    return get_security_agent().analyze_task(task_type, repo, file_paths, code_changes)


# Logging on module import
logger.info("[SecurityAgent] Module loaded - Phase 4 PR-2")
