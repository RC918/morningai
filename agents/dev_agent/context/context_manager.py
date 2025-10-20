"""
Context Manager - Multi-file Context Understanding

Analyzes project structure, dependencies, and relationships between files.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class FileContext:
    """Context information for a single file"""
    path: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    lines_of_code: int = 0


@dataclass
class ProjectContext:
    """Context information for entire project"""
    root_path: str
    files: Dict[str, FileContext] = field(default_factory=dict)
    dependency_graph: Dict[str, Set[str]] = field(default_factory=dict)
    call_graph: Dict[str, Set[str]] = field(default_factory=dict)
    total_files: int = 0
    total_lines: int = 0


class ContextManager:
    """
    Manages multi-file context understanding.
    
    Provides capabilities for:
    - Project structure analysis
    - Dependency graph construction
    - Related files discovery
    - Function call chain analysis
    """
    
    def __init__(self, supported_extensions: Optional[List[str]] = None):
        self.supported_extensions = supported_extensions or ['.py', '.js', '.ts', '.tsx', '.jsx']
        self.project_context: Optional[ProjectContext] = None
    
    def analyze_project(self, root_path: str, max_depth: int = 10) -> ProjectContext:
        """
        Analyze entire project structure and build context.
        
        Args:
            root_path: Root directory of the project
            max_depth: Maximum directory depth to traverse
        
        Returns:
            ProjectContext with full project analysis
        """
        print(f"🔍 Analyzing project: {root_path}")
        
        root = Path(root_path)
        if not root.exists():
            raise ValueError(f"Project root does not exist: {root_path}")
        
        context = ProjectContext(root_path=str(root.absolute()))
        
        files_to_analyze = self._discover_files(root, max_depth)
        print(f"   Found {len(files_to_analyze)} files to analyze")
        
        for file_path in files_to_analyze:
            try:
                file_context = self._analyze_file(file_path)
                rel_path = str(Path(file_path).relative_to(root))
                context.files[rel_path] = file_context
                context.total_files += 1
                context.total_lines += file_context.lines_of_code
            except Exception as e:
                print(f"   ⚠️  Failed to analyze {file_path}: {e}")
                continue
        
        self._build_dependency_graph(context)
        
        self._build_call_graph(context)
        
        self.project_context = context
        
        print(f"✅ Analysis complete:")
        print(f"   Files: {context.total_files}")
        print(f"   Lines of Code: {context.total_lines}")
        print(f"   Dependencies: {len(context.dependency_graph)}")
        
        return context
    
    def get_related_files(self, file_path: str, max_depth: int = 2) -> List[str]:
        """
        Get all files related to the specified file.
        
        Args:
            file_path: Path to the file (relative to project root)
            max_depth: Maximum depth of dependency traversal
        
        Returns:
            List of related file paths
        """
        if not self.project_context:
            raise ValueError("Project context not initialized. Call analyze_project() first.")
        
        if file_path not in self.project_context.files:
            return []
        
        related = set()
        to_visit = {file_path}
        visited = set()
        current_depth = 0
        
        while to_visit and current_depth < max_depth:
            current_level = to_visit.copy()
            to_visit.clear()
            
            for path in current_level:
                if path in visited:
                    continue
                
                visited.add(path)
                file_ctx = self.project_context.files.get(path)
                
                if file_ctx:
                    related.update(file_ctx.dependencies)
                    to_visit.update(file_ctx.dependencies - visited)
                    
                    related.update(file_ctx.dependents)
                    to_visit.update(file_ctx.dependents - visited)
            
            current_depth += 1
        
        related.discard(file_path)
        
        return sorted(list(related))
    
    def get_call_chain(self, function_name: str) -> Dict[str, Any]:
        """
        Get the complete call chain for a function.
        
        Args:
            function_name: Name of the function
        
        Returns:
            Dictionary with callers and callees
        """
        if not self.project_context:
            raise ValueError("Project context not initialized")
        
        call_chain = {
            'function': function_name,
            'callers': [],
            'callees': []
        }
        
        for func, called_funcs in self.project_context.call_graph.items():
            if function_name in called_funcs:
                call_chain['callers'].append(func)
        
        if function_name in self.project_context.call_graph:
            call_chain['callees'] = list(self.project_context.call_graph[function_name])
        
        return call_chain
    
    def find_function(self, function_name: str) -> List[Dict[str, str]]:
        """
        Find all occurrences of a function across the project.
        
        Args:
            function_name: Name of the function to find
        
        Returns:
            List of matches with file and context
        """
        if not self.project_context:
            raise ValueError("Project context not initialized")
        
        matches = []
        
        for file_path, file_ctx in self.project_context.files.items():
            if function_name in file_ctx.functions:
                matches.append({
                    'file': file_path,
                    'type': 'definition',
                    'context': f"Function defined in {file_path}"
                })
        
        return matches
    
    def _discover_files(self, root: Path, max_depth: int) -> List[str]:
        """Discover all supported files in the project"""
        files = []
        
        for ext in self.supported_extensions:
            pattern = f"**/*{ext}"
            found_files = list(root.glob(pattern))
            
            for file in found_files:
                try:
                    rel_path = file.relative_to(root)
                    depth = len(rel_path.parts)
                    
                    if depth <= max_depth:
                        if any(part.startswith('.') or part in ['node_modules', 'venv', '__pycache__', 'dist', 'build'] 
                               for part in rel_path.parts):
                            continue
                        
                        files.append(str(file.absolute()))
                except ValueError:
                    continue
        
        return files
    
    def _analyze_file(self, file_path: str) -> FileContext:
        """Analyze a single file and extract context"""
        ext = Path(file_path).suffix
        
        if ext == '.py':
            return self._analyze_python_file(file_path)
        else:
            return self._analyze_generic_file(file_path)
    
    def _analyze_python_file(self, file_path: str) -> FileContext:
        """Analyze Python file using AST"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_ctx = FileContext(path=file_path)
        file_ctx.lines_of_code = len(content.splitlines())
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        file_ctx.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        file_ctx.imports.append(node.module)
            
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    file_ctx.functions.append(node.name)
                    file_ctx.exports.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    file_ctx.classes.append(node.name)
                    file_ctx.exports.append(node.name)
        
        except SyntaxError:
            pass  # Skip files with syntax errors
        
        return file_ctx
    
    def _analyze_generic_file(self, file_path: str) -> FileContext:
        """Analyze non-Python files using basic parsing"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        file_ctx = FileContext(path=file_path)
        file_ctx.lines_of_code = len(content.splitlines())
        
        if file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            import_patterns = [
                r'import .+ from [\'"](.+)[\'"]',
                r'require\([\'"](.+)[\'"]\)',
            ]
            
            import re
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                file_ctx.imports.extend(matches)
        
        return file_ctx
    
    def _build_dependency_graph(self, context: ProjectContext):
        """Build dependency graph from file contexts"""
        module_to_file = {}
        
        for file_path, file_ctx in context.files.items():
            if file_path.endswith('.py'):
                module_name = file_path.replace('/', '.').replace('.py', '')
                module_to_file[module_name] = file_path
        
        for file_path, file_ctx in context.files.items():
            dependencies = set()
            
            for imp in file_ctx.imports:
                for module_name, dep_file_path in module_to_file.items():
                    if imp in module_name or module_name in imp:
                        dependencies.add(dep_file_path)
                        
                        if dep_file_path in context.files:
                            context.files[dep_file_path].dependents.add(file_path)
            
            file_ctx.dependencies = dependencies
            context.dependency_graph[file_path] = dependencies
    
    def _build_call_graph(self, context: ProjectContext):
        """Build function call graph (simplified)"""
        
        all_functions = []
        
        for file_ctx in context.files.values():
            all_functions.extend(file_ctx.functions)
        
        for func in all_functions:
            context.call_graph[func] = set()


def create_context_manager(supported_extensions: Optional[List[str]] = None) -> ContextManager:
    """Factory function to create ContextManager"""
    return ContextManager(supported_extensions)
