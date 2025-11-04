# MCP Client Testing Guide

**Version**: 1.0  
**Last Updated**: 2025-10-19  
**Author**: Devin AI

---

## Overview

This guide covers testing the MCP Client using the Mock MCP Server. The mock server allows unit testing without requiring a real MCP server infrastructure.

---

## Quick Start

### Running Tests

```bash
cd handoff/20250928/40_App/orchestrator

# Run all MCP client tests
pytest tests/test_mcp_client_with_mock.py -v

# Run with coverage
pytest tests/test_mcp_client_with_mock.py --cov=mcp.client --cov-report=html

# Run specific test
pytest tests/test_mcp_client_with_mock.py::test_mcp_client_context_manager -v
```

---

## Mock MCP Server

### Features

The `MockMCPServer` provides:

1. **JSON-RPC 2.0 Protocol** - Full MCP protocol support
2. **Tool Simulation** - Simulates shell, browser, render tools
3. **Error Simulation** - Can simulate server errors for testing
4. **Response Delay** - Simulate slow responses for timeout testing
5. **Call History** - Track all calls for assertions

### Basic Usage

```python
import asyncio
from tests.mock_mcp_server import MockMCPServer

async def test_example():
    # Start server
    async with MockMCPServer(host="localhost", port=8765) as server:
        # Server is running, use it in tests
        pass
        # Server automatically stops when exiting context
```

### Configuration

```python
server = MockMCPServer(host="localhost", port=8765)

# Simulate errors
server.simulate_errors = True

# Add response delay (seconds)
server.response_delay = 2.0

# Reset state
server.reset()

# Check call history
total_calls = server.get_call_count()
shell_calls = server.get_call_count("shell")
```

---

## Test Structure

### Test File Organization

```
tests/
├── mock_mcp_server.py         # Mock server implementation
├── test_mcp_client_with_mock.py  # MCP client unit tests
├── test_ops_agent_sandbox.py  # E2E sandbox tests
└── conftest.py                # Pytest configuration (if needed)
```

### Test Categories

**1. Basic Functionality Tests**
- Context manager usage
- Manual connect/disconnect
- Session cleanup

**2. Tool Execution Tests**
- Shell commands
- Browser automation
- Render API calls

**3. Error Handling Tests**
- Connection errors
- Server errors
- Timeout handling
- Invalid state errors

**4. Edge Cases**
- Multiple concurrent calls
- Calling without connection
- Exception during operation

---

## Writing Tests

### Template for New Tests

```python
@pytest.mark.asyncio
async def test_my_feature(mock_server):
    """Test description"""
    # Arrange
    async with MCPClient("http://localhost:8765", "test-agent") as client:
        # Act
        result = await client.execute_shell('echo "test"')
        
        # Assert
        assert result["status"] == "success"
        assert mock_server.get_call_count("shell") == 1
```

### Using Fixtures

```python
@pytest.fixture
async def mock_server():
    """Fixture to create and start mock MCP server"""
    server = MockMCPServer(host="localhost", port=8765)
    await server.start()
    yield server
    await server.stop()


@pytest.fixture
async def mcp_client(mock_server):
    """Fixture to create MCP client"""
    async with MCPClient("http://localhost:8765", "test-agent") as client:
        yield client
```

---

## Testing Error Scenarios

### Connection Errors

```python
@pytest.mark.asyncio
async def test_connection_error():
    """Test connection to unavailable server"""
    with pytest.raises(MCPConnectionError):
        async with MCPClient("http://localhost:9999", "test-agent") as client:
            await client.execute_shell('echo "test"')
```

### Timeout Errors

```python
@pytest.mark.asyncio
async def test_timeout(mock_server):
    """Test timeout handling"""
    mock_server.response_delay = 10.0  # 10 second delay
    
    client = MCPClient("http://localhost:8765", "test-agent", timeout=1)
    
    with pytest.raises((asyncio.TimeoutError, ConnectionError)):
        async with client:
            await client.execute_shell('echo "test"')
```

### Server Errors

```python
@pytest.mark.asyncio
async def test_server_error(mock_server):
    """Test handling of server error responses"""
    mock_server.simulate_errors = True
    
    async with MCPClient("http://localhost:8765", "test-agent") as client:
        with pytest.raises(Exception) as exc_info:
            await client.execute_shell('echo "test"')
        
        assert "error" in str(exc_info.value).lower()
```

---

## Test Coverage Goals

### Current Coverage

Run coverage report:
```bash
pytest tests/test_mcp_client_with_mock.py --cov=mcp.client --cov-report=term-missing
```

### Target Coverage

| Component | Target | Priority |
|-----------|--------|----------|
| `mcp/client.py` | 85%+ | High |
| `exceptions.py` | 100% | High |
| `utils/retry.py` | 80%+ | Medium |
| `tools/github_api.py` | 75%+ | Medium |

### Coverage Improvement Strategy

**Phase 1 (Week 1)**: 50% coverage
- Basic functionality tests
- Happy path scenarios
- Context manager tests

**Phase 2 (Week 2)**: 75% coverage
- Error handling tests
- Edge cases
- Timeout scenarios

**Phase 3 (Week 3)**: 85%+ coverage
- Concurrent operations
- State management
- Integration scenarios

---

## CI/CD Integration

### GitHub Actions Configuration

```yaml
name: MCP Client Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests with coverage
        run: |
          cd handoff/20250928/40_App/orchestrator
          pytest tests/test_mcp_client_with_mock.py \
            --cov=mcp.client \
            --cov-report=xml \
            --cov-report=term
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./coverage.xml
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run tests
pytest tests/test_mcp_client_with_mock.py -v -s
```

### Inspect Mock Server Calls

```python
@pytest.mark.asyncio
async def test_with_inspection(mock_server):
    async with MCPClient("http://localhost:8765", "test-agent") as client:
        await client.execute_shell('echo "test"')
    
    # Inspect all calls
    for call in mock_server.call_history:
        print(f"Method: {call.get('method')}")
        print(f"Params: {call.get('params')}")
```

### Test Individual Components

```python
# Test session management separately
@pytest.mark.asyncio
async def test_session_lifecycle():
    client = MCPClient("http://localhost:8765", "test-agent")
    
    assert client._connected is False
    assert client.session is None
    
    await client.connect()
    assert client._connected is True
    assert client.session is not None
    
    await client.disconnect()
    assert client._connected is False
```

---

## Manual Testing

### Start Mock Server Manually

```bash
cd handoff/20250928/40_App/orchestrator
python -m tests.mock_mcp_server
```

Server runs on `http://localhost:8765`

### Test with curl

```bash
# Test MCP endpoint
curl -X POST http://localhost:8765/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "shell",
      "arguments": {"command": "echo test"}
    },
    "id": "test-1"
  }'
```

### Test with Python

```python
import asyncio
from mcp.client import MCPClient

async def manual_test():
    async with MCPClient("http://localhost:8765", "manual-test") as client:
        # Test shell
        result = await client.execute_shell('echo "Hello World"')
        print("Shell result:", result)
        
        # Test browser
        result = await client.browse_url("https://example.com")
        print("Browser result:", result)

asyncio.run(manual_test())
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8765
lsof -i :8765

# Kill process
kill -9 <PID>

# Or use different port
MockMCPServer(host="localhost", port=8766)
```

### Tests Hanging

- Check for missing `await` keywords
- Verify server is properly started/stopped
- Check timeout configuration
- Use `pytest -v -s` to see output

### Import Errors

```bash
# Ensure you're in correct directory
cd handoff/20250928/40_App/orchestrator

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run tests
pytest tests/test_mcp_client_with_mock.py -v
```

---

## Best Practices

### DO ✅

- Use async context managers (`async with`)
- Test both success and error paths
- Clean up resources in fixtures
- Use descriptive test names
- Add docstrings to tests
- Test edge cases
- Mock external dependencies

### DON'T ❌

- Don't use real MCP servers in unit tests
- Don't forget to `await` async operations
- Don't leave servers running after tests
- Don't test implementation details
- Don't ignore timeouts
- Don't skip error handling tests

---

## Next Steps

1. **Run existing tests** to establish baseline
2. **Add missing tests** for uncovered code paths
3. **Improve coverage** to 85%+ target
4. **Document findings** in test reports
5. **Integrate with CI/CD** for automated testing

---

## Resources

- **Mock MCP Server**: `tests/mock_mcp_server.py`
- **MCP Client**: `mcp/client.py`
- **Exception Types**: `exceptions.py`
- **Retry Utilities**: `utils/retry.py`

---

**Questions?** Check the main documentation or create an issue.
