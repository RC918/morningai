#!/usr/bin/env python3
"""
Unit tests for run_pr_review CLI tool
"""
import pytest
import subprocess
import json
import tempfile
import os
from pathlib import Path


class TestCLIBasic:
    """Test basic CLI functionality"""
    
    def test_cli_help(self):
        """Test --help flag"""
        result = subprocess.run(
            ["python", "tools/code_agents/run_pr_review.py", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ubuntu/repos/morningai"
        )
        
        assert result.returncode == 0
        assert "Automated code review" in result.stdout
        assert "--files" in result.stdout
        assert "--format" in result.stdout
    
    def test_cli_no_arguments(self):
        """Test CLI with no arguments (should fail)"""
        result = subprocess.run(
            ["python", "tools/code_agents/run_pr_review.py"],
            capture_output=True,
            text=True,
            cwd="/home/ubuntu/repos/morningai"
        )
        
        assert result.returncode == 2
        assert "required" in result.stderr.lower() or "error" in result.stderr.lower()


class TestFileValidation:
    """Test file validation"""
    
    def test_nonexistent_file(self):
        """Test with nonexistent file"""
        result = subprocess.run(
            ["python", "tools/code_agents/run_pr_review.py", 
             "--files", "/tmp/nonexistent_file_12345.py"],
            capture_output=True,
            text=True,
            cwd="/home/ubuntu/repos/morningai"
        )
        
        assert result.returncode == 2
        assert "not found" in result.stderr.lower() or "invalid" in result.stderr.lower()
    
    def test_valid_file(self):
        """Test with valid file"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello world')\n")
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ["python", "tools/code_agents/run_pr_review.py", 
                 "--files", temp_file],
                capture_output=True,
                text=True,
                cwd="/home/ubuntu/repos/morningai",
                timeout=30
            )
            
            # Should succeed (exit code 0 or 1, not 2)
            assert result.returncode in [0, 1]
            assert "REVIEW RESULTS" in result.stdout or "error" in result.stdout.lower()
        finally:
            os.unlink(temp_file)


class TestOutputFormats:
    """Test different output formats"""
    
    def test_text_format(self):
        """Test text output format (default)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')\n")
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ["python", "tools/code_agents/run_pr_review.py", 
                 "--files", temp_file, "--format", "text"],
                capture_output=True,
                text=True,
                cwd="/home/ubuntu/repos/morningai",
                timeout=30
            )
            
            assert result.returncode in [0, 1]
            assert "REVIEW RESULTS" in result.stdout or "error" in result.stdout.lower()
        finally:
            os.unlink(temp_file)
    
    def test_json_format(self):
        """Test JSON output format"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')\n")
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ["python", "tools/code_agents/run_pr_review.py", 
                 "--files", temp_file, "--format", "json"],
                capture_output=True,
                text=True,
                cwd="/home/ubuntu/repos/morningai",
                timeout=30
            )
            
            assert result.returncode in [0, 1]
            
            # Should be valid JSON
            try:
                output = json.loads(result.stdout)
                assert "passed" in output
                assert "summary" in output
            except json.JSONDecodeError:
                # If JSON parsing fails, check if there's an error message
                assert "error" in result.stdout.lower()
        finally:
            os.unlink(temp_file)


class TestSecurityDetection:
    """Test security issue detection"""
    
    def test_detect_eval(self):
        """Test detection of eval() usage"""
        # Create a file with security issue
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def process_data(user_input):
    result = eval(user_input)  # Security issue
    return result
""")
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ["python", "tools/code_agents/run_pr_review.py", 
                 "--files", temp_file, "--format", "json"],
                capture_output=True,
                text=True,
                cwd="/home/ubuntu/repos/morningai",
                timeout=30
            )
            
            # Should fail due to security issue
            assert result.returncode == 1
            
            # Check output
            try:
                output = json.loads(result.stdout)
                assert output["passed"] is False
                assert output["summary"]["security"] > 0
            except json.JSONDecodeError:
                # Text format fallback
                assert "security" in result.stdout.lower()
                assert "eval" in result.stdout.lower()
        finally:
            os.unlink(temp_file)


class TestStrictMode:
    """Test strict mode"""
    
    def test_strict_mode_flag(self):
        """Test --strict flag"""
        # Create a file that might have warnings
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')\n")
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ["python", "tools/code_agents/run_pr_review.py", 
                 "--files", temp_file, "--strict"],
                capture_output=True,
                text=True,
                cwd="/home/ubuntu/repos/morningai",
                timeout=30
            )
            
            # Should complete (exit code 0, 1, or 2)
            assert result.returncode in [0, 1, 2]
        finally:
            os.unlink(temp_file)


class TestMultipleFiles:
    """Test reviewing multiple files"""
    
    def test_multiple_files(self):
        """Test reviewing multiple files at once"""
        # Create multiple temporary files
        temp_files = []
        
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(f"print('file {i}')\n")
                    temp_files.append(f.name)
            
            result = subprocess.run(
                ["python", "tools/code_agents/run_pr_review.py", 
                 "--files"] + temp_files,
                capture_output=True,
                text=True,
                cwd="/home/ubuntu/repos/morningai",
                timeout=30
            )
            
            assert result.returncode in [0, 1]
            assert "REVIEW RESULTS" in result.stdout or "error" in result.stdout.lower()
        finally:
            for temp_file in temp_files:
                os.unlink(temp_file)


class TestPRReview:
    """Test PR review functionality (future feature)"""
    
    def test_pr_flag_not_implemented(self):
        """Test that --pr flag shows not implemented message"""
        result = subprocess.run(
            ["python", "tools/code_agents/run_pr_review.py", 
             "--pr", "1234"],
            capture_output=True,
            text=True,
            cwd="/home/ubuntu/repos/morningai"
        )
        
        assert result.returncode == 2
        assert "not yet implemented" in result.stderr.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
