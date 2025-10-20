#!/usr/bin/env python3
"""
FileSystem Tool - Enhanced file operations for Dev Agent
Provides comprehensive file system operations with path whitelist validation
Phase 1 Week 4: Added path security validation
"""
import logging
import os
from typing import Dict, Any, Optional, Set
import requests

from error_handler import ErrorCode, create_error, create_success

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileSystemTool:
    """File system operations tool with path whitelist"""

    DEFAULT_WHITELIST = {
        '/workspace',
        '/tmp',
        '/var/tmp',
        '.',
        '..'
    }

    FORBIDDEN_PATHS = {
        '/etc',
        '/root',
        '/sys',
        '/proc',
        '/boot',
        '/dev'
    }

    def __init__(
        self,
        sandbox_endpoint: str,
        path_whitelist: Optional[Set[str]] = None
    ):
        self.sandbox_endpoint = sandbox_endpoint
        self.path_whitelist = path_whitelist or self.DEFAULT_WHITELIST

    def _validate_path(self, file_path: str) -> Dict[str, Any]:
        """Validate path against whitelist and forbidden paths"""
        abs_path = os.path.abspath(file_path)

        for forbidden in self.FORBIDDEN_PATHS:
            if abs_path.startswith(forbidden):
                return create_error(
                    ErrorCode.PATH_NOT_WHITELISTED,
                    f"Access to {forbidden} is forbidden",
                    hint="File operations are restricted to /workspace and /tmp directories",
                    path=file_path
                )

        is_whitelisted = False
        for allowed in self.path_whitelist:
            allowed_abs = os.path.abspath(allowed)
            if abs_path.startswith(allowed_abs) or file_path.startswith(allowed):
                is_whitelisted = True
                break

        if not is_whitelisted:
            return create_error(
                ErrorCode.PATH_NOT_WHITELISTED,
                f"Path {file_path} not in whitelist",
                hint="Add path to whitelist or use /workspace directory",
                path=file_path,
                whitelist=list(self.path_whitelist)
            )

        return create_success()

    async def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read file contents with path validation

        Args:
            file_path: Path to file relative to workspace

        Returns:
            Dict with success status and file content
        """
        validation = self._validate_path(file_path)
        if not validation['success']:
            return validation

        try:
            response = requests.post(
                f"{self.sandbox_endpoint}/api/file/read",
                json={'file_path': file_path}
            )
            result = response.json()
            if result.get('success'):
                return create_success(content=result.get('content', ''))
            else:
                return create_error(
                    ErrorCode.FILE_NOT_FOUND,
                    result.get('error', 'Failed to read file'),
                    path=file_path
                )
        except Exception as e:
            logger.error(f"Read file failed: {e}")
            return create_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"Read operation failed: {str(e)}",
                path=file_path
            )

    async def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to file with path validation

        Args:
            file_path: Path to file relative to workspace
            content: File content to write

        Returns:
            Dict with success status
        """
        validation = self._validate_path(file_path)
        if not validation['success']:
            return validation

        try:
            response = requests.post(
                f"{self.sandbox_endpoint}/api/file/write",
                json={
                    'file_path': file_path,
                    'content': content
                }
            )
            result = response.json()
            if result.get('success'):
                return create_success(path=file_path)
            else:
                return create_error(
                    ErrorCode.PERMISSION_DENIED,
                    result.get('error', 'Failed to write file'),
                    path=file_path
                )
        except Exception as e:
            logger.error(f"Write file failed: {e}")
            return create_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"Write operation failed: {str(e)}",
                path=file_path
            )

    async def list_files(self, directory: str = '.', pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        List files in directory

        Args:
            directory: Directory path
            pattern: Optional glob pattern to filter files

        Returns:
            Dict with success status and file list
        """
        try:
            if pattern:
                command = f"find {directory} -name '{pattern}'"
            else:
                command = f"ls -la {directory}"

            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"List files failed: {e}")
            return {'success': False, 'error': str(e)}

    async def create_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Create directory

        Args:
            directory_path: Path to directory to create

        Returns:
            Dict with success status
        """
        try:
            command = f"mkdir -p {directory_path}"

            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Create directory failed: {e}")
            return {'success': False, 'error': str(e)}

    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete file

        Args:
            file_path: Path to file to delete

        Returns:
            Dict with success status
        """
        try:
            command = f"rm -f {file_path}"

            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Delete file failed: {e}")
            return {'success': False, 'error': str(e)}

    async def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy file

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            Dict with success status
        """
        try:
            command = f"cp {source} {destination}"

            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Copy file failed: {e}")
            return {'success': False, 'error': str(e)}

    async def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Move/rename file

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            Dict with success status
        """
        try:
            command = f"mv {source} {destination}"

            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Move file failed: {e}")
            return {'success': False, 'error': str(e)}

    async def search_files(self, query: str, directory: str = '.') -> Dict[str, Any]:
        """
        Search for text in files

        Args:
            query: Search query
            directory: Directory to search in

        Returns:
            Dict with success status and search results
        """
        try:
            command = f"grep -rn '{query}' {directory}"

            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Search files failed: {e}")
            return {'success': False, 'error': str(e)}

    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get file information

        Args:
            file_path: Path to file

        Returns:
            Dict with success status and file info
        """
        try:
            command = f"stat {file_path}"

            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Get file info failed: {e}")
            return {'success': False, 'error': str(e)}


def get_filesystem_tool(sandbox_endpoint: str) -> FileSystemTool:
    """Factory function to create FileSystemTool instance"""
    return FileSystemTool(sandbox_endpoint)
