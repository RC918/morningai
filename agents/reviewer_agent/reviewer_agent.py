#!/usr/bin/env python3
"""
Reviewer Agent v1 - Automated code review
Phase 2 Day 5-7: Reviewer Agent

Performs:
1. Lint checks (flake8, eslint)
2. Accessibility checks (a11y patterns)
3. Security checks (dangerous patterns)
4. Generates review comments with suggestions
"""
import logging
import re
import subprocess
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReviewComment:
    """A single review comment"""
    file_path: str
    line_number: Optional[int]
    severity: str  # "error", "warning", "info"
    category: str  # "lint", "security", "accessibility", "style"
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class ReviewResult:
    """Result of code review"""
    passed: bool
    comments: List[ReviewComment] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    adoption_rate: float = 0.0


class ReviewerAgent:
    """
    Automated Code Reviewer v1
    
    Features:
    - Lint checking (Python: flake8, JS/TS: eslint)
    - Security pattern detection
    - Accessibility checks for React components
    - Actionable suggestions for improvements
    """
    
    SECURITY_PATTERNS = {
        'eval_usage': {
            'pattern': r'\beval\s*\(',
            'severity': 'error',
            'message': 'Avoid using eval() - security risk',
            'suggestion': 'Use safer alternatives like json.loads() or ast.literal_eval()'
        },
        'exec_usage': {
            'pattern': r'\bexec\s*\(',
            'severity': 'error',
            'message': 'Avoid using exec() - security risk',
            'suggestion': 'Refactor to use explicit function calls'
        },
        'os_system': {
            'pattern': r'\bos\.system\s*\(',
            'severity': 'error',
            'message': 'Avoid os.system() - use subprocess with shell=False',
            'suggestion': 'Use subprocess.run() with explicit arguments'
        },
        'sql_injection': {
            'pattern': r'(execute|cursor\.execute)\s*\(\s*["\'].*%s.*["\']',
            'severity': 'error',
            'message': 'Potential SQL injection vulnerability',
            'suggestion': 'Use parameterized queries with ? or %s placeholders'
        },
        'hardcoded_secret': {
            'pattern': r'(password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']',
            'severity': 'error',
            'message': 'Potential hardcoded secret detected',
            'suggestion': 'Use environment variables or secret management'
        },
        'pickle_loads': {
            'pattern': r'\bpickle\.loads\s*\(',
            'severity': 'warning',
            'message': 'pickle.loads() can execute arbitrary code',
            'suggestion': 'Use json.loads() or validate input source'
        },
    }
    
    A11Y_PATTERNS = {
        'missing_alt': {
            'pattern': r'<img[^>]*(?!alt=)[^>]*>',
            'severity': 'error',
            'message': 'Image missing alt attribute',
            'suggestion': 'Add alt="" for decorative images or descriptive alt text'
        },
        'onclick_without_role': {
            'pattern': r'<div[^>]*onClick[^>]*(?!role=)[^>]*>',
            'severity': 'warning',
            'message': 'onClick on div without role attribute',
            'suggestion': 'Add role="button" and onKeyPress handler for keyboard accessibility'
        },
        'missing_label': {
            'pattern': r'<input[^>]*(?!aria-label|aria-labelledby)[^>]*>',
            'severity': 'warning',
            'message': 'Input missing label or aria-label',
            'suggestion': 'Add <label> or aria-label attribute'
        },
        'button_without_type': {
            'pattern': r'<button[^>]*(?!type=)[^>]*>',
            'severity': 'info',
            'message': 'Button missing type attribute',
            'suggestion': 'Add type="button" or type="submit"'
        },
    }
    
    def __init__(self, repo_root: str = "."):
        """
        Initialize Reviewer Agent
        
        Args:
            repo_root: Root directory of repository
        """
        self.repo_root = Path(repo_root).resolve()
        logger.info(f"ReviewerAgent initialized for: {self.repo_root}")
    
    def review_files(self, file_paths: List[str]) -> ReviewResult:
        """
        Review multiple files
        
        Args:
            file_paths: List of file paths to review
        
        Returns:
            ReviewResult with all comments
        """
        logger.info(f"Reviewing {len(file_paths)} files...")
        
        all_comments = []
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
            
            ext = Path(file_path).suffix
            
            if ext == '.py':
                all_comments.extend(self._review_python_file(file_path))
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                all_comments.extend(self._review_javascript_file(file_path))
            else:
                logger.info(f"Skipping unsupported file type: {file_path}")
        
        summary = self._calculate_summary(all_comments)
        
        error_count = summary.get('error', 0)
        passed = error_count == 0
        
        result = ReviewResult(
            passed=passed,
            comments=all_comments,
            summary=summary
        )
        
        logger.info(f"Review complete: {len(all_comments)} comments, passed={passed}")
        
        return result
    
    def _review_python_file(self, file_path: str) -> List[ReviewComment]:
        """Review Python file"""
        comments = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return comments
        
        comments.extend(self._run_flake8(file_path))
        
        comments.extend(self._check_security_patterns(file_path, content))
        
        comments.extend(self._check_python_best_practices(file_path, content))
        
        return comments
    
    def _review_javascript_file(self, file_path: str) -> List[ReviewComment]:
        """Review JavaScript/TypeScript file"""
        comments = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return comments
        
        comments.extend(self._run_eslint(file_path))
        
        if file_path.endswith(('.jsx', '.tsx')):
            comments.extend(self._check_accessibility_patterns(file_path, content))
        
        comments.extend(self._check_security_patterns(file_path, content))
        
        return comments
    
    def _run_flake8(self, file_path: str) -> List[ReviewComment]:
        """Run flake8 lint checker"""
        comments = []
        
        try:
            result = subprocess.run(
                ['flake8', file_path, '--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    
                    match = re.match(r'([^:]+):(\d+):(\d+):\s*(\w+)\s+(.+)', line)
                    if match:
                        path, line_num, col, code, message = match.groups()
                        
                        severity = 'error' if code.startswith('E') else 'warning'
                        
                        comments.append(ReviewComment(
                            file_path=file_path,
                            line_number=int(line_num),
                            severity=severity,
                            category='lint',
                            message=f"{code}: {message}",
                            suggestion=self._get_flake8_suggestion(code)
                        ))
        
        except subprocess.TimeoutExpired:
            logger.warning(f"flake8 timeout for {file_path}")
        except FileNotFoundError:
            logger.warning("flake8 not found, skipping lint checks")
        except Exception as e:
            logger.warning(f"flake8 failed for {file_path}: {e}")
        
        return comments
    
    def _run_eslint(self, file_path: str) -> List[ReviewComment]:
        """Run eslint checker"""
        comments = []
        
        try:
            result = subprocess.run(
                ['npx', 'eslint', file_path, '--format=json'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.repo_root
            )
            
            import json
            try:
                output = json.loads(result.stdout)
                
                for file_result in output:
                    for message in file_result.get('messages', []):
                        severity = 'error' if message.get('severity') == 2 else 'warning'
                        
                        comments.append(ReviewComment(
                            file_path=file_path,
                            line_number=message.get('line'),
                            severity=severity,
                            category='lint',
                            message=f"{message.get('ruleId', 'unknown')}: {message.get('message', '')}",
                            suggestion=self._get_eslint_suggestion(message.get('ruleId', ''))
                        ))
            
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse eslint output for {file_path}")
        
        except subprocess.TimeoutExpired:
            logger.warning(f"eslint timeout for {file_path}")
        except FileNotFoundError:
            logger.info("eslint not found, skipping lint checks")
        except Exception as e:
            logger.warning(f"eslint failed for {file_path}: {e}")
        
        return comments
    
    def _check_security_patterns(self, file_path: str, content: str) -> List[ReviewComment]:
        """Check for security vulnerabilities"""
        comments = []
        
        lines = content.split('\n')
        
        for pattern_name, pattern_info in self.SECURITY_PATTERNS.items():
            pattern = pattern_info['pattern']
            
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    comments.append(ReviewComment(
                        file_path=file_path,
                        line_number=line_num,
                        severity=pattern_info['severity'],
                        category='security',
                        message=pattern_info['message'],
                        suggestion=pattern_info['suggestion'],
                        code_snippet=line.strip()
                    ))
        
        return comments
    
    def _check_accessibility_patterns(self, file_path: str, content: str) -> List[ReviewComment]:
        """Check for accessibility issues in React components"""
        comments = []
        
        lines = content.split('\n')
        
        for pattern_name, pattern_info in self.A11Y_PATTERNS.items():
            pattern = pattern_info['pattern']
            
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    comments.append(ReviewComment(
                        file_path=file_path,
                        line_number=line_num,
                        severity=pattern_info['severity'],
                        category='accessibility',
                        message=pattern_info['message'],
                        suggestion=pattern_info['suggestion'],
                        code_snippet=line.strip()
                    ))
        
        return comments
    
    def _check_python_best_practices(self, file_path: str, content: str) -> List[ReviewComment]:
        """Check Python best practices"""
        comments = []
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if re.search(r'\bprint\s*\(', line) and not line.strip().startswith('#'):
                comments.append(ReviewComment(
                    file_path=file_path,
                    line_number=line_num,
                    severity='info',
                    category='style',
                    message='Consider using logging instead of print()',
                    suggestion='Use logger.info(), logger.debug(), etc.'
                ))
        
        for line_num, line in enumerate(lines, 1):
            if re.search(r'except\s*:', line):
                comments.append(ReviewComment(
                    file_path=file_path,
                    line_number=line_num,
                    severity='warning',
                    category='style',
                    message='Bare except clause catches all exceptions',
                    suggestion='Catch specific exceptions: except ValueError:'
                ))
        
        return comments
    
    def _get_flake8_suggestion(self, code: str) -> Optional[str]:
        """Get suggestion for flake8 error code"""
        suggestions = {
            'E501': 'Break long lines at logical points (operators, commas)',
            'E302': 'Add 2 blank lines before function/class definition',
            'E303': 'Remove extra blank lines',
            'E231': 'Add space after comma',
            'W291': 'Remove trailing whitespace',
            'F401': 'Remove unused import or use it',
            'F841': 'Remove unused variable or use it',
        }
        
        return suggestions.get(code)
    
    def _get_eslint_suggestion(self, rule_id: str) -> Optional[str]:
        """Get suggestion for eslint rule"""
        suggestions = {
            'no-unused-vars': 'Remove unused variable or prefix with underscore',
            'no-console': 'Remove console.log or use proper logging',
            'react/prop-types': 'Add PropTypes validation or use TypeScript',
            'react-hooks/exhaustive-deps': 'Add missing dependency to useEffect',
        }
        
        return suggestions.get(rule_id)
    
    def _calculate_summary(self, comments: List[ReviewComment]) -> Dict[str, int]:
        """Calculate summary statistics"""
        summary = {
            'total': len(comments),
            'error': 0,
            'warning': 0,
            'info': 0,
            'lint': 0,
            'security': 0,
            'accessibility': 0,
            'style': 0,
        }
        
        for comment in comments:
            summary[comment.severity] += 1
            summary[comment.category] += 1
        
        return summary
    
    def format_review_comments(self, result: ReviewResult) -> str:
        """
        Format review comments for display
        
        Args:
            result: ReviewResult object
        
        Returns:
            Formatted string with all comments
        """
        output = []
        
        output.append("=" * 80)
        output.append("CODE REVIEW RESULTS")
        output.append("=" * 80)
        output.append(f"Status: {'✓ PASSED' if result.passed else '✗ FAILED'}")
        output.append(f"Total Comments: {result.summary['total']}")
        output.append(f"  Errors: {result.summary['error']}")
        output.append(f"  Warnings: {result.summary['warning']}")
        output.append(f"  Info: {result.summary['info']}")
        output.append("")
        output.append(f"By Category:")
        output.append(f"  Lint: {result.summary['lint']}")
        output.append(f"  Security: {result.summary['security']}")
        output.append(f"  Accessibility: {result.summary['accessibility']}")
        output.append(f"  Style: {result.summary['style']}")
        output.append("=" * 80)
        
        if result.comments:
            output.append("")
            output.append("DETAILED COMMENTS:")
            output.append("-" * 80)
            
            by_file = {}
            for comment in result.comments:
                if comment.file_path not in by_file:
                    by_file[comment.file_path] = []
                by_file[comment.file_path].append(comment)
            
            for file_path, comments in by_file.items():
                output.append(f"\n{file_path}:")
                
                for comment in comments:
                    severity_icon = {
                        'error': '✗',
                        'warning': '⚠',
                        'info': 'ℹ'
                    }.get(comment.severity, '•')
                    
                    line_info = f":{comment.line_number}" if comment.line_number else ""
                    output.append(f"  {severity_icon} [{comment.category.upper()}]{line_info}")
                    output.append(f"    {comment.message}")
                    
                    if comment.suggestion:
                        output.append(f"    💡 Suggestion: {comment.suggestion}")
                    
                    if comment.code_snippet:
                        output.append(f"    Code: {comment.code_snippet}")
                    
                    output.append("")
        
        output.append("=" * 80)
        
        return "\n".join(output)


def review_code(file_paths: List[str], repo_root: str = ".") -> ReviewResult:
    """
    Convenience function to review code files
    
    Args:
        file_paths: List of file paths to review
        repo_root: Root directory of repository
    
    Returns:
        ReviewResult object
    """
    agent = ReviewerAgent(repo_root=repo_root)
    return agent.review_files(file_paths)
