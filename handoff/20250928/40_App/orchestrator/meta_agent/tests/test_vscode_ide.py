"""
Unit tests for VS Code IDE Integration

Tests cover:
- IDE session lifecycle (create, close, get)
- File operations (open, edit)
- Code search
- Code formatting
- Linting
- Test execution
- LSP support
- File tree navigation
- Terminal command execution
- Language detection
- Session statistics
- MCP HTTP client integration
"""

import time

import pytest
from datetime import datetime

from meta_agent.vscode_ide import (
    FileContent,
    IDESession,
    IDESessionStatus,
    Language,
    LintResult,
    MCP_ERROR_LOG_MAX_LENGTH,
    SearchResult,
    TERMINAL_ACCESS_CAPABILITY,
    TestResult,
    TestStatus,
    TestSuiteResult,
    VSCodeIDEService,
    _truncate_error_message,
    get_vscode_ide_service,
    vscode_ide_service,
)


class TestDataclasses:
    """Tests for dataclass serialization"""

    def test_file_content_to_dict(self):
        """Test FileContent serialization"""
        content = FileContent(
            path="test.py",
            content="print('hello')",
            language=Language.PYTHON,
            line_count=1,
            size_bytes=14,
            last_modified=datetime(2024, 1, 1, 12, 0, 0),
        )
        result = content.to_dict()

        assert result["path"] == "test.py"
        assert result["content"] == "print('hello')"
        assert result["language"] == "python"
        assert result["line_count"] == 1
        assert result["size_bytes"] == 14
        assert result["last_modified"] == "2024-01-01T12:00:00"

    def test_file_content_to_dict_no_language(self):
        """Test FileContent serialization without language"""
        content = FileContent(path="test.txt", content="hello")
        result = content.to_dict()

        assert result["language"] is None
        assert result["last_modified"] is None

    def test_search_result_to_dict(self):
        """Test SearchResult serialization"""
        result = SearchResult(
            file_path="test.py",
            line_number=10,
            line_content="def test():",
            match_start=4,
            match_end=8,
            context_before=["# comment"],
            context_after=["    pass"],
        )
        data = result.to_dict()

        assert data["file_path"] == "test.py"
        assert data["line_number"] == 10
        assert data["line_content"] == "def test():"
        assert data["match_start"] == 4
        assert data["match_end"] == 8
        assert data["context_before"] == ["# comment"]
        assert data["context_after"] == ["    pass"]

    def test_lint_result_to_dict(self):
        """Test LintResult serialization"""
        result = LintResult(
            file_path="test.py",
            line_number=5,
            column=10,
            severity="error",
            message="undefined variable",
            rule_id="E001",
        )
        data = result.to_dict()

        assert data["file_path"] == "test.py"
        assert data["line_number"] == 5
        assert data["column"] == 10
        assert data["severity"] == "error"
        assert data["message"] == "undefined variable"
        assert data["rule_id"] == "E001"

    def test_test_result_to_dict(self):
        """Test TestResult serialization"""
        result = TestResult(
            test_name="test_example",
            status=TestStatus.PASSED,
            duration_ms=100.5,
            file_path="test_example.py",
            line_number=10,
        )
        data = result.to_dict()

        assert data["test_name"] == "test_example"
        assert data["status"] == "passed"
        assert data["duration_ms"] == 100.5
        assert data["file_path"] == "test_example.py"
        assert data["line_number"] == 10

    def test_test_result_failed_with_error(self):
        """Test TestResult with failure details"""
        result = TestResult(
            test_name="test_fail",
            status=TestStatus.FAILED,
            duration_ms=50.0,
            error_message="AssertionError",
            stack_trace="Traceback...",
        )
        data = result.to_dict()

        assert data["status"] == "failed"
        assert data["error_message"] == "AssertionError"
        assert data["stack_trace"] == "Traceback..."

    def test_test_suite_result_to_dict(self):
        """Test TestSuiteResult serialization"""
        tests = [
            TestResult("test1", TestStatus.PASSED, 100.0),
            TestResult("test2", TestStatus.FAILED, 50.0),
        ]
        suite = TestSuiteResult(
            suite_name="my_suite",
            tests=tests,
            total_duration_ms=150.0,
            passed_count=1,
            failed_count=1,
            skipped_count=0,
            error_count=0,
        )
        data = suite.to_dict()

        assert data["suite_name"] == "my_suite"
        assert len(data["tests"]) == 2
        assert data["total_duration_ms"] == 150.0
        assert data["passed_count"] == 1
        assert data["failed_count"] == 1

    def test_ide_session_to_dict(self):
        """Test IDESession serialization"""
        session = IDESession(
            session_id="ide-test-12345678",
            vm_id="vm-test-12345678",
            task_id="task-12345678",
            status=IDESessionStatus.READY,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            workspace_path="/workspace",
            vscode_endpoint="http://localhost:8443",
            mcp_endpoint="http://localhost:8080",
            active_file="/workspace/test.py",
            open_files=["/workspace/test.py"],
            last_activity=datetime(2024, 1, 1, 12, 30, 0),
            metadata={"key": "value"},
        )
        data = session.to_dict()

        assert data["session_id"] == "ide-test-12345678"
        assert data["vm_id"] == "vm-test-12345678"
        assert data["task_id"] == "task-12345678"
        assert data["status"] == "ready"
        assert data["created_at"] == "2024-01-01T12:00:00"
        assert data["workspace_path"] == "/workspace"
        assert data["vscode_endpoint"] == "http://localhost:8443"
        assert data["mcp_endpoint"] == "http://localhost:8080"
        assert data["active_file"] == "/workspace/test.py"
        assert data["open_files"] == ["/workspace/test.py"]
        assert data["last_activity"] == "2024-01-01T12:30:00"
        assert data["metadata"] == {"key": "value"}

    def test_ide_session_to_dict_minimal(self):
        """Test IDESession serialization with minimal data"""
        session = IDESession(
            session_id="ide-test-12345678",
            vm_id="vm-test-12345678",
            task_id="task-12345678",
            status=IDESessionStatus.INITIALIZING,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        data = session.to_dict()

        assert data["last_activity"] is None
        assert data["error"] is None
        assert data["active_file"] is None


class TestEnums:
    """Tests for enum values"""

    def test_ide_session_status_values(self):
        """Test IDESessionStatus enum values"""
        assert IDESessionStatus.INITIALIZING.value == "initializing"
        assert IDESessionStatus.READY.value == "ready"
        assert IDESessionStatus.ACTIVE.value == "active"
        assert IDESessionStatus.SUSPENDED.value == "suspended"
        assert IDESessionStatus.CLOSED.value == "closed"
        assert IDESessionStatus.ERROR.value == "error"

    def test_test_status_values(self):
        """Test TestStatus enum values"""
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.RUNNING.value == "running"
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"
        assert TestStatus.ERROR.value == "error"

    def test_language_values(self):
        """Test Language enum values"""
        assert Language.PYTHON.value == "python"
        assert Language.TYPESCRIPT.value == "typescript"
        assert Language.JAVASCRIPT.value == "javascript"
        assert Language.GO.value == "go"
        assert Language.RUST.value == "rust"
        assert Language.JAVA.value == "java"


class TestVSCodeIDEService:
    """Tests for VSCodeIDEService"""

    @pytest.fixture
    def service(self):
        """Create a fresh VSCodeIDEService instance"""
        return VSCodeIDEService()

    @pytest.fixture
    def mock_session(self):
        """Create a mock IDE session"""
        return IDESession(
            session_id="ide-test-12345678",
            vm_id="vm-test-12345678",
            task_id="task-12345678",
            status=IDESessionStatus.READY,
            created_at=datetime.now(),
            workspace_path="/workspace",
            vscode_endpoint="http://localhost:8443",
            mcp_endpoint="http://localhost:8080",
        )

    @pytest.fixture
    def mock_mcp_response(self):
        """Create a mock MCP response for testing"""
        async def _mock_execute_mcp_command(session, endpoint, payload, **kwargs):
            """Mock MCP command execution that returns success"""
            return {
                "success": True,
                "endpoint": endpoint,
                "payload": payload,
                "content": "mock content",
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
            }
        return _mock_execute_mcp_command

    @pytest.fixture
    def mock_shell_response(self):
        """Create a mock shell response for testing"""
        async def _mock_execute_shell_command(session, command, timeout_seconds=60):
            """Mock shell command execution that returns success"""
            return {
                "success": True,
                "command": command,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
            }
        return _mock_execute_shell_command

    @pytest.mark.asyncio
    async def test_create_session(self, service):
        """Test creating an IDE session"""
        async def _noop_initialize(session):
            pass

        service._initialize_session = _noop_initialize

        session = await service.create_session(
            vm_id="vm-test-12345678",
            task_id="task-12345678",
            mcp_endpoint="http://localhost:8080",
            workspace_path="/workspace",
        )

        assert session.session_id.startswith("ide-task-123")
        assert session.vm_id == "vm-test-12345678"
        assert session.task_id == "task-12345678"
        assert session.status == IDESessionStatus.READY
        assert session.workspace_path == "/workspace"
        assert session.vscode_endpoint == "http://localhost:8443"
        assert session.mcp_endpoint == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_create_session_custom_workspace(self, service):
        """Test creating session with custom workspace"""
        async def _noop_initialize(session):
            pass

        service._initialize_session = _noop_initialize

        session = await service.create_session(
            vm_id="vm-test",
            task_id="task-test",
            mcp_endpoint="http://localhost:8080",
            workspace_path="/custom/workspace",
        )

        assert session.workspace_path == "/custom/workspace"

    @pytest.mark.asyncio
    async def test_close_session(self, service):
        """Test closing an IDE session"""
        async def _noop_initialize(session):
            pass

        service._initialize_session = _noop_initialize

        session = await service.create_session(
            vm_id="vm-test",
            task_id="task-test",
            mcp_endpoint="http://localhost:8080",
        )

        result = await service.close_session(session.session_id)

        assert result is True
        closed_session = await service.get_session(session.session_id)
        assert closed_session.status == IDESessionStatus.CLOSED

    @pytest.mark.asyncio
    async def test_close_nonexistent_session(self, service):
        """Test closing a non-existent session"""
        result = await service.close_session("nonexistent-session")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_session(self, service):
        """Test getting a session by ID"""
        async def _noop_initialize(session):
            pass

        service._initialize_session = _noop_initialize

        created = await service.create_session(
            vm_id="vm-test",
            task_id="task-test",
            mcp_endpoint="http://localhost:8080",
        )

        session = await service.get_session(created.session_id)

        assert session is not None
        assert session.session_id == created.session_id

    @pytest.mark.asyncio
    async def test_get_session_nonexistent(self, service):
        """Test getting a non-existent session"""
        session = await service.get_session("nonexistent")
        assert session is None

    @pytest.mark.asyncio
    async def test_get_session_for_task(self, service):
        """Test getting session by task ID"""
        async def _noop_initialize(session):
            pass

        service._initialize_session = _noop_initialize

        await service.create_session(
            vm_id="vm-test",
            task_id="task-12345678",
            mcp_endpoint="http://localhost:8080",
        )

        session = await service.get_session_for_task("task-12345678")

        assert session is not None
        assert session.task_id == "task-12345678"

    @pytest.mark.asyncio
    async def test_get_session_for_task_closed(self, service):
        """Test that closed sessions are not returned"""
        async def _noop_initialize(session):
            pass

        service._initialize_session = _noop_initialize

        created = await service.create_session(
            vm_id="vm-test",
            task_id="task-12345678",
            mcp_endpoint="http://localhost:8080",
        )
        await service.close_session(created.session_id)

        session = await service.get_session_for_task("task-12345678")
        assert session is None

    @pytest.mark.asyncio
    async def test_open_file(self, service, mock_session, mock_mcp_response, mocker):
        """Test opening a file"""
        service._sessions[mock_session.session_id] = mock_session
        mocker.patch.object(service, "_execute_mcp_command", new=mock_mcp_response)

        result = await service.open_file(mock_session, "test.py")

        assert result["success"] is True
        assert mock_session.active_file == "/workspace/test.py"
        assert "/workspace/test.py" in mock_session.open_files
        assert mock_session.status == IDESessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_open_file_closed_session(self, service, mock_session):
        """Test opening file in closed session"""
        mock_session.status = IDESessionStatus.CLOSED

        result = await service.open_file(mock_session, "test.py")

        assert result["success"] is False
        assert "closed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_edit_file(self, service, mock_session, mock_mcp_response, mocker):
        """Test editing a file"""
        service._sessions[mock_session.session_id] = mock_session
        mocker.patch.object(service, "_execute_mcp_command", new=mock_mcp_response)

        result = await service.edit_file(
            mock_session,
            "test.py",
            "print('hello world')"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_edit_file_closed_session(self, service, mock_session):
        """Test editing file in closed session"""
        mock_session.status = IDESessionStatus.CLOSED

        result = await service.edit_file(mock_session, "test.py", "content")

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_search_code(self, service, mock_session, mock_shell_response, mocker):
        """Test searching code"""
        service._sessions[mock_session.session_id] = mock_session
        mocker.patch.object(service, "_execute_shell_command", new=mock_shell_response)

        result = await service.search_code(mock_session, "def test")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_search_code_with_pattern(
        self, service, mock_session, mock_shell_response, mocker
    ):
        """Test searching code with file pattern"""
        service._sessions[mock_session.session_id] = mock_session
        mocker.patch.object(service, "_execute_shell_command", new=mock_shell_response)

        result = await service.search_code(
            mock_session,
            "import",
            file_pattern="*.py"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_search_code_closed_session(self, service, mock_session):
        """Test searching in closed session"""
        mock_session.status = IDESessionStatus.CLOSED

        result = await service.search_code(mock_session, "test")

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_format_code_python(
        self, service, mock_session, mock_shell_response, mocker
    ):
        """Test formatting Python code"""
        service._sessions[mock_session.session_id] = mock_session
        mocker.patch.object(service, "_execute_shell_command", new=mock_shell_response)

        result = await service.format_code(
            mock_session,
            "test.py",
            Language.PYTHON
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_format_code_auto_detect(
        self, service, mock_session, mock_shell_response, mocker
    ):
        """Test formatting with auto-detected language"""
        service._sessions[mock_session.session_id] = mock_session
        mocker.patch.object(service, "_execute_shell_command", new=mock_shell_response)

        result = await service.format_code(mock_session, "test.py")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_format_code_unknown_language(self, service, mock_session):
        """Test formatting with unknown file type"""
        service._sessions[mock_session.session_id] = mock_session

        result = await service.format_code(mock_session, "test.xyz")

        assert result["success"] is False
        assert "detect" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_format_code_closed_session(self, service, mock_session):
        """Test formatting in closed session"""
        mock_session.status = IDESessionStatus.CLOSED

        result = await service.format_code(mock_session, "test.py")

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_run_linter_python(self, service, mock_session):
        """Test running Python linter"""
        service._sessions[mock_session.session_id] = mock_session

        result = await service.run_linter(
            mock_session,
            "test.py",
            Language.PYTHON
        )

        assert "lint_results" in result

    @pytest.mark.asyncio
    async def test_run_linter_auto_detect(self, service, mock_session):
        """Test linting with auto-detected language"""
        service._sessions[mock_session.session_id] = mock_session

        result = await service.run_linter(mock_session, "test.ts")

        assert "lint_results" in result

    @pytest.mark.asyncio
    async def test_run_linter_closed_session(self, service, mock_session):
        """Test linting in closed session"""
        mock_session.status = IDESessionStatus.CLOSED

        result = await service.run_linter(mock_session, "test.py")

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_run_tests(self, service, mock_session):
        """Test running tests"""
        service._sessions[mock_session.session_id] = mock_session

        result = await service.run_tests(mock_session)

        assert "test_suite" in result

    @pytest.mark.asyncio
    async def test_run_tests_with_path(self, service, mock_session):
        """Test running tests with specific path"""
        service._sessions[mock_session.session_id] = mock_session

        result = await service.run_tests(
            mock_session,
            test_path="tests/test_example.py"
        )

        assert "test_suite" in result

    @pytest.mark.asyncio
    async def test_run_tests_with_pattern(self, service, mock_session):
        """Test running tests with pattern filter"""
        service._sessions[mock_session.session_id] = mock_session

        result = await service.run_tests(
            mock_session,
            test_pattern="test_specific",
            language=Language.PYTHON
        )

        assert "test_suite" in result

    @pytest.mark.asyncio
    async def test_run_tests_closed_session(self, service, mock_session):
        """Test running tests in closed session"""
        mock_session.status = IDESessionStatus.CLOSED

        result = await service.run_tests(mock_session)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_start_lsp(self, service, mock_session, mock_mcp_response, mocker):
        """Test starting LSP server"""
        service._sessions[mock_session.session_id] = mock_session
        mocker.patch.object(service, "_execute_mcp_command", new=mock_mcp_response)

        result = await service.start_lsp(mock_session, Language.PYTHON)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_start_lsp_closed_session(self, service, mock_session):
        """Test starting LSP in closed session"""
        mock_session.status = IDESessionStatus.CLOSED

        result = await service.start_lsp(mock_session, Language.PYTHON)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_file_tree(self, service, mock_session, mock_shell_response, mocker):
        """Test getting file tree"""
        service._sessions[mock_session.session_id] = mock_session
        mocker.patch.object(service, "_execute_shell_command", new=mock_shell_response)

        result = await service.get_file_tree(mock_session)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_file_tree_custom_path(
        self, service, mock_session, mock_shell_response, mocker
    ):
        """Test getting file tree with custom path"""
        service._sessions[mock_session.session_id] = mock_session
        mocker.patch.object(service, "_execute_shell_command", new=mock_shell_response)

        result = await service.get_file_tree(mock_session, path="src", max_depth=2)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_file_tree_closed_session(self, service, mock_session):
        """Test getting file tree in closed session"""
        mock_session.status = IDESessionStatus.CLOSED

        result = await service.get_file_tree(mock_session)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_terminal_command(
        self, service, mock_session, mock_shell_response, mocker
    ):
        """Test executing terminal command with capability enabled"""
        service._sessions[mock_session.session_id] = mock_session
        mocker.patch.object(service, "_execute_shell_command", new=mock_shell_response)
        # Issue #2023: Grant terminal access capability
        mock_session.metadata[TERMINAL_ACCESS_CAPABILITY] = True

        result = await service.execute_terminal_command(mock_session, "ls -la")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_terminal_command_no_capability(
        self, service, mock_session
    ):
        """Test executing terminal command without capability (Issue #2023)"""
        service._sessions[mock_session.session_id] = mock_session
        # Capability not granted - should be denied

        result = await service.execute_terminal_command(mock_session, "ls -la")

        assert result["success"] is False
        assert "Terminal access is not enabled" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_terminal_command_closed_session(
        self, service, mock_session
    ):
        """Test executing command in closed session"""
        mock_session.status = IDESessionStatus.CLOSED

        result = await service.execute_terminal_command(mock_session, "ls")

        assert result["success"] is False


class TestLanguageDetection:
    """Tests for language detection"""

    @pytest.fixture
    def service(self):
        return VSCodeIDEService()

    def test_detect_python(self, service):
        """Test detecting Python files"""
        assert service._detect_language("test.py") == Language.PYTHON

    def test_detect_typescript(self, service):
        """Test detecting TypeScript files"""
        assert service._detect_language("test.ts") == Language.TYPESCRIPT
        assert service._detect_language("test.tsx") == Language.TYPESCRIPT

    def test_detect_javascript(self, service):
        """Test detecting JavaScript files"""
        assert service._detect_language("test.js") == Language.JAVASCRIPT
        assert service._detect_language("test.jsx") == Language.JAVASCRIPT

    def test_detect_go(self, service):
        """Test detecting Go files"""
        assert service._detect_language("test.go") == Language.GO

    def test_detect_rust(self, service):
        """Test detecting Rust files"""
        assert service._detect_language("test.rs") == Language.RUST

    def test_detect_java(self, service):
        """Test detecting Java files"""
        assert service._detect_language("Test.java") == Language.JAVA

    def test_detect_unknown(self, service):
        """Test unknown file types"""
        assert service._detect_language("test.xyz") is None
        assert service._detect_language("test.txt") is None
        assert service._detect_language("Makefile") is None


class TestOutputParsing:
    """Tests for output parsing"""

    @pytest.fixture
    def service(self):
        return VSCodeIDEService()

    def test_parse_grep_output(self, service):
        """Test parsing grep output"""
        output = """test.py:10:def test_function():
test.py:20:def another_function():
utils.py:5:def helper():"""

        results = service._parse_grep_output(output)

        assert len(results) == 3
        assert results[0].file_path == "test.py"
        assert results[0].line_number == 10
        assert results[0].line_content == "def test_function():"
        assert results[1].line_number == 20
        assert results[2].file_path == "utils.py"

    def test_parse_grep_output_empty(self, service):
        """Test parsing empty grep output"""
        results = service._parse_grep_output("")
        assert len(results) == 0

    def test_parse_grep_output_invalid_lines(self, service):
        """Test parsing grep output with invalid lines"""
        output = """test.py:10:valid line
invalid line without colons
:invalid:format
test.py:abc:non-numeric line"""

        results = service._parse_grep_output(output)

        assert len(results) == 1
        assert results[0].file_path == "test.py"

    def test_parse_lint_output(self, service):
        """Test parsing lint output"""
        output = """test.py:10:5: undefined variable 'x'
test.py:20:1: missing docstring"""

        results = service._parse_lint_output(output, Language.PYTHON)

        assert len(results) == 2
        assert results[0].file_path == "test.py"
        assert results[0].line_number == 10
        assert results[0].column == 5
        assert "undefined" in results[0].message

    def test_parse_lint_output_empty(self, service):
        """Test parsing empty lint output"""
        results = service._parse_lint_output("", Language.PYTHON)
        assert len(results) == 0

    def test_parse_test_output_passed(self, service):
        """Test parsing test output with passed tests"""
        output = """test_one PASSED
test_two PASSED
test_three passed"""

        result = service._parse_test_output(output, Language.PYTHON)

        assert result.passed_count == 3
        assert result.failed_count == 0

    def test_parse_test_output_mixed(self, service):
        """Test parsing test output with mixed results"""
        output = """test_one PASSED
test_two FAILED
test_three SKIPPED
test_four ERROR"""

        result = service._parse_test_output(output, Language.PYTHON)

        assert result.passed_count == 1
        assert result.failed_count == 1
        assert result.skipped_count == 1
        assert result.error_count == 1


class TestSessionStatistics:
    """Tests for session statistics"""

    @pytest.fixture
    def service(self):
        return VSCodeIDEService()

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, service):
        """Test getting active sessions"""
        async def _noop_initialize(session):
            pass

        service._initialize_session = _noop_initialize

        await service.create_session(
            vm_id="vm-1",
            task_id="task-1",
            mcp_endpoint="http://localhost:8080",
        )
        session2 = await service.create_session(
            vm_id="vm-2",
            task_id="task-2",
            mcp_endpoint="http://localhost:8080",
        )
        await service.close_session(session2.session_id)

        active = service.get_active_sessions()

        assert len(active) == 1
        assert active[0].task_id == "task-1"

    @pytest.mark.asyncio
    async def test_get_session_stats(self, service):
        """Test getting session statistics"""
        async def _noop_initialize(session):
            pass

        service._initialize_session = _noop_initialize

        await service.create_session(
            vm_id="vm-1",
            task_id="task-1",
            mcp_endpoint="http://localhost:8080",
        )
        session2 = await service.create_session(
            vm_id="vm-2",
            task_id="task-2",
            mcp_endpoint="http://localhost:8080",
        )
        await service.close_session(session2.session_id)

        stats = service.get_session_stats()

        assert stats["total_sessions"] == 2
        assert stats["active_sessions"] == 1
        assert stats["status_counts"]["ready"] == 1
        assert stats["status_counts"]["closed"] == 1


class TestGlobalInstance:
    """Tests for global service instance"""

    def test_global_instance_exists(self):
        """Test that global instance exists"""
        assert vscode_ide_service is not None
        assert isinstance(vscode_ide_service, VSCodeIDEService)

    def test_get_vscode_ide_service(self):
        """Test get_vscode_ide_service function"""
        service = get_vscode_ide_service()
        assert service is vscode_ide_service


class TestFormatterAndLinterConfig:
    """Tests for formatter and linter configuration"""

    def test_formatters_defined(self):
        """Test that formatters are defined for all languages"""
        service = VSCodeIDEService()

        assert Language.PYTHON in service.FORMATTERS
        assert Language.TYPESCRIPT in service.FORMATTERS
        assert Language.JAVASCRIPT in service.FORMATTERS
        assert Language.GO in service.FORMATTERS
        assert Language.RUST in service.FORMATTERS
        assert Language.JAVA in service.FORMATTERS

    def test_linters_defined(self):
        """Test that linters are defined for all languages"""
        service = VSCodeIDEService()

        assert Language.PYTHON in service.LINTERS
        assert Language.TYPESCRIPT in service.LINTERS
        assert Language.JAVASCRIPT in service.LINTERS
        assert Language.GO in service.LINTERS
        assert Language.RUST in service.LINTERS
        assert Language.JAVA in service.LINTERS

    def test_test_runners_defined(self):
        """Test that test runners are defined for all languages"""
        service = VSCodeIDEService()

        assert Language.PYTHON in service.TEST_RUNNERS
        assert Language.TYPESCRIPT in service.TEST_RUNNERS
        assert Language.JAVASCRIPT in service.TEST_RUNNERS
        assert Language.GO in service.TEST_RUNNERS
        assert Language.RUST in service.TEST_RUNNERS
        assert Language.JAVA in service.TEST_RUNNERS

    def test_formatter_commands(self):
        """Test formatter command strings"""
        service = VSCodeIDEService()

        assert "black" in service.FORMATTERS[Language.PYTHON]
        assert "prettier" in service.FORMATTERS[Language.TYPESCRIPT]
        assert "gofmt" in service.FORMATTERS[Language.GO]
        assert "rustfmt" in service.FORMATTERS[Language.RUST]

    def test_linter_commands(self):
        """Test linter command strings"""
        service = VSCodeIDEService()

        assert "ruff" in service.LINTERS[Language.PYTHON]
        assert "eslint" in service.LINTERS[Language.TYPESCRIPT]
        assert "golangci-lint" in service.LINTERS[Language.GO]
        assert "clippy" in service.LINTERS[Language.RUST]

    def test_test_runner_commands(self):
        """Test test runner command strings"""
        service = VSCodeIDEService()

        assert "pytest" in service.TEST_RUNNERS[Language.PYTHON]
        assert "npm test" in service.TEST_RUNNERS[Language.TYPESCRIPT]
        assert "go test" in service.TEST_RUNNERS[Language.GO]
        assert "cargo test" in service.TEST_RUNNERS[Language.RUST]


class TestTruncateErrorMessage:
    """Tests for _truncate_error_message function (Issue #2075)"""

    def test_truncate_short_message(self):
        """Test that short messages are not truncated"""
        message = "Short error message"
        result = _truncate_error_message(message)
        assert result == message

    def test_truncate_exact_length_message(self):
        """Test message at exactly max length is not truncated"""
        message = "a" * MCP_ERROR_LOG_MAX_LENGTH
        result = _truncate_error_message(message)
        assert result == message
        assert len(result) == MCP_ERROR_LOG_MAX_LENGTH

    def test_truncate_long_message(self):
        """Test that long messages are truncated"""
        message = "a" * (MCP_ERROR_LOG_MAX_LENGTH + 100)
        result = _truncate_error_message(message)
        assert len(result) < len(message)
        assert result.endswith("... [truncated]")
        assert result.startswith("a" * 100)

    def test_truncate_empty_message(self):
        """Test that empty messages are handled"""
        result = _truncate_error_message("")
        assert result == ""

    def test_truncate_none_message(self):
        """Test that None messages are handled"""
        result = _truncate_error_message(None)
        assert result is None

    def test_truncate_custom_max_length(self):
        """Test truncation with custom max length"""
        message = "a" * 100
        result = _truncate_error_message(message, max_length=50)
        assert len(result) == 50 + len("... [truncated]")
        assert result.endswith("... [truncated]")

    def test_truncate_preserves_beginning(self):
        """Test that truncation preserves the beginning of the message"""
        message = "ERROR: " + "x" * 1000
        result = _truncate_error_message(message, max_length=100)
        assert result.startswith("ERROR: ")

    def test_truncate_sensitive_data_scenario(self):
        """Test truncation of message containing sensitive-looking data"""
        sensitive_message = (
            "Error: Connection failed\n"
            "Stack trace:\n"
            "  at connect() line 123\n"
            "Environment: API_KEY=sk-secret-key-12345\n"
            "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\n"
            + "x" * 1000
        )
        result = _truncate_error_message(sensitive_message, max_length=100)
        assert len(result) == 100 + len("... [truncated]")
        assert result.endswith("... [truncated]")
        assert "sk-secret-key-12345" not in result


class TestInitializeSession:
    """Tests for _initialize_session method (#2243)"""

    @pytest.fixture
    def service(self):
        """Create a fresh VSCodeIDEService instance"""
        return VSCodeIDEService()

    @pytest.fixture
    def mock_session(self):
        """Create a mock IDE session"""
        return IDESession(
            session_id="ide-test-12345678",
            vm_id="vm-test-12345678",
            task_id="task-12345678",
            status=IDESessionStatus.INITIALIZING,
            created_at=datetime.now(),
            workspace_path="/workspace",
            vscode_endpoint="http://localhost:8443",
            mcp_endpoint="http://localhost:8080",
        )

    @pytest.fixture
    def mock_mcp_success(self):
        """Shared MCP mock that always returns success"""
        async def _mock_mcp(session, endpoint, payload, timeout_seconds=30):
            return {"success": True}
        return _mock_mcp

    @pytest.fixture
    def mock_shell_for_startup(self):
        """
        Shared shell mock for code-server startup tests.
        Returns a factory that creates mock functions with configurable behavior.
        """
        def _create_mock(
            code_server_running: bool = False,
            healthz_response: str = "200",
            commands_list: list = None,
        ):
            async def mock_shell(session, command, timeout_seconds=60):
                if commands_list is not None:
                    commands_list.append(command)
                if "pgrep" in command and "curl" in command:
                    if code_server_running:
                        return {"success": True, "exit_code": 0, "stdout": "12345", "stderr": ""}
                    return {"success": False, "exit_code": 1, "stdout": "", "stderr": ""}
                if "code-server --bind-addr" in command:
                    return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}
                if "curl" in command and "healthz" in command and "http_code" in command:
                    return {"success": True, "exit_code": 0, "stdout": healthz_response, "stderr": ""}
                if "mkdir -p" in command:
                    return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}
                if "base64" in command:
                    return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}
                return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}
            return mock_shell
        return _create_mock

    @pytest.mark.asyncio
    async def test_initialize_session_code_server_already_running(
        self, service, mock_session
    ):
        """Test initialization when code-server is already running"""
        shell_call_count = 0
        mcp_call_count = 0

        async def mock_shell(session, command, timeout_seconds=60):
            nonlocal shell_call_count
            shell_call_count += 1
            return {"success": True, "exit_code": 0, "stdout": "12345", "stderr": ""}

        async def mock_mcp(session, endpoint, payload, timeout_seconds=30):
            nonlocal mcp_call_count
            mcp_call_count += 1
            return {"success": True}

        service._execute_shell_command = mock_shell
        service._execute_mcp_command = mock_mcp

        await service._initialize_session(mock_session)

        assert mock_session.metadata.get("code_server_url") == "http://localhost:8443"
        assert "initialized_at" in mock_session.metadata
        assert shell_call_count >= 3
        assert mcp_call_count >= 1

    @pytest.mark.asyncio
    async def test_initialize_session_starts_code_server(self, service, mock_session):
        """Test initialization starts code-server when not running"""
        call_sequence = []
        mcp_call_count = 0
        healthz_call_count = 0

        async def mock_shell(session, command, timeout_seconds=60):
            nonlocal healthz_call_count
            call_sequence.append(command)
            if "pgrep" in command and "curl" in command:
                return {"success": False, "exit_code": 1, "stdout": "", "stderr": ""}
            if "code-server --bind-addr" in command:
                return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}
            if "curl" in command and "healthz" in command and "http_code" in command:
                healthz_call_count += 1
                return {"success": True, "exit_code": 0, "stdout": "200", "stderr": ""}
            if "mkdir -p" in command:
                return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}
            if "base64" in command:
                return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}
            return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}

        async def mock_mcp(session, endpoint, payload, timeout_seconds=30):
            nonlocal mcp_call_count
            mcp_call_count += 1
            return {"success": True}

        service._execute_shell_command = mock_shell
        service._execute_mcp_command = mock_mcp

        await service._initialize_session(mock_session)

        assert any("code-server --bind-addr" in cmd for cmd in call_sequence)
        assert mock_session.metadata.get("code_server_url") == "http://localhost:8443"
        assert mock_session.metadata.get("code_server_token") is not None
        assert len(call_sequence) >= 5
        assert mcp_call_count >= 1
        assert healthz_call_count >= 1

    @pytest.mark.asyncio
    async def test_initialize_session_code_server_fails_to_start(
        self, service, mock_session
    ):
        """Test initialization raises error when code-server fails to start"""
        async def mock_shell(session, command, timeout_seconds=60):
            if "pgrep" in command and "curl" in command:
                return {"success": False, "exit_code": 1, "stdout": "", "stderr": ""}
            if "code-server --bind-addr" in command:
                return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}
            if "curl" in command and "healthz" in command and "http_code" in command:
                return {"success": True, "exit_code": 0, "stdout": "500", "stderr": ""}
            return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}

        async def mock_mcp(session, endpoint, payload, timeout_seconds=30):
            return {"success": True}

        service._execute_shell_command = mock_shell
        service._execute_mcp_command = mock_mcp
        service.DEFAULT_STARTUP_RETRIES = 2
        service.DEFAULT_STARTUP_RETRY_INTERVAL = 0.1

        with pytest.raises(RuntimeError, match="code-server failed to start"):
            await service._initialize_session(mock_session)

    @pytest.mark.asyncio
    async def test_initialize_session_workspace_creation_fails(
        self, service, mock_session
    ):
        """Test initialization raises error when workspace creation fails"""
        async def mock_shell(session, command, timeout_seconds=60):
            if "pgrep" in command:
                return {"success": True, "exit_code": 0, "stdout": "12345", "stderr": ""}
            if "mkdir -p" in command and "/workspace" in command and ".vscode" not in command:
                return {"success": False, "exit_code": 1, "stdout": "", "stderr": "Permission denied"}
            return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}

        async def mock_mcp(session, endpoint, payload, timeout_seconds=30):
            return {"success": True}

        service._execute_shell_command = mock_shell
        service._execute_mcp_command = mock_mcp

        with pytest.raises(RuntimeError, match="Failed to create workspace"):
            await service._initialize_session(mock_session)

    @pytest.mark.asyncio
    async def test_initialize_session_settings_fallback(self, service, mock_session):
        """Test initialization uses shell fallback when MCP file/write fails"""
        shell_commands = []

        async def mock_shell(session, command, timeout_seconds=60):
            shell_commands.append(command)
            return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}

        async def mock_mcp(session, endpoint, payload, timeout_seconds=30):
            if endpoint == "file/write":
                return {"success": False, "error": "MCP unavailable"}
            return {"success": True}

        service._execute_shell_command = mock_shell
        service._execute_mcp_command = mock_mcp

        await service._initialize_session(mock_session)

        assert any("base64" in cmd and "settings.json" in cmd for cmd in shell_commands)

    @pytest.mark.asyncio
    async def test_poll_healthz_success_first_attempt(self, service, mock_session):
        """Test _poll_healthz returns True on first successful health check"""
        async def mock_shell(session, command, timeout_seconds=60):
            if "curl" in command and "healthz" in command:
                return {"success": True, "exit_code": 0, "stdout": "200", "stderr": ""}
            return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}

        service._execute_shell_command = mock_shell
        service.DEFAULT_STARTUP_RETRY_INTERVAL = 0.01

        result = await service._poll_healthz(mock_session, "127.0.0.1", 8443)

        assert result is True

    @pytest.mark.asyncio
    async def test_poll_healthz_success_after_retries(self, service, mock_session):
        """Test _poll_healthz returns True after multiple retries"""
        attempt_count = 0

        async def mock_shell(session, command, timeout_seconds=60):
            nonlocal attempt_count
            if "curl" in command and "healthz" in command:
                attempt_count += 1
                if attempt_count >= 3:
                    return {"success": True, "exit_code": 0, "stdout": "200", "stderr": ""}
                return {"success": True, "exit_code": 0, "stdout": "500", "stderr": ""}
            return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}

        service._execute_shell_command = mock_shell
        service.DEFAULT_STARTUP_RETRY_INTERVAL = 0.01

        result = await service._poll_healthz(mock_session, "127.0.0.1", 8443)

        assert result is True
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_poll_healthz_exhausts_retries(self, service, mock_session):
        """Test _poll_healthz returns False when all retries exhausted"""
        async def mock_shell(session, command, timeout_seconds=60):
            if "curl" in command and "healthz" in command:
                return {"success": True, "exit_code": 0, "stdout": "500", "stderr": ""}
            return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}

        service._execute_shell_command = mock_shell
        service.DEFAULT_STARTUP_RETRIES = 3
        service.DEFAULT_STARTUP_RETRY_INTERVAL = 0.01

        result = await service._poll_healthz(mock_session, "127.0.0.1", 8443)

        assert result is False

    @pytest.mark.asyncio
    async def test_poll_healthz_handles_curl_connection_failure(self, service, mock_session):
        """Test _poll_healthz handles curl connection failures (#2355)"""
        attempt_count = 0

        async def mock_shell(session, command, timeout_seconds=60):
            nonlocal attempt_count
            if "curl" in command and "healthz" in command:
                attempt_count += 1
                if attempt_count >= 3:
                    return {"success": True, "exit_code": 0, "stdout": "200", "stderr": ""}
                return {"success": False, "exit_code": 7, "stdout": "", "stderr": "Connection refused"}
            return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}

        service._execute_shell_command = mock_shell
        service.DEFAULT_STARTUP_RETRY_INTERVAL = 0.01

        result = await service._poll_healthz(mock_session, "127.0.0.1", 8443)

        assert result is True
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_poll_healthz_no_initial_delay(self, service, mock_session):
        """Test _poll_healthz runs first attempt immediately without delay (#2355)"""
        start_time = time.time()
        call_times = []

        async def mock_shell(session, command, timeout_seconds=60):
            if "curl" in command and "healthz" in command:
                call_times.append(time.time() - start_time)
                return {"success": True, "exit_code": 0, "stdout": "200", "stderr": ""}
            return {"success": True, "exit_code": 0, "stdout": "", "stderr": ""}

        service._execute_shell_command = mock_shell
        service.DEFAULT_STARTUP_RETRY_INTERVAL = 1.0

        result = await service._poll_healthz(mock_session, "127.0.0.1", 8443)

        assert result is True
        assert len(call_times) == 1
        assert call_times[0] < 0.5

    @pytest.mark.asyncio
    async def test_initialize_session_uses_token_auth(
        self, service, mock_session, mock_shell_for_startup, mock_mcp_success
    ):
        """Test initialization uses token-based auth instead of --auth none"""
        commands = []
        service._execute_shell_command = mock_shell_for_startup(
            code_server_running=False, commands_list=commands
        )
        service._execute_mcp_command = mock_mcp_success

        await service._initialize_session(mock_session)

        startup_cmd = next(
            (cmd for cmd in commands if "code-server --bind-addr" in cmd), None
        )
        assert startup_cmd is not None
        assert "--auth password" in startup_cmd
        assert "--auth none" not in startup_cmd
        assert "PASSWORD=" in startup_cmd
        assert mock_session.metadata.get("code_server_token") is not None

    @pytest.mark.asyncio
    async def test_initialize_session_uses_localhost_binding(
        self, service, mock_session, mock_shell_for_startup, mock_mcp_success
    ):
        """Test initialization binds to 127.0.0.1 instead of 0.0.0.0"""
        commands = []
        service._execute_shell_command = mock_shell_for_startup(
            code_server_running=False, commands_list=commands
        )
        service._execute_mcp_command = mock_mcp_success

        await service._initialize_session(mock_session)

        startup_cmd = next(
            (cmd for cmd in commands if "code-server --bind-addr" in cmd), None
        )
        assert startup_cmd is not None
        assert "127.0.0.1:8443" in startup_cmd
        assert "0.0.0.0" not in startup_cmd

    @pytest.mark.asyncio
    async def test_initialize_session_sets_cors_metadata(
        self, service, mock_session, mock_shell_for_startup, mock_mcp_success
    ):
        """Test initialization sets CORS / iframe metadata (#2353)"""
        service._execute_shell_command = mock_shell_for_startup(
            code_server_running=True
        )
        service._execute_mcp_command = mock_mcp_success

        await service._initialize_session(mock_session)

        assert "iframe_allowed_origins" in mock_session.metadata
        assert "public_url" in mock_session.metadata
        assert mock_session.metadata["public_url"] == mock_session.vscode_endpoint


class TestCorsConfig:
    """Tests for CORS / iframe configuration (#2353)"""

    @pytest.fixture
    def service(self):
        return VSCodeIDEService()

    def test_get_cors_config_default_empty(self, service, monkeypatch):
        """Test get_cors_config returns empty origins by default"""
        monkeypatch.setattr(
            "common.config.settings.settings.vscode_iframe_allowed_origins", ""
        )
        monkeypatch.setattr(
            "common.config.settings.settings.vscode_public_base_url", None
        )

        config = service.get_cors_config()

        assert config["allowed_origins"] == []
        assert config["public_url"] is None
        assert config["iframe_enabled"] is False

    def test_get_cors_config_with_origins(self, service, monkeypatch):
        """Test get_cors_config parses comma-separated origins"""
        monkeypatch.setattr(
            "common.config.settings.settings.vscode_iframe_allowed_origins",
            "https://app.morningai.com,https://staging.morningai.com"
        )
        monkeypatch.setattr(
            "common.config.settings.settings.vscode_public_base_url",
            "https://ide.morningai.com"
        )

        config = service.get_cors_config()

        assert config["allowed_origins"] == [
            "https://app.morningai.com",
            "https://staging.morningai.com"
        ]
        assert config["public_url"] == "https://ide.morningai.com"
        assert config["iframe_enabled"] is True

    def test_get_cors_headers_disabled(self, service, monkeypatch):
        """Test get_cors_headers returns DENY when iframe is disabled"""
        monkeypatch.setattr(
            "common.config.settings.settings.vscode_iframe_allowed_origins", ""
        )
        monkeypatch.setattr(
            "common.config.settings.settings.vscode_public_base_url", None
        )

        headers = service.get_cors_headers()

        assert headers["X-Frame-Options"] == "DENY"
        assert "Content-Security-Policy" not in headers

    def test_get_cors_headers_single_origin(self, service, monkeypatch):
        """Test get_cors_headers with single origin sets both headers"""
        monkeypatch.setattr(
            "common.config.settings.settings.vscode_iframe_allowed_origins",
            "https://app.morningai.com"
        )
        monkeypatch.setattr(
            "common.config.settings.settings.vscode_public_base_url", None
        )

        headers = service.get_cors_headers()

        expected_csp = "frame-ancestors 'self' https://app.morningai.com"
        assert headers["Content-Security-Policy"] == expected_csp
        assert headers["X-Frame-Options"] == "ALLOW-FROM https://app.morningai.com"

    def test_get_cors_headers_multiple_origins(self, service, monkeypatch):
        """Test get_cors_headers with multiple origins only sets CSP"""
        monkeypatch.setattr(
            "common.config.settings.settings.vscode_iframe_allowed_origins",
            "https://app.morningai.com,https://staging.morningai.com"
        )
        monkeypatch.setattr(
            "common.config.settings.settings.vscode_public_base_url", None
        )

        headers = service.get_cors_headers()

        expected_csp = (
            "frame-ancestors 'self' "
            "https://app.morningai.com https://staging.morningai.com"
        )
        assert headers["Content-Security-Policy"] == expected_csp
        assert "X-Frame-Options" not in headers
