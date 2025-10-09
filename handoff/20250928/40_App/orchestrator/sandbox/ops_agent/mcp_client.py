#!/usr/bin/env python3
"""
MCP Client runner for Ops_Agent Sandbox
"""
import asyncio
import os
import sys

sys.path.append('/app')

from mcp.client import MCPClient

async def main():
    """Main entry point for MCP client in sandbox"""
    server_url = os.getenv('MCP_SERVER_URL', 'http://host.docker.internal:8080')
    agent_id = os.getenv('AGENT_ID', 'ops-agent-unknown')
    
    print(f"Starting MCP client for agent {agent_id}")
    print(f"Connecting to MCP server at {server_url}")
    
    client = MCPClient(server_url, agent_id)
    await client.connect()
    
    print("MCP client connected and ready")
    
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
