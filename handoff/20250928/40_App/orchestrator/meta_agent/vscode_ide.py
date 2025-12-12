"""
VS Code IDE Integration - Built-in IDE Editing and Testing

This module provides VS Code IDE integration for task execution environments,
enabling code editing, testing, and development workflows within isolated VMs.

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化

Architecture:
    TaskVM → VSCodeIDEService → code-server → IDE Features
                                    ↓
                            - File editing
                            - Code search
                            - Linting/formatting
                            - Test execution
                            - LSP integration

Features:
    - File operations (open, edit, save)
    - Code search and navigation
    - Code formatting and linting
    - Test execution and results
    - Language Server Protocol support
    - Terminal/shell access
"""

import asyncio
import logging
import shlex
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

# MCP Client configuration
MCP_DEFAULT_TIMEOUT = 30  # seconds
# Note: With MCP_MAX_RETRIES=3 and MCP_RETRY_DELAY=1.0, exponential backoff (1s, 2s, 4s)
# behaves similarly to linear backoff (1s, 2s, 3s). The difference becomes significant
# only with higher retry counts. Using exponential backoff for future scalability.
MCP_MAX_RETRIES = 3
MCP_RETRY_DELAY = 1.0  # seconds, base delay for exponential backoff (delay = MCP_RETRY_DELAY * 2^attempt)
MCP_ERROR_LOG_MAX_LENGTH = 500  # Max characters for error logs (Issue #2075)
MCP_SHELL_EXEC_TIMEOUT_BUFFER = 5  # seconds, buffer for network latency (Issue #2071)

# Session capability constants (Issue #2023)
# Terminal access is a privileged capability that allows execution of arbitrary
# shell commands in the VM. This capability must be explicitly granted by trusted
# services/admins and should never be wired to untrusted user input.
# See: handoff/20250928/40_App/orchestrator/docs/TERMINAL_ACCESS.md
TERMINAL_ACCESS_CAPABILITY = "terminal_access_enabled"


def _truncate_error_message(message: Optional[str], max_length: int = MCP_ERROR_LOG_MAX_LENGTH) -> Optional[str]:
    """
    Truncate error message to prevent sensitive data leakage in logs.

    Issue #2075: MCP server error responses may contain sensitive information
    (stack traces, environment variables, tokens). This function truncates
    error messages to a safe length for logging.

    Args:
        message: Error message to truncate
        max_length: Maximum allowed length (default: MCP_ERROR_LOG_MAX_LENGTH)

    Returns:
        Truncated message with ellipsis if truncated
    """
    if not message or len(message) <= max_length:
        return message
    return message[:max_length] + "... [truncated]"


class IDESessionStatus(Enum):
    """IDE session lifecycle status"""
    INITIALIZING = "initializing"  # Session being created
    READY = "ready"  # Session ready for use
    ACTIVE = "active"  # Session in active use
    SUSPENDED = "suspended"  # Session temporarily suspended
    CLOSED = "closed"  # Session closed
    ERROR = "error"  # Session in error state


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"


@dataclass
class FileContent:
    """Represents file content with metadata"""
    path: str
    content: str
    language: Optional[Language] = None
    line_count: int = 0
    size_bytes: int = 0
    last_modified: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "path": self.path,
            "content": self.content,
            "language": self.language.value if self.language else None,
            "line_count": self.line_count,
            "size_bytes": self.size_bytes,
            "last_modified": (
                self.last_modified.isoformat() if self.last_modified else None
            ),
        }


@dataclass
class SearchResult:
    """Represents a code search result"""
    file_path: str
    line_number: int
    line_content: str
    match_start: int = 0
    match_end: int = 0
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_content": self.line_content,
            "match_start": self.match_start,
            "match_end": self.match_end,
            "context_before": self.context_before,
            "context_after": self.context_after,
        }


@dataclass
class LintResult:
    """Represents a linting result"""
    file_path: str
    line_number: int
    column: int
    severity: str  # error, warning, info
    message: str
    rule_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "severity": self.severity,
            "message": self.message,
            "rule_id": self.rule_id,
        }


@dataclass
class TestResult:
    """Represents a test execution result"""
    test_name: str
    status: TestStatus
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "test_name": self.test_name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "file_path": self.file_path,
            "line_number": self.line_number,
        }


@dataclass
class TestSuiteResult:
    """Represents a test suite execution result"""
    suite_name: str
    tests: List[TestResult]
    total_duration_ms: float = 0.0
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "suite_name": self.suite_name,
            "tests": [t.to_dict() for t in self.tests],
            "total_duration_ms": self.total_duration_ms,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
        }


@dataclass
class IDESession:
    """Represents an IDE session for a task VM"""
    session_id: str
    vm_id: str
    task_id: str
    status: IDESessionStatus
    created_at: datetime
    workspace_path: str = "/workspace"
    vscode_endpoint: Optional[str] = None
    mcp_endpoint: Optional[str] = None
    active_file: Optional[str] = None
    open_files: List[str] = field(default_factory=list)
    last_activity: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "vm_id": self.vm_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "workspace_path": self.workspace_path,
            "vscode_endpoint": self.vscode_endpoint,
            "mcp_endpoint": self.mcp_endpoint,
            "active_file": self.active_file,
            "open_files": self.open_files,
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "error": self.error,
            "metadata": self.metadata,
        }


class VSCodeIDEService:
    """
    VS Code IDE integration service for task execution environments.

    This service provides IDE capabilities through code-server, enabling:
    - File editing and management
    - Code search and navigation
    - Linting and formatting
    - Test execution
    - Language Server Protocol support
    """

    # Default ports for code-server
    DEFAULT_VSCODE_PORT = 8443
    DEFAULT_MCP_PORT = 8080

    # Supported formatters by language
    FORMATTERS: Dict[Language, str] = {
        Language.PYTHON: "black",
        Language.TYPESCRIPT: "prettier --write",
        Language.JAVASCRIPT: "prettier --write",
        Language.GO: "gofmt -w",
        Language.RUST: "rustfmt",
        Language.JAVA: "google-java-format -i",
    }

    # Supported linters by language
    LINTERS: Dict[Language, str] = {
        Language.PYTHON: "ruff check",
        Language.TYPESCRIPT: "eslint",
        Language.JAVASCRIPT: "eslint",
        Language.GO: "golangci-lint run",
        Language.RUST: "cargo clippy",
        Language.JAVA: "checkstyle",
    }

    # Supported test runners by language
    TEST_RUNNERS: Dict[Language, str] = {
        Language.PYTHON: "pytest -v --tb=short",
        Language.TYPESCRIPT: "npm test",
        Language.JAVASCRIPT: "npm test",
        Language.GO: "go test -v",
        Language.RUST: "cargo test",
        Language.JAVA: "mvn test",
    }

    # Issue #2042: Class constant for terminal access capability key
    _TERMINAL_ACCESS_KEY = "terminal_access_enabled"

    def __init__(self):
        """Initialize the VS Code IDE service"""
        self._sessions: Dict[str, IDESession] = {}
        self._lock = asyncio.Lock()
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._http_session_lock = asyncio.Lock()
        logger.info("[VSCodeIDEService] Initialized")

    async def _get_http_session(self) -> aiohttp.ClientSession:
        """
        Get or create the shared aiohttp ClientSession.

        Issue #2076: Reuse ClientSession for better connection pooling,
        DNS caching, and reduced connection overhead.

        Returns:
            Shared aiohttp ClientSession instance
        """
        if self._http_session is None or self._http_session.closed:
            async with self._http_session_lock:
                if self._http_session is None or self._http_session.closed:
                    self._http_session = aiohttp.ClientSession()
                    logger.debug("[VSCodeIDEService] Created shared HTTP session")
        return self._http_session

    async def close(self) -> None:
        """
        Close the service and release resources.

        Issue #2076: Properly close the shared ClientSession to release
        TCP connections and other resources.
        """
        if self._http_session is not None and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None
            logger.info("[VSCodeIDEService] Closed shared HTTP session")

    async def create_session(
        self,
        vm_id: str,
        task_id: str,
        mcp_endpoint: str,
        workspace_path: str = "/workspace",
    ) -> IDESession:
        """
        Create a new IDE session for a task VM.

        Args:
            vm_id: ID of the VM
            task_id: ID of the task
            mcp_endpoint: MCP endpoint URL for the VM
            workspace_path: Path to the workspace directory

        Returns:
            IDESession instance
        """
        import uuid

        session_id = f"ide-{task_id[:8]}-{uuid.uuid4().hex[:8]}"

        # Derive VS Code endpoint from MCP endpoint
        vscode_endpoint = mcp_endpoint.replace(
            str(self.DEFAULT_MCP_PORT),
            str(self.DEFAULT_VSCODE_PORT)
        )

        session = IDESession(
            session_id=session_id,
            vm_id=vm_id,
            task_id=task_id,
            status=IDESessionStatus.INITIALIZING,
            created_at=datetime.now(),
            workspace_path=workspace_path,
            vscode_endpoint=vscode_endpoint,
            mcp_endpoint=mcp_endpoint,
        )

        async with self._lock:
            self._sessions[session_id] = session

        # Initialize the IDE session
        try:
            await self._initialize_session(session)
            session.status = IDESessionStatus.READY
            session.last_activity = datetime.now()
            logger.info(
                "[VSCodeIDEService] Created session %s for task %s",
                session_id, task_id[:8]
            )
        except Exception as e:
            logger.error(
                "[VSCodeIDEService] Failed to initialize session %s: %s",
                session_id, e
            )
            session.status = IDESessionStatus.ERROR
            session.error = str(e)

        return session

    async def _initialize_session(self, session: IDESession) -> None:
        """
        Initialize the IDE session by starting code-server if needed.

        This method:
        1. Checks if code-server is already running via health check
        2. Starts code-server if not running
        3. Ensures workspace directory exists
        4. Configures basic workspace settings (.vscode/settings.json)

        Args:
            session: IDE session to initialize

        Raises:
            RuntimeError: If code-server fails to start or workspace setup fails
        """
        session_id = session.session_id[:8]
        workspace_path = session.workspace_path

        logger.info(
            "[VSCodeIDEService] Initializing session %s for workspace %s",
            session_id, workspace_path
        )

        health_check = await self._execute_shell_command(
            session,
            "pgrep -f code-server || curl -s http://127.0.0.1:8443/healthz",
            timeout_seconds=10,
        )

        if not health_check.get("success") or health_check.get("exit_code") != 0:
            logger.info(
                "[VSCodeIDEService] code-server not running, starting for session %s",
                session_id
            )
            start_result = await self._execute_shell_command(
                session,
                f"code-server --bind-addr 0.0.0.0:8443 --auth none {shlex.quote(workspace_path)} &",
                timeout_seconds=10,
            )

            if not start_result.get("success"):
                raise RuntimeError(
                    f"Failed to start code-server: {start_result.get('stderr', 'Unknown error')}"
                )

            await asyncio.sleep(2)

            verify_result = await self._execute_shell_command(
                session,
                "pgrep -f code-server",
                timeout_seconds=5,
            )
            if not verify_result.get("success") or verify_result.get("exit_code") != 0:
                raise RuntimeError("code-server failed to start after 2 seconds")

            logger.info(
                "[VSCodeIDEService] code-server started successfully for session %s",
                session_id
            )
        else:
            logger.debug(
                "[VSCodeIDEService] code-server already running for session %s",
                session_id
            )

        mkdir_result = await self._execute_shell_command(
            session,
            f"mkdir -p {shlex.quote(workspace_path)}",
            timeout_seconds=10,
        )
        if not mkdir_result.get("success"):
            raise RuntimeError(
                f"Failed to create workspace directory: {mkdir_result.get('stderr', 'Unknown error')}"
            )

        vscode_dir = f"{workspace_path}/.vscode"
        settings_path = f"{vscode_dir}/settings.json"
        default_settings = '{"editor.formatOnSave": true, "editor.tabSize": 4}'

        await self._execute_shell_command(
            session,
            f"mkdir -p {shlex.quote(vscode_dir)}",
            timeout_seconds=10,
        )

        settings_result = await self._execute_mcp_command(
            session,
            "file/write",
            {
                "file_path": settings_path,
                "content": default_settings,
            },
            timeout_seconds=10,
        )

        if not settings_result.get("success"):
            fallback_result = await self._execute_shell_command(
                session,
                f"echo '{default_settings}' > {shlex.quote(settings_path)}",
                timeout_seconds=10,
            )
            if not fallback_result.get("success"):
                logger.warning(
                    "[VSCodeIDEService] Failed to create settings.json for session %s: %s",
                    session_id, fallback_result.get("stderr", "Unknown error")
                )

        session.metadata["code_server_url"] = session.vscode_endpoint
        session.metadata["initialized_at"] = datetime.now().isoformat()

        logger.info(
            "[VSCodeIDEService] Session %s initialized successfully",
            session_id
        )

    async def close_session(self, session_id: str) -> bool:
        """
        Close an IDE session.

        Args:
            session_id: ID of the session to close

        Returns:
            True if session was closed successfully
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False

            session.status = IDESessionStatus.CLOSED
            session.last_activity = datetime.now()
            logger.info("[VSCodeIDEService] Closed session %s", session_id)
            return True

    async def get_session(self, session_id: str) -> Optional[IDESession]:
        """Get an IDE session by ID"""
        return self._sessions.get(session_id)

    async def get_session_for_task(self, task_id: str) -> Optional[IDESession]:
        """Get the IDE session for a task"""
        for session in self._sessions.values():
            if session.task_id == task_id and session.status != IDESessionStatus.CLOSED:
                return session
        return None

    async def open_file(
        self,
        session: IDESession,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Open a file in the IDE.

        Args:
            session: IDE session
            file_path: Path to the file (relative to workspace)

        Returns:
            Dict with success status and file content
        """
        if session.status == IDESessionStatus.CLOSED:
            return {"success": False, "error": "Session is closed"}

        try:
            result = await self._execute_mcp_command(
                session,
                "file/read",
                {"file_path": file_path}
            )

            if result.get("success"):
                full_path = f"{session.workspace_path}/{file_path}"
                if full_path not in session.open_files:
                    session.open_files.append(full_path)
                session.active_file = full_path
                session.last_activity = datetime.now()
                session.status = IDESessionStatus.ACTIVE

            return result
        except Exception as e:
            logger.error(
                "[VSCodeIDEService] Failed to open file %s: %s",
                file_path, e
            )
            return {"success": False, "error": str(e)}

    async def edit_file(
        self,
        session: IDESession,
        file_path: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        Edit a file in the IDE.

        Args:
            session: IDE session
            file_path: Path to the file (relative to workspace)
            content: New file content

        Returns:
            Dict with success status
        """
        if session.status == IDESessionStatus.CLOSED:
            return {"success": False, "error": "Session is closed"}

        try:
            result = await self._execute_mcp_command(
                session,
                "file/write",
                {"file_path": file_path, "content": content}
            )

            if result.get("success"):
                session.last_activity = datetime.now()

            return result
        except Exception as e:
            logger.error(
                "[VSCodeIDEService] Failed to edit file %s: %s",
                file_path, e
            )
            return {"success": False, "error": str(e)}

    async def search_code(
        self,
        session: IDESession,
        query: str,
        file_pattern: Optional[str] = None,
        context_lines: int = 2,
    ) -> Dict[str, Any]:
        """
        Search for code in the workspace.

        Args:
            session: IDE session
            query: Search query (regex supported)
            file_pattern: Optional file pattern to filter (e.g., '*.py')
            context_lines: Number of context lines to include

        Returns:
            Dict with success status and search results
        """
        if session.status == IDESessionStatus.CLOSED:
            return {"success": False, "error": "Session is closed"}

        try:
            # Build grep command with proper escaping to prevent command injection
            include_flag = (
                f" --include={shlex.quote(file_pattern)}" if file_pattern else ""
            )
            context_flag = f" -C {context_lines}" if context_lines > 0 else ""
            command = f"grep -rn{context_flag} {shlex.quote(query)} .{include_flag}"

            result = await self._execute_shell_command(session, command)

            if result.get("success"):
                session.last_activity = datetime.now()
                # Parse grep output into SearchResult objects
                results = self._parse_grep_output(result.get("stdout", ""))
                result["results"] = [r.to_dict() for r in results]

            return result
        except Exception as e:
            logger.error(
                "[VSCodeIDEService] Failed to search code: %s", e
            )
            return {"success": False, "error": str(e)}

    def _parse_grep_output(self, output: str) -> List[SearchResult]:
        """Parse grep output into SearchResult objects"""
        results = []
        for line in output.strip().split("\n"):
            if not line or ":" not in line:
                continue
            try:
                # Format: file:line:content
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    results.append(SearchResult(
                        file_path=parts[0],
                        line_number=int(parts[1]),
                        line_content=parts[2],
                    ))
            except (ValueError, IndexError):
                continue
        return results

    async def format_code(
        self,
        session: IDESession,
        file_path: str,
        language: Optional[Language] = None,
    ) -> Dict[str, Any]:
        """
        Format code using language-specific formatter.

        Args:
            session: IDE session
            file_path: Path to the file to format
            language: Programming language (auto-detected if not provided)

        Returns:
            Dict with success status
        """
        if session.status == IDESessionStatus.CLOSED:
            return {"success": False, "error": "Session is closed"}

        # Auto-detect language if not provided
        if not language:
            language = self._detect_language(file_path)

        if not language:
            return {"success": False, "error": "Could not detect language"}

        formatter = self.FORMATTERS.get(language)
        if not formatter:
            return {"success": False, "error": f"No formatter for {language.value}"}

        try:
            # Use shlex.quote to prevent command injection
            command = f"{formatter} {shlex.quote(file_path)}"
            result = await self._execute_shell_command(session, command)

            if result.get("success"):
                session.last_activity = datetime.now()

            return result
        except Exception as e:
            logger.error(
                "[VSCodeIDEService] Failed to format %s: %s",
                file_path, e
            )
            return {"success": False, "error": str(e)}

    async def run_linter(
        self,
        session: IDESession,
        file_path: str,
        language: Optional[Language] = None,
    ) -> Dict[str, Any]:
        """
        Run linter on code.

        Args:
            session: IDE session
            file_path: Path to the file to lint
            language: Programming language (auto-detected if not provided)

        Returns:
            Dict with success status and lint results
        """
        if session.status == IDESessionStatus.CLOSED:
            return {"success": False, "error": "Session is closed"}

        # Auto-detect language if not provided
        if not language:
            language = self._detect_language(file_path)

        if not language:
            return {"success": False, "error": "Could not detect language"}

        linter = self.LINTERS.get(language)
        if not linter:
            return {"success": False, "error": f"No linter for {language.value}"}

        try:
            # Use shlex.quote to prevent command injection
            command = f"{linter} {shlex.quote(file_path)}"
            result = await self._execute_shell_command(session, command)

            session.last_activity = datetime.now()

            # Parse linter output into LintResult objects
            lint_results = self._parse_lint_output(
                result.get("stdout", "") + result.get("stderr", ""),
                language
            )
            result["lint_results"] = [r.to_dict() for r in lint_results]

            return result
        except Exception as e:
            logger.error(
                "[VSCodeIDEService] Failed to lint %s: %s",
                file_path, e
            )
            return {"success": False, "error": str(e)}

    def _parse_lint_output(
        self,
        output: str,
        language: Language
    ) -> List[LintResult]:
        """Parse linter output into LintResult objects"""
        results = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            try:
                # Generic parsing - format varies by linter
                # Most linters use: file:line:column: message
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    results.append(LintResult(
                        file_path=parts[0],
                        line_number=int(parts[1]) if parts[1].isdigit() else 0,
                        column=int(parts[2]) if parts[2].isdigit() else 0,
                        severity="error",
                        message=parts[3].strip(),
                    ))
            except (ValueError, IndexError):
                continue
        return results

    async def run_tests(
        self,
        session: IDESession,
        test_path: Optional[str] = None,
        language: Optional[Language] = None,
        test_pattern: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run tests in the workspace.

        Args:
            session: IDE session
            test_path: Path to test file or directory (default: workspace root)
            language: Programming language (auto-detected if not provided)
            test_pattern: Optional pattern to filter tests

        Returns:
            Dict with success status and test results
        """
        if session.status == IDESessionStatus.CLOSED:
            return {"success": False, "error": "Session is closed"}

        # Auto-detect language if not provided
        if not language:
            language = self._detect_project_language(session)

        if not language:
            return {"success": False, "error": "Could not detect project language"}

        test_runner = self.TEST_RUNNERS.get(language)
        if not test_runner:
            return {"success": False, "error": f"No test runner for {language.value}"}

        try:
            # Build test command with proper escaping to prevent command injection
            command = test_runner
            if test_path:
                command = f"{command} {shlex.quote(test_path)}"
            if test_pattern and language == Language.PYTHON:
                command = f"{command} -k {shlex.quote(test_pattern)}"

            result = await self._execute_shell_command(session, command)

            session.last_activity = datetime.now()

            # Parse test output into TestSuiteResult
            test_suite = self._parse_test_output(
                result.get("stdout", "") + result.get("stderr", ""),
                language
            )
            result["test_suite"] = test_suite.to_dict()

            return result
        except Exception as e:
            logger.error(
                "[VSCodeIDEService] Failed to run tests: %s", e
            )
            return {"success": False, "error": str(e)}

    def _parse_test_output(
        self,
        output: str,
        language: Language
    ) -> TestSuiteResult:
        """Parse test output into TestSuiteResult"""
        tests = []
        passed = 0
        failed = 0
        skipped = 0
        errors = 0

        # Simple parsing - real implementation would be language-specific
        for line in output.strip().split("\n"):
            if "PASSED" in line or "passed" in line:
                passed += 1
            elif "FAILED" in line or "failed" in line:
                failed += 1
            elif "SKIPPED" in line or "skipped" in line:
                skipped += 1
            elif "ERROR" in line or "error" in line:
                errors += 1

        return TestSuiteResult(
            suite_name="test_suite",
            tests=tests,
            passed_count=passed,
            failed_count=failed,
            skipped_count=skipped,
            error_count=errors,
        )

    async def start_lsp(
        self,
        session: IDESession,
        language: Language,
    ) -> Dict[str, Any]:
        """
        Start Language Server Protocol server for a language.

        Args:
            session: IDE session
            language: Programming language

        Returns:
            Dict with success status and LSP server info
        """
        if session.status == IDESessionStatus.CLOSED:
            return {"success": False, "error": "Session is closed"}

        try:
            result = await self._execute_mcp_command(
                session,
                "lsp/start",
                {"language": language.value}
            )

            if result.get("success"):
                session.last_activity = datetime.now()

            return result
        except Exception as e:
            logger.error(
                "[VSCodeIDEService] Failed to start LSP for %s: %s",
                language.value, e
            )
            return {"success": False, "error": str(e)}

    async def get_file_tree(
        self,
        session: IDESession,
        path: str = ".",
        max_depth: int = 3,
    ) -> Dict[str, Any]:
        """
        Get file tree structure.

        Args:
            session: IDE session
            path: Root path (default: workspace root)
            max_depth: Maximum depth to traverse

        Returns:
            Dict with success status and file tree
        """
        if session.status == IDESessionStatus.CLOSED:
            return {"success": False, "error": "Session is closed"}

        try:
            # Use shlex.quote to prevent command injection
            command = (
                f"tree -L {max_depth} "
                f"-I 'node_modules|__pycache__|.git|.venv' {shlex.quote(path)}"
            )
            result = await self._execute_shell_command(session, command)

            if result.get("success"):
                session.last_activity = datetime.now()

            return result
        except Exception as e:
            logger.error(
                "[VSCodeIDEService] Failed to get file tree: %s", e
            )
            return {"success": False, "error": str(e)}

    async def execute_terminal_command(
        self,
        session: IDESession,
        command: str,
        timeout_seconds: int = 60,
    ) -> Dict[str, Any]:
        """
        Execute a command in the terminal.

        SECURITY WARNING: This is a low-level, privileged API that executes
        arbitrary shell commands in the VM. Unlike other methods in this class
        (search_code, format_code, etc.) which construct commands from
        sanitized inputs, this method passes the command string directly to
        the shell without any escaping or validation.

        This method MUST only be called by:
        - Trusted, authenticated users via the IDE UI
        - Highly privileged internal components

        This method MUST NOT be:
        - Wired directly to untrusted HTTP request parameters
        - Called with user-supplied input without proper authorization checks

        CAPABILITY GATE (Issue #2023):
        This method requires the TERMINAL_ACCESS_CAPABILITY to be set in the
        session metadata. Sessions are created with this capability disabled
        by default. To enable terminal access, set:
            session.metadata[TERMINAL_ACCESS_CAPABILITY] = True

        For detailed authorization flow, see:
            handoff/20250928/40_App/orchestrator/docs/TERMINAL_ACCESS.md

        Args:
            session: IDE session
            command: Command to execute (passed directly to shell - no escaping)
            timeout_seconds: Command timeout in seconds

        Returns:
            Dict with success status and command output
        """
        if session.status == IDESessionStatus.CLOSED:
            return {"success": False, "error": "Session is closed"}

        # Issue #2023: Capability gate for terminal access
        if not self._has_terminal_capability(session):
            logger.warning(
                "[VSCodeIDEService] Denied terminal command for task %s: "
                "%s capability not granted",
                session.task_id[:8],
                TERMINAL_ACCESS_CAPABILITY,
            )
            return {
                "success": False,
                "error": f"Terminal access is not enabled for this session. "
                f"Set session.metadata['{TERMINAL_ACCESS_CAPABILITY}'] = True to enable.",
            }

        try:
            result = await self._execute_shell_command(
                session,
                command,
                timeout_seconds
            )

            if result.get("success"):
                session.last_activity = datetime.now()

            return result
        except Exception as e:
            logger.error(
                "[VSCodeIDEService] Failed to execute command: %s", e
            )
            return {"success": False, "error": str(e)}

    async def _execute_mcp_command(
        self,
        session: IDESession,
        endpoint: str,
        payload: Dict[str, Any],
        timeout_seconds: int = MCP_DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Execute a command via MCP endpoint with retry logic.

        Args:
            session: IDE session containing MCP endpoint
            endpoint: MCP endpoint path (e.g., 'file/read', 'file/write')
            payload: Request payload
            timeout_seconds: Request timeout in seconds

        Returns:
            Dict with success status and response data
        """
        if not session.mcp_endpoint:
            return {"success": False, "error": "No MCP endpoint configured"}

        url = f"{session.mcp_endpoint}/{endpoint}"
        last_error = None

        for attempt in range(MCP_MAX_RETRIES):
            try:
                http_session = await self._get_http_session()
                timeout = aiohttp.ClientTimeout(total=timeout_seconds)
                async with http_session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=timeout,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(
                            "[VSCodeIDEService] MCP command %s succeeded",
                            endpoint
                        )
                        return {"success": True, **data}
                    else:
                        error_text = await response.text()
                        # Issue #2075: Truncate error logs to prevent sensitive data leakage
                        truncated_error = _truncate_error_message(error_text)
                        logger.warning(
                            "[VSCodeIDEService] MCP command %s failed: %s - %s",
                            endpoint, response.status, truncated_error
                        )
                        last_error = f"HTTP {response.status}: {truncated_error}"

            except asyncio.TimeoutError:
                last_error = f"Request timeout after {timeout_seconds}s"
                logger.warning(
                    "[VSCodeIDEService] MCP command %s timed out (attempt %d/%d)",
                    endpoint, attempt + 1, MCP_MAX_RETRIES
                )
            except aiohttp.ClientError as e:
                # Issue #2075: Truncate error logs to prevent sensitive data leakage
                truncated_error = _truncate_error_message(str(e))
                last_error = f"Connection error: {truncated_error}"
                logger.warning(
                    "[VSCodeIDEService] MCP command %s connection error: %s (attempt %d/%d)",
                    endpoint, truncated_error, attempt + 1, MCP_MAX_RETRIES
                )
            except Exception as e:
                # Issue #2075: Truncate error logs to prevent sensitive data leakage
                truncated_error = _truncate_error_message(str(e))
                last_error = f"Unexpected error: {truncated_error}"
                logger.error(
                    "[VSCodeIDEService] MCP command %s unexpected error: %s",
                    endpoint, truncated_error
                )
                break  # Don't retry on unexpected errors

            # Wait before retry (except on last attempt)
            # Issue #2070: Use exponential backoff for better server load handling
            if attempt < MCP_MAX_RETRIES - 1:
                await asyncio.sleep(MCP_RETRY_DELAY * (2 ** attempt))

        return {"success": False, "error": last_error}

    async def _execute_shell_command(
        self,
        session: IDESession,
        command: str,
        timeout_seconds: int = 60,
    ) -> Dict[str, Any]:
        """
        Execute a shell command in the VM via MCP shell API.

        Args:
            session: IDE session
            command: Shell command to execute
            timeout_seconds: Command timeout in seconds

        Returns:
            Dict with success status, stdout, stderr, and exit_code
        """
        result = await self._execute_mcp_command(
            session,
            "shell/execute",
            {
                "command": command,
                "timeout": timeout_seconds,
                "cwd": session.workspace_path,
            },
            timeout_seconds=timeout_seconds + MCP_SHELL_EXEC_TIMEOUT_BUFFER,
        )

        if not result.get("success"):
            return {
                "success": False,
                "command": command,
                "stdout": "",
                "stderr": result.get("error", "Unknown error"),
                "exit_code": -1,
            }

        return {
            "success": True,
            "command": command,
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exit_code", 0),
        }

    def _has_terminal_capability(self, session: IDESession) -> bool:
        """
        Check if session has terminal access capability (Issue #2023).

        Terminal access is a privileged capability that must be explicitly
        granted. Sessions are created with this capability disabled by default.

        Args:
            session: IDE session to check

        Returns:
            True if terminal access is enabled, False otherwise
        """
        return bool(session.metadata.get(TERMINAL_ACCESS_CAPABILITY, False))

    def _detect_language(self, file_path: str) -> Optional[Language]:
        """Detect programming language from file extension"""
        extension_map = {
            ".py": Language.PYTHON,
            ".ts": Language.TYPESCRIPT,
            ".tsx": Language.TYPESCRIPT,
            ".js": Language.JAVASCRIPT,
            ".jsx": Language.JAVASCRIPT,
            ".go": Language.GO,
            ".rs": Language.RUST,
            ".java": Language.JAVA,
        }

        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang
        return None

    def _detect_project_language(self, session: IDESession) -> Optional[Language]:
        """Detect primary project language from workspace"""
        # In a real implementation, this would check for:
        # - pyproject.toml / setup.py → Python
        # - package.json → TypeScript/JavaScript
        # - go.mod → Go
        # - Cargo.toml → Rust
        # - pom.xml / build.gradle → Java
        return Language.PYTHON  # Default to Python

    def get_active_sessions(self) -> List[IDESession]:
        """Get all active IDE sessions"""
        return [
            s for s in self._sessions.values()
            if s.status not in [IDESessionStatus.CLOSED, IDESessionStatus.ERROR]
        ]

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about IDE sessions"""
        sessions = list(self._sessions.values())
        status_counts = {}
        for session in sessions:
            status = session.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_sessions": len(sessions),
            "active_sessions": len(self.get_active_sessions()),
            "status_counts": status_counts,
        }


# Global IDE service instance
vscode_ide_service = VSCodeIDEService()


def get_vscode_ide_service() -> VSCodeIDEService:
    """Get the global VS Code IDE service instance"""
    return vscode_ide_service
