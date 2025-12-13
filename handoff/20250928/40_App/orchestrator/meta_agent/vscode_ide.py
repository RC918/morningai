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
import base64
import json
import logging
import secrets
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

    # Default bind address for code-server (#2351 security hardening)
    # Use 127.0.0.1 instead of 0.0.0.0 to restrict access to localhost only
    DEFAULT_BIND_ADDRESS = "127.0.0.1"

    # Startup polling configuration (#2351 reliability improvement)
    # Replace fixed sleep with polling /healthz endpoint
    DEFAULT_STARTUP_RETRIES = 10
    DEFAULT_STARTUP_RETRY_INTERVAL = 1  # seconds

    # Default VS Code workspace settings (#2243)
    DEFAULT_VSCODE_SETTINGS: Dict[str, Any] = {
        "editor.formatOnSave": True,
        "editor.tabSize": 4,
    }

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
        2. Starts code-server with token auth if not running (#2351 security)
        3. Polls /healthz endpoint until ready (#2351 reliability)
        4. Ensures workspace directory exists
        5. Configures basic workspace settings (.vscode/settings.json)

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

        port = self.DEFAULT_VSCODE_PORT
        bind_addr = self.DEFAULT_BIND_ADDRESS
        health_check = await self._execute_shell_command(
            session,
            f"pgrep -f code-server || curl -s http://{bind_addr}:{port}/healthz",
            timeout_seconds=10,
        )

        if not health_check.get("success") or health_check.get("exit_code") != 0:
            logger.info(
                "[VSCodeIDEService] code-server not running, starting for session %s",
                session_id
            )

            auth_token = secrets.token_urlsafe(32)
            session.metadata["code_server_token"] = auth_token

            start_result = await self._execute_shell_command(
                session,
                f"PASSWORD={shlex.quote(auth_token)} code-server "
                f"--bind-addr {bind_addr}:{port} --auth password "
                f"{shlex.quote(workspace_path)} &",
                timeout_seconds=10,
            )

            if not start_result.get("success"):
                raise RuntimeError(
                    f"Failed to start code-server: {start_result.get('stderr', 'Unknown error')}"
                )

            started = await self._poll_healthz(session, bind_addr, port)
            if not started:
                raise RuntimeError(
                    f"code-server failed to start after "
                    f"{self.DEFAULT_STARTUP_RETRIES} retries"
                )

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
        settings_json = json.dumps(self.DEFAULT_VSCODE_SETTINGS, separators=(",", ":"))

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
                "content": settings_json,
            },
            timeout_seconds=10,
        )

        if not settings_result.get("success"):
            settings_b64 = base64.b64encode(settings_json.encode("utf-8")).decode("ascii")
            fallback_result = await self._execute_shell_command(
                session,
                f"printf '%s' {shlex.quote(settings_b64)} | base64 -d > {shlex.quote(settings_path)}",
                timeout_seconds=10,
            )
            if not fallback_result.get("success"):
                logger.warning(
                    "[VSCodeIDEService] Failed to create settings.json for session %s: %s",
                    session_id, fallback_result.get("stderr", "Unknown error")
                )

        session.metadata["code_server_url"] = session.vscode_endpoint
        session.metadata["initialized_at"] = datetime.now().isoformat()

        # Add CORS / iframe configuration to metadata (#2353)
        cors_config = self.get_cors_config()
        session.metadata["iframe_allowed_origins"] = cors_config["allowed_origins"]
        session.metadata["public_url"] = cors_config["public_url"] or session.vscode_endpoint

        # Auto-install extensions (#2353)
        await self._ensure_extensions_installed(session)

        logger.info(
            "[VSCodeIDEService] Session %s initialized successfully",
            session_id
        )

    async def _poll_healthz(
        self,
        session: IDESession,
        bind_addr: str,
        port: int,
    ) -> bool:
        """
        Poll code-server /healthz endpoint until it responds successfully.

        This replaces the fixed asyncio.sleep(2) with a more reliable polling
        mechanism that waits for code-server to actually be ready (#2351).

        Improvements (#2355):
        - First attempt runs immediately without delay
        - Distinguishes between connection failures and HTTP errors
        - Provides detailed logging for different error types

        Args:
            session: IDE session for executing commands
            bind_addr: Address code-server is bound to
            port: Port code-server is listening on

        Returns:
            True if code-server is ready, False if all retries exhausted
        """
        session_id = session.session_id[:8]
        retries = self.DEFAULT_STARTUP_RETRIES
        interval = self.DEFAULT_STARTUP_RETRY_INTERVAL

        for attempt in range(1, retries + 1):
            # Sleep after first attempt, not before (#2355 optimization)
            if attempt > 1:
                await asyncio.sleep(interval)

            health_result = await self._execute_shell_command(
                session,
                f"curl -s -o /dev/null -w '%{{http_code}}' http://{bind_addr}:{port}/healthz",
                timeout_seconds=5,
            )

            # Check if curl command itself failed (connection refused, timeout, etc.)
            if not health_result.get("success"):
                stderr = health_result.get("stderr", "").strip()
                logger.debug(
                    "[VSCodeIDEService] curl failed for session %s, attempt %d/%d: %s",
                    session_id, attempt, retries,
                    stderr or "connection failed"
                )
                continue

            stdout = health_result.get("stdout", "").strip()
            if stdout == "200":
                logger.debug(
                    "[VSCodeIDEService] code-server ready after %d attempt(s) "
                    "for session %s",
                    attempt, session_id
                )
                return True

            # HTTP response received but not 200
            logger.debug(
                "[VSCodeIDEService] code-server returned HTTP %s, attempt %d/%d "
                "for session %s",
                stdout or "unknown", attempt, retries, session_id
            )

        logger.warning(
            "[VSCodeIDEService] code-server failed to become ready after %d "
            "attempts for session %s",
            retries, session_id
        )
        return False

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

    def get_cors_config(self) -> Dict[str, Any]:
        """
        Get CORS / iframe configuration from settings (#2353).

        Returns a dictionary with:
        - allowed_origins: List of origins allowed to embed IDE in iframe
        - public_url: Public base URL for IDE access (or None if not configured)
        - iframe_enabled: Whether iframe embedding is enabled

        Returns:
            Dict with CORS configuration
        """
        try:
            from common.config.settings import settings
            origins_str = settings.vscode_iframe_allowed_origins or ""
            allowed_origins = [
                o.strip() for o in origins_str.split(",") if o.strip()
            ]
            public_url = settings.vscode_public_base_url
        except ImportError:
            logger.warning(
                "[VSCodeIDEService] Could not import settings, using defaults"
            )
            allowed_origins = []
            public_url = None

        return {
            "allowed_origins": allowed_origins,
            "public_url": public_url,
            "iframe_enabled": len(allowed_origins) > 0,
        }

    def get_cors_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for CORS / iframe support (#2353).

        Returns headers that should be set by the reverse proxy layer
        when serving IDE content. These headers enable iframe embedding
        from allowed origins.

        Returns:
            Dict of HTTP headers to set
        """
        config = self.get_cors_config()
        headers: Dict[str, str] = {}

        if not config["iframe_enabled"]:
            headers["X-Frame-Options"] = "DENY"
            return headers

        allowed_origins = config["allowed_origins"]

        origins_str = " ".join(allowed_origins)
        headers["Content-Security-Policy"] = f"frame-ancestors 'self' {origins_str}"

        if len(allowed_origins) == 1:
            headers["X-Frame-Options"] = f"ALLOW-FROM {allowed_origins[0]}"

        return headers

    def get_extension_config(self) -> Dict[str, Any]:
        """
        Get Extension auto-install configuration from settings (#2353).

        Returns a dictionary with:
        - default_extensions: List of extension IDs to auto-install

        Returns:
            Dict with extension configuration
        """
        try:
            from common.config.settings import settings
            extensions_str = settings.vscode_default_extensions or ""
            default_extensions = [
                e.strip() for e in extensions_str.split(",") if e.strip()
            ]
        except ImportError:
            logger.warning(
                "[VSCodeIDEService] Could not import settings for extensions, "
                "using defaults"
            )
            default_extensions = []

        return {
            "default_extensions": default_extensions,
        }

    def _get_desired_extensions(self, session: IDESession) -> List[str]:
        """
        Get the list of extensions to install for a session (#2353).

        Combines default extensions from settings with any per-task
        extra extensions from session metadata.

        Args:
            session: IDE session

        Returns:
            List of extension IDs to install (deduplicated, order preserved)
        """
        config = self.get_extension_config()
        default_exts = config["default_extensions"]
        extra_exts = session.metadata.get("extra_extensions") or []
        combined = default_exts + list(extra_exts)
        return list(dict.fromkeys(combined))

    async def _ensure_extensions_installed(self, session: IDESession) -> None:
        """
        Ensure desired extensions are installed for the session (#2353).

        This method:
        1. Gets the list of desired extensions (defaults + per-task extras)
        2. Lists currently installed extensions
        3. Installs any missing extensions
        4. Records installation status in session metadata

        Extension installation is best-effort and non-blocking; failures
        are logged but don't prevent session initialization.

        Args:
            session: IDE session to install extensions for
        """
        session_id = session.session_id[:8]
        desired = self._get_desired_extensions(session)

        if not desired:
            logger.debug(
                "[VSCodeIDEService] No extensions to install for session %s",
                session_id
            )
            return

        list_cmd = "code-server --list-extensions"
        result = await self._execute_shell_command(
            session, list_cmd, timeout_seconds=15
        )

        if not result.get("success"):
            logger.warning(
                "[VSCodeIDEService] Failed to list extensions for session %s: %s",
                session_id,
                result.get("stderr", "Unknown error"),
            )
            session.metadata["extensions_error"] = "Failed to list extensions"
            return

        installed = {
            line.strip()
            for line in (result.get("stdout") or "").splitlines()
            if line.strip()
        }
        to_install = [ext for ext in desired if ext not in installed]

        if not to_install:
            logger.debug(
                "[VSCodeIDEService] All %d extensions already installed for "
                "session %s",
                len(desired),
                session_id
            )
            session.metadata["extensions_desired"] = desired
            session.metadata["extensions_installed"] = list(installed & set(desired))
            session.metadata["extensions_failed"] = []
            return

        logger.info(
            "[VSCodeIDEService] Installing %d extensions for session %s: %s",
            len(to_install),
            session_id,
            to_install
        )

        installed_exts = []
        failed_exts = []

        for ext in to_install:
            cmd = f"code-server --install-extension {shlex.quote(ext)}"
            install_res = await self._execute_shell_command(
                session, cmd, timeout_seconds=60
            )

            if install_res.get("success"):
                installed_exts.append(ext)
                logger.debug(
                    "[VSCodeIDEService] Installed extension %s for session %s",
                    ext,
                    session_id
                )
            else:
                failed_exts.append(ext)
                logger.warning(
                    "[VSCodeIDEService] Failed to install extension %s for "
                    "session %s: %s",
                    ext,
                    session_id,
                    install_res.get("stderr", "Unknown error"),
                )

        session.metadata["extensions_desired"] = desired
        all_installed_desired = [
            ext for ext in desired if ext in installed or ext in installed_exts
        ]
        session.metadata["extensions_installed"] = all_installed_desired
        session.metadata["extensions_failed"] = failed_exts

        if failed_exts:
            logger.warning(
                "[VSCodeIDEService] %d/%d extensions failed to install for "
                "session %s",
                len(failed_exts),
                len(to_install),
                session_id
            )
        else:
            logger.info(
                "[VSCodeIDEService] All %d extensions installed successfully for "
                "session %s",
                len(to_install),
                session_id
            )

    def get_resource_limits(self) -> Dict[str, Any]:
        """
        Get resource limit configuration for IDE sessions.

        Returns configuration values for:
        - idle_timeout: Session idle timeout in seconds
        - cpu_limit_percent: CPU usage threshold for overload protection
        - memory_limit_percent: Memory usage threshold for overload protection
        - max_sessions: Maximum concurrent sessions allowed

        Returns:
            Dict with resource limit configuration
        """
        try:
            from common.config.settings import settings
            return {
                "idle_timeout": settings.vscode_session_idle_timeout,
                "cpu_limit_percent": settings.vscode_session_cpu_limit_percent,
                "memory_limit_percent": settings.vscode_session_memory_limit_percent,
                "max_sessions": settings.vscode_max_sessions,
            }
        except ImportError:
            logger.warning(
                "[VSCodeIDEService] settings module not available, using defaults"
            )
            return {
                "idle_timeout": 1800,
                "cpu_limit_percent": 80,
                "memory_limit_percent": 85,
                "max_sessions": 10,
            }

    async def _collect_resource_usage(
        self,
        session: IDESession,
    ) -> Dict[str, Any]:
        """
        Collect current resource usage metrics for the IDE session's VM.

        Uses shell commands to gather CPU and memory usage statistics.
        This is a best-effort operation; failures return empty metrics.

        Args:
            session: IDE session to collect metrics for

        Returns:
            Dict with resource usage metrics:
            - cpu_percent: Current CPU usage percentage (0-100)
            - memory_percent: Current memory usage percentage (0-100)
            - memory_used_mb: Memory used in MB
            - memory_total_mb: Total memory in MB
            - collected_at: ISO timestamp of collection
        """
        session_id = session.session_id[:8]
        metrics: Dict[str, Any] = {
            "cpu_percent": None,
            "memory_percent": None,
            "memory_used_mb": None,
            "memory_total_mb": None,
            "collected_at": datetime.now().isoformat(),
        }

        cpu_result = await self._execute_shell_command(
            session,
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1",
            timeout_seconds=10,
        )
        if cpu_result.get("success") and cpu_result.get("stdout"):
            try:
                cpu_str = cpu_result["stdout"].strip()
                metrics["cpu_percent"] = float(cpu_str)
            except (ValueError, TypeError):
                logger.debug(
                    "[VSCodeIDEService] Failed to parse CPU usage for session %s",
                    session_id
                )

        mem_result = await self._execute_shell_command(
            session,
            "free -m | awk 'NR==2{printf \"%s %s %.1f\", $3, $2, $3*100/$2}'",
            timeout_seconds=10,
        )
        if mem_result.get("success") and mem_result.get("stdout"):
            try:
                parts = mem_result["stdout"].strip().split()
                if len(parts) >= 3:
                    metrics["memory_used_mb"] = int(parts[0])
                    metrics["memory_total_mb"] = int(parts[1])
                    metrics["memory_percent"] = float(parts[2])
            except (ValueError, TypeError, IndexError):
                logger.debug(
                    "[VSCodeIDEService] Failed to parse memory usage for session %s",
                    session_id
                )

        return metrics

    async def check_resource_overload(
        self,
        session: Optional[IDESession] = None,
    ) -> Dict[str, Any]:
        """
        Check if system resources are overloaded for IDE sessions.

        This method checks:
        1. Current session count against max_sessions limit
        2. CPU usage against cpu_limit_percent threshold
        3. Memory usage against memory_limit_percent threshold

        Args:
            session: Optional IDE session to collect metrics from.
                     If None, only session count is checked.

        Returns:
            Dict with overload status:
            - is_overloaded: True if any limit is exceeded
            - reasons: List of reasons for overload
            - metrics: Current resource metrics
            - limits: Configured resource limits
            - can_create_session: True if new session can be created
        """
        limits = self.get_resource_limits()
        result: Dict[str, Any] = {
            "is_overloaded": False,
            "reasons": [],
            "metrics": {},
            "limits": limits,
            "can_create_session": True,
        }

        active_sessions = self.get_active_sessions()
        active_count = len(active_sessions)
        result["metrics"]["active_sessions"] = active_count

        max_sessions = limits["max_sessions"]
        if max_sessions > 0 and active_count >= max_sessions:
            result["is_overloaded"] = True
            result["can_create_session"] = False
            result["reasons"].append(
                f"Session limit reached: {active_count}/{max_sessions}"
            )
            logger.warning(
                "[VSCodeIDEService] Session limit reached: %d/%d",
                active_count, max_sessions
            )

        if session is not None:
            resource_metrics = await self._collect_resource_usage(session)
            result["metrics"].update(resource_metrics)

            cpu_percent = resource_metrics.get("cpu_percent")
            if cpu_percent is not None:
                cpu_limit = limits["cpu_limit_percent"]
                if cpu_percent >= cpu_limit:
                    result["is_overloaded"] = True
                    result["can_create_session"] = False
                    result["reasons"].append(
                        f"CPU overloaded: {cpu_percent:.1f}% >= {cpu_limit}%"
                    )
                    logger.warning(
                        "[VSCodeIDEService] CPU overloaded: %.1f%% >= %d%%",
                        cpu_percent, cpu_limit
                    )

            memory_percent = resource_metrics.get("memory_percent")
            if memory_percent is not None:
                memory_limit = limits["memory_limit_percent"]
                if memory_percent >= memory_limit:
                    result["is_overloaded"] = True
                    result["can_create_session"] = False
                    result["reasons"].append(
                        f"Memory overloaded: {memory_percent:.1f}% >= {memory_limit}%"
                    )
                    logger.warning(
                        "[VSCodeIDEService] Memory overloaded: %.1f%% >= %d%%",
                        memory_percent, memory_limit
                    )

        return result

    async def get_idle_sessions(self) -> List[IDESession]:
        """
        Get list of sessions that have exceeded the idle timeout.

        Returns:
            List of IDESession objects that are idle and eligible for cleanup
        """
        limits = self.get_resource_limits()
        idle_timeout = limits["idle_timeout"]

        if idle_timeout <= 0:
            return []

        idle_sessions: List[IDESession] = []
        now = datetime.now()

        async with self._lock:
            for session in self._sessions.values():
                if session.status in (IDESessionStatus.CLOSED, IDESessionStatus.ERROR):
                    continue

                last_activity = session.last_activity or session.created_at
                idle_seconds = (now - last_activity).total_seconds()

                if idle_seconds >= idle_timeout:
                    idle_sessions.append(session)
                    logger.info(
                        "[VSCodeIDEService] Session %s idle for %.0f seconds "
                        "(timeout: %d)",
                        session.session_id[:8], idle_seconds, idle_timeout
                    )

        return idle_sessions

    async def update_session_activity(self, session_id: str) -> bool:
        """
        Update the last_activity timestamp for a session.

        This should be called when the session is actively used to prevent
        idle timeout cleanup.

        Args:
            session_id: ID of the session to update

        Returns:
            True if session was found and updated, False otherwise
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            session.last_activity = datetime.now()
            return True

    async def collect_session_metrics(
        self,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Collect and store resource metrics for a specific session.

        This method collects metrics and stores them in session.metadata
        for observability integration.

        Args:
            session_id: ID of the session to collect metrics for

        Returns:
            Dict with collected metrics, or None if session not found
        """
        session = await self.get_session(session_id)
        if session is None:
            return None

        metrics = await self._collect_resource_usage(session)

        session.metadata["resource_metrics"] = metrics
        session.metadata["resource_metrics_collected_at"] = metrics["collected_at"]

        overload_status = await self.check_resource_overload(session)
        session.metadata["resource_overload_status"] = {
            "is_overloaded": overload_status["is_overloaded"],
            "reasons": overload_status["reasons"],
        }

        return {
            "session_id": session_id,
            "metrics": metrics,
            "overload_status": overload_status,
        }


# Global IDE service instance
vscode_ide_service = VSCodeIDEService()


def get_vscode_ide_service() -> VSCodeIDEService:
    """Get the global VS Code IDE service instance"""
    return vscode_ide_service
