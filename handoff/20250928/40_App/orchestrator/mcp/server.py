#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server
Provides tools to agent sandboxes with access control and HITL gates
"""
import asyncio
import logging
from aiohttp import web
from typing import Dict, Any
import json
import sys
import os

sys.path.append('/home/ubuntu/repos/morningai')
from hitl_approval_system import HITLApprovalSystem, ApprovalPriority

class MCPServer:
    """MCP server providing tools to agents"""
    
    def __init__(self, hitl_system: HITLApprovalSystem):
        self.logger = logging.getLogger(__name__)
        self.hitl_system = hitl_system
        self.tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools"""
        from .tools.shell_tool import ShellTool
        from .tools.browser_tool import BrowserTool
        from .tools.render_tool import RenderTool
        from .tools.sentry_tool import SentryTool
        
        self.tools = {
            'shell': ShellTool(),
            'browser': BrowserTool(),
            'render': RenderTool(),
            'sentry': SentryTool()
        }
    
    async def handle_mcp_request(self, request: web.Request) -> web.Response:
        """Handle MCP JSON-RPC request"""
        try:
            data = await request.json()
            
            if data.get('jsonrpc') != '2.0':
                return web.json_response({
                    'jsonrpc': '2.0',
                    'error': {'code': -32600, 'message': 'Invalid request'},
                    'id': data.get('id')
                })
            
            method = data.get('method')
            params = data.get('params', {})
            request_id = data.get('id')
            
            if method == 'tools/call':
                result = await self._handle_tool_call(params)
                return web.json_response({
                    'jsonrpc': '2.0',
                    'result': result,
                    'id': request_id
                })
            
            return web.json_response({
                'jsonrpc': '2.0',
                'error': {'code': -32601, 'message': 'Method not found'},
                'id': request_id
            })
            
        except Exception as e:
            self.logger.error(f"MCP request failed: {e}")
            return web.json_response({
                'jsonrpc': '2.0',
                'error': {'code': -32603, 'message': str(e)},
                'id': data.get('id') if 'data' in locals() else None
            })
    
    async def _handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call with HITL gating"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if tool_name not in self.tools:
            raise Exception(f"Unknown tool: {tool_name}")
        
        tool = self.tools[tool_name]
        
        if tool.requires_approval(arguments):
            self.logger.info(f"Tool {tool_name} requires HITL approval")
            
            approval_request = await self.hitl_system.create_approval_request(
                title=f"Ops_Agent: {tool_name} operation",
                description=tool.get_approval_description(arguments),
                context=arguments,
                requester_agent="ops_agent",
                priority=ApprovalPriority.HIGH.value
            )
            
            return {
                'status': 'pending_approval',
                'approval_request_id': approval_request.request_id,
                'message': 'Operation requires human approval'
            }
        
        result = await tool.execute(arguments)
        return {'status': 'success', 'result': result}
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({'status': 'healthy'})

async def start_mcp_server(port: int = 8080):
    """Start MCP server"""
    hitl_system = HITLApprovalSystem()
    mcp_server = MCPServer(hitl_system)
    
    app = web.Application()
    app.router.add_post('/mcp', mcp_server.handle_mcp_request)
    app.router.add_get('/health', mcp_server.health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logging.info(f"MCP Server started on port {port}")
    
    await asyncio.Event().wait()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_mcp_server())
