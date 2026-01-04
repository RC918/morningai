#!/usr/bin/env python3
"""
Task Classifier - Classifies tasks into code generation types
Phase 2 Day 3-4: Task Classification for Code Generation
"""
import logging
import re
from typing import Dict, Any
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Supported task types for code generation"""
    BACKEND_UTILS_BUG_FIX = "backend_utils_bug_fix"
    FRONTEND_UI_TOKENS = "frontend_ui_tokens"
    SIMPLE_API_ENDPOINT = "simple_api_endpoint"
    TEST_GENERATION = "test_generation"
    DOCUMENTATION_UPDATE = "documentation_update"
    LINT_FIX = "lint_fix"  # Issue #3557: CI failure auto-fix support
    UNKNOWN = "unknown"


class TaskClassifier:
    """
    Classifies tasks into code generation types

    Supports 6 task types:
    1. Backend Utils Bug Fix - Simple Python utility function bugs
    2. Frontend UI Tokens - React component prop/token updates
    3. Simple API Endpoint - Basic CRUD endpoint creation
    4. Test Generation - Unit test creation for existing code
    5. Documentation Updates - README/docstring improvements
    6. Lint Fix - CI failure auto-fix for lint/style errors (Issue #3557)
    """

    def __init__(self):
        """Initialize task classifier with pattern matchers"""
        self.patterns = {
            TaskType.BACKEND_UTILS_BUG_FIX: [
                r'fix.*bug.*\.py',
                r'bug.*python.*util',
                r'error.*function.*\.py',
                r'typeerror.*\.py',
                r'valueerror.*\.py',
                r'fix.*helper.*\.py',
                r'bug.*backend.*util',
            ],
            TaskType.FRONTEND_UI_TOKENS: [
                r'update.*prop.*react',
                r'change.*token.*component',
                r'ui.*token.*\.jsx',
                r'ui.*token.*\.tsx',
                r'update.*component.*prop',
                r'change.*react.*prop',
                r'frontend.*token',
            ],
            TaskType.SIMPLE_API_ENDPOINT: [
                r'create.*api.*endpoint',
                r'add.*rest.*endpoint',
                r'new.*api.*route',
                r'crud.*endpoint',
                r'api.*get.*post.*put.*delete',
                r'create.*route.*api',
            ],
            TaskType.TEST_GENERATION: [
                r'generate.*test',
                r'create.*test.*for',
                r'add.*unit.*test',
                r'write.*test.*for',
                r'test.*coverage',
                r'add.*test.*case',
            ],
            TaskType.DOCUMENTATION_UPDATE: [
                r'update.*readme',
                r'update.*documentation',
                r'add.*docstring',
                r'improve.*documentation',
                r'update.*comment',
                r'fix.*documentation',
                r'update.*\.md',
            ],
            # Issue #3557: LINT_FIX patterns for CI failure auto-fix
            TaskType.LINT_FIX: [
                r'fix.*lint.*error',
                r'lint.*error.*fix',
                r'fix.*flake8',
                r'fix.*pylint',
                r'fix.*eslint',
                r'undefined.*name',
                r'unused.*variable',
                r'unused.*import',
                r'\bF\d{3}\b',  # Flake8 error codes (F401, F821, etc.)
                r'\bE\d{3}\b',  # PEP8 error codes (E501, E302, etc.)
                r'\bW\d{3}\b',  # PEP8 warning codes (W291, W293, etc.)
                r'fix.*typo',
                r'typo.*fix',
            ],
        }

    def classify(self, task_description: str, task_title: str = "") -> TaskType:
        """
        Classify a task based on description and title

        Args:
            task_description: Task description text
            task_title: Task title (optional)

        Returns:
            TaskType enum value
        """
        combined_text = f"{task_title} {task_description}".lower()

        for task_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    logger.info(f"Classified task as {task_type.value} (matched: {pattern})")
                    return task_type

        heuristic_type = self._classify_by_heuristics(combined_text)
        if heuristic_type != TaskType.UNKNOWN:
            logger.info(f"Classified task as {heuristic_type.value} (heuristic)")
            return heuristic_type

        logger.warning("Could not classify task, returning UNKNOWN")
        return TaskType.UNKNOWN

    def _classify_by_heuristics(self, text: str) -> TaskType:
        """
        Classify using heuristics when patterns don't match

        Args:
            text: Combined task text (lowercase)

        Returns:
            TaskType enum value
        """
        if any(word in text for word in ['bug', 'error', 'fix']) and \
           any(word in text for word in ['.py', 'python', 'backend', 'util', 'helper']):
            return TaskType.BACKEND_UTILS_BUG_FIX

        if any(word in text for word in ['react', 'component', 'jsx', 'tsx']) and \
           any(word in text for word in ['prop', 'token', 'ui', 'update', 'change']):
            return TaskType.FRONTEND_UI_TOKENS

        if any(word in text for word in ['api', 'endpoint', 'route']) and \
           any(word in text for word in ['create', 'add', 'new', 'crud', 'get', 'post']):
            return TaskType.SIMPLE_API_ENDPOINT

        if any(word in text for word in ['test', 'testing', 'coverage']) and \
           any(word in text for word in ['generate', 'create', 'add', 'write']):
            return TaskType.TEST_GENERATION

        if any(word in text for word in ['documentation', 'readme', 'docstring', 'comment', '.md']) and \
           any(word in text for word in ['update', 'improve', 'add', 'fix']):
            return TaskType.DOCUMENTATION_UPDATE

        # Issue #3557: LINT_FIX heuristics for CI failure auto-fix
        if any(word in text for word in ['lint', 'flake8', 'pylint', 'eslint', 'style']) and \
           any(word in text for word in ['fix', 'error', 'warning']):
            return TaskType.LINT_FIX

        if any(word in text for word in ['undefined', 'unused', 'typo']) and \
           any(word in text for word in ['fix', 'name', 'variable', 'import']):
            return TaskType.LINT_FIX

        return TaskType.UNKNOWN

    def get_task_metadata(self, task_type: TaskType) -> Dict[str, Any]:
        """
        Get metadata for a task type

        Args:
            task_type: TaskType enum value

        Returns:
            Dict with task metadata (complexity, estimated_time, etc.)
        """
        metadata = {
            TaskType.BACKEND_UTILS_BUG_FIX: {
                "complexity": "low",
                "estimated_time_minutes": 15,
                "requires_tests": True,
                "requires_review": True,
                "file_patterns": ["*.py"],
                "description": "Simple Python utility function bug fix"
            },
            TaskType.FRONTEND_UI_TOKENS: {
                "complexity": "low",
                "estimated_time_minutes": 10,
                "requires_tests": False,
                "requires_review": True,
                "file_patterns": ["*.jsx", "*.tsx"],
                "description": "React component prop/token update"
            },
            TaskType.SIMPLE_API_ENDPOINT: {
                "complexity": "medium",
                "estimated_time_minutes": 30,
                "requires_tests": True,
                "requires_review": True,
                "file_patterns": ["*.py", "*.js", "*.ts"],
                "description": "Basic CRUD API endpoint creation"
            },
            TaskType.TEST_GENERATION: {
                "complexity": "low",
                "estimated_time_minutes": 20,
                "requires_tests": False,
                "requires_review": True,
                "file_patterns": ["test_*.py", "*_test.py", "*.test.js", "*.test.ts"],
                "description": "Unit test generation for existing code"
            },
            TaskType.DOCUMENTATION_UPDATE: {
                "complexity": "low",
                "estimated_time_minutes": 10,
                "requires_tests": False,
                "requires_review": False,
                "file_patterns": ["*.md", "*.py", "*.js", "*.ts"],
                "description": "README/docstring improvements"
            },
            # Issue #3557: LINT_FIX metadata for CI failure auto-fix
            TaskType.LINT_FIX: {
                "complexity": "low",
                "estimated_time_minutes": 5,
                "requires_tests": False,
                "requires_review": False,
                "file_patterns": ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"],
                "description": "CI failure auto-fix for lint/style errors"
            },
            TaskType.UNKNOWN: {
                "complexity": "unknown",
                "estimated_time_minutes": 0,
                "requires_tests": False,
                "requires_review": True,
                "file_patterns": [],
                "description": "Unknown task type"
            }
        }

        return metadata.get(task_type, metadata[TaskType.UNKNOWN])

    def is_supported(self, task_type: TaskType) -> bool:
        """
        Check if a task type is supported for code generation

        Args:
            task_type: TaskType enum value

        Returns:
            bool: True if supported, False otherwise
        """
        return task_type != TaskType.UNKNOWN


def classify_task(task_description: str, task_title: str = "") -> Dict[str, Any]:
    """
    Convenience function to classify a task and get metadata

    Args:
        task_description: Task description text
        task_title: Task title (optional)

    Returns:
        Dict with task_type, metadata, and supported flag
    """
    classifier = TaskClassifier()
    task_type = classifier.classify(task_description, task_title)
    metadata = classifier.get_task_metadata(task_type)

    return {
        "task_type": task_type.value,
        "task_type_enum": task_type,
        "metadata": metadata,
        "supported": classifier.is_supported(task_type)
    }
