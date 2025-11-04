#!/usr/bin/env python3
"""
Shell Tool - Execute bash commands in sandbox
"""
import asyncio
import logging
from typing import Dict, Any

class ShellTool:
    """Shell command execution tool"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        self.high_risk_commands = [
            'rm -rf',
            'dd if=',
            'mkfs',
            ':(){:|:&};:',
            'chmod 777',
            'chown root'
        ]
    
    def requires_approval(self, arguments: Dict[str, Any]) -> bool:
        """Check if command requires HITL approval"""
        command = arguments.get('command', '')
        
        for pattern in self.high_risk_commands:
            if pattern in command:
                return True
        
        return False
    
    def get_approval_description(self, arguments: Dict[str, Any]) -> str:
        """Get human-readable description for approval"""
        command = arguments.get('command', '')
        return f"Execute potentially risky shell command: {command}"
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shell command"""
        command = arguments.get('command', '')
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=30.0
            )
            
            return {
                'stdout': stdout.decode('utf-8'),
                'stderr': stderr.decode('utf-8'),
                'return_code': proc.returncode
            }
            
        except asyncio.TimeoutError:
            self.logger.error(f"Command timeout: {command}")
            return {
                'error': 'Command execution timeout (30s)',
                'stdout': '',
                'stderr': '',
                'return_code': -1
            }
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return {
                'error': str(e),
                'stdout': '',
                'stderr': '',
                'return_code': -1
            }
