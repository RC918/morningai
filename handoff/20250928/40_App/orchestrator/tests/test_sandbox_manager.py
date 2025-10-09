#!/usr/bin/env python3
"""
Unit tests for Agent Sandbox Manager
"""
import pytest
import asyncio
from sandbox.manager import AgentSandboxManager, SandboxConfig, SandboxStatus

@pytest.mark.asyncio
async def test_create_sandbox():
    """Test sandbox creation"""
    manager = AgentSandboxManager()
    
    config = SandboxConfig(
        agent_id='test-agent-001',
        agent_type='ops_agent'
    )
    
    sandbox = await manager.create_sandbox(config)
    
    assert sandbox is not None
    assert sandbox.status == SandboxStatus.READY
    assert sandbox.container_id is not None
    
    await manager.destroy_sandbox(sandbox.sandbox_id)

@pytest.mark.asyncio
async def test_destroy_sandbox():
    """Test sandbox destruction"""
    manager = AgentSandboxManager()
    
    config = SandboxConfig(
        agent_id='test-agent-002',
        agent_type='ops_agent'
    )
    
    sandbox = await manager.create_sandbox(config)
    result = await manager.destroy_sandbox(sandbox.sandbox_id)
    
    assert result is True
    assert sandbox.sandbox_id not in manager.sandboxes

@pytest.mark.asyncio
async def test_cleanup_expired_sandboxes():
    """Test cleanup of expired sandboxes"""
    manager = AgentSandboxManager()
    
    await manager.cleanup_expired_sandboxes()
