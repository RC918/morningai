#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Client
Runs inside agent sandbox and communicates with MCP Server for tool access
"""
import asyncio
import aiohttp
import logging
import json
import sys
import os
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions import MCPConnectionError

class MCPClient:
    """MCP client for agent-side tool access"""
    
    def __init__(self, server_url: str, agent_id: str, timeout: int = 30):
        self.server_url = server_url
        self.agent_id = agent_id
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures session is closed"""
        await self.disconnect()
        return False
    
    async def connect(self):
        """Connect to MCP server"""
        if self._connected:
            self.logger.warning("MCP client already connected")
            return
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            self._connected = True
            self.logger.info(f"MCP client connected to {self.server_url}")
        except Exception as e:
            self.logger.error(f"Failed to create MCP client session: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MCP server and ensure session is closed"""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                self.logger.info("MCP client session closed")
            except Exception as e:
                self.logger.error(f"Error closing MCP client session: {e}")
            finally:
                self.session = None
                self._connected = False
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool via MCP protocol"""
        if not self.session or not self._connected:
            error_msg = "MCP client not connected. Call connect() first or use async context manager."
            self.logger.error(error_msg)
            raise MCPConnectionError(error_msg)
        
        if self.session.closed:
            error_msg = "MCP client session is closed"
            self.logger.error(error_msg)
            raise MCPConnectionError(error_msg)
        
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
                if response.status >= 400:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                
                result = await response.json()
                
                if "error" in result:
                    error_msg = result['error'].get('message', 'Unknown error')
                    self.logger.error(f"MCP tool call failed: {error_msg}")
                    raise Exception(f"MCP tool error: {error_msg}")
                
                return result.get("result", {})
                
        except aiohttp.ClientError as e:
            error_msg = f"Cannot connect to host localhost: {e}"
            self.logger.error(f"Failed to call tool {tool_name}: {error_msg}")
            raise MCPConnectionError(error_msg) from e
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
