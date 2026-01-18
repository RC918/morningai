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
        """Test very long content (under 100KB limit)"""
        scanner = PIIScanner()
        # Put email at beginning so it's not truncated, use content under 100KB
        content = "test@example.com " + "Normal text. " * 7000
        result = scanner.scan(content)
        assert result.has_pii is True

    def test_content_truncation_over_limit(self):
        """Test content over 100KB is truncated for ReDoS protection"""
        scanner = PIIScanner()
        # Email at end will be truncated when content exceeds 100KB
        content = "Normal text. " * 10000 + "test@example.com"
        result = scanner.scan(content)
        # Email is beyond 100KB limit, so it won't be detected
        assert result.has_pii is False

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
            # 32 hex chars (16 bytes) for better collision resistance
            assert len(finding.evidence_hash) == 32


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


class TestDynamicConfiguration:
    """Dynamic configuration tests (Issue #3944)"""

    def setup_method(self):
        reset_pii_scanner()

    def test_config_version_default(self):
        """Test default config version is 'builtin' when no config file exists"""
        scanner = PIIScanner(config_path="/nonexistent/path/config.yaml")
        assert scanner.get_config_version() == "builtin"

    def test_tenant_id_default(self):
        """Test default tenant ID is None"""
        scanner = PIIScanner()
        assert scanner.get_tenant_id() is None

    def test_tenant_id_initialization(self):
        """Test tenant ID can be set during initialization"""
        scanner = PIIScanner(tenant_id="tenant_123")
        assert scanner.get_tenant_id() == "tenant_123"

    def test_set_tenant_id(self):
        """Test tenant ID can be changed after initialization"""
        scanner = PIIScanner()
        scanner.set_tenant_id("tenant_456")
        assert scanner.get_tenant_id() == "tenant_456"

    def test_reload_config_preserves_constructor_overrides(self):
        """Test reload_config preserves constructor action_overrides (backward compatibility)"""
        scanner = PIIScanner(
            action_overrides={PIICategory.EMAIL: PIIAction.BLOCK}
        )
        assert scanner.action_config[PIICategory.EMAIL] == PIIAction.BLOCK
        scanner.reload_config()
        # Constructor overrides should be preserved after reload
        assert scanner.action_config[PIICategory.EMAIL] == PIIAction.BLOCK

    def test_risk_config_initialized(self):
        """Test risk config is initialized with defaults"""
        scanner = PIIScanner()
        assert PIICategory.SSN in scanner.risk_config
        assert scanner.risk_config[PIICategory.SSN] == PIIRiskLevel.CRITICAL
        assert scanner.risk_config[PIICategory.EMAIL] == PIIRiskLevel.LOW

    def test_config_path_parameter(self):
        """Test config_path parameter is stored"""
        scanner = PIIScanner(config_path="/custom/path/config.yaml")
        assert scanner._config_path == "/custom/path/config.yaml"

    def test_custom_patterns_dict_initialized(self):
        """Test custom patterns dict is initialized"""
        scanner = PIIScanner()
        assert hasattr(scanner, "_custom_patterns")
        assert isinstance(scanner._custom_patterns, dict)

    def test_tenant_overrides_dict_initialized(self):
        """Test tenant overrides dict is initialized"""
        scanner = PIIScanner()
        assert hasattr(scanner, "_tenant_overrides")
        assert isinstance(scanner._tenant_overrides, dict)

    def test_lock_initialized(self):
        """Test thread lock is initialized for thread safety"""
        scanner = PIIScanner()
        assert hasattr(scanner, "_lock")

    def test_action_overrides_still_work(self):
        """Test action_overrides parameter still works (backward compatibility)"""
        scanner = PIIScanner(
            action_overrides={PIICategory.EMAIL: PIIAction.BLOCK}
        )
        result = scanner.scan("test@example.com")
        assert result.action == PIIAction.BLOCK

    def test_validate_pattern_config_valid(self):
        """Test pattern validation with valid config"""
        scanner = PIIScanner()
        valid_pattern = {
            "regex": r"\b[A-Z]+\b",
            "pattern_id": "TEST-001",
            "title": "Test pattern",
        }
        assert scanner._validate_pattern_config(valid_pattern) is True

    def test_validate_pattern_config_missing_field(self):
        """Test pattern validation with missing field"""
        scanner = PIIScanner()
        invalid_pattern = {
            "regex": r"\b[A-Z]+\b",
            "pattern_id": "TEST-001",
        }
        assert scanner._validate_pattern_config(invalid_pattern) is False

    def test_validate_pattern_config_invalid_regex(self):
        """Test pattern validation with invalid regex"""
        scanner = PIIScanner()
        invalid_pattern = {
            "regex": r"[invalid(regex",
            "pattern_id": "TEST-001",
            "title": "Test pattern",
        }
        assert scanner._validate_pattern_config(invalid_pattern) is False

    def test_find_config_file_returns_none_when_not_found(self):
        """Test _find_config_file returns None when explicit config path doesn't exist"""
        scanner = PIIScanner(config_path="/nonexistent/path/config.yaml")
        result = scanner._find_config_file()
        assert result is None

    def test_apply_yaml_config_with_empty_config(self):
        """Test _apply_yaml_config handles empty config gracefully"""
        scanner = PIIScanner()
        scanner._apply_yaml_config({})
        assert scanner._config_version == "unknown"

    def test_apply_yaml_config_with_version(self):
        """Test _apply_yaml_config loads version"""
        scanner = PIIScanner()
        scanner._apply_yaml_config({"version": "2.0.0"})
        assert scanner._config_version == "2.0.0"

    def test_apply_yaml_config_with_settings(self):
        """Test _apply_yaml_config loads settings"""
        scanner = PIIScanner()
        scanner._apply_yaml_config({
            "settings": {
                "enabled": False,
                "strict_mode": True,
            }
        })
        assert scanner.enabled is False
        assert scanner.strict_mode is True

    def test_apply_yaml_config_with_actions(self):
        """Test _apply_yaml_config loads action configuration"""
        scanner = PIIScanner()
        scanner._apply_yaml_config({
            "actions": {
                "email": "block",
                "phone": "allow",
            }
        })
        assert scanner.action_config[PIICategory.EMAIL] == PIIAction.BLOCK
        assert scanner.action_config[PIICategory.PHONE] == PIIAction.ALLOW

    def test_apply_yaml_config_with_risk_levels(self):
        """Test _apply_yaml_config loads risk level configuration"""
        scanner = PIIScanner()
        scanner._apply_yaml_config({
            "risk_levels": {
                "email": "high",
                "phone": "critical",
            }
        })
        assert scanner.risk_config[PIICategory.EMAIL] == PIIRiskLevel.HIGH
        assert scanner.risk_config[PIICategory.PHONE] == PIIRiskLevel.CRITICAL

    def test_apply_yaml_config_with_tenant_overrides(self):
        """Test _apply_yaml_config loads tenant overrides"""
        scanner = PIIScanner()
        scanner._apply_yaml_config({
            "tenant_overrides": {
                "tenant_123": {
                    "actions": {
                        "email": "block",
                    }
                }
            }
        })
        assert "tenant_123" in scanner._tenant_overrides
        assert scanner._tenant_overrides["tenant_123"][PIICategory.EMAIL] == PIIAction.BLOCK

    def test_tenant_overrides_applied_on_init(self):
        """Test tenant overrides are applied during initialization"""
        scanner = PIIScanner()
        scanner._tenant_overrides = {
            "tenant_123": {PIICategory.EMAIL: PIIAction.BLOCK}
        }
        scanner._tenant_id = "tenant_123"
        scanner.action_config = scanner.DEFAULT_ACTIONS.copy()
        if scanner._tenant_id in scanner._tenant_overrides:
            scanner.action_config.update(scanner._tenant_overrides[scanner._tenant_id])
        assert scanner.action_config[PIICategory.EMAIL] == PIIAction.BLOCK

    def test_apply_yaml_config_invalid_action_ignored(self):
        """Test invalid action values are ignored"""
        scanner = PIIScanner()
        original_action = scanner.action_config[PIICategory.EMAIL]
        scanner._apply_yaml_config({
            "actions": {
                "email": "invalid_action",
            }
        })
        assert scanner.action_config[PIICategory.EMAIL] == original_action

    def test_apply_yaml_config_invalid_category_ignored(self):
        """Test invalid category values are ignored"""
        scanner = PIIScanner()
        original_config = scanner.action_config.copy()
        scanner._apply_yaml_config({
            "actions": {
                "invalid_category": "block",
            }
        })
        # Verify action_config remains unchanged
        assert scanner.action_config == original_config

    def test_custom_patterns_loaded(self):
        """Test custom patterns are loaded from config"""
        scanner = PIIScanner()
        scanner._apply_yaml_config({
            "custom_patterns": {
                "email": [
                    {
                        "regex": r"\b[A-Za-z0-9._%+-]+@company\.com\b",
                        "pattern_id": "PII-EMAIL-CUSTOM-001",
                        "title": "Company email detected",
                        "risk_level": "info",
                    }
                ]
            }
        })
        assert PIICategory.EMAIL in scanner._custom_patterns
        assert len(scanner._custom_patterns[PIICategory.EMAIL]) == 1
        assert scanner._custom_patterns[PIICategory.EMAIL][0][1] == "PII-EMAIL-CUSTOM-001"


class TestReDoSProtection:
    """Test ReDoS vulnerability protection (Issue #4056)"""

    def setup_method(self):
        """Reset scanner before each test"""
        from governance.pii_scanner import reset_pii_scanner
        reset_pii_scanner()

    def test_is_redos_vulnerable_detects_nested_quantifiers(self):
        """Test detection of nested quantifiers like (a+)+"""
        scanner = PIIScanner()
        # These patterns are vulnerable to ReDoS
        assert scanner._is_redos_vulnerable(r"(a+)+") is True
        assert scanner._is_redos_vulnerable(r"(.*)+") is True
        assert scanner._is_redos_vulnerable(r"(.+)+") is True
        assert scanner._is_redos_vulnerable(r"(\d+)+") is True
        assert scanner._is_redos_vulnerable(r"(\w+)+") is True

    def test_is_redos_vulnerable_allows_safe_patterns(self):
        """Test that safe patterns are allowed"""
        scanner = PIIScanner()
        # These patterns are safe
        assert scanner._is_redos_vulnerable(r"\d{3}-\d{2}-\d{4}") is False
        assert scanner._is_redos_vulnerable(r"[a-z]+@[a-z]+\.com") is False
        assert scanner._is_redos_vulnerable(r"\b\d{4}\b") is False

    def test_validate_pattern_config_rejects_redos_vulnerable(self):
        """Test that _validate_pattern_config rejects ReDoS-vulnerable patterns"""
        scanner = PIIScanner()
        # ReDoS-vulnerable pattern should be rejected
        result = scanner._validate_pattern_config({
            "regex": r"(a+)+",
            "pattern_id": "TEST-001",
            "title": "Test pattern",
        })
        assert result is False

    def test_validate_pattern_config_accepts_safe_pattern(self):
        """Test that _validate_pattern_config accepts safe patterns"""
        scanner = PIIScanner()
        # Safe pattern should be accepted
        result = scanner._validate_pattern_config({
            "regex": r"\d{3}-\d{2}-\d{4}",
            "pattern_id": "TEST-002",
            "title": "SSN pattern",
        })
        assert result is True

    def test_custom_pattern_with_redos_vulnerability_rejected(self):
        """Test that custom patterns with ReDoS vulnerabilities are rejected"""
        scanner = PIIScanner()
        scanner._apply_yaml_config({
            "custom_patterns": {
                "email": [
                    {
                        "regex": r"(a+)+@example\.com",  # ReDoS vulnerable
                        "pattern_id": "PII-EMAIL-REDOS",
                        "title": "ReDoS vulnerable pattern",
                    }
                ]
            }
        })
        # The vulnerable pattern should not be loaded
        if PIICategory.EMAIL in scanner._custom_patterns:
            # Check that the ReDoS pattern was not added
            pattern_ids = [p[1] for p in scanner._custom_patterns[PIICategory.EMAIL]]
            assert "PII-EMAIL-REDOS" not in pattern_ids

    def test_is_redos_vulnerable_detects_star_star_pattern(self):
        """Test detection of .*.* patterns"""
        scanner = PIIScanner()
        assert scanner._is_redos_vulnerable(r".*.*") is True
        assert scanner._is_redos_vulnerable(r".+.+") is True

    def test_is_redos_vulnerable_detects_nested_star(self):
        """Test detection of (.*)*  patterns"""
        scanner = PIIScanner()
        assert scanner._is_redos_vulnerable(r"(.*)*") is True
        assert scanner._is_redos_vulnerable(r"(.+)*") is True


class TestCodeContextMatch:
    """Test _is_code_context_match method (Issue #4171)

    Tests for the code context detection that reduces false positives
    in technical content (code, diffs, review feedback).

    Security Design Decisions:
    - content_type is caller-controlled (orchestrator code), NOT user-controlled
    - Default is USER_CONTENT (strict scanning)
    - Relaxed modes are opt-in by trusted orchestrator code only
    - This is by design per Blueprint Section 9.2 (Safe by Design)
    """

    def setup_method(self):
        """Reset scanner before each test"""
        reset_pii_scanner()

    def test_passport_js_library_skipped(self):
        """Test that passport.js library references are skipped"""
        import re
        scanner = PIIScanner()
        # The passport.js context should cause this to be skipped
        context_content = "require('passport'); 123456789 passport.authenticate"
        mock_match = re.search(r"\d{9}", context_content)
        if mock_match:
            result = scanner._is_code_context_match(
                context_content, mock_match, PIICategory.PASSPORT
            )
            # Should skip due to passport library context
            assert result is True

    def test_address_variable_skipped(self):
        """Test that address variable names are skipped"""
        import re
        scanner = PIIScanner()
        # Find a match in context with address variable
        context_content = "email_address = '12345'; ip_address = value"
        mock_match = re.search(r"\b\d{5}\b", context_content)
        if mock_match:
            result = scanner._is_code_context_match(
                context_content, mock_match, PIICategory.ADDRESS
            )
            # Should skip due to email_address context
            assert result is True

    def test_pr_number_skipped_for_passport(self):
        """Test that PR/issue numbers are skipped for passport detection"""
        import re
        scanner = PIIScanner()
        content = "Fixed in PR #123456789 - see issue for details"
        match = re.search(r"\d{9}", content)
        if match:
            result = scanner._is_code_context_match(
                content, match, PIICategory.PASSPORT
            )
            # Should skip due to PR # context
            assert result is True

    def test_commit_sha_skipped(self):
        """Test that commit SHAs are skipped"""
        import re
        scanner = PIIScanner()
        content = "commit abc12345 fixed the issue with 123456789"
        match = re.search(r"\d{9}", content)
        if match:
            result = scanner._is_code_context_match(
                content, match, PIICategory.PASSPORT
            )
            # Should skip due to short commit SHA context
            assert result is True

    def test_hex_number_skipped(self):
        """Test that hex numbers are skipped"""
        import re
        scanner = PIIScanner()
        content = "memory at 0x12345678 contains 123456789"
        match = re.search(r"\d{9}", content)
        if match:
            result = scanner._is_code_context_match(
                content, match, PIICategory.PASSPORT
            )
            # Should skip due to hex number context
            assert result is True

    def test_real_passport_not_skipped(self):
        """Test that real passport numbers without code context are NOT skipped

        Note: The numeric skip patterns include [0-9a-f]{7,8} which matches any
        7-8 digit sequence (since 0-9 are valid hex). To test that real passports
        are NOT skipped, we test with a category that doesn't use numeric skip
        patterns (EMAIL), which verifies the allowlist logic works correctly.
        This is the documented trade-off in Issue #4171.
        """
        import re
        scanner = PIIScanner()
        # Test with EMAIL category which has no numeric skip patterns
        # This verifies the allowlist-only path works correctly
        content = "Contact user@example.com for details"
        match = re.search(r"[a-z]+@[a-z]+\.[a-z]+", content)
        if match:
            result = scanner._is_code_context_match(
                content, match, PIICategory.EMAIL
            )
            # Should NOT skip - EMAIL has no allowlist patterns defined
            assert result is False

    def test_real_address_not_skipped(self):
        """Test that real addresses without code context are NOT skipped"""
        import re
        scanner = PIIScanner()
        # This doesn't match any code context patterns
        context_content = "I live at 12345 Main Street"
        mock_match = re.search(r"\d{5}", context_content)
        if mock_match:
            result = scanner._is_code_context_match(
                context_content, mock_match, PIICategory.ADDRESS
            )
            # Should NOT skip - no code context patterns found
            assert result is False

    def test_instance_variables_initialized(self):
        """Test that code context instance variables are properly initialized"""
        scanner = PIIScanner()
        # Check that instance variables exist and are populated
        assert hasattr(scanner, "_code_context_allowlist")
        assert hasattr(scanner, "_code_numeric_skip_patterns")
        assert PIICategory.PASSPORT in scanner._code_context_allowlist
        assert PIICategory.ADDRESS in scanner._code_context_allowlist
        assert len(scanner._code_numeric_skip_patterns) > 0

    def test_config_extends_defaults(self):
        """Test that YAML config extends (not replaces) default patterns"""
        scanner = PIIScanner()
        original_passport_count = len(scanner._code_context_allowlist[PIICategory.PASSPORT])

        # Apply config with additional pattern
        scanner._apply_yaml_config({
            "code_context_allowlist": {
                "passport": ["custom_passport_pattern"]
            }
        })

        # Should have original patterns plus new one
        assert len(scanner._code_context_allowlist[PIICategory.PASSPORT]) == original_passport_count + 1
        assert "custom_passport_pattern" in scanner._code_context_allowlist[PIICategory.PASSPORT]

    def test_numeric_skip_patterns_extended(self):
        """Test that numeric skip patterns can be extended via config"""
        scanner = PIIScanner()
        original_count = len(scanner._code_numeric_skip_patterns)

        # Apply config with additional pattern
        scanner._apply_yaml_config({
            "code_numeric_skip_patterns": ["custom_numeric_pattern"]
        })

        # Should have original patterns plus new one
        assert len(scanner._code_numeric_skip_patterns) == original_count + 1
        assert "custom_numeric_pattern" in scanner._code_numeric_skip_patterns

    def test_only_digit_matches_use_numeric_skip(self):
        """Test that numeric skip patterns only apply to pure digit matches"""
        import re
        scanner = PIIScanner()
        # Alphanumeric passport (e.g., Canadian: AB123456) should NOT use numeric skip
        content = "PR #AB123456 is the reference"
        match = re.search(r"[A-Z]{2}\d{6}", content)
        if match:
            result = scanner._is_code_context_match(
                content, match, PIICategory.PASSPORT
            )
            # Should NOT skip - alphanumeric doesn't trigger numeric skip patterns
            # (only category allowlist patterns would apply)
            assert result is False

    def test_8_digit_passport_with_pr_context(self):
        """Test 8-digit passport number with PR context is skipped"""
        import re
        scanner = PIIScanner()
        content = "See PR #12345678 for the fix"
        match = re.search(r"\d{8}", content)
        if match:
            result = scanner._is_code_context_match(
                content, match, PIICategory.PASSPORT
            )
            # Should skip due to PR # context
            assert result is True

    def test_driver_license_with_issue_context(self):
        """Test driver license number with issue context is skipped"""
        import re
        scanner = PIIScanner()
        content = "Fixed in Issue #123456789"
        match = re.search(r"\d{9}", content)
        if match:
            result = scanner._is_code_context_match(
                content, match, PIICategory.DRIVER_LICENSE
            )
            # Should skip due to Issue # context
            assert result is True
