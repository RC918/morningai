"""
Code Indexer for Dev_Agent

Scans and indexes code repositories into the knowledge graph.
Extracts entities (functions, classes, variables) and their relationships.
"""

import os
import re
from typing import List, Dict, Optional, Any, Set
from pathlib import Path
import ast
import json


class CodeIndexer:
    """
    Index code repositories into knowledge graph.
    
    Supports:
    - Python code parsing (AST-based)
    - Function/class/variable extraction
    - Import relationship tracking
    - File structure indexing
    """
    
    SUPPORTED_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
    }
    
    IGNORE_PATTERNS = [
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        "*.pyc",
        ".DS_Store",
    ]
    
    def __init__(self, knowledge_graph_manager):
        """
        Initialize Code Indexer.
        
        Args:
            knowledge_graph_manager: KnowledgeGraphManager instance
        """
        self.kg = knowledge_graph_manager
    
    def should_ignore(self, path: Path) -> bool:
        """
        Check if path should be ignored.
        
        Args:
            path: File or directory path
            
        Returns:
            True if should be ignored
        """
        path_str = str(path)
        for pattern in self.IGNORE_PATTERNS:
            if pattern in path_str:
                return True
        return False
    
    def scan_directory(
        self,
        directory: str,
        session_id: str,
        max_files: int = 1000,
        max_file_size: int = 100000
    ) -> Dict[str, Any]:
        """
        Scan directory and index all code files.
        
        Args:
            directory: Root directory to scan
            session_id: Session UUID
            max_files: Maximum number of files to index
            max_file_size: Maximum file size in bytes
            
        Returns:
            Indexing statistics
        """
        directory_path = Path(directory)
        
        if not directory_path.exists():
            raise ValueError(f"Directory not found: {directory}")
        
        stats = {
            "files_scanned": 0,
            "files_indexed": 0,
            "entities_created": 0,
            "relationships_created": 0,
            "errors": []
        }
        
        for file_path in directory_path.rglob("*"):
            if stats["files_scanned"] >= max_files:
                break
            
            if not file_path.is_file():
                continue
            
            if self.should_ignore(file_path):
                continue
            
            if file_path.suffix not in self.SUPPORTED_EXTENSIONS:
                continue
            
            stats["files_scanned"] += 1
            
            if file_path.stat().st_size > max_file_size:
                stats["errors"].append(f"File too large: {file_path}")
                continue
            
            try:
                result = self.index_file(str(file_path), session_id)
                stats["files_indexed"] += 1
                stats["entities_created"] += result["entities_created"]
                stats["relationships_created"] += result["relationships_created"]
            except Exception as e:
                stats["errors"].append(f"Error indexing {file_path}: {str(e)}")
        
        return stats
    
    def index_file(
        self,
        file_path: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Index a single file into knowledge graph.
        
        Args:
            file_path: Path to file
            session_id: Session UUID
            
        Returns:
            Indexing statistics for the file
        """
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix
        language = self.SUPPORTED_EXTENSIONS.get(extension, "unknown")
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source_code = f.read()
        
        file_entity_id = self.kg.add_entity(
            session_id=session_id,
            entity_type="file",
            entity_name=file_path_obj.name,
            file_path=file_path,
            line_start=1,
            line_end=len(source_code.splitlines()),
            source_code=source_code[:1000],
            metadata={"language": language, "size": len(source_code)}
        )
        
        entities_created = 1
        relationships_created = 0
        
        if language == "python":
            python_result = self.index_python_file(
                file_path, source_code, session_id, file_entity_id
            )
            entities_created += python_result["entities_created"]
            relationships_created += python_result["relationships_created"]
        
        return {
            "entities_created": entities_created,
            "relationships_created": relationships_created
        }
    
    def index_python_file(
        self,
        file_path: str,
        source_code: str,
        session_id: str,
        file_entity_id: int
    ) -> Dict[str, Any]:
        """
        Index Python file using AST parsing.
        
        Args:
            file_path: Path to file
            source_code: Source code content
            session_id: Session UUID
            file_entity_id: File entity ID
            
        Returns:
            Indexing statistics
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return {"entities_created": 0, "relationships_created": 0}
        
        entities_created = 0
        relationships_created = 0
        
        entity_map = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                entity_id = self._index_function(
                    node, file_path, source_code, session_id
                )
                if entity_id:
                    entities_created += 1
                    entity_map[node.name] = entity_id
                    
                    rel_id = self.kg.add_relationship(
                        file_entity_id, entity_id, "contains"
                    )
                    if rel_id:
                        relationships_created += 1
            
            elif isinstance(node, ast.ClassDef):
                entity_id = self._index_class(
                    node, file_path, source_code, session_id
                )
                if entity_id:
                    entities_created += 1
                    entity_map[node.name] = entity_id
                    
                    rel_id = self.kg.add_relationship(
                        file_entity_id, entity_id, "contains"
                    )
                    if rel_id:
                        relationships_created += 1
                    
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_entity = self.kg.get_entity_by_name(
                                base.id, session_id, "class"
                            )
                            if base_entity:
                                rel_id = self.kg.add_relationship(
                                    entity_id, base_entity["id"], "inherits"
                                )
                                if rel_id:
                                    relationships_created += 1
            
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    entity_id = self.kg.add_entity(
                        session_id=session_id,
                        entity_type="import",
                        entity_name=alias.name,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        source_code=f"import {alias.name}",
                        metadata={"alias": alias.asname}
                    )
                    if entity_id:
                        entities_created += 1
                        rel_id = self.kg.add_relationship(
                            file_entity_id, entity_id, "imports"
                        )
                        if rel_id:
                            relationships_created += 1
            
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    full_name = f"{node.module}.{alias.name}" if node.module else alias.name
                    entity_id = self.kg.add_entity(
                        session_id=session_id,
                        entity_type="import",
                        entity_name=full_name,
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        source_code=f"from {node.module} import {alias.name}",
                        metadata={"alias": alias.asname, "module": node.module}
                    )
                    if entity_id:
                        entities_created += 1
                        rel_id = self.kg.add_relationship(
                            file_entity_id, entity_id, "imports"
                        )
                        if rel_id:
                            relationships_created += 1
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in entity_map:
                        parent_entity_id = self._find_parent_entity(
                            node, tree, entity_map
                        )
                        if parent_entity_id:
                            rel_id = self.kg.add_relationship(
                                parent_entity_id, entity_map[func_name], "calls"
                            )
                            if rel_id:
                                relationships_created += 1
        
        return {
            "entities_created": entities_created,
            "relationships_created": relationships_created
        }
    
    def _index_function(
        self,
        node: ast.FunctionDef,
        file_path: str,
        source_code: str,
        session_id: str
    ) -> Optional[int]:
        """Index a function node."""
        lines = source_code.splitlines()
        func_source = "\n".join(lines[node.lineno - 1:node.end_lineno])
        
        args = [arg.arg for arg in node.args.args]
        returns = ast.unparse(node.returns) if node.returns else None
        
        return self.kg.add_entity(
            session_id=session_id,
            entity_type="function",
            entity_name=node.name,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            source_code=func_source[:500],
            metadata={
                "args": args,
                "returns": returns,
                "decorators": [ast.unparse(d) for d in node.decorator_list],
                "is_async": isinstance(node, ast.AsyncFunctionDef)
            }
        )
    
    def _index_class(
        self,
        node: ast.ClassDef,
        file_path: str,
        source_code: str,
        session_id: str
    ) -> Optional[int]:
        """Index a class node."""
        lines = source_code.splitlines()
        class_source = "\n".join(lines[node.lineno - 1:min(node.lineno + 10, len(lines))])
        
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        bases = [ast.unparse(b) for b in node.bases]
        
        return self.kg.add_entity(
            session_id=session_id,
            entity_type="class",
            entity_name=node.name,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            source_code=class_source[:500],
            metadata={
                "methods": methods,
                "bases": bases,
                "decorators": [ast.unparse(d) for d in node.decorator_list]
            }
        )
    
    def _find_parent_entity(
        self,
        node: ast.AST,
        tree: ast.AST,
        entity_map: Dict[str, int]
    ) -> Optional[int]:
        """Find the parent entity (function/class) of a node."""
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.FunctionDef, ast.ClassDef)):
                if any(child is node for child in ast.walk(parent)):
                    return entity_map.get(parent.name)
        return None
    
    def get_file_structure(
        self,
        session_id: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get structured view of indexed files.
        
        Args:
            session_id: Session UUID
            file_path: Optional filter by file path
            
        Returns:
            File structure with entities
        """
        self.kg.connect()
        
        query = """
            SELECT 
                file_path,
                entity_type,
                entity_name,
                line_start,
                line_end,
                metadata
            FROM code_entities
            WHERE session_id = %s
        """
        params = [session_id]
        
        if file_path:
            query += " AND file_path = %s"
            params.append(file_path)
        
        query += " ORDER BY file_path, line_start"
        
        with self.kg.db_conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        
        structure = {}
        for row in rows:
            fpath = row[0]
            if fpath not in structure:
                structure[fpath] = {
                    "entities": []
                }
            
            structure[fpath]["entities"].append({
                "type": row[1],
                "name": row[2],
                "line_start": row[3],
                "line_end": row[4],
                "metadata": row[5]
            })
        
        return structure
