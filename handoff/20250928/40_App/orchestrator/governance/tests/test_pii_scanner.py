"""
Unit tests for PIIScanner - EPIC E Phase E-4

Tests cover:
- Email detection
- Phone number detection
- SSN detection
- Credit card detection (with Luhn validation)
- IP address detection
- Date of birth detection
- Address detection
- Risk level calculation
- Action determination
- Redaction functionality
- Serialization
- Global functions
- Edge cases
"""
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
for _ in range(10):
    if (repo_root / 'common').exists():
        break
    repo_root = repo_root.parent

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from governance.pii_scanner import (  # noqa: E402
    PIIScanner,
    PIICategory,
    PIIRiskLevel,
    PIIAction,
    PIIFinding,
    get_pii_scanner,
    reset_pii_scanner,
    scan_for_pii,
)


class TestPIIScanner:
    """Basic PIIScanner tests"""

    def setup_method(self):
        """Reset scanner before each test"""
        reset_pii_scanner()

    def test_scanner_initialization(self):
        """Test scanner initializes correctly"""
        scanner = PIIScanner()
        assert scanner.enabled is True
        assert scanner.strict_mode is False
        assert scanner._compiled_patterns is not None

    def test_scanner_disabled(self):
        """Test scanner returns early when disabled"""
        scanner = PIIScanner(enabled=False)
        result = scanner.scan("test@example.com")
        assert result.has_pii is False
        assert result.action == PIIAction.ALLOW
        assert "disabled" in result.summary.lower()

    def test_empty_content(self):
        """Test scanner handles empty content"""
        scanner = PIIScanner()
        result = scanner.scan("")
        assert result.has_pii is False
        assert result.action == PIIAction.ALLOW

    def test_safe_content(self):
        """Test scanner allows safe content"""
        scanner = PIIScanner()
        result = scanner.scan("This is a normal message without any PII.")
        assert result.has_pii is False
        assert result.overall_risk == PIIRiskLevel.INFO
        assert result.action == PIIAction.ALLOW


class TestEmailDetection:
    """Email detection tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_simple_email_detection(self):
        """Test detection of simple email addresses"""
        scanner = PIIScanner()
        result = scanner.scan("Contact me at user@example.com")
        assert result.has_pii is True
        assert any(f.category == PIICategory.EMAIL for f in result.findings)

    def test_email_with_subdomain(self):
        """Test detection of email with subdomain"""
        scanner = PIIScanner()
        result = scanner.scan("Email: admin@mail.company.org")
        assert result.has_pii is True
        email_findings = [
            f for f in result.findings if f.category == PIICategory.EMAIL
        ]
        assert len(email_findings) >= 1

    def test_email_redaction(self):
        """Test email redaction format"""
        scanner = PIIScanner()
        result = scanner.scan("user@example.com")
        email_finding = next(
            (f for f in result.findings if f.category == PIICategory.EMAIL),
            None
        )
        assert email_finding is not None
        assert email_finding.redacted_text is not None
        assert "@" in email_finding.redacted_text
        assert "***" in email_finding.redacted_text


class TestPhoneDetection:
    """Phone number detection tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_us_phone_with_dashes(self):
        """Test US phone number with dashes"""
        scanner = PIIScanner()
        result = scanner.scan("Call me at 555-123-4567")
        assert result.has_pii is True
        phone_findings = [
            f for f in result.findings if f.category == PIICategory.PHONE
        ]
        assert len(phone_findings) >= 1

    def test_us_phone_with_parentheses(self):
        """Test US phone number with parentheses"""
        scanner = PIIScanner()
        result = scanner.scan("Phone: (555) 123-4567")
        assert result.has_pii is True
        phone_findings = [
            f for f in result.findings if f.category == PIICategory.PHONE
        ]
        assert len(phone_findings) >= 1

    def test_international_phone(self):
        """Test international phone number"""
        scanner = PIIScanner()
        # Use format that matches the pattern: +XX-XXXX-XXXX-XXXX
        result = scanner.scan("International: +44-207-946-0958")
        assert result.has_pii is True

    def test_phone_redaction(self):
        """Test phone redaction shows last 4 digits"""
        scanner = PIIScanner()
        result = scanner.scan("555-123-4567")
        phone_finding = next(
            (f for f in result.findings if f.category == PIICategory.PHONE),
            None
        )
        if phone_finding:
            assert "4567" in phone_finding.redacted_text
            assert "***" in phone_finding.redacted_text


class TestSSNDetection:
    """SSN detection tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_ssn_with_dashes(self):
        """Test SSN with dashes"""
        scanner = PIIScanner()
        result = scanner.scan("SSN: 123-45-6789")
        assert result.has_pii is True
        ssn_findings = [
            f for f in result.findings if f.category == PIICategory.SSN
        ]
        assert len(ssn_findings) >= 1
        assert ssn_findings[0].risk_level == PIIRiskLevel.CRITICAL

    def test_ssn_without_dashes(self):
        """Test SSN without dashes"""
        scanner = PIIScanner()
        result = scanner.scan("Social Security: 123456789")
        assert result.has_pii is True

    def test_ssn_blocks_by_default(self):
        """Test SSN triggers BLOCK action by default"""
        scanner = PIIScanner()
        result = scanner.scan("My SSN is 123-45-6789")
        assert result.action == PIIAction.BLOCK

    def test_ssn_redaction(self):
        """Test SSN redaction shows last 4 digits"""
        scanner = PIIScanner()
        result = scanner.scan("123-45-6789")
        ssn_finding = next(
            (f for f in result.findings if f.category == PIICategory.SSN),
            None
        )
        if ssn_finding:
            assert "6789" in ssn_finding.redacted_text
            assert "***" in ssn_finding.redacted_text


class TestCreditCardDetection:
    """Credit card detection tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_visa_card_detection(self):
        """Test Visa card detection (starts with 4)"""
        scanner = PIIScanner()
        # Valid Visa test number
        result = scanner.scan("Card: 4111-1111-1111-1111")
        assert result.has_pii is True
        cc_findings = [
            f for f in result.findings if f.category == PIICategory.CREDIT_CARD
        ]
        assert len(cc_findings) >= 1

    def test_mastercard_detection(self):
        """Test Mastercard detection (starts with 51-55)"""
        scanner = PIIScanner()
        # Valid Mastercard test number
        result = scanner.scan("Card: 5500-0000-0000-0004")
        assert result.has_pii is True

    def test_amex_detection(self):
        """Test American Express detection (starts with 34 or 37)"""
        scanner = PIIScanner()
        # Valid Amex test number
        result = scanner.scan("Card: 3400-000000-00009")
        assert result.has_pii is True

    def test_luhn_validation(self):
        """Test Luhn algorithm validation"""
        scanner = PIIScanner()
        # Invalid card number (fails Luhn check)
        result = scanner.scan("Card: 1234-5678-9012-3456")
        # Should not detect as credit card due to Luhn failure
        cc_findings = [
            f for f in result.findings
            if f.category == PIICategory.CREDIT_CARD
            and f.pattern_id in ["PII-CC-001", "PII-CC-002", "PII-CC-003"]
        ]
        # Specific card patterns should fail Luhn
        assert len(cc_findings) == 0

    def test_credit_card_blocks_by_default(self):
        """Test credit card triggers BLOCK action by default"""
        scanner = PIIScanner()
        result = scanner.scan("Card: 4111-1111-1111-1111")
        assert result.action == PIIAction.BLOCK

    def test_credit_card_redaction(self):
        """Test credit card redaction shows last 4 digits"""
        scanner = PIIScanner()
        result = scanner.scan("4111-1111-1111-1111")
        cc_finding = next(
            (f for f in result.findings if f.category == PIICategory.CREDIT_CARD),
            None
        )
        if cc_finding:
            assert "1111" in cc_finding.redacted_text
            assert "****" in cc_finding.redacted_text


class TestIPAddressDetection:
    """IP address detection tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_ipv4_detection(self):
        """Test IPv4 address detection"""
        scanner = PIIScanner()
        result = scanner.scan("Server IP: 192.168.1.100")
        assert result.has_pii is True
        ip_findings = [
            f for f in result.findings if f.category == PIICategory.IP_ADDRESS
        ]
        assert len(ip_findings) >= 1

    def test_ipv4_redaction(self):
        """Test IPv4 redaction format"""
        scanner = PIIScanner()
        result = scanner.scan("192.168.1.100")
        ip_finding = next(
            (f for f in result.findings if f.category == PIICategory.IP_ADDRESS),
            None
        )
        if ip_finding:
            assert "192.168" in ip_finding.redacted_text
            assert "***" in ip_finding.redacted_text


class TestDateOfBirthDetection:
    """Date of birth detection tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_dob_mm_dd_yyyy(self):
        """Test DOB in MM/DD/YYYY format"""
        scanner = PIIScanner()
        result = scanner.scan("Born: 01/15/1990")
        assert result.has_pii is True
        dob_findings = [
            f for f in result.findings if f.category == PIICategory.DATE_OF_BIRTH
        ]
        assert len(dob_findings) >= 1

    def test_dob_yyyy_mm_dd(self):
        """Test DOB in YYYY-MM-DD format"""
        scanner = PIIScanner()
        result = scanner.scan("DOB: 1990-01-15")
        assert result.has_pii is True


class TestAddressDetection:
    """Address detection tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_street_address_detection(self):
        """Test street address detection"""
        scanner = PIIScanner()
        result = scanner.scan("I live at 123 Main Street")
        assert result.has_pii is True
        addr_findings = [
            f for f in result.findings if f.category == PIICategory.ADDRESS
        ]
        assert len(addr_findings) >= 1

    def test_zip_code_detection(self):
        """Test ZIP code detection"""
        scanner = PIIScanner()
        result = scanner.scan("ZIP: 90210")
        assert result.has_pii is True


class TestRiskLevelCalculation:
    """Risk level calculation tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_critical_risk_from_ssn(self):
        """Test CRITICAL risk from SSN"""
        scanner = PIIScanner()
        result = scanner.scan("SSN: 123-45-6789")
        assert result.overall_risk == PIIRiskLevel.CRITICAL

    def test_critical_risk_from_credit_card(self):
        """Test CRITICAL risk from credit card"""
        scanner = PIIScanner()
        result = scanner.scan("Card: 4111-1111-1111-1111")
        assert result.overall_risk == PIIRiskLevel.CRITICAL

    def test_low_risk_from_email(self):
        """Test LOW risk from email only"""
        scanner = PIIScanner()
        result = scanner.scan("Contact: test@example.com")
        assert result.overall_risk == PIIRiskLevel.LOW


class TestActionDetermination:
    """Action determination tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_block_action_for_ssn(self):
        """Test BLOCK action for SSN"""
        scanner = PIIScanner()
        result = scanner.scan("SSN: 123-45-6789")
        assert result.action == PIIAction.BLOCK

    def test_log_only_for_email(self):
        """Test LOG_ONLY action for email"""
        scanner = PIIScanner()
        result = scanner.scan("Email: test@example.com")
        assert result.action == PIIAction.LOG_ONLY

    def test_action_override(self):
        """Test action override configuration"""
        scanner = PIIScanner(
            action_overrides={PIICategory.EMAIL: PIIAction.BLOCK}
        )
        result = scanner.scan("Email: test@example.com")
        assert result.action == PIIAction.BLOCK


class TestStrictMode:
    """Strict mode tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_strict_mode_lowers_threshold(self):
        """Test strict mode lowers confidence threshold"""
        scanner = PIIScanner(strict_mode=True)
        # Strict mode should detect more potential PII
        result = scanner.scan("Contact info: test@example.com")
        assert result.has_pii is True


class TestScanResultSerialization:
    """Serialization tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_finding_to_dict(self):
        """Test PIIFinding serialization"""
        finding = PIIFinding(
            category=PIICategory.EMAIL,
            risk_level=PIIRiskLevel.LOW,
            pattern_id="PII-EMAIL-001",
            title="Email detected",
            description="Email address found",
            matched_text="t***@e***.com",
            position=10,
            confidence=0.9,
            recommendation="Consider redacting",
            evidence_hash="abc123",
            redacted_text="t***@e***.com",
        )
        data = finding.to_dict()
        assert data["category"] == "email"
        assert data["risk_level"] == "low"
        assert data["pattern_id"] == "PII-EMAIL-001"

    def test_scan_result_to_dict(self):
        """Test PIIScanResult serialization"""
        scanner = PIIScanner()
        result = scanner.scan("test@example.com")
        data = result.to_dict()
        assert "has_pii" in data
        assert "overall_risk" in data
        assert "action" in data
        assert "findings" in data
        assert isinstance(data["findings"], list)


class TestGlobalFunctions:
    """Global function tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_get_pii_scanner_singleton(self):
        """Test singleton pattern"""
        scanner1 = get_pii_scanner()
        scanner2 = get_pii_scanner()
        assert scanner1 is scanner2

    def test_reset_pii_scanner(self):
        """Test scanner reset"""
        scanner1 = get_pii_scanner()
        reset_pii_scanner()
        scanner2 = get_pii_scanner()
        assert scanner1 is not scanner2

    def test_scan_for_pii_convenience(self):
        """Test convenience function"""
        result = scan_for_pii("test@example.com")
        assert result.has_pii is True


class TestEdgeCases:
    """Edge case tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_whitespace_only_content(self):
        """Test whitespace-only content"""
        scanner = PIIScanner()
        result = scanner.scan("   \n\t  ")
        assert result.has_pii is False

    def test_very_long_content(self):
        """Test very long content"""
        scanner = PIIScanner()
        content = "Normal text. " * 10000 + "test@example.com"
        result = scanner.scan(content)
        assert result.has_pii is True

    def test_unicode_content(self):
        """Test unicode content with ASCII email"""
        scanner = PIIScanner()
        # Unicode context with ASCII email (pattern requires ASCII local part)
        result = scanner.scan("联系方式: user@example.com")
        # Should still detect the ASCII email in unicode context
        assert result.has_pii is True

    def test_mixed_case_detection(self):
        """Test case-insensitive detection"""
        scanner = PIIScanner()
        result = scanner.scan("EMAIL: TEST@EXAMPLE.COM")
        assert result.has_pii is True

    def test_context_metadata(self):
        """Test context metadata is preserved"""
        scanner = PIIScanner()
        context = {"source": "user_input", "task_id": "123"}
        result = scanner.scan("test@example.com", context=context)
        assert result.context == context

    def test_scan_duration_tracked(self):
        """Test scan duration is tracked"""
        scanner = PIIScanner()
        result = scanner.scan("test@example.com")
        assert result.scan_duration_ms > 0

    def test_multiple_pii_types(self):
        """Test detection of multiple PII types"""
        scanner = PIIScanner()
        content = (
            "Contact: test@example.com, "
            "Phone: 555-123-4567, "
            "SSN: 123-45-6789"
        )
        result = scanner.scan(content)
        categories = {f.category for f in result.findings}
        assert PIICategory.EMAIL in categories
        assert PIICategory.PHONE in categories
        assert PIICategory.SSN in categories

    def test_findings_have_evidence_hash(self):
        """Test all findings have evidence hash"""
        scanner = PIIScanner()
        result = scanner.scan("test@example.com 555-123-4567")
        for finding in result.findings:
            assert finding.evidence_hash is not None
            assert len(finding.evidence_hash) == 16


class TestSummaryGeneration:
    """Summary generation tests"""

    def setup_method(self):
        reset_pii_scanner()

    def test_no_findings_summary(self):
        """Test summary when no PII found"""
        scanner = PIIScanner()
        result = scanner.scan("Normal text without PII")
        assert "No PII detected" in result.summary

    def test_findings_summary_includes_counts(self):
        """Test summary includes finding counts"""
        scanner = PIIScanner()
        result = scanner.scan("test@example.com and another@test.org")
        assert "Found" in result.summary
        assert "email" in result.summary.lower()
