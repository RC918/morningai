#!/usr/bin/env python3
"""
E2E tests for Ops_Agent sandbox
"""
import pytest
import asyncio
from sandbox.manager import sandbox_manager, SandboxConfig
from mcp.client import MCPClient

@pytest.mark.asyncio
async def test_ops_agent_shell_execution():
    """Test shell command execution in sandbox"""
    config = SandboxConfig(
        agent_id='test-ops-agent-001',
        agent_type='ops_agent'
    )
    
    sandbox = await sandbox_manager.create_sandbox(config)
    
    try:
        client = MCPClient(sandbox.mcp_endpoint, sandbox.agent_id)
        await client.connect()
        
        result = await client.execute_shell('echo "Hello from sandbox"')
        
        assert result['status'] == 'success'
        assert 'Hello from sandbox' in result['result']['stdout']
        
        await client.disconnect()
    finally:
        await sandbox_manager.destroy_sandbox(sandbox.sandbox_id)

@pytest.mark.asyncio
async def test_ops_agent_browser_automation():
    """Test browser automation in sandbox"""
    config = SandboxConfig(
        agent_id='test-ops-agent-002',
        agent_type='ops_agent'
    )
    
    sandbox = await sandbox_manager.create_sandbox(config)
    
    try:
        client = MCPClient(sandbox.mcp_endpoint, sandbox.agent_id)
        await client.connect()
        
        result = await client.browse_url('https://example.com')
        
        assert result['status'] == 'success'
        assert 'title' in result['result']
        
        await client.disconnect()
    finally:
        await sandbox_manager.destroy_sandbox(sandbox.sandbox_id)

@pytest.mark.asyncio
async def test_ops_agent_hitl_approval():
    """Test HITL approval for high-risk operations"""
    config = SandboxConfig(
        agent_id='test-ops-agent-003',
        agent_type='ops_agent'
    )
    
    sandbox = await sandbox_manager.create_sandbox(config)
    
    try:
        client = MCPClient(sandbox.mcp_endpoint, sandbox.agent_id)
        await client.connect()
        
        result = await client.execute_shell('rm -rf /tmp/test')
        
        assert result['status'] == 'pending_approval'
        assert 'approval_request_id' in result
        
        await client.disconnect()
    finally:
        await sandbox_manager.destroy_sandbox(sandbox.sandbox_id)
