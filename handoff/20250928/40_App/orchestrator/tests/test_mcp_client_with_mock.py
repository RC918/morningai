#!/usr/bin/env python3
"""
Unit tests for MCP Client using Mock MCP Server

Tests MCP client functionality without requiring a real MCP server.
"""
import pytest
import pytest_asyncio
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.client import MCPClient
from tests.mock_mcp_server import MockMCPServer
from exceptions import MCPConnectionError, MCPTimeoutError


@pytest_asyncio.fixture
async def mock_server():
    """Fixture to create and start mock MCP server"""
    server = MockMCPServer(host="localhost", port=8765)
    await server.start()
    yield server
    await server.stop()


@pytest.mark.asyncio
async def test_mcp_client_context_manager(mock_server):
    """Test MCP client with async context manager"""
    async with MCPClient("http://localhost:8765", "test-agent") as client:
        result = await client.execute_shell('echo "test"')
        
        assert result["status"] == "success"
        assert "stdout" in result["result"]
        assert "test" in result["result"]["stdout"]
    
    assert mock_server.get_call_count("shell") == 1


@pytest.mark.asyncio
async def test_mcp_client_shell_execution(mock_server):
    """Test shell command execution via MCP"""
    async with MCPClient("http://localhost:8765", "test-agent") as client:
        result = await client.execute_shell('ls -la')
        
        assert result["status"] == "success"
        assert result["result"]["exit_code"] == 0
        assert "ls -la" in result["result"]["stdout"]


@pytest.mark.asyncio
async def test_mcp_client_browser_automation(mock_server):
    """Test browser automation via MCP"""
    async with MCPClient("http://localhost:8765", "test-agent") as client:
        result = await client.browse_url("https://example.com")
        
        assert result["status"] == "success"
        assert "title" in result["result"]
        assert "example.com" in result["result"]["url"]


@pytest.mark.asyncio
async def test_mcp_client_render_api(mock_server):
    """Test Render API calls via MCP"""
    async with MCPClient("http://localhost:8765", "test-agent") as client:
        result = await client.render_api_call("/api/test", method="POST", data={"key": "value"})
        
        assert result["status"] == "success"
        assert result["result"]["endpoint"] == "/api/test"
        assert result["result"]["method"] == "POST"


@pytest.mark.asyncio
async def test_mcp_client_multiple_calls(mock_server):
    """Test multiple MCP calls in sequence"""
    async with MCPClient("http://localhost:8765", "test-agent") as client:
        await client.execute_shell('echo "call 1"')
        await client.execute_shell('echo "call 2"')
        await client.browse_url("https://example1.com")
        await client.browse_url("https://example2.com")
    
    assert mock_server.get_call_count() == 4
    assert mock_server.get_call_count("shell") == 2
    assert mock_server.get_call_count("browser") == 2


@pytest.mark.asyncio
async def test_mcp_client_connection_error():
    """Test connection error handling"""
    with pytest.raises(MCPConnectionError):
        async with MCPClient("http://localhost:9999", "test-agent") as client:
            await client.execute_shell('echo "test"')


@pytest.mark.asyncio
async def test_mcp_client_not_connected():
    """Test error when calling without connection"""
    client = MCPClient("http://localhost:8765", "test-agent")
    
    with pytest.raises(MCPConnectionError):
        await client.execute_shell('echo "test"')


@pytest.mark.asyncio
async def test_mcp_client_manual_connect_disconnect(mock_server):
    """Test manual connect/disconnect (legacy API)"""
    client = MCPClient("http://localhost:8765", "test-agent")
    
    await client.connect()
    result = await client.execute_shell('echo "test"')
    assert result["status"] == "success"
    
    await client.disconnect()
    
    with pytest.raises(MCPConnectionError):
        await client.execute_shell('echo "test"')


@pytest.mark.asyncio
async def test_mcp_client_timeout(mock_server):
    """Test timeout handling"""
    mock_server.response_delay = 10.0
    
    client = MCPClient("http://localhost:8765", "test-agent", timeout=1)
    
    with pytest.raises((asyncio.TimeoutError, MCPConnectionError)):
        async with client:
            await client.execute_shell('echo "test"')


@pytest.mark.asyncio
async def test_mcp_server_error_response(mock_server):
    """Test handling of server error responses"""
    mock_server.simulate_errors = True
    
    async with MCPClient("http://localhost:8765", "test-agent") as client:
        with pytest.raises(Exception) as exc_info:
            await client.execute_shell('echo "test"')
        
        assert "MCP tool error" in str(exc_info.value) or "Simulated error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_mcp_client_session_cleanup(mock_server):
    """Test that session is properly cleaned up"""
    client = MCPClient("http://localhost:8765", "test-agent")
    
    async with client:
        await client.execute_shell('echo "test"')
        assert client._connected is True
        assert client.session is not None
        assert not client.session.closed
    
    assert client._connected is False
    assert client.session is None


@pytest.mark.asyncio
async def test_mcp_client_exception_during_operation(mock_server):
    """Test that session is cleaned up even when exception occurs"""
    client = MCPClient("http://localhost:8765", "test-agent")
    
    try:
        async with client:
            await client.execute_shell('echo "test"')
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    assert client._connected is False
    assert client.session is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
