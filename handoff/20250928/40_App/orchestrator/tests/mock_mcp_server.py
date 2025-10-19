#!/usr/bin/env python3
"""
Mock MCP Server for testing

Provides a lightweight mock implementation of the MCP protocol
for unit testing without requiring a real MCP server.
"""
import asyncio
import json
import logging
from aiohttp import web
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MockMCPServer:
    """
    Mock MCP server for testing
    
    Simulates MCP protocol responses for common tools:
    - shell: Execute shell commands
    - browser: Browser automation
    - render: Render API calls
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_post("/mcp", self.handle_mcp_request)
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        self.call_history: list = []
        self.simulate_errors = False
        self.response_delay = 0.0
    
    async def handle_mcp_request(self, request: web.Request) -> web.Response:
        """Handle incoming MCP JSON-RPC requests"""
        try:
            data = await request.json()
            
            logger.info(f"MockMCP received request: {data.get('method')}")
            
            self.call_history.append(data)
            
            if self.simulate_errors:
                return web.json_response({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "Simulated error for testing"
                    },
                    "id": data.get("id")
                })
            
            if self.response_delay > 0:
                await asyncio.sleep(self.response_delay)
            
            method = data.get("method")
            params = data.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if method == "tools/call":
                result = await self._handle_tool_call(tool_name, arguments)
            else:
                result = {"status": "success", "message": "Mock response"}
            
            return web.json_response({
                "jsonrpc": "2.0",
                "result": result,
                "id": data.get("id")
            })
            
        except Exception as e:
            logger.error(f"MockMCP error handling request: {e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": data.get("id", None)
            }, status=500)
    
    async def _handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle specific tool calls"""
        if tool_name == "shell":
            command = arguments.get("command", "")
            return {
                "status": "success",
                "result": {
                    "stdout": f"Mock output for: {command}",
                    "stderr": "",
                    "exit_code": 0
                }
            }
        
        elif tool_name == "browser":
            url = arguments.get("url", "")
            action = arguments.get("action", "navigate")
            return {
                "status": "success",
                "result": {
                    "title": f"Mock page: {url}",
                    "action": action,
                    "url": url
                }
            }
        
        elif tool_name == "render":
            endpoint = arguments.get("endpoint", "")
            method = arguments.get("method", "GET")
            return {
                "status": "success",
                "result": {
                    "endpoint": endpoint,
                    "method": method,
                    "mock": True
                }
            }
        
        else:
            return {
                "status": "success",
                "result": {
                    "tool": tool_name,
                    "arguments": arguments,
                    "mock": True
                }
            }
    
    async def start(self):
        """Start the mock server"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"MockMCPServer started on http://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the mock server"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("MockMCPServer stopped")
    
    def reset(self):
        """Reset call history and configuration"""
        self.call_history.clear()
        self.simulate_errors = False
        self.response_delay = 0.0
    
    def get_call_count(self, tool_name: Optional[str] = None) -> int:
        """Get number of calls made (optionally filtered by tool name)"""
        if tool_name is None:
            return len(self.call_history)
        
        return sum(
            1 for call in self.call_history
            if call.get("params", {}).get("name") == tool_name
        )
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
        return False


async def create_mock_mcp_server(host: str = "localhost", port: int = 8765) -> MockMCPServer:
    """
    Factory function to create and start a mock MCP server
    
    Args:
        host: Server host (default: localhost)
        port: Server port (default: 8765)
    
    Returns:
        Running MockMCPServer instance
    
    Example:
        async with create_mock_mcp_server() as server:
            pass
    """
    server = MockMCPServer(host, port)
    await server.start()
    return server


if __name__ == "__main__":
    async def main():
        async with MockMCPServer() as server:
            print(f"Mock MCP server running on http://{server.host}:{server.port}")
            print("Press Ctrl+C to stop")
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping server...")
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
