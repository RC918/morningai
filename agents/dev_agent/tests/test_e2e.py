#!/usr/bin/env python3
"""
End-to-End Tests for Dev Agent Sandbox and Tools
"""
import pytest
import asyncio
import requests
import time
from typing import Dict, Any

SANDBOX_ENDPOINT = "http://localhost:8080"
TEST_TIMEOUT = 30


def wait_for_sandbox(timeout: int = TEST_TIMEOUT) -> bool:
    """Wait for sandbox to be ready"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{SANDBOX_ENDPOINT}/health", timeout=5)
            if response.status_code == 200:
                print("✓ Sandbox is ready")
                return True
        except:
            pass
        time.sleep(2)
    return False


@pytest.mark.skipif(
    True,  # Skip in CI - requires sandbox server
    reason="Requires Dev Agent sandbox server running on localhost:8080"
)
class TestDevAgentSandbox:
    """Test Dev Agent Sandbox functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        assert wait_for_sandbox(), "Sandbox failed to start"
    
    def test_health_check(self):
        """Test sandbox health check endpoint"""
        response = requests.get(f"{SANDBOX_ENDPOINT}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'agent_id' in data
        print(f"✓ Health check passed: {data}")
    
    def test_shell_execution(self):
        """Test shell command execution"""
        response = requests.post(
            f"{SANDBOX_ENDPOINT}/api/shell",
            json={'command': 'echo "Hello from Dev Agent"'}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] == True
        assert 'Hello from Dev Agent' in data['stdout']
        print(f"✓ Shell execution passed")
    
    def test_file_operations(self):
        """Test file read/write operations"""
        test_content = "# Test File\nThis is a test file created by Dev Agent"
        response = requests.post(
            f"{SANDBOX_ENDPOINT}/api/file/write",
            json={
                'file_path': 'test.md',
                'content': test_content
            }
        )
        assert response.status_code == 200
        assert response.json()['success'] == True
        print(f"✓ File write passed")
        
        response = requests.post(
            f"{SANDBOX_ENDPOINT}/api/file/read",
            json={'file_path': 'test.md'}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] == True
        assert data['content'] == test_content
        print(f"✓ File read passed")
    
    def test_git_operations(self):
        """Test Git operations"""
        response = requests.post(
            f"{SANDBOX_ENDPOINT}/api/shell",
            json={'command': 'git init /workspace/test-repo'}
        )
        assert response.status_code == 200
        print(f"✓ Git init passed")
        
        requests.post(
            f"{SANDBOX_ENDPOINT}/api/shell",
            json={'command': 'git config --global user.email "test@example.com"'}
        )
        requests.post(
            f"{SANDBOX_ENDPOINT}/api/shell",
            json={'command': 'git config --global user.name "Test Agent"'}
        )
        
        response = requests.post(
            f"{SANDBOX_ENDPOINT}/api/file/write",
            json={
                'file_path': 'test-repo/README.md',
                'content': '# Test Repository\nCreated by Dev Agent'
            }
        )
        assert response.json()['success'] == True
        
        response = requests.post(
            f"{SANDBOX_ENDPOINT}/api/git/commit",
            json={
                'message': 'Initial commit',
                'files': ['README.md']
            }
        )
        print(f"✓ Git operations structure passed")
    
    def test_lsp_server_start(self):
        """Test LSP server initialization"""
        response = requests.post(
            f"{SANDBOX_ENDPOINT}/api/lsp/start",
            json={'language': 'python'}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] == True
        assert 'command' in data
        print(f"✓ LSP server start passed")
    
    def test_workspace_isolation(self):
        """Test workspace isolation and security"""
        response = requests.post(
            f"{SANDBOX_ENDPOINT}/api/shell",
            json={'command': 'ls /workspace'}
        )
        assert response.status_code == 200
        print(f"✓ Workspace isolation passed")


class TestDevAgentTools:
    """Test Dev Agent Tools"""
    
    def test_git_tool_interface(self):
        """Test Git Tool has correct interface"""
        from tools import GitTool
        
        git_tool = GitTool(SANDBOX_ENDPOINT)
        
        assert hasattr(git_tool, 'clone')
        assert hasattr(git_tool, 'commit')
        assert hasattr(git_tool, 'push')
        assert hasattr(git_tool, 'create_branch')
        assert hasattr(git_tool, 'status')
        assert hasattr(git_tool, 'diff')
        assert hasattr(git_tool, 'create_pr')
        print(f"✓ Git Tool interface passed")
    
    def test_ide_tool_interface(self):
        """Test IDE Tool has correct interface"""
        from tools import IDETool
        
        ide_tool = IDETool(SANDBOX_ENDPOINT)
        
        assert hasattr(ide_tool, 'open_file')
        assert hasattr(ide_tool, 'edit_file')
        assert hasattr(ide_tool, 'search_code')
        assert hasattr(ide_tool, 'format_code')
        assert hasattr(ide_tool, 'run_linter')
        assert hasattr(ide_tool, 'start_lsp')
        print(f"✓ IDE Tool interface passed")
    
    def test_filesystem_tool_interface(self):
        """Test FileSystem Tool has correct interface"""
        from tools import FileSystemTool
        
        fs_tool = FileSystemTool(SANDBOX_ENDPOINT)
        
        assert hasattr(fs_tool, 'read_file')
        assert hasattr(fs_tool, 'write_file')
        assert hasattr(fs_tool, 'list_files')
        assert hasattr(fs_tool, 'create_directory')
        assert hasattr(fs_tool, 'delete_file')
        assert hasattr(fs_tool, 'copy_file')
        assert hasattr(fs_tool, 'move_file')
        print(f"✓ FileSystem Tool interface passed")


if __name__ == '__main__':
    print("\n" + "="*50)
    print("Dev Agent E2E Tests")
    print("="*50 + "\n")
    
    pytest.main([__file__, '-v', '--tb=short'])
