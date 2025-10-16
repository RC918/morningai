"""
Knowledge Graph Manager for Dev_Agent

Manages code knowledge graph with pgvector for semantic search.
Enables Dev_Agent to understand codebase structure and relationships.
"""

from typing import List, Dict, Optional, Any, Tuple
import os
import asyncio
from datetime import datetime
import hashlib
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    from pgvector.psycopg2 import register_vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


class KnowledgeGraphManager:
    """
    Manages codebase knowledge graph with vector embeddings.
    
    Features:
    - Code entity indexing (files, functions, classes, variables)
    - Semantic search using pgvector
    - Relationship tracking (calls, imports, inherits)
    - Pattern learning and matching
    """
    
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSION = 1536
    
    def __init__(
        self,
        db_config: Optional[Dict[str, str]] = None,
        openai_api_key: Optional[str] = None,
        enable_vector_search: bool = True
    ):
        """
        Initialize Knowledge Graph Manager.
        
        Args:
            db_config: PostgreSQL connection config
            openai_api_key: OpenAI API key for embeddings
            enable_vector_search: Whether to enable vector search (requires pgvector)
        """
        self.db_config = db_config or self._get_default_db_config()
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.enable_vector_search = enable_vector_search and PGVECTOR_AVAILABLE
        
        self.db_conn = None
        self.openai_client = None
        
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
        
        if self.enable_vector_search:
            if not OPENAI_AVAILABLE:
                raise ImportError("openai is required for vector search. Install with: pip install openai")
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required for vector search")
            self.openai_client = openai.Client(api_key=self.openai_api_key)
    
    def _get_default_db_config(self) -> Dict[str, str]:
        """Get default database config from environment variables."""
        supabase_url = os.getenv("SUPABASE_URL", "")
        if "supabase.co" in supabase_url:
            project_id = supabase_url.split("//")[1].split(".")[0]
            return {
                "host": f"db.{project_id}.supabase.co",
                "port": "5432",
                "database": "postgres",
                "user": "postgres",
                "password": os.getenv("SUPABASE_DB_PASSWORD", ""),
            }
        
        return {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "morningai"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        }
    
    def connect(self):
        """Establish database connection."""
        if self.db_conn is None or self.db_conn.closed:
            self.db_conn = psycopg2.connect(**self.db_config)
            
            if self.enable_vector_search and PGVECTOR_AVAILABLE:
                register_vector(self.db_conn)
    
    def close(self):
        """Close database connection."""
        if self.db_conn and not self.db_conn.closed:
            self.db_conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def initialize_schema(self):
        """
        Initialize database schema for knowledge graph.
        Creates tables if they don't exist.
        """
        self.connect()
        
        with self.db_conn.cursor() as cur:
            if self.enable_vector_search:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS code_entities (
                    id SERIAL PRIMARY KEY,
                    session_id UUID,
                    entity_type VARCHAR(50),
                    entity_name VARCHAR(255),
                    file_path TEXT,
                    line_start INT,
                    line_end INT,
                    source_code TEXT,
                    """ + (
                    "embedding VECTOR(1536)," if self.enable_vector_search else ""
                ) + """
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS entity_relationships (
                    id SERIAL PRIMARY KEY,
                    from_entity_id INT REFERENCES code_entities(id) ON DELETE CASCADE,
                    to_entity_id INT REFERENCES code_entities(id) ON DELETE CASCADE,
                    relationship_type VARCHAR(50),
                    weight FLOAT DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_type VARCHAR(50),
                    pattern_name VARCHAR(255),
                    pattern_data JSONB,
                    frequency INT DEFAULT 1,
                    success_rate FLOAT DEFAULT 0.0,
                    last_used TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            if self.enable_vector_search:
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_entities_embedding 
                    ON code_entities USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_entities_type_name 
                ON code_entities(entity_type, entity_name);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_entities_file 
                ON code_entities(file_path);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_relationships_from 
                ON entity_relationships(from_entity_id);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_relationships_to 
                ON entity_relationships(to_entity_id);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_type 
                ON learned_patterns(pattern_type);
            """)
            
            self.db_conn.commit()
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using OpenAI API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if disabled/failed
        """
        if not self.enable_vector_search or not self.openai_client:
            return None
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=text[:8000]
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def add_entity(
        self,
        session_id: str,
        entity_type: str,
        entity_name: str,
        file_path: str,
        line_start: int,
        line_end: int,
        source_code: str,
        metadata: Optional[Dict] = None
    ) -> Optional[int]:
        """
        Add a code entity to the knowledge graph.
        
        Args:
            session_id: Session UUID
            entity_type: Type of entity (file, function, class, variable)
            entity_name: Name of the entity
            file_path: Path to the file
            line_start: Starting line number
            line_end: Ending line number
            source_code: Source code of the entity
            metadata: Additional metadata
            
        Returns:
            Entity ID or None if failed
        """
        self.connect()
        
        embedding_text = f"{entity_type} {entity_name}\n{source_code}"
        embedding = self.generate_embedding(embedding_text)
        
        with self.db_conn.cursor() as cur:
            if self.enable_vector_search and embedding:
                cur.execute("""
                    INSERT INTO code_entities 
                    (session_id, entity_type, entity_name, file_path, 
                     line_start, line_end, source_code, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    session_id, entity_type, entity_name, file_path,
                    line_start, line_end, source_code, embedding,
                    Json(metadata or {})
                ))
            else:
                cur.execute("""
                    INSERT INTO code_entities 
                    (session_id, entity_type, entity_name, file_path, 
                     line_start, line_end, source_code, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    session_id, entity_type, entity_name, file_path,
                    line_start, line_end, source_code,
                    Json(metadata or {})
                ))
            
            entity_id = cur.fetchone()[0]
            self.db_conn.commit()
            return entity_id
    
    def add_relationship(
        self,
        from_entity_id: int,
        to_entity_id: int,
        relationship_type: str,
        weight: float = 1.0
    ) -> Optional[int]:
        """
        Add a relationship between two entities.
        
        Args:
            from_entity_id: Source entity ID
            to_entity_id: Target entity ID
            relationship_type: Type of relationship (calls, imports, inherits, uses)
            weight: Relationship strength (0.0-1.0)
            
        Returns:
            Relationship ID or None if failed
        """
        self.connect()
        
        with self.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO entity_relationships 
                (from_entity_id, to_entity_id, relationship_type, weight)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (from_entity_id, to_entity_id, relationship_type, weight))
            
            rel_id = cur.fetchone()[0]
            self.db_conn.commit()
            return rel_id
    
    def semantic_search(
        self,
        query: str,
        session_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on code entities.
        
        Args:
            query: Search query
            session_id: Filter by session ID
            entity_type: Filter by entity type
            top_k: Number of results to return
            
        Returns:
            List of matching entities with similarity scores
        """
        if not self.enable_vector_search:
            return self.keyword_search(query, session_id, entity_type, top_k)
        
        self.connect()
        query_embedding = self.generate_embedding(query)
        
        if not query_embedding:
            return []
        
        conditions = []
        params = [query_embedding, top_k]
        
        if session_id:
            conditions.append("session_id = %s")
            params.insert(-1, session_id)
        
        if entity_type:
            conditions.append("entity_type = %s")
            params.insert(-1, entity_type)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT 
                    id, entity_type, entity_name, file_path,
                    line_start, line_end, source_code, metadata,
                    1 - (embedding <=> %s) as similarity
                FROM code_entities
                {where_clause}
                ORDER BY embedding <=> %s
                LIMIT %s;
            """, params)
            
            return [dict(row) for row in cur.fetchall()]
    
    def keyword_search(
        self,
        query: str,
        session_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search (fallback when vector search unavailable).
        
        Args:
            query: Search query
            session_id: Filter by session ID
            entity_type: Filter by entity type
            top_k: Number of results to return
            
        Returns:
            List of matching entities
        """
        self.connect()
        
        conditions = ["(entity_name ILIKE %s OR source_code ILIKE %s)"]
        params = [f"%{query}%", f"%{query}%"]
        
        if session_id:
            conditions.append("session_id = %s")
            params.append(session_id)
        
        if entity_type:
            conditions.append("entity_type = %s")
            params.append(entity_type)
        
        params.append(top_k)
        
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT 
                    id, entity_type, entity_name, file_path,
                    line_start, line_end, source_code, metadata
                FROM code_entities
                WHERE {' AND '.join(conditions)}
                ORDER BY 
                    CASE WHEN entity_name ILIKE %s THEN 1 ELSE 2 END,
                    entity_name
                LIMIT %s;
            """, [*params[:-1], f"%{query}%", params[-1]])
            
            return [dict(row) for row in cur.fetchall()]
    
    def find_related_entities(
        self,
        entity_id: int,
        relationship_types: Optional[List[str]] = None,
        depth: int = 2,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find related entities through relationship graph traversal.
        
        Args:
            entity_id: Starting entity ID
            relationship_types: Filter by relationship types
            depth: Maximum traversal depth
            max_results: Maximum number of results
            
        Returns:
            List of related entities with relationship paths
        """
        self.connect()
        
        relationship_filter = ""
        params = [entity_id, depth, max_results]
        
        if relationship_types:
            relationship_filter = "AND r.relationship_type = ANY(%s)"
            params.insert(1, relationship_types)
        
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                WITH RECURSIVE entity_graph AS (
                    SELECT 
                        ce.id, ce.entity_type, ce.entity_name, ce.file_path,
                        ce.line_start, ce.line_end, ce.source_code, ce.metadata,
                        0 as depth,
                        ARRAY[ce.id] as path,
                        ARRAY[]::text[] as relationship_path
                    FROM code_entities ce
                    WHERE ce.id = %s
                    
                    UNION ALL
                    
                    SELECT 
                        ce.id, ce.entity_type, ce.entity_name, ce.file_path,
                        ce.line_start, ce.line_end, ce.source_code, ce.metadata,
                        eg.depth + 1,
                        eg.path || ce.id,
                        eg.relationship_path || r.relationship_type
                    FROM entity_graph eg
                    JOIN entity_relationships r ON r.from_entity_id = eg.id
                    JOIN code_entities ce ON ce.id = r.to_entity_id
                    WHERE 
                        eg.depth < %s 
                        AND NOT ce.id = ANY(eg.path)
                        {relationship_filter}
                )
                SELECT DISTINCT ON (id)
                    id, entity_type, entity_name, file_path,
                    line_start, line_end, source_code, metadata,
                    depth, path, relationship_path
                FROM entity_graph
                WHERE depth > 0
                ORDER BY id, depth
                LIMIT %s;
            """, params)
            
            return [dict(row) for row in cur.fetchall()]
    
    def get_entity_by_name(
        self,
        entity_name: str,
        session_id: Optional[str] = None,
        entity_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get entity by exact name match.
        
        Args:
            entity_name: Entity name
            session_id: Filter by session ID
            entity_type: Filter by entity type
            
        Returns:
            Entity data or None if not found
        """
        self.connect()
        
        conditions = ["entity_name = %s"]
        params = [entity_name]
        
        if session_id:
            conditions.append("session_id = %s")
            params.append(session_id)
        
        if entity_type:
            conditions.append("entity_type = %s")
            params.append(entity_type)
        
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT 
                    id, entity_type, entity_name, file_path,
                    line_start, line_end, source_code, metadata
                FROM code_entities
                WHERE {' AND '.join(conditions)}
                LIMIT 1;
            """, params)
            
            row = cur.fetchone()
            return dict(row) if row else None
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session's knowledge graph.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Statistics dictionary
        """
        self.connect()
        
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_entities,
                    COUNT(DISTINCT entity_type) as entity_types,
                    COUNT(DISTINCT file_path) as files_indexed,
                    MAX(updated_at) as last_updated
                FROM code_entities
                WHERE session_id = %s;
            """, (session_id,))
            
            stats = dict(cur.fetchone())
            
            cur.execute("""
                SELECT entity_type, COUNT(*) as count
                FROM code_entities
                WHERE session_id = %s
                GROUP BY entity_type;
            """, (session_id,))
            
            stats["entities_by_type"] = {
                row["entity_type"]: row["count"]
                for row in cur.fetchall()
            }
            
            cur.execute("""
                SELECT COUNT(*) as total_relationships
                FROM entity_relationships er
                JOIN code_entities ce ON ce.id = er.from_entity_id
                WHERE ce.session_id = %s;
            """, (session_id,))
            
            stats["total_relationships"] = cur.fetchone()["total_relationships"]
            
            return stats
    
    def clear_session(self, session_id: str):
        """
        Clear all knowledge graph data for a session.
        
        Args:
            session_id: Session UUID
        """
        self.connect()
        
        with self.db_conn.cursor() as cur:
            cur.execute("""
                DELETE FROM code_entities
                WHERE session_id = %s;
            """, (session_id,))
            
            self.db_conn.commit()
