#!/usr/bin/env python3
"""
CI Output Classifier for Python Scripts CI Workflow

This script classifies Python script output to determine if errors are acceptable
(network/timeout) or critical (syntax/import). It implements the 5-tier error
detection logic used by the Python Scripts CI workflow.

Usage:
    python .github/scripts/classify_ci_output.py <exit_code> < output.txt

Exit Codes:
    0 - PASS (acceptable error or success)
    1 - FAIL (critical error)

Tiers:
    1. Critical syntax/import errors → FAIL
    2. Timeout (exit 124) → PASS
    3. Network errors → PASS
    4. Success (exit 0) → PASS
    5. Unknown errors → FAIL
"""

import re
import sys
from typing import List, Tuple


NETWORK_ERROR_PATTERNS: List[Tuple[str, str]] = [
    (r'\brequests\.exceptions\.ConnectionError\b', 'requests.exceptions.ConnectionError'),
    (r'\brequests\.exceptions\.Timeout\b', 'requests.exceptions.Timeout'),
    (r'\brequests\.exceptions\.ConnectTimeout\b', 'requests.exceptions.ConnectTimeout'),
    (r'\brequests\.exceptions\.ReadTimeout\b', 'requests.exceptions.ReadTimeout'),
    (r'\brequests\.exceptions\.RequestException\b', 'requests.exceptions.RequestException'),
    
    (r'\burllib3\.exceptions\.NewConnectionError\b', 'urllib3.exceptions.NewConnectionError'),
    (r'\burllib3\.exceptions\.MaxRetryError\b', 'urllib3.exceptions.MaxRetryError'),
    (r'\burllib3\.exceptions\.TimeoutError\b', 'urllib3.exceptions.TimeoutError'),
    (r'\burllib3\.exceptions\.ReadTimeoutError\b', 'urllib3.exceptions.ReadTimeoutError'),
    
    (r'\bhttpx\.ConnectError\b', 'httpx.ConnectError'),
    (r'\bhttpx\.ConnectTimeout\b', 'httpx.ConnectTimeout'),
    (r'\bhttpx\.ReadTimeout\b', 'httpx.ReadTimeout'),
    (r'\bhttpx\.WriteTimeout\b', 'httpx.WriteTimeout'),
    (r'\bhttpx\.PoolTimeout\b', 'httpx.PoolTimeout'),
    (r'\bhttpx\.NetworkError\b', 'httpx.NetworkError'),
    (r'\bhttpx\.TimeoutException\b', 'httpx.TimeoutException'),
    
    (r'\baiohttp\.ClientConnectionError\b', 'aiohttp.ClientConnectionError'),
    (r'\baiohttp\.ClientConnectorError\b', 'aiohttp.ClientConnectorError'),
    (r'\baiohttp\.ServerTimeoutError\b', 'aiohttp.ServerTimeoutError'),
    (r'\baiohttp\.ServerDisconnectedError\b', 'aiohttp.ServerDisconnectedError'),
    
    (r'\bsocket\.gaierror\b', 'socket.gaierror'),
    (r'\bsocket\.timeout\b', 'socket.timeout'),
    (r'\bsocket\.herror\b', 'socket.herror'),
    
    (r'\bConnectionRefusedError\b', 'ConnectionRefusedError'),
    (r'\bConnectionResetError\b', 'ConnectionResetError'),
    (r'\bConnectionAbortedError\b', 'ConnectionAbortedError'),
    (r'\bTimeoutError\b', 'TimeoutError'),
    (r'\bOSError.*Connection\b', 'OSError (Connection)'),
    
    (r'\bHTTPSConnectionPool\b', 'HTTPSConnectionPool'),
    (r'\bHTTPConnectionPool\b', 'HTTPConnectionPool'),
    (r'\bMax retries exceeded\b', 'Max retries exceeded'),
    
    (r'\bConnection refused\b', 'Connection refused'),
    (r'\bConnection reset\b', 'Connection reset'),
    (r'\bConnection aborted\b', 'Connection aborted'),
    (r'\bConnection closed\b', 'Connection closed'),
    
    (r'\bECONNREFUSED\b', 'ECONNREFUSED'),
    (r'\bECONNRESET\b', 'ECONNRESET'),
    (r'\bETIMEDOUT\b', 'ETIMEDOUT'),
    (r'\bEHOSTUNREACH\b', 'EHOSTUNREACH'),
    (r'\bENETUNREACH\b', 'ENETUNREACH'),
    
    (r'\btimed out\b', 'timed out'),
    (r'\bConnection timed out\b', 'Connection timed out'),
    
    (r'\bNameResolutionError\b', 'NameResolutionError'),
    (r'\bTemporary failure in name resolution\b', 'Temporary failure in name resolution'),
    (r'\bName or service not known\b', 'Name or service not known'),
    (r'\bgaierror\b', 'gaierror'),
    (r'\bFailed to resolve\b', 'Failed to resolve'),
    
    (r'\bNetwork is unreachable\b', 'Network is unreachable'),
    (r'\bHost is unreachable\b', 'Host is unreachable'),
]

CRITICAL_ERROR_PATTERNS: List[Tuple[str, str]] = [
    (r'\bSyntaxError\b', 'SyntaxError'),
    (r'\bIndentationError\b', 'IndentationError'),
    (r'\bImportError\b', 'ImportError'),
    (r'\bModuleNotFoundError\b', 'ModuleNotFoundError'),
]


def classify_output(output: str, exit_code: int) -> Tuple[str, str, str]:
    """
    Classify script output according to 5-tier logic.
    
    Args:
        output: Script output (stdout + stderr)
        exit_code: Script exit code
    
    Returns:
        Tuple of (tier, status, reason)
        - tier: "1", "2", "3", "4", or "5"
        - status: "PASS" or "FAIL"
        - reason: Human-readable explanation
    """
    for pattern, name in CRITICAL_ERROR_PATTERNS:
        if re.search(pattern, output, re.IGNORECASE):
            return ("1", "FAIL", f"Critical error detected: {name}")
    
    if exit_code == 124:
        return ("2", "PASS", "Script timed out (expected in CI)")
    
    for pattern, name in NETWORK_ERROR_PATTERNS:
        if re.search(pattern, output, re.IGNORECASE):
            return ("3", "PASS", f"Network error detected: {name}")
    
    if exit_code == 0:
        return ("4", "PASS", "Script executed successfully")
    
    return ("5", "FAIL", f"Unknown error (exit code {exit_code})")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: classify_ci_output.py <exit_code>", file=sys.stderr)
        print("Reads output from stdin", file=sys.stderr)
        sys.exit(2)
    
    try:
        exit_code = int(sys.argv[1])
    except ValueError:
        print(f"Error: Invalid exit code '{sys.argv[1]}'", file=sys.stderr)
        sys.exit(2)
    
    output = sys.stdin.read()
    
    tier, status, reason = classify_output(output, exit_code)
    
    print(f"TIER={tier}")
    print(f"STATUS={status}")
    print(f"REASON={reason}")
    
    sys.exit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
