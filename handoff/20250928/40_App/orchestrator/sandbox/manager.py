#!/usr/bin/env python3
"""
Agent Sandbox Manager - Manages lifecycle of agent sandboxes
"""
import asyncio
import logging
import uuid
import os
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class SandboxStatus(Enum):
    CREATING = "creating"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class SandboxConfig:
    """Configuration for agent sandbox"""
    agent_id: str
    agent_type: str
    cpu_limit: float = 1.0
    memory_limit_mb: int = 2048
    disk_limit_mb: int = 10240
    network_enabled: bool = True
    idle_timeout_minutes: int = 30
    max_runtime_hours: int = 2

@dataclass
class Sandbox:
    """Represents an agent sandbox instance"""
    sandbox_id: str
    agent_id: str
    agent_type: str
    status: SandboxStatus
    created_at: datetime
    container_id: Optional[str] = None
    mcp_endpoint: Optional[str] = None
    last_activity: Optional[datetime] = None

class AgentSandboxManager:
    """Manages agent sandbox lifecycle"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sandboxes: Dict[str, Sandbox] = {}
        self._lock = asyncio.Lock()
    
    async def create_sandbox(self, config: SandboxConfig) -> Sandbox:
        """Create a new agent sandbox"""
        async with self._lock:
            sandbox_id = str(uuid.uuid4())
            
            sandbox_enabled = os.getenv('SANDBOX_ENABLED', 'false').lower() == 'true'
            
            self.logger.info(f"Creating sandbox {sandbox_id} for agent {config.agent_id} (SANDBOX_ENABLED={sandbox_enabled})")
            
            sandbox = Sandbox(
                sandbox_id=sandbox_id,
                agent_id=config.agent_id,
                agent_type=config.agent_type,
                status=SandboxStatus.CREATING,
                created_at=datetime.now()
            )
            
            self.sandboxes[sandbox_id] = sandbox
            
            try:
                if not sandbox_enabled:
                    self.logger.warning(f"Sandbox disabled via SANDBOX_ENABLED=false - skipping Docker container creation")
                    sandbox.status = SandboxStatus.READY
                    sandbox.mcp_endpoint = "http://localhost:8080"
                    sandbox.last_activity = datetime.now()
                    return sandbox
                
                from .docker_sandbox import DockerSandbox
                
                docker_sandbox = DockerSandbox(config)
                container_id = await docker_sandbox.create()
                
                sandbox.container_id = container_id
                sandbox.mcp_endpoint = docker_sandbox.get_mcp_endpoint()
                sandbox.status = SandboxStatus.READY
                sandbox.last_activity = datetime.now()
                
                self.logger.info(f"Sandbox {sandbox_id} created successfully")
                return sandbox
                
            except Exception as e:
                self.logger.error(f"Failed to create sandbox {sandbox_id}: {e}")
                sandbox.status = SandboxStatus.ERROR
                raise
    
    async def destroy_sandbox(self, sandbox_id: str) -> bool:
        """Destroy an agent sandbox"""
        async with self._lock:
            if sandbox_id not in self.sandboxes:
                self.logger.warning(f"Sandbox {sandbox_id} not found")
                return False
            
            sandbox = self.sandboxes[sandbox_id]
            sandbox_enabled = os.getenv('SANDBOX_ENABLED', 'false').lower() == 'true'
            
            try:
                if not sandbox_enabled or not sandbox.container_id:
                    self.logger.info(f"Sandbox {sandbox_id} cleanup skipped (SANDBOX_ENABLED={sandbox_enabled})")
                    sandbox.status = SandboxStatus.STOPPED
                    del self.sandboxes[sandbox_id]
                    return True
                
                from .docker_sandbox import DockerSandbox
                
                docker_sandbox = DockerSandbox(None)
                await docker_sandbox.destroy(sandbox.container_id)
                
                sandbox.status = SandboxStatus.STOPPED
                del self.sandboxes[sandbox_id]
                
                self.logger.info(f"Sandbox {sandbox_id} destroyed successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to destroy sandbox {sandbox_id}: {e}")
                return False
    
    async def get_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        """Get sandbox by ID"""
        return self.sandboxes.get(sandbox_id)
    
    async def cleanup_expired_sandboxes(self):
        """Clean up idle or expired sandboxes"""
        now = datetime.now()
        expired_sandboxes = []
        
        for sandbox_id, sandbox in self.sandboxes.items():
            if sandbox.last_activity:
                idle_time = now - sandbox.last_activity
                if idle_time > timedelta(minutes=30):
                    expired_sandboxes.append(sandbox_id)
            
            runtime = now - sandbox.created_at
            if runtime > timedelta(hours=2):
                expired_sandboxes.append(sandbox_id)
        
        for sandbox_id in expired_sandboxes:
            await self.destroy_sandbox(sandbox_id)

sandbox_manager = AgentSandboxManager()
