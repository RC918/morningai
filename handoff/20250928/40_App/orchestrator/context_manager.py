#!/usr/bin/env python3
"""
Context Manager - Code Context Extraction for LLM Planner
Phase 1 (B) Supplemental Implementation

Extracts relevant code context for LLM-based planning:
- Top-K file selection using keyword overlap + similarity
- Python signature extraction using AST
- Token budget enforcement (<2000 tokens)
"""
import ast
import difflib
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

from common.config.settings import settings
from resource_telemetry import (
    log_context_file_scan,
    log_context_file_select,
    log_context_token_budget,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_tiktoken_encoder = None
_tiktoken_available = False

def _init_tiktoken():
    """Initialize tiktoken encoder if enabled and available"""
    global _tiktoken_encoder, _tiktoken_available
    
    if _tiktoken_available or _tiktoken_encoder is not None:
        return
    
    try:
        use_tiktoken = settings.use_tiktoken_estimator
        if not use_tiktoken:
            return
        
        import tiktoken
        _tiktoken_encoder = tiktoken.encoding_for_model("gpt-4")
        _tiktoken_available = True
        logger.info("[ContextManager] Tiktoken estimator initialized successfully")
    except ImportError:
        logger.warning("[ContextManager] Tiktoken not available, using heuristic estimation")
    except Exception as e:
        logger.warning(f"[ContextManager] Failed to initialize tiktoken: {e}, using heuristic")

def _estimate_tokens(text: str) -> int:
    """
    Estimate token count for text using tiktoken or heuristic fallback
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    _init_tiktoken()
    
    if _tiktoken_available and _tiktoken_encoder:
        try:
            return len(_tiktoken_encoder.encode(text))
        except Exception as e:
            logger.warning(f"[ContextManager] Tiktoken encoding failed: {e}, using heuristic")
    
    return max(1, len(text) // 4)

STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
    'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
}

EXCLUDED_DIRS = {
    '.git', '.venv', 'node_modules', 'build', 'dist', '.next',
    '__pycache__', '.pytest_cache', 'venv', 'env', '.tox'
}


def discover_repo_root() -> Optional[str]:
    """
    Discover repository root path with production-safe fallback chain.
    
    Fallback order:
    1. MORNINGAI_REPO_PATH environment variable (production/staging)
    2. REPO_ROOT_PATH environment variable (testing/CI)
    3. Git repository root detection (git rev-parse --show-toplevel)
    4. Project root via Path(__file__) traversal
    
    Returns:
        Absolute path to repository root, or None if not found
    """
    repo_path = settings.morningai_repo_path
    if repo_path and os.path.exists(repo_path):
        logger.info(f"[ContextManager] Using MORNINGAI_REPO_PATH: {repo_path}")
        return os.path.abspath(repo_path)
    
    repo_path = settings.repo_root_path
    if repo_path and os.path.exists(repo_path):
        logger.info(f"[ContextManager] Using REPO_ROOT_PATH: {repo_path}")
        return os.path.abspath(repo_path)
    
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        repo_path = result.stdout.strip()
        if repo_path and os.path.exists(repo_path):
            logger.info(f"[ContextManager] Detected git repo root: {repo_path}")
            return os.path.abspath(repo_path)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    current = Path(__file__).resolve()
    markers = ['.git', 'config', 'handoff', 'agents', 'pyproject.toml', 'setup.py']
    
    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in markers):
            logger.info(f"[ContextManager] Detected project root via markers: {parent}")
            return str(parent)
    
    return None


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into keywords (lowercase, filter stopwords)

    Args:
        text: Input text

    Returns:
        List of keywords
    """
    words = re.findall(r'\w+', text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def calculate_file_score(goal_keywords: List[str], file_path: str, file_content: str) -> float:
    """
    Calculate relevance score for a file

    Args:
        goal_keywords: Keywords from goal
        file_path: Path to file
        file_content: File content (first 2000 chars)

    Returns:
        Combined score (0.0-1.0)
    """
    file_text = f"{file_path} {file_content[:2000]}".lower()
    file_keywords = tokenize_text(file_text)

    keyword_matches = sum(1 for kw in goal_keywords if kw in file_keywords)
    keyword_score = keyword_matches / max(len(goal_keywords), 1)

    goal_text = ' '.join(goal_keywords)
    similarity = difflib.SequenceMatcher(None, goal_text, file_text[:2000]).ratio()

    combined_score = 0.7 * keyword_score + 0.3 * similarity
    return combined_score


def extract_python_signatures(file_path: str, file_content: str) -> List[str]:
    """
    Extract function and class signatures from Python file using AST

    Args:
        file_path: Path to file
        file_content: File content

    Returns:
        List of signatures
    """
    signatures = []

    try:
        tree = ast.parse(file_content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                args = ', '.join(arg.arg for arg in node.args.args)
                signatures.append(f"def {node.name}({args})")
            elif isinstance(node, ast.ClassDef):
                signatures.append(f"class {node.name}")
    except SyntaxError as e:
        logger.warning(f"Failed to parse {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Error extracting signatures from {file_path}: {e}")

    return signatures


def find_relevant_files(
    repo_path: str,
    goal: str,
    max_files: int = 5,
    max_scan: int = 1000
) -> List[Tuple[str, float]]:
    """
    Find top-K relevant Python files

    Args:
        repo_path: Path to repository
        goal: User's goal
        max_files: Maximum files to return
        max_scan: Maximum files to scan

    Returns:
        List of (file_path, score) tuples
    """
    goal_keywords = tokenize_text(goal)

    if not goal_keywords:
        logger.warning("No keywords extracted from goal")
        return []

    scored_files = []
    scanned = 0

    search_dirs = ['agents', 'common', 'handoff', 'tools']

    for search_dir in search_dirs:
        dir_path = os.path.join(repo_path, search_dir)
        if not os.path.exists(dir_path):
            continue

        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

            for file in files:
                if not file.endswith('.py'):
                    continue

                if scanned >= max_scan:
                    break

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(50000)

                    score = calculate_file_score(goal_keywords, rel_path, content)
                    scored_files.append((rel_path, score, content))
                    scanned += 1

                except Exception as e:
                    logger.warning(f"Error reading {file_path}: {e}")

            if scanned >= max_scan:
                break

    scored_files.sort(key=lambda x: x[1], reverse=True)

    log_context_file_scan(
        goal=goal,
        files_scanned=scanned,
        search_dirs=search_dirs,
        max_scan=max_scan,
    )

    selected = [(path, score) for path, score, _ in scored_files[:max_files]]

    log_context_file_select(
        selected_files=selected,
        max_files=max_files,
    )

    return selected


def build_context_string(
    repo_path: str,
    relevant_files: List[Tuple[str, float]],
    max_tokens: int = 2000
) -> str:
    """
    Build context string from relevant files

    Args:
        repo_path: Path to repository
        relevant_files: List of (file_path, score) tuples
        max_tokens: Maximum tokens (approximate)

    Returns:
        Context string
    """
    context_parts = []
    estimated_tokens = 0
    included_files = []
    excluded_files = []
    budget_exceeded = False

    for file_path, score in relevant_files:
        full_path = os.path.join(repo_path, file_path)

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            signatures = extract_python_signatures(file_path, content)

            file_header = f"\n## {file_path} (score: {score:.2f})\n"

            if signatures:
                sig_text = "\n".join(f"  - {sig}" for sig in signatures[:10])
                file_block = f"{file_header}Signatures:\n{sig_text}\n"
            else:
                snippet = content[:500].strip()
                file_block = f"{file_header}Snippet:\n{snippet}...\n"

            block_tokens = _estimate_tokens(file_block)

            if estimated_tokens + block_tokens > max_tokens:
                excluded_files.append(file_path)
                budget_exceeded = True
                continue

            context_parts.append(file_block)
            estimated_tokens += block_tokens
            included_files.append(file_path)

        except Exception as e:
            logger.warning(f"Error building context for {file_path}: {e}")

    context = "".join(context_parts)

    if estimated_tokens > max_tokens:
        char_limit = max_tokens * 4
        context = context[:char_limit]

    log_context_token_budget(
        files_included=len(included_files),
        files_excluded=len(excluded_files),
        tokens_used=estimated_tokens,
        max_tokens=max_tokens,
        budget_exceeded=budget_exceeded,
        excluded_files=excluded_files if excluded_files else None,
    )

    return context


def get_code_context(
    repo: str,
    goal: str,
    max_files: int = 5,
    max_tokens: int = 2000
) -> str:
    """
    Get code context for LLM planner

    Args:
        repo: Repository name (owner/repo format)
        goal: User's goal
        max_files: Maximum files to include
        max_tokens: Maximum tokens (approximate)

    Returns:
        Code context string (<max_tokens)
    """
    repo_path = discover_repo_root()

    if not repo_path or not os.path.exists(repo_path):
        logger.warning(f"Repository path not found: {repo_path}")
        return f"Repository: {repo}\nGoal: {goal}\n\nNote: Repository not found locally"

    logger.info(f"[ContextManager] Extracting context for goal: {goal[:50]}...")

    relevant_files = find_relevant_files(repo_path, goal, max_files=max_files)

    if not relevant_files:
        logger.warning("[ContextManager] No relevant files found")
        return f"Repository: {repo}\nGoal: {goal}\n\nNote: No relevant files found"

    header = f"Repository: {repo}\nGoal: {goal}\n\nRelevant Files:\n"
    header_tokens = len(header) // 4
    remaining_tokens = max_tokens - header_tokens

    context = header + build_context_string(repo_path, relevant_files, max_tokens=remaining_tokens)

    if len(context) // 4 > max_tokens:
        char_limit = max_tokens * 4
        context = context[:char_limit]

    logger.info(f"[ContextManager] Extracted context from {len(relevant_files)} files (~{len(context)//4} tokens)")

    return context
