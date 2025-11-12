#!/usr/bin/env python3
"""
Unit tests for classify_ci_output.py

Tests all 5 tiers of error detection logic with positive and negative cases.
"""

import unittest
from classify_ci_output import classify_output


class TestClassifyCIOutput(unittest.TestCase):
    """Test cases for CI output classifier."""
    
    
    def test_tier1_syntax_error(self):
        """Test Tier 1: SyntaxError detection."""
        output = "  File test.py, line 5\n    def foo(\nSyntaxError: invalid syntax"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "1")
        self.assertEqual(status, "FAIL")
        self.assertIn("SyntaxError", reason)
    
    def test_tier1_indentation_error(self):
        """Test Tier 1: IndentationError detection."""
        output = "IndentationError: unexpected indent"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "1")
        self.assertEqual(status, "FAIL")
        self.assertIn("IndentationError", reason)
    
    def test_tier1_import_error(self):
        """Test Tier 1: ImportError detection."""
        output = "ImportError: cannot import name 'foo' from 'bar'"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "1")
        self.assertEqual(status, "FAIL")
        self.assertIn("ImportError", reason)
    
    def test_tier1_module_not_found(self):
        """Test Tier 1: ModuleNotFoundError detection."""
        output = "ModuleNotFoundError: No module named 'requests'"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "1")
        self.assertEqual(status, "FAIL")
        self.assertIn("ModuleNotFoundError", reason)
    
    
    def test_tier2_timeout(self):
        """Test Tier 2: Timeout (exit 124) detection."""
        output = "Script running...\nProcessing data..."
        tier, status, reason = classify_output(output, 124)
        self.assertEqual(tier, "2")
        self.assertEqual(status, "PASS")
        self.assertIn("timed out", reason)
    
    
    def test_tier3_requests_connection_error(self):
        """Test Tier 3: requests.exceptions.ConnectionError."""
        output = "requests.exceptions.ConnectionError: Failed to establish connection"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_urllib3_new_connection_error(self):
        """Test Tier 3: urllib3.exceptions.NewConnectionError."""
        output = "urllib3.exceptions.NewConnectionError: Failed to establish a new connection"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_httpx_connect_error(self):
        """Test Tier 3: httpx.ConnectError."""
        output = "httpx.ConnectError: All connection attempts failed"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_aiohttp_client_connection_error(self):
        """Test Tier 3: aiohttp.ClientConnectionError."""
        output = "aiohttp.ClientConnectionError: Cannot connect to host"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_socket_gaierror(self):
        """Test Tier 3: socket.gaierror."""
        output = "socket.gaierror: [Errno -2] Name or service not known"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_connection_refused_error(self):
        """Test Tier 3: ConnectionRefusedError."""
        output = "ConnectionRefusedError: [Errno 111] Connection refused"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_timeout_error(self):
        """Test Tier 3: TimeoutError."""
        output = "TimeoutError: Connection timed out"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_connection_refused_message(self):
        """Test Tier 3: 'Connection refused' message."""
        output = "Error: Connection refused by server"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_econnrefused(self):
        """Test Tier 3: ECONNREFUSED error code."""
        output = "Error: ECONNREFUSED - Connection refused"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_max_retries_exceeded(self):
        """Test Tier 3: Max retries exceeded."""
        output = "HTTPSConnectionPool: Max retries exceeded with url"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_dns_resolution_error(self):
        """Test Tier 3: DNS resolution error."""
        output = "Temporary failure in name resolution"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    def test_tier3_network_unreachable(self):
        """Test Tier 3: Network unreachable."""
        output = "OSError: Network is unreachable"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
        self.assertIn("Network error", reason)
    
    
    def test_tier4_success(self):
        """Test Tier 4: Successful execution."""
        output = "Script completed successfully\nAll tasks done"
        tier, status, reason = classify_output(output, 0)
        self.assertEqual(tier, "4")
        self.assertEqual(status, "PASS")
        self.assertIn("successfully", reason)
    
    
    def test_tier5_value_error(self):
        """Test Tier 5: ValueError (non-network error)."""
        output = "ValueError: invalid literal for int() with base 10"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "5")
        self.assertEqual(status, "FAIL")
        self.assertIn("Unknown error", reason)
    
    def test_tier5_key_error(self):
        """Test Tier 5: KeyError (non-network error)."""
        output = "KeyError: 'missing_key'"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "5")
        self.assertEqual(status, "FAIL")
        self.assertIn("Unknown error", reason)
    
    def test_tier5_attribute_error(self):
        """Test Tier 5: AttributeError (non-network error)."""
        output = "AttributeError: 'NoneType' object has no attribute 'foo'"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "5")
        self.assertEqual(status, "FAIL")
        self.assertIn("Unknown error", reason)
    
    def test_tier5_unknown_exit_code(self):
        """Test Tier 5: Unknown exit code."""
        output = "Some generic error message"
        tier, status, reason = classify_output(output, 42)
        self.assertEqual(tier, "5")
        self.assertEqual(status, "FAIL")
        self.assertIn("exit code 42", reason)
    
    
    def test_no_false_positive_timeout_in_message(self):
        """Test that 'timeout' in non-network context doesn't match Tier 3."""
        output = "ValueError: timeout parameter must be positive"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "5")
        self.assertEqual(status, "FAIL")
    
    def test_tier1_takes_precedence_over_tier3(self):
        """Test that Tier 1 (critical) takes precedence over Tier 3 (network)."""
        output = "SyntaxError: invalid syntax\nConnection refused"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "1")
        self.assertEqual(status, "FAIL")
        self.assertIn("SyntaxError", reason)
    
    def test_case_insensitive_matching(self):
        """Test that pattern matching is case-insensitive."""
        output = "connectionrefusederror: connection refused"
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
    
    def test_multiline_output(self):
        """Test classification with multiline output."""
        output = """
        Starting script...
        Connecting to server...
        requests.exceptions.ConnectionError: Failed to connect
        Traceback (most recent call last):
          File "test.py", line 10, in <module>
        """
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "3")
        self.assertEqual(status, "PASS")
    
    def test_empty_output(self):
        """Test classification with empty output."""
        output = ""
        tier, status, reason = classify_output(output, 1)
        self.assertEqual(tier, "5")
        self.assertEqual(status, "FAIL")
    
    def test_empty_output_success(self):
        """Test classification with empty output but success exit code."""
        output = ""
        tier, status, reason = classify_output(output, 0)
        self.assertEqual(tier, "4")
        self.assertEqual(status, "PASS")


if __name__ == "__main__":
    unittest.main()
