"""
Tests for PII Scanner Helper Classes

Issue #3942: Extract pattern checkers for PIIScanner - SRP refactoring
Issue #3943: Enhanced passport and driver license patterns

Blueprint Reference: Section 3.3 (Agent Separation Principle)
"""
import re

from governance.pii_scanner import PIICategory
from governance.pii_helpers import (
    PIIPatternValidator,
    PIIRedactor,
    PIIConfidenceCalculator,
    get_pattern_validator,
    get_redactor,
    get_confidence_calculator,
)


class TestPIIPatternValidator:
    """Tests for PIIPatternValidator class."""

    def test_luhn_check_valid_visa(self):
        """Test Luhn check with valid Visa card."""
        validator = PIIPatternValidator()
        assert validator.luhn_check("4111111111111111") is True

    def test_luhn_check_valid_mastercard(self):
        """Test Luhn check with valid Mastercard."""
        validator = PIIPatternValidator()
        assert validator.luhn_check("5500000000000004") is True

    def test_luhn_check_invalid_card(self):
        """Test Luhn check with invalid card number."""
        validator = PIIPatternValidator()
        assert validator.luhn_check("4111111111111112") is False

    def test_luhn_check_with_spaces(self):
        """Test Luhn check handles spaces in card number."""
        validator = PIIPatternValidator()
        assert validator.luhn_check("4111 1111 1111 1111") is True

    def test_luhn_check_with_dashes(self):
        """Test Luhn check handles dashes in card number."""
        validator = PIIPatternValidator()
        assert validator.luhn_check("4111-1111-1111-1111") is True

    def test_luhn_check_too_short(self):
        """Test Luhn check rejects too short numbers."""
        validator = PIIPatternValidator()
        assert validator.luhn_check("411111111111") is False

    def test_luhn_check_too_long(self):
        """Test Luhn check rejects too long numbers."""
        validator = PIIPatternValidator()
        assert validator.luhn_check("41111111111111111111") is False

    def test_validate_credit_card(self):
        """Test validate method for credit cards."""
        validator = PIIPatternValidator()
        assert validator.validate("4111111111111111", PIICategory.CREDIT_CARD) is True
        assert validator.validate("4111111111111112", PIICategory.CREDIT_CARD) is False

    def test_validate_passport_us_format(self):
        """Test validate method for US passport format."""
        validator = PIIPatternValidator()
        assert validator.validate_passport("123456789") is True

    def test_validate_passport_canadian_format(self):
        """Test validate method for Canadian passport format."""
        validator = PIIPatternValidator()
        assert validator.validate_passport("AB123456") is True

    def test_validate_passport_australian_format(self):
        """Test validate method for Australian passport format."""
        validator = PIIPatternValidator()
        assert validator.validate_passport("N1234567") is True
        assert validator.validate_passport("PA1234567") is True

    def test_validate_passport_chinese_format(self):
        """Test validate method for Chinese passport format."""
        validator = PIIPatternValidator()
        assert validator.validate_passport("E12345678") is True
        assert validator.validate_passport("G12345678") is True

    def test_validate_driver_license_california(self):
        """Test validate method for California DL format."""
        validator = PIIPatternValidator()
        assert validator.validate_driver_license("A1234567") is True

    def test_validate_driver_license_new_york(self):
        """Test validate method for New York DL format."""
        validator = PIIPatternValidator()
        assert validator.validate_driver_license("123456789") is True

    def test_validate_driver_license_ohio(self):
        """Test validate method for Ohio DL format."""
        validator = PIIPatternValidator()
        assert validator.validate_driver_license("AB123456") is True

    def test_validate_driver_license_florida(self):
        """Test validate method for Florida DL format."""
        validator = PIIPatternValidator()
        assert validator.validate_driver_license("A123456789012") is True

    def test_get_passport_country_us(self):
        """Test passport country identification for US."""
        validator = PIIPatternValidator()
        assert validator.get_passport_country("123456789") == "United States"

    def test_get_passport_country_canada(self):
        """Test passport country identification for Canada."""
        validator = PIIPatternValidator()
        assert validator.get_passport_country("AB123456") == "Canada"

    def test_get_passport_country_unknown(self):
        """Test passport country identification for unknown format."""
        validator = PIIPatternValidator()
        assert validator.get_passport_country("XYZ") is None

    def test_get_dl_state_california(self):
        """Test DL state identification for California."""
        validator = PIIPatternValidator()
        assert validator.get_dl_state("A1234567") == "California"

    def test_get_dl_state_ohio(self):
        """Test DL state identification for Ohio."""
        validator = PIIPatternValidator()
        assert validator.get_dl_state("AB123456") == "Ohio"

    def test_get_dl_state_unknown(self):
        """Test DL state identification for unknown format."""
        validator = PIIPatternValidator()
        assert validator.get_dl_state("XYZ") is None


class TestPIIRedactor:
    """Tests for PIIRedactor class."""

    def test_redact_email(self):
        """Test email redaction."""
        redactor = PIIRedactor()
        result = redactor.redact("user@example.com", PIICategory.EMAIL)
        assert result == "u***@e***.com"

    def test_redact_phone(self):
        """Test phone number redaction."""
        redactor = PIIRedactor()
        result = redactor.redact("123-456-7890", PIICategory.PHONE)
        assert result == "***-***-7890"

    def test_redact_ssn(self):
        """Test SSN redaction."""
        redactor = PIIRedactor()
        result = redactor.redact("123-45-6789", PIICategory.SSN)
        assert result == "***-**-6789"

    def test_redact_credit_card(self):
        """Test credit card redaction."""
        redactor = PIIRedactor()
        result = redactor.redact("4111-1111-1111-1111", PIICategory.CREDIT_CARD)
        assert result == "****-****-****-1111"

    def test_redact_ip_address(self):
        """Test IP address redaction."""
        redactor = PIIRedactor()
        result = redactor.redact("192.168.1.100", PIICategory.IP_ADDRESS)
        assert result == "192.168.***.***"

    def test_redact_passport(self):
        """Test passport redaction."""
        redactor = PIIRedactor()
        result = redactor.redact("123456789", PIICategory.PASSPORT)
        assert result == "12*****89"

    def test_redact_driver_license(self):
        """Test driver license redaction."""
        redactor = PIIRedactor()
        result = redactor.redact("A1234567", PIICategory.DRIVER_LICENSE)
        assert result == "A1****67"

    def test_redact_generic(self):
        """Test generic redaction for unknown category."""
        redactor = PIIRedactor()
        result = redactor.redact("some text", PIICategory.NAME)
        assert result == "[REDACTED_NAME]"

    def test_sanitize_for_log_short_text(self):
        """Test sanitize for log with short text."""
        redactor = PIIRedactor()
        result = redactor.sanitize_for_log("12345")
        assert result == "12*45"

    def test_sanitize_for_log_very_short_text(self):
        """Test sanitize for log with very short text."""
        redactor = PIIRedactor()
        result = redactor.sanitize_for_log("1234")
        assert result == "****"

    def test_sanitize_for_log_long_text(self):
        """Test sanitize for log with long text."""
        redactor = PIIRedactor()
        result = redactor.sanitize_for_log("12345678901234567890123456789")
        assert result == "12****************89"

    def test_sanitize_for_log_empty(self):
        """Test sanitize for log with empty text."""
        redactor = PIIRedactor()
        result = redactor.sanitize_for_log("")
        assert result == ""


class TestPIIConfidenceCalculator:
    """Tests for PIIConfidenceCalculator class."""

    def test_calculate_base_confidence(self):
        """Test base confidence calculation."""
        calculator = PIIConfidenceCalculator()
        content = "Contact me at test@example.com"
        match = re.search(r'test@example\.com', content)
        result = calculator.calculate(match, content, PIICategory.EMAIL)
        assert 0.8 <= result <= 1.0

    def test_calculate_with_context_keyword(self):
        """Test confidence boost with context keyword."""
        calculator = PIIConfidenceCalculator()
        content = "My email address is test@example.com"
        match = re.search(r'test@example\.com', content)
        result = calculator.calculate(match, content, PIICategory.EMAIL)
        assert result >= 0.9  # Should be boosted by "email" keyword

    def test_calculate_short_match_penalty(self):
        """Test confidence penalty for short matches."""
        calculator = PIIConfidenceCalculator()
        content = "The code is 1234"
        match = re.search(r'1234', content)
        result = calculator.calculate(match, content, PIICategory.CREDIT_CARD)
        assert result < 0.8  # Should be penalized for short match

    def test_calculate_passport_with_context(self):
        """Test passport confidence with travel context."""
        calculator = PIIConfidenceCalculator()
        content = "My US passport number is 123456789"
        match = re.search(r'123456789', content)
        result = calculator.calculate(match, content, PIICategory.PASSPORT)
        assert result >= 0.9  # Should be boosted by "passport" keyword

    def test_calculate_passport_generic_context_penalty(self):
        """Test passport confidence penalty with generic context."""
        calculator = PIIConfidenceCalculator()
        content = "Order number 123456789"
        match = re.search(r'123456789', content)
        result = calculator.calculate(match, content, PIICategory.PASSPORT)
        assert result < 0.8  # Should be penalized by "order" keyword

    def test_calculate_driver_license_with_context(self):
        """Test driver license confidence with DMV context."""
        calculator = PIIConfidenceCalculator()
        content = "My driver license number is A1234567"
        match = re.search(r'A1234567', content)
        result = calculator.calculate(match, content, PIICategory.DRIVER_LICENSE)
        assert result >= 0.9  # Should be boosted by "driver" keyword

    def test_calculate_driver_license_generic_context_penalty(self):
        """Test driver license confidence penalty with generic context."""
        calculator = PIIConfidenceCalculator()
        content = "Employee ID A1234567"
        match = re.search(r'A1234567', content)
        result = calculator.calculate(match, content, PIICategory.DRIVER_LICENSE)
        assert result < 0.8  # Should be penalized by "employee" keyword


class TestSingletonGetters:
    """Tests for singleton getter functions."""

    def test_get_pattern_validator_returns_same_instance(self):
        """Test that get_pattern_validator returns singleton."""
        v1 = get_pattern_validator()
        v2 = get_pattern_validator()
        assert v1 is v2

    def test_get_redactor_returns_same_instance(self):
        """Test that get_redactor returns singleton."""
        r1 = get_redactor()
        r2 = get_redactor()
        assert r1 is r2

    def test_get_confidence_calculator_returns_same_instance(self):
        """Test that get_confidence_calculator returns singleton."""
        c1 = get_confidence_calculator()
        c2 = get_confidence_calculator()
        assert c1 is c2


class TestEnhancedPatternIntegration:
    """Integration tests for enhanced passport and driver license patterns."""

    def test_passport_validation_via_pii_scanner(self):
        """Test passport validation through PIIScanner._validate_match."""
        from governance.pii_scanner import PIIScanner
        scanner = PIIScanner()
        # US passport format
        assert scanner._validate_match("123456789", PIICategory.PASSPORT) is True
        # Canadian passport format
        assert scanner._validate_match("AB123456", PIICategory.PASSPORT) is True

    def test_driver_license_validation_via_pii_scanner(self):
        """Test driver license validation through PIIScanner._validate_match."""
        from governance.pii_scanner import PIIScanner
        scanner = PIIScanner()
        # California DL format
        assert scanner._validate_match("A1234567", PIICategory.DRIVER_LICENSE) is True
        # Ohio DL format
        assert scanner._validate_match("AB123456", PIICategory.DRIVER_LICENSE) is True

    def test_confidence_calculation_via_pii_scanner(self):
        """Test confidence calculation through PIIScanner._calculate_confidence."""
        from governance.pii_scanner import PIIScanner
        scanner = PIIScanner()
        content = "My passport number is 123456789"
        match = re.search(r'123456789', content)
        confidence = scanner._calculate_confidence(match, content, PIICategory.PASSPORT)
        assert confidence >= 0.9  # Should be boosted by "passport" keyword
