# VSCode IDE Service Test Strategy

This document describes the testing strategy for `VSCodeIDEService` in the MorningAI orchestrator.

## Overview

The `VSCodeIDEService` class manages IDE sessions for code editing, testing, and debugging. Due to its complexity and external dependencies (code-server, MCP endpoints, shell commands), we employ a layered testing approach that balances test isolation with integration coverage.

## Test Architecture

### Test Class Organization

| Test Class | Purpose | Mock Strategy |
|------------|---------|---------------|
| `TestDataclasses` | Dataclass serialization | No mocks needed |
| `TestEnums` | Enum value verification | No mocks needed |
| `TestVSCodeIDEService` | Session lifecycle management | Mock `_initialize_session` as no-op |
| `TestInitializeSession` | IDE initialization logic | Mock shell/MCP commands |
| `TestCorsConfig` | CORS configuration | Mock settings |
| `TestExtensionConfig` | Extension auto-install | Mock settings/shell |
| `TestResourceMonitoring` | Resource monitoring | Mock settings/shell |
| `TestLanguageDetection` | Language detection | No external mocks |
| `TestOutputParsing` | Output parsing utilities | No external mocks |
| `TestSessionStatistics` | Session statistics | Mock `_initialize_session` |
| `TestFormatterAndLinterConfig` | Formatter/linter config | No external mocks |
| `TestTruncateErrorMessage` | Error message truncation | No external mocks |

### Mock Strategy Rationale

#### Why Mock `_initialize_session` in `TestVSCodeIDEService`

The `TestVSCodeIDEService` class tests session lifecycle management (create, close, get, etc.). These tests mock `_initialize_session` as a no-op for the following reasons:

1. **Test Isolation**: Session management logic should be tested independently from IDE initialization
2. **Speed**: Real initialization involves multiple shell commands and health checks
3. **Determinism**: Avoiding external dependencies ensures consistent test results
4. **Focus**: Each test class has a single responsibility

```python
async def _noop_initialize(session):
    pass

monkeypatch.setattr(service, "_initialize_session", _noop_initialize)
```

#### Why Test `_initialize_session` Separately

The `TestInitializeSession` class provides dedicated coverage for initialization logic:

1. **Complexity**: Initialization involves code-server startup, health checks, workspace setup, and settings configuration
2. **Error Handling**: Multiple failure modes need explicit testing
3. **Security**: Token-based auth and localhost binding require verification
4. **Integration Points**: MCP and shell command interactions need coverage

### Test Isolation Guarantees

All tests in `TestInitializeSession` are designed to be environment-independent:

- **No subprocess calls**: All shell commands are mocked
- **No socket connections**: All HTTP/MCP calls are mocked
- **No file system access**: All file operations are mocked
- **No external requests**: No network calls to real services

This ensures tests can run in any CI environment without special setup.

## Edge Case Coverage

### Health Check Edge Cases

| Scenario | Test | Status |
|----------|------|--------|
| First attempt success | `test_poll_healthz_success_first_attempt` | Covered |
| Success after retries | `test_poll_healthz_success_after_retries` | Covered |
| All retries exhausted | `test_poll_healthz_exhausts_retries` | Covered |
| curl connection failure | `test_poll_healthz_handles_curl_connection_failure` | Covered |
| No initial delay | `test_poll_healthz_no_initial_delay` | Covered |
| curl success but pgrep fails | `test_poll_healthz_curl_success_pgrep_fails` | **NEW** |
| Unexpected stderr output | `test_poll_healthz_unexpected_stderr` | **NEW** |
| Empty stdout handling | `test_poll_healthz_empty_stdout` | **NEW** |

### Settings Configuration Edge Cases

| Scenario | Test | Status |
|----------|------|--------|
| MCP write success | `test_initialize_session_starts_code_server` | Covered |
| MCP write failure (shell fallback) | `test_initialize_session_settings_fallback` | Covered |
| Shell fallback partial failure | `test_initialize_session_settings_shell_partial_failure` | **NEW** |

### Resource Monitoring Edge Cases

| Scenario | Test | Status |
|----------|------|--------|
| CPU/memory collection success | `test_collect_resource_usage_success` | Covered |
| Command failure | `test_collect_resource_usage_command_failure` | Covered |
| Parse failure (invalid format) | `test_collect_resource_usage_parse_failure` | **NEW** |

## Call Count Assertions

To ensure correct interaction patterns, tests should verify call counts for critical operations:

```python
assert shell_call_count >= 3  # Minimum expected shell calls
assert mcp_call_count >= 1    # At least one MCP call for settings
assert healthz_call_count >= 1  # At least one health check
```

### Recommended Call Count Assertions

| Operation | Minimum Calls | Rationale |
|-----------|---------------|-----------|
| Shell commands (startup) | 3 | pgrep, code-server start, healthz |
| Shell commands (running) | 2 | pgrep, mkdir |
| MCP commands | 1 | settings.json write |
| Health checks | 1 | Verify server is ready |

## Integration Testing

### Current State

Unit tests mock all external dependencies. For true integration testing, we need:

1. **code-server container**: A Docker image with code-server pre-installed
2. **MCP mock server**: A lightweight server that responds to MCP commands
3. **Test VM**: A sandboxed environment for shell command execution

### Integration Test Design

```
+-------------------+     +-------------------+
|   Test Runner     |---->|  code-server      |
|   (pytest)        |     |  (container)      |
+-------------------+     +-------------------+
        |                         |
        v                         v
+-------------------+     +-------------------+
|   MCP Mock        |     |   Test Workspace  |
|   Server          |     |   (volume)        |
+-------------------+     +-------------------+
```

### Integration Test Execution

Integration tests should be:
- **Marked separately**: `@pytest.mark.integration`
- **Skipped in CI by default**: Only run on explicit request
- **Documented**: Clear setup instructions for local execution

```python
@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled"
)
async def test_real_code_server_startup():
    """Integration test with real code-server"""
    pass
```

### Manual Integration Test Guide

For manual integration testing without containerization:

1. **Prerequisites**:
   - code-server installed (`npm install -g code-server`)
   - MCP server running locally
   - Test workspace directory

2. **Environment Setup**:
   ```bash
   export RUN_INTEGRATION_TESTS=1
   export CODE_SERVER_PATH=/usr/local/bin/code-server
   export MCP_ENDPOINT=http://localhost:8080
   ```

3. **Run Tests**:
   ```bash
   pytest -m integration -v
   ```

## CI Integration

### Test Isolation Check

To prevent accidental environment dependencies, CI should verify:

```yaml
- name: Verify Test Isolation
  run: |
    # Run tests in isolated environment (no network, no code-server)
    pytest handoff/20250928/40_App/orchestrator/meta_agent/tests/test_vscode_ide.py \
      --ignore-glob='**/test_integration_*.py' \
      -v
```

### Future: Integration Test CI Job

```yaml
integration-tests:
  runs-on: ubuntu-latest
  services:
    code-server:
      image: codercom/code-server:latest
      ports:
        - 8443:8443
  steps:
    - name: Run Integration Tests
      env:
        RUN_INTEGRATION_TESTS: "1"
      run: pytest -m integration -v
```

## Design Decisions

### Decision 1: Mock `_initialize_session` for Session Tests

**Context**: `TestVSCodeIDEService` tests session lifecycle management.

**Decision**: Mock `_initialize_session` as a no-op function.

**Rationale**:
- Session management logic is independent of initialization
- Initialization has its own dedicated test class
- Reduces test complexity and execution time
- Ensures deterministic test results

**Trade-offs**:
- Less end-to-end coverage in session tests
- Mitigated by `TestInitializeSession` coverage

### Decision 2: Separate Test Class for Initialization

**Context**: `_initialize_session` has complex logic with multiple failure modes.

**Decision**: Create dedicated `TestInitializeSession` class.

**Rationale**:
- Single responsibility principle
- Easier to add new initialization tests
- Clear ownership of initialization coverage
- Better test organization

### Decision 3: Shell Command Mocking Pattern

**Context**: Tests need to mock shell commands with different responses.

**Decision**: Use factory fixtures that create configurable mock functions.

**Rationale**:
- Reusable across multiple tests
- Configurable behavior (success/failure, output)
- Captures command history for assertions
- Reduces boilerplate

```python
@pytest.fixture
def mock_shell_for_startup(self):
    def _create_mock(code_server_running=False, healthz_response="200"):
        async def mock_shell(session, command, timeout_seconds=60):
            # ... mock logic
        return mock_shell
    return _create_mock
```

## References

- PR #2350: Original `_initialize_session` implementation
- PR #2354: Initialization hardening
- PR #2355: Health check improvements
- PR #2360: Resource monitoring
- Issue #2352: This test strategy documentation
- Epic #2311: Phase 3A orchestrator improvements
