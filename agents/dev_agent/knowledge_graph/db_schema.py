#!/usr/bin/env python3
"""
Database Schema Definitions for Knowledge Graph
Phase 1 Week 5: Knowledge Graph System
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CodeEmbedding:
    """Code embedding record"""
    id: Optional[int]
    file_path: str
    file_hash: str
    content_preview: str
    embedding: list
    language: str
    tokens_count: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


@dataclass
class CodePattern:
    """Code pattern record"""
    id: Optional[int]
    pattern_name: str
    pattern_type: str
    pattern_template: str
    language: str
    frequency: int
    confidence_score: float
    examples: list
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class CodeRelationship:
    """Code relationship record"""
    id: Optional[int]
    source_file: str
    target_file: str
    relationship_type: str
    source_entity: Optional[str]
    target_entity: Optional[str]
    strength: float
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class EmbeddingCacheStats:
    """Embedding cache statistics record"""
    id: Optional[int]
    date: datetime
    api_calls_count: int
    cache_hits_count: int
    cache_miss_count: int
    tokens_used: int
    estimated_cost: float
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


QUERIES = {
    'insert_embedding': """
        INSERT INTO code_embeddings
        (file_path, file_hash, content_preview, embedding, language, tokens_count, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (file_path, file_hash) DO UPDATE
        SET embedding = EXCLUDED.embedding,
            content_preview = EXCLUDED.content_preview,
            tokens_count = EXCLUDED.tokens_count,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        RETURNING id;
    """,

    'get_embedding_by_path': """
        SELECT * FROM code_embeddings
        WHERE file_path = %s
        ORDER BY updated_at DESC
        LIMIT 1;
    """,

    'search_similar_code': """
        SELECT file_path, content_preview, language,
               1 - (embedding <=> %s::vector) AS similarity
        FROM code_embeddings
        WHERE language = %s OR %s IS NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """,

    'insert_pattern': """
        INSERT INTO code_patterns
        (pattern_name, pattern_type, pattern_template, language, frequency, confidence_score, examples, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (pattern_name, language) DO UPDATE
        SET frequency = code_patterns.frequency + 1,
            confidence_score = GREATEST(code_patterns.confidence_score, EXCLUDED.confidence_score),
            examples = code_patterns.examples || EXCLUDED.examples,
            updated_at = NOW()
        RETURNING id;
    """,

    'get_patterns_by_language': """
        SELECT * FROM code_patterns
        WHERE language = %s
        ORDER BY frequency DESC, confidence_score DESC
        LIMIT %s;
    """,

    'insert_relationship': """
        INSERT INTO code_relationships
        (source_file, target_file, relationship_type, source_entity, target_entity, strength, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """,

    'get_relationships_by_file': """
        SELECT * FROM code_relationships
        WHERE source_file = %s OR target_file = %s
        ORDER BY strength DESC;
    """,

    'update_cache_stats': """
        INSERT INTO embedding_cache_stats
        (date, api_calls_count, cache_hits_count, cache_miss_count, tokens_used, estimated_cost)
        VALUES (CURRENT_DATE, %s, %s, %s, %s, %s)
        ON CONFLICT (date) DO UPDATE
        SET api_calls_count = embedding_cache_stats.api_calls_count + EXCLUDED.api_calls_count,
            cache_hits_count = embedding_cache_stats.cache_hits_count + EXCLUDED.cache_hits_count,
            cache_miss_count = embedding_cache_stats.cache_miss_count + EXCLUDED.cache_miss_count,
            tokens_used = embedding_cache_stats.tokens_used + EXCLUDED.tokens_used,
            estimated_cost = embedding_cache_stats.estimated_cost + EXCLUDED.estimated_cost,
            updated_at = NOW();
    """,

    'get_cache_stats': """
        SELECT * FROM embedding_cache_stats
        WHERE date >= %s
        ORDER BY date DESC;
    """,

    'delete_stale_embeddings': """
        DELETE FROM code_embeddings
        WHERE updated_at < NOW() - INTERVAL '%s days'
        RETURNING file_path;
    """,
}
