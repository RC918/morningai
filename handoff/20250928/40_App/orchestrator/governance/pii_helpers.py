"""
PII Scanner Helper Classes - EPIC E Phase E-5 SRP Refactoring

Blueprint Reference: Section 3.3 (Agent Separation Principle)
Issue #3942: Extract pattern checkers for PIIScanner - SRP refactoring
Issue #3943: Enhanced passport and driver license patterns

This module extracts validation and redaction logic from PIIScanner
to follow Single Responsibility Principle (SRP).

Classes:
- PIIPatternValidator: Validation logic for PII patterns (Luhn, checksums, etc.)
- PIIRedactor: Redaction logic for different PII types
- PIIConfidenceCalculator: Context-aware confidence scoring
"""
import logging
import re
import threading
from typing import Dict, List, Optional

from governance.pii_scanner import PIICategory

logger = logging.getLogger(__name__)


class PIIPatternValidator:
    """
    Validates PII matches using category-specific rules.

    Issue #3942: Extracted from PIIScanner for SRP compliance.
    Issue #3943: Enhanced validation for passport and driver license.

    Blueprint Alignment:
    - Section 3.3: Agent Separation Principle - single responsibility
    - Section 4.2: Compliance Radar v2 - improved accuracy
    """

    # US State driver license formats (Issue #3943)
    # Format: (prefix_pattern, digit_count, state_name)
    US_DL_FORMATS: Dict[str, tuple] = {
        # California: 1 letter + 7 digits
        "CA": (r"^[A-Z]\d{7}$", "California"),
        # New York: 9 digits or 1 letter + 7 digits + 1 digit
        "NY": (r"^(\d{9}|[A-Z]\d{7}\d)$", "New York"),
        # Texas: 8 digits
        "TX": (r"^\d{8}$", "Texas"),
        # Florida: 1 letter + 12 digits
        "FL": (r"^[A-Z]\d{12}$", "Florida"),
        # Illinois: 1 letter + 11 digits
        "IL": (r"^[A-Z]\d{11}$", "Illinois"),
        # Pennsylvania: 8 digits
        "PA": (r"^\d{8}$", "Pennsylvania"),
        # Ohio: 2 letters + 6 digits
        "OH": (r"^[A-Z]{2}\d{6}$", "Ohio"),
        # Georgia: 7-9 digits
        "GA": (r"^\d{7,9}$", "Georgia"),
        # North Carolina: 1-12 digits
        "NC": (r"^\d{1,12}$", "North Carolina"),
        # Michigan: 1 letter + 12 digits
        "MI": (r"^[A-Z]\d{12}$", "Michigan"),
    }

    # Country-specific passport formats (Issue #3943)
    # Format: (pattern, checksum_func_name, country_name)
    PASSPORT_FORMATS: Dict[str, tuple] = {
        # US: 9 digits (no checksum)
        "US": (r"^\d{9}$", None, "United States"),
        # UK: 9 digits (no checksum)
        "UK": (r"^\d{9}$", None, "United Kingdom"),
        # Canada: 2 letters + 6 digits
        "CA": (r"^[A-Z]{2}\d{6}$", None, "Canada"),
        # Germany: 9 alphanumeric (ICAO format with checksum)
        "DE": (r"^[CFGHJKLMNPRTVWXYZ0-9]{9}$", "icao_checksum", "Germany"),
        # France: 9 alphanumeric
        "FR": (r"^[0-9A-Z]{9}$", None, "France"),
        # Australia: 1-2 letters + 7 digits
        "AU": (r"^[A-Z]{1,2}\d{7}$", None, "Australia"),
        # Japan: 2 letters + 7 digits
        "JP": (r"^[A-Z]{2}\d{7}$", None, "Japan"),
        # China: E/G + 8 digits or 9 digits
        "CN": (r"^([EG]\d{8}|\d{9})$", None, "China"),
    }

    def validate(self, text: str, category: PIICategory) -> bool:
        """
        Validate a match using category-specific rules.

        Args:
            text: The matched text to validate
            category: The PII category

        Returns:
            True if the match is valid, False otherwise
        """
        if category == PIICategory.CREDIT_CARD:
            return self.luhn_check(text)
        elif category == PIICategory.PASSPORT:
            return self.validate_passport(text)
        elif category == PIICategory.DRIVER_LICENSE:
            return self.validate_driver_license(text)
        return True

    def luhn_check(self, card_number: str) -> bool:
        """
        Validate credit card number using Luhn algorithm.

        Args:
            card_number: The card number to validate

        Returns:
            True if valid Luhn checksum, False otherwise
        """
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

    def validate_passport(self, text: str) -> bool:
        """
        Validate passport number format.

        Issue #3943: Enhanced validation with country-specific patterns.

        Args:
            text: The passport number to validate

        Returns:
            True if matches any known passport format, False otherwise
        """
        # Clean the text
        clean_text = re.sub(r'[\s-]', '', text.upper())

        # Check against known formats
        for country_code, (pattern, checksum_func, _) in self.PASSPORT_FORMATS.items():
            if re.match(pattern, clean_text):
                # If checksum validation is required
                if checksum_func == "icao_checksum":
                    if self._icao_checksum(clean_text):
                        return True
                else:
                    return True

        # Fallback: accept if it looks like a passport number
        # 8-9 alphanumeric characters
        if re.match(r'^[A-Z0-9]{8,9}$', clean_text):
            return True

        return False

    def validate_driver_license(self, text: str) -> bool:
        """
        Validate driver license number format.

        Issue #3943: Enhanced validation with state-specific patterns.

        Args:
            text: The driver license number to validate

        Returns:
            True if matches any known DL format, False otherwise
        """
        # Clean the text
        clean_text = re.sub(r'[\s-]', '', text.upper())

        # Check against known US state formats
        for state_code, (pattern, _) in self.US_DL_FORMATS.items():
            if re.match(pattern, clean_text):
                return True

        # Fallback: accept generic alphanumeric format
        # 7-13 alphanumeric characters starting with letter(s)
        if re.match(r'^[A-Z]{1,2}[A-Z0-9]{5,11}$', clean_text):
            return True

        return False

    def _icao_checksum(self, text: str) -> bool:
        """
        Validate ICAO Machine Readable Zone checksum.

        Used for some passport formats (e.g., German passports).

        Args:
            text: The text to validate

        Returns:
            True if valid checksum, False otherwise
        """
        # ICAO checksum weights: 7, 3, 1 repeating
        weights = [7, 3, 1]
        char_values = {
            '<': 0, '0': 0, '1': 1, '2': 2, '3': 3, '4': 4,
            '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14,
            'F': 15, 'G': 16, 'H': 17, 'I': 18, 'J': 19,
            'K': 20, 'L': 21, 'M': 22, 'N': 23, 'O': 24,
            'P': 25, 'Q': 26, 'R': 27, 'S': 28, 'T': 29,
            'U': 30, 'V': 31, 'W': 32, 'X': 33, 'Y': 34, 'Z': 35,
        }

        try:
            total = 0
            for i, char in enumerate(text[:-1]):  # Exclude check digit
                value = char_values.get(char.upper(), 0)
                total += value * weights[i % 3]
            expected_check = total % 10
            actual_check = int(text[-1])
            return expected_check == actual_check
        except (ValueError, KeyError) as e:
            logger.debug(
                "ICAO checksum validation failed for input: %s, error: %s",
                text[:2] + "***" if len(text) > 2 else "***",
                type(e).__name__,
            )
            return False

    def get_passport_country(self, text: str) -> Optional[str]:
        """
        Identify the country of a passport number.

        Args:
            text: The passport number

        Returns:
            Country name if identified, None otherwise
        """
        clean_text = re.sub(r'[\s-]', '', text.upper())

        for country_code, (pattern, _, country_name) in self.PASSPORT_FORMATS.items():
            if re.match(pattern, clean_text):
                return country_name

        return None

    def get_dl_state(self, text: str) -> Optional[str]:
        """
        Identify the US state of a driver license number.

        Args:
            text: The driver license number

        Returns:
            State name if identified, None otherwise
        """
        clean_text = re.sub(r'[\s-]', '', text.upper())

        for state_code, (pattern, state_name) in self.US_DL_FORMATS.items():
            if re.match(pattern, clean_text):
                return state_name

        return None


class PIIRedactor:
    """
    Handles redaction of PII text.

    Issue #3942: Extracted from PIIScanner for SRP compliance.

    Blueprint Alignment:
    - Section 3.3: Agent Separation Principle - single responsibility
    - Section 9.2: Safe by Design - redaction protects PII/secrets
    """

    # Maximum length for matched text in logs (security)
    MAX_MATCHED_TEXT_LOG_LENGTH = 20

    def sanitize_for_log(self, text: str) -> str:
        """
        Sanitize matched text for logging (prevent full PII exposure).

        Args:
            text: The text to sanitize

        Returns:
            Sanitized text safe for logging
        """
        if not text:
            return ""
        if len(text) <= self.MAX_MATCHED_TEXT_LOG_LENGTH:
            # Still partially redact even short text
            if len(text) > 4:
                return text[:2] + "*" * (len(text) - 4) + text[-2:]
            return "*" * len(text)
        # For longer text, show first 2 and last 2 chars
        return text[:2] + "*" * 16 + text[-2:]

    def redact(self, text: str, category: PIICategory) -> str:
        """
        Generate redacted version of PII text.

        Args:
            text: The text to redact
            category: The PII category

        Returns:
            Redacted version of the text
        """
        if category == PIICategory.EMAIL:
            return self._redact_email(text)
        elif category == PIICategory.PHONE:
            return self._redact_phone(text)
        elif category == PIICategory.SSN:
            return self._redact_ssn(text)
        elif category == PIICategory.CREDIT_CARD:
            return self._redact_credit_card(text)
        elif category == PIICategory.IP_ADDRESS:
            return self._redact_ip(text)
        elif category == PIICategory.PASSPORT:
            return self._redact_passport(text)
        elif category == PIICategory.DRIVER_LICENSE:
            return self._redact_driver_license(text)
        else:
            return f"[REDACTED_{category.value.upper()}]"

    def _redact_email(self, text: str) -> str:
        """Redact email: user@domain.com -> u***@d***.com"""
        parts = text.split("@")
        if len(parts) == 2:
            user = parts[0][0] + "***" if parts[0] else "***"
            domain_parts = parts[1].split(".")
            if len(domain_parts) >= 2:
                domain = domain_parts[0][0] + "***" if domain_parts[0] else "***"
                tld = ".".join(domain_parts[1:])
                return f"{user}@{domain}.{tld}"
        return "[REDACTED_EMAIL]"

    def _redact_phone(self, text: str) -> str:
        """Redact phone: show last 4 digits."""
        digits = re.sub(r'\D', '', text)
        if len(digits) >= 4:
            return "***-***-" + digits[-4:]
        return "[REDACTED_PHONE]"

    def _redact_ssn(self, text: str) -> str:
        """Redact SSN: show last 4 digits."""
        digits = re.sub(r'\D', '', text)
        if len(digits) >= 4:
            return "***-**-" + digits[-4:]
        return "[REDACTED_SSN]"

    def _redact_credit_card(self, text: str) -> str:
        """Redact credit card: show last 4 digits."""
        digits = re.sub(r'\D', '', text)
        if len(digits) >= 4:
            return "****-****-****-" + digits[-4:]
        return "[REDACTED_CC]"

    def _redact_ip(self, text: str) -> str:
        """Redact IP: show first two octets."""
        parts = text.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.***.***"
        return "[REDACTED_IP]"

    def _redact_passport(self, text: str) -> str:
        """Redact passport: show first 2 and last 2 chars."""
        if len(text) > 4:
            return text[:2] + "*" * (len(text) - 4) + text[-2:]
        elif len(text) == 4:
            return text[0] + "**" + text[-1]
        return "[REDACTED_PASSPORT]"

    def _redact_driver_license(self, text: str) -> str:
        """Redact driver license: show first 2 and last 2 chars."""
        if len(text) > 4:
            return text[:2] + "*" * (len(text) - 4) + text[-2:]
        elif len(text) == 4:
            return text[0] + "**" + text[-1]
        return "[REDACTED_DL]"


class PIIConfidenceCalculator:
    """
    Calculates confidence scores for PII matches.

    Issue #3942: Extracted from PIIScanner for SRP compliance.
    Issue #3943: Enhanced context keywords for passport and driver license.

    Blueprint Alignment:
    - Section 3.3: Agent Separation Principle - single responsibility
    - Section 4.2: Compliance Radar v2 - improved accuracy
    """

    # Context keywords that increase confidence (Issue #3943: enhanced)
    CONTEXT_KEYWORDS: Dict[PIICategory, List[str]] = {
        PIICategory.EMAIL: ["email", "contact", "reach", "send", "mail"],
        PIICategory.PHONE: ["phone", "call", "mobile", "cell", "tel", "fax"],
        PIICategory.SSN: ["ssn", "social security", "tax id", "taxpayer"],
        PIICategory.CREDIT_CARD: [
            "card", "payment", "credit", "debit", "visa", "mastercard", "amex"
        ],
        PIICategory.ADDRESS: [
            "address", "live", "reside", "located", "street", "avenue"
        ],
        PIICategory.DATE_OF_BIRTH: ["born", "birthday", "dob", "birth", "age"],
        PIICategory.PASSPORT: [
            "passport", "travel", "visa", "immigration", "border",
            "international", "document", "id number"
        ],
        PIICategory.DRIVER_LICENSE: [
            "driver", "license", "licence", "dl", "driving", "dmv",
            "motor vehicle", "id card", "identification"
        ],
        PIICategory.IP_ADDRESS: ["ip", "address", "network", "server", "host"],
        PIICategory.NAME: ["name", "called", "known as", "mr", "ms", "mrs"],
    }

    def calculate(
        self,
        match: re.Match,
        content: str,
        category: PIICategory,
        strict_mode: bool = False,
    ) -> float:
        """
        Calculate confidence score for a match.

        Args:
            match: The regex match object
            content: The full content being scanned
            category: The PII category
            strict_mode: Whether to use stricter thresholds

        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.8

        # Adjust based on context
        matched_text = match.group(0)
        start = max(0, match.start() - 50)
        end = min(len(content), match.end() + 50)
        context_text = content[start:end].lower()

        # Look for contextual keywords that increase confidence
        keywords = self.CONTEXT_KEYWORDS.get(category, [])
        keyword_boost = 0.0
        for keyword in keywords:
            if keyword in context_text:
                keyword_boost = 0.1
                break

        base_confidence = min(1.0, base_confidence + keyword_boost)

        # Reduce confidence for very short matches
        if len(matched_text) < 5:
            base_confidence *= 0.7

        # Issue #3943: Additional confidence adjustments for passport/DL
        if category == PIICategory.PASSPORT:
            base_confidence = self._adjust_passport_confidence(
                matched_text, context_text, base_confidence
            )
        elif category == PIICategory.DRIVER_LICENSE:
            base_confidence = self._adjust_dl_confidence(
                matched_text, context_text, base_confidence
            )

        return round(base_confidence, 2)

    def _adjust_passport_confidence(
        self,
        matched_text: str,
        context_text: str,
        base_confidence: float,
    ) -> float:
        """
        Adjust confidence for passport numbers.

        Issue #3943: Reduce false positives for generic patterns.
        """
        # Boost if context mentions specific countries
        country_keywords = [
            "us passport", "uk passport", "canadian", "german",
            "french", "australian", "japanese", "chinese"
        ]
        for keyword in country_keywords:
            if keyword in context_text:
                return min(1.0, base_confidence + 0.15)

        # Reduce confidence if the number looks like a generic ID
        # (e.g., employee ID, order number)
        generic_keywords = [
            "order", "employee", "customer", "account", "reference",
            "invoice", "ticket", "confirmation"
        ]
        for keyword in generic_keywords:
            if keyword in context_text:
                return base_confidence * 0.6

        return base_confidence

    def _adjust_dl_confidence(
        self,
        matched_text: str,
        context_text: str,
        base_confidence: float,
    ) -> float:
        """
        Adjust confidence for driver license numbers.

        Issue #3943: Reduce false positives for generic patterns.
        """
        # Boost if context mentions specific states
        state_keywords = [
            "california", "new york", "texas", "florida", "illinois",
            "pennsylvania", "ohio", "georgia", "north carolina", "michigan"
        ]
        for keyword in state_keywords:
            if keyword in context_text:
                return min(1.0, base_confidence + 0.15)

        # Reduce confidence if the number looks like a generic ID
        generic_keywords = [
            "order", "employee", "customer", "account", "reference",
            "invoice", "ticket", "confirmation", "serial"
        ]
        for keyword in generic_keywords:
            if keyword in context_text:
                return base_confidence * 0.6

        return base_confidence


# Singleton instances for convenience
# Thread-safe initialization using double-checked locking pattern
_validator: Optional[PIIPatternValidator] = None
_redactor: Optional[PIIRedactor] = None
_confidence_calculator: Optional[PIIConfidenceCalculator] = None
_validator_lock = threading.Lock()
_redactor_lock = threading.Lock()
_confidence_calculator_lock = threading.Lock()


def get_pattern_validator() -> PIIPatternValidator:
    """Get or create global PIIPatternValidator instance (thread-safe)."""
    global _validator
    if _validator is None:
        with _validator_lock:
            if _validator is None:
                _validator = PIIPatternValidator()
    return _validator


def get_redactor() -> PIIRedactor:
    """Get or create global PIIRedactor instance (thread-safe)."""
    global _redactor
    if _redactor is None:
        with _redactor_lock:
            if _redactor is None:
                _redactor = PIIRedactor()
    return _redactor


def get_confidence_calculator() -> PIIConfidenceCalculator:
    """Get or create global PIIConfidenceCalculator instance (thread-safe)."""
    global _confidence_calculator
    if _confidence_calculator is None:
        with _confidence_calculator_lock:
            if _confidence_calculator is None:
                _confidence_calculator = PIIConfidenceCalculator()
    return _confidence_calculator
