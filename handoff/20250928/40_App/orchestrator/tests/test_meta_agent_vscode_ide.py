"""
Wrapper test file for VS Code IDE integration tests.

This file imports and re-exports tests from meta_agent/tests/test_vscode_ide.py
to ensure they are discovered by CI which runs `pytest tests/`.

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化
"""

import sys
from pathlib import Path

# Add orchestrator to path for imports
orchestrator_path = Path(__file__).parent.parent
if str(orchestrator_path) not in sys.path:
    sys.path.insert(0, str(orchestrator_path))

# Import all test classes from the original test file
from meta_agent.tests.test_vscode_ide import (  # noqa: E402
    TestDataclasses,
    TestEnums,
    TestVSCodeIDEService,
    TestLanguageDetection,
    TestOutputParsing,
    TestSessionStatistics,
    TestGlobalInstance,
    TestFormatterAndLinterConfig,
)

# Re-export all test classes so pytest discovers them
__all__ = [
    "TestDataclasses",
    "TestEnums",
    "TestVSCodeIDEService",
    "TestLanguageDetection",
    "TestOutputParsing",
    "TestSessionStatistics",
    "TestGlobalInstance",
    "TestFormatterAndLinterConfig",
]
