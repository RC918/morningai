#!/usr/bin/env python3
"""
IDE Tool - VSCode Server integration for Dev Agent
Provides IDE capabilities through code-server API
"""
import logging
from typing import Dict, Any, Optional
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IDETool:
    """IDE tool providing VSCode Server integration"""
    
    def __init__(self, sandbox_endpoint: str, vscode_endpoint: Optional[str] = None):
        self.sandbox_endpoint = sandbox_endpoint
        self.vscode_endpoint = vscode_endpoint or sandbox_endpoint.replace('8080', '8443')
        
    async def open_file(self, file_path: str) -> Dict[str, Any]:
        """
        Open a file in the IDE
        
        Args:
            file_path: Path to file relative to workspace
            
        Returns:
            Dict with success status and file content
        """
        try:
            response = requests.post(
                f"{self.sandbox_endpoint}/api/file/read",
                json={'file_path': file_path}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Open file failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def edit_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Edit a file in the IDE
        
        Args:
            file_path: Path to file relative to workspace
            content: New file content
            
        Returns:
            Dict with success status
        """
        try:
            response = requests.post(
                f"{self.sandbox_endpoint}/api/file/write",
                json={
                    'file_path': file_path,
                    'content': content
                }
            )
            return response.json()
        except Exception as e:
            logger.error(f"Edit file failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def search_code(self, query: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for code in workspace
        
        Args:
            query: Search query
            file_pattern: Optional file pattern to filter (e.g., '*.py')
            
        Returns:
            Dict with success status and search results
        """
        try:
            file_flag = f" --include='{file_pattern}'" if file_pattern else ""
            command = f"grep -rn '{query}' .{file_flag}"
            
            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Search code failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def format_code(self, file_path: str, language: str = 'python') -> Dict[str, Any]:
        """
        Format code using language-specific formatter
        
        Args:
            file_path: Path to file to format
            language: Programming language (python, typescript, etc.)
            
        Returns:
            Dict with success status
        """
        try:
            if language == 'python':
                command = f"black {file_path}"
            elif language in ['typescript', 'javascript']:
                command = f"prettier --write {file_path}"
            else:
                return {'success': False, 'error': f'Unsupported language: {language}'}
            
            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Format code failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_linter(self, file_path: str, language: str = 'python') -> Dict[str, Any]:
        """
        Run linter on code
        
        Args:
            file_path: Path to file to lint
            language: Programming language
            
        Returns:
            Dict with success status and lint results
        """
        try:
            if language == 'python':
                command = f"ruff check {file_path}"
            elif language in ['typescript', 'javascript']:
                command = f"eslint {file_path}"
            else:
                return {'success': False, 'error': f'Unsupported language: {language}'}
            
            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Run linter failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def start_lsp(self, language: str) -> Dict[str, Any]:
        """
        Start Language Server Protocol server
        
        Args:
            language: Programming language (python, typescript, etc.)
            
        Returns:
            Dict with success status and LSP server info
        """
        try:
            response = requests.post(
                f"{self.sandbox_endpoint}/api/lsp/start",
                json={'language': language}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Start LSP failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_file_tree(self, path: str = '.') -> Dict[str, Any]:
        """
        Get file tree structure
        
        Args:
            path: Root path (default: workspace root)
            
        Returns:
            Dict with success status and file tree
        """
        try:
            command = f"tree -L 3 -I 'node_modules|__pycache__|.git' {path}"
            
            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Get file tree failed: {e}")
            return {'success': False, 'error': str(e)}


def get_ide_tool(sandbox_endpoint: str) -> IDETool:
    """Factory function to create IDETool instance"""
    return IDETool(sandbox_endpoint)
