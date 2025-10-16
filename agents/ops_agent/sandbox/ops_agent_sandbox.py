#!/usr/bin/env python3
"""
Ops Agent Sandbox - Performance monitoring and system operations
"""
import asyncio
import logging
import os
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpsAgentSandbox:
    """Operations Agent Sandbox for performance monitoring and capacity management"""
    
    def __init__(self):
        self.workspace = os.getenv('WORKSPACE_PATH', '/workspace')
        self.agent_id = os.getenv('AGENT_ID', 'ops-agent')
        
    async def execute_shell(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute shell command in sandbox"""
        try:
            working_dir = cwd or self.workspace
            logger.info(f"Executing: {command} in {working_dir}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'success': process.returncode == 0,
                'return_code': process.returncode,
                'stdout': stdout.decode('utf-8'),
                'stderr': stderr.decode('utf-8')
            }
            
        except Exception as e:
            logger.error(f"Shell execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def monitor_performance(self) -> Dict[str, Any]:
        """Monitor system performance metrics"""
        try:
            cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
            memory_cmd = "free | grep Mem | awk '{print ($3/$2) * 100.0}'"
            
            cpu_result = await self.execute_shell(cpu_cmd)
            memory_result = await self.execute_shell(memory_cmd)
            
            return {
                'success': True,
                'metrics': {
                    'cpu_usage': cpu_result.get('stdout', '0').strip(),
                    'memory_usage': memory_result.get('stdout', '0').strip(),
                    'timestamp': asyncio.get_event_loop().time()
                }
            }
        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def check_capacity(self) -> Dict[str, Any]:
        """Check system capacity"""
        try:
            disk_cmd = "df -h / | tail -1 | awk '{print $5}'"
            disk_result = await self.execute_shell(disk_cmd)
            
            return {
                'success': True,
                'capacity': {
                    'disk_usage': disk_result.get('stdout', '0%').strip(),
                    'status': 'healthy'
                }
            }
        except Exception as e:
            logger.error(f"Capacity check failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'agent_id': self.agent_id,
            'workspace': self.workspace,
            'type': 'ops_agent'
        }

if __name__ == '__main__':
    sandbox = OpsAgentSandbox()
    logger.info(f"Ops Agent Sandbox initialized for {sandbox.agent_id}")
    logger.info(f"Workspace: {sandbox.workspace}")
