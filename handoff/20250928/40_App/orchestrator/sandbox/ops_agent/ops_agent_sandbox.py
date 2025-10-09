#!/usr/bin/env python3
"""
Ops_Agent Sandbox Runner
Extends the base Ops_Agent with MCP tool access
"""
import asyncio
import sys
import os

sys.path.append('/home/ubuntu/repos/morningai')

from ops_agent import OpsAgent
from mcp.client import MCPClient

class OpsAgentSandbox(OpsAgent):
    """Ops_Agent with sandbox capabilities"""
    
    def __init__(self, mcp_client: MCPClient):
        super().__init__()
        self.mcp_client = mcp_client
    
    async def execute_shell_command(self, command: str):
        """Execute shell command via MCP"""
        return await self.mcp_client.execute_shell(command)
    
    async def check_service_health(self, service_url: str):
        """Check service health via browser"""
        return await self.mcp_client.browse_url(service_url)

async def main():
    """Main entry point"""
    server_url = os.getenv('MCP_SERVER_URL', 'http://host.docker.internal:8080')
    agent_id = os.getenv('AGENT_ID', 'ops-agent-unknown')
    
    mcp_client = MCPClient(server_url, agent_id)
    await mcp_client.connect()
    
    ops_agent = OpsAgentSandbox(mcp_client)
    
    print(f"Ops_Agent sandbox initialized: {agent_id}")
    
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
