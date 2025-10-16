#!/usr/bin/env python3
"""
Code Indexer - Concurrent code indexing with progress tracking
Phase 1 Week 5: Knowledge Graph System
"""
import logging
import os
import ast
import hashlib
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time

from agents.dev_agent.knowledge_graph.knowledge_graph_manager import KnowledgeGraphManager
from agents.dev_agent.error_handler import ErrorCode, create_error, create_success

logger = logging.getLogger(__name__)


@dataclass
class IndexingProgress:
    """Progress tracking for indexing operation"""
    total_files: int
    processed_files: int
    successful: int
    failed: int
    skipped: int
    start_time: float
    current_file: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds"""
        return time.time() - self.start_time

    @property
    def estimated_remaining_time(self) -> Optional[float]:
        """Estimate remaining time in seconds"""
        if self.processed_files == 0:
            return None
        time_per_file = self.elapsed_time / self.processed_files
        remaining_files = self.total_files - self.processed_files
        return time_per_file * remaining_files


@dataclass
class CodeFile:
    """Code file metadata"""
    path: str
    language: str
    size: int
    hash: str
    content: str
    imports: List[str]
    classes: List[str]
    functions: List[str]


class CodeIndexer:
    """Indexes code files with concurrent processing and progress tracking"""

    SUPPORTED_LANGUAGES = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
    }

    IGNORED_DIRS = {
        'node_modules', '__pycache__', '.git', '.venv', 'venv',
        'dist', 'build', '.pytest_cache', '.mypy_cache', 'coverage',
        '.next', '.nuxt', 'vendor'
    }

    MAX_FILE_SIZE = 1024 * 1024

    def __init__(
            self,
            kg_manager: KnowledgeGraphManager,
            max_workers: int = 4):
        """
        Initialize Code Indexer

        Args:
            kg_manager: Knowledge Graph Manager instance
            max_workers: Maximum concurrent workers
        """
        self.kg_manager = kg_manager
        self.max_workers = max_workers
        self.progress = None
        self.indexed_hashes: Set[str] = set()

    def _calculate_file_hash(self, content: str) -> str:
        """Calculate SHA256 hash of file content"""
        return hashlib.sha256(content.encode()).hexdigest()

    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        return self.SUPPORTED_LANGUAGES.get(ext)

    def _parse_python_file(self, content: str) -> Dict[str, List[str]]:
        """Parse Python file using AST to extract structure"""
        try:
            tree = ast.parse(content)

            imports = []
            classes = []
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)

            return {
                'imports': imports,
                'classes': classes,
                'functions': functions
            }
        except Exception as e:
            logger.debug(f"AST parsing failed: {e}")
            return {'imports': [], 'classes': [], 'functions': []}

    def _parse_javascript_file(self, content: str) -> Dict[str, List[str]]:
        """Parse JavaScript/TypeScript file (basic regex-based)"""
        import re

        imports = re.findall(r'import\s+.*?from\s+[\'"](.+?)[\'"]', content)
        classes = re.findall(r'class\s+(\w+)', content)
        functions = re.findall(r'function\s+(\w+)', content)
        functions.extend(
            re.findall(
                r'const\s+(\w+)\s*=\s*\(.*?\)\s*=>',
                content))

        return {
            'imports': imports,
            'classes': classes,
            'functions': functions
        }

    def _parse_file_structure(
            self, content: str, language: str) -> Dict[str, List[str]]:
        """Parse file structure based on language"""
        if language == 'python':
            return self._parse_python_file(content)
        elif language in ['javascript', 'typescript']:
            return self._parse_javascript_file(content)
        else:
            return {'imports': [], 'classes': [], 'functions': []}

    def _should_index_file(self, file_path: str) -> bool:
        """Check if file should be indexed"""
        path = Path(file_path)

        for ignored_dir in self.IGNORED_DIRS:
            if ignored_dir in path.parts:
                return False

        if not self._detect_language(file_path):
            return False

        if path.stat().st_size > self.MAX_FILE_SIZE:
            logger.debug(f"Skipping large file: {file_path}")
            return False

        return True

    def _index_file(self, file_path: str) -> Dict[str, Any]:
        """Index a single file"""
        try:
            if not self._should_index_file(file_path):
                return create_success({'skipped': True, 'reason': 'filtered'})

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            file_hash = self._calculate_file_hash(content)

            if file_hash in self.indexed_hashes:
                return create_success(
                    {'skipped': True, 'reason': 'already_indexed'})

            language = self._detect_language(file_path)
            structure = self._parse_file_structure(content, language)

            content_preview = content[:500] + \
                ('...' if len(content) > 500 else '')

            embedding_result = self.kg_manager.generate_embedding(content)
            if not embedding_result.get('success'):
                return embedding_result

            embedding_data = embedding_result['data']

            store_result = self.kg_manager.store_embedding(
                file_path=file_path,
                file_hash=file_hash,
                content_preview=content_preview,
                embedding=embedding_data['embedding'],
                language=language,
                tokens_count=embedding_data.get('tokens', 0),
                metadata={
                    'imports': structure['imports'],
                    'classes': structure['classes'],
                    'functions': structure['functions'],
                    'file_size': len(content)
                }
            )

            if store_result.get('success'):
                self.indexed_hashes.add(file_hash)
                return create_success({
                    'file_path': file_path,
                    'embedding_id': store_result['data']['embedding_id'],
                    'tokens': embedding_data.get('tokens', 0),
                    'cached': embedding_data.get('cached', False)
                })
            else:
                return store_result

        except Exception as e:
            logger.error(f"Failed to index {file_path}: {e}")
            return create_error(
                ErrorCode.FILE_OPERATION_FAILED,
                f"Indexing failed: {str(e)}"
            )

    def _find_code_files(self, directory: str) -> List[str]:
        """Recursively find all code files in directory"""
        code_files = []

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS]

            for file in files:
                file_path = os.path.join(root, file)
                if self._should_index_file(file_path):
                    code_files.append(file_path)

        return code_files

    def index_directory(
        self,
        directory: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Index all code files in directory with concurrent processing

        Args:
            directory: Directory to index
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with indexing results
        """
        if not os.path.isdir(directory):
            return create_error(
                ErrorCode.FILE_NOT_FOUND,
                f"Directory not found: {directory}"
            )

        logger.info(f"Finding code files in {directory}...")
        code_files = self._find_code_files(directory)

        if not code_files:
            return create_success({
                'message': 'No code files found to index',
                'total_files': 0
            })

        self.progress = IndexingProgress(
            total_files=len(code_files),
            processed_files=0,
            successful=0,
            failed=0,
            skipped=0,
            start_time=time.time()
        )

        logger.info(
            f"Indexing {
                len(code_files)} files with {
                self.max_workers} workers...")

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._index_file, file_path): file_path
                for file_path in code_files
            }

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                self.progress.current_file = file_path

                try:
                    result = future.result()
                    results.append({
                        'file': file_path,
                        'result': result
                    })

                    if result.get('success'):
                        if result.get('data', {}).get('skipped'):
                            self.progress.skipped += 1
                        else:
                            self.progress.successful += 1
                    else:
                        self.progress.failed += 1

                except Exception as e:
                    logger.error(f"Exception processing {file_path}: {e}")
                    self.progress.failed += 1
                    results.append({
                        'file': file_path,
                        'result': create_error(ErrorCode.UNKNOWN_ERROR, str(e))
                    })

                self.progress.processed_files += 1

                if progress_callback:
                    progress_callback(self.progress)

                if self.progress.processed_files % 10 == 0:
                    logger.info(
                        f"Progress: {self.progress.progress_percent:.1f}% "
                        f"({self.progress.processed_files}/{self.progress.total_files}) - "
                        f"Success: {self.progress.successful}, "
                        f"Failed: {self.progress.failed}, "
                        f"Skipped: {self.progress.skipped}"
                    )

        elapsed = self.progress.elapsed_time
        logger.info(
            f"Indexing completed in {elapsed:.2f}s - "
            f"Success: {self.progress.successful}, "
            f"Failed: {self.progress.failed}, "
            f"Skipped: {self.progress.skipped}"
        )

        return create_success({
            'total_files': self.progress.total_files,
            'successful': self.progress.successful,
            'failed': self.progress.failed,
            'skipped': self.progress.skipped,
            'elapsed_time': elapsed,
            'files_per_second': self.progress.total_files / elapsed if elapsed > 0 else 0,
            'results': results
        })

    def get_progress(self) -> Optional[IndexingProgress]:
        """Get current indexing progress"""
        return self.progress


def create_code_indexer(
        kg_manager: KnowledgeGraphManager,
        max_workers: int = 4) -> CodeIndexer:
    """Factory function to create Code Indexer"""
    return CodeIndexer(kg_manager, max_workers)
