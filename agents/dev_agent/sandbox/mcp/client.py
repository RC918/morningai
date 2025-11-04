#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Client
Runs inside agent sandbox and communicates with MCP Server for tool access
"""
import asyncio
import aiohttp
import logging
import json
from typing import Dict, Any, Optional

class MCPClient:
    """MCP client for agent-side tool access"""
    
    def __init__(self, server_url: str, agent_id: str):
        self.server_url = server_url
        self.agent_id = agent_id
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def connect(self):
        """Connect to MCP server"""
        self.session = aiohttp.ClientSession()
        self.logger.info(f"MCP client connected to {self.server_url}")
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.session:
            await self.session.close()
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool via MCP protocol"""
        if not self.session:
            raise Exception("MCP client not connected")
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            },
            "id": self.agent_id
        }
        
        try:
            async with self.session.post(
                f"{self.server_url}/mcp",
                json=request,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if "error" in result:
                    self.logger.error(f"MCP tool call failed: {result['error']}")
                    raise Exception(result['error']['message'])
                
                return result.get("result", {})
                
        except Exception as e:
            self.logger.error(f"Failed to call tool {tool_name}: {e}")
            raise
    
    async def execute_shell(self, command: str) -> Dict[str, Any]:
        """Execute shell command"""
        return await self.call_tool("shell", {"command": command})
    
    async def browse_url(self, url: str, action: str = "navigate") -> Dict[str, Any]:
        """Browser automation"""
        return await self.call_tool("browser", {"url": url, "action": action})
    
    async def render_api_call(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Call Render API"""
        return await self.call_tool("render", {"endpoint": endpoint, "method": method, "data": data})
