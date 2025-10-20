#!/usr/bin/env python3
"""
Bug Fix Pattern Learner - Learn bug and fix patterns for workflow
Phase 1 Week 6: Bug Fix Workflow
Adapted from PR #291 to use PR #292's schema
"""
import logging
from typing import List, Dict, Any, Optional
from psycopg2.extras import RealDictCursor, Json

from error_handler import (
    create_success, create_error, ErrorCode
)

logger = logging.getLogger(__name__)


class BugFixPatternLearner:
    """
    Learn and match bug/fix patterns using PR #292's schema.
    Stores bug patterns in code_patterns table,
    tracks history in bug_fix_history.
    """

    def __init__(self, knowledge_graph_manager):
        """
        Initialize Bug Fix Pattern Learner.

        Args:
            knowledge_graph_manager: KnowledgeGraphManager instance
        """
        self.kg = knowledge_graph_manager

    def learn_bug_pattern(
        self,
        bug_description: str,
        root_cause: str,
        bug_type: str,
        affected_code: str = "",
        language: str = "python",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Learn a bug pattern and store in code_patterns table."""
        if not self.kg.db_pool:
            return create_error(
                ErrorCode.DATABASE_ERROR, "Database not configured"
            )

        pattern_name = f"bug_{bug_type}_{hash(root_cause) % 10000}"
        pattern_template = f"Bug: {bug_description[:100]}"

        conn = None
        try:
            conn = self.kg._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO code_patterns
                (pattern_name, pattern_type, pattern_template, language,
                 frequency, confidence_score, examples, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pattern_name, language) DO UPDATE
                SET frequency = code_patterns.frequency + 1,
                    updated_at = NOW()
                RETURNING id;
            """, (
                pattern_name,
                'bug_pattern',
                pattern_template,
                language,
                1,
                0.8,
                Json([{
                    'bug_description': bug_description,
                    'root_cause': root_cause,
                    'bug_type': bug_type,
                    'affected_code': affected_code[:500]
                }]),
                Json(metadata or {})
            ))

            pattern_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                f"Learned bug pattern: {pattern_name} (ID: {pattern_id})"
            )
            return create_success({
                'pattern_id': pattern_id,
                'pattern_name': pattern_name
            })

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to learn bug pattern: {e}")
            return create_error(ErrorCode.KNOWLEDGE_GRAPH_ERROR, str(e))
        finally:
            if conn:
                self.kg._return_connection(conn)

    def learn_fix_pattern(
        self,
        bug_description: str,
        fix_strategy: str,
        fix_code: str,
        success: bool,
        language: str = "python",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Learn a fix pattern and store in code_patterns table."""
        if not self.kg.db_pool:
            return create_error(
                ErrorCode.DATABASE_ERROR, "Database not configured"
            )

        pattern_name = f"fix_{hash(fix_strategy) % 10000}"
        pattern_template = f"Fix: {fix_strategy[:100]}"

        conn = None
        try:
            conn = self.kg._get_connection()
            cursor = conn.cursor()

            success_score = 1.0 if success else 0.0

            cursor.execute("""
                INSERT INTO code_patterns
                (pattern_name, pattern_type, pattern_template, language,
                 frequency, confidence_score, examples, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pattern_name, language) DO UPDATE
                SET frequency = code_patterns.frequency + 1,
                    confidence_score = (
                        code_patterns.confidence_score *
                        code_patterns.frequency + %s
                    ) / (code_patterns.frequency + 1),
                    examples = code_patterns.examples || EXCLUDED.examples,
                    updated_at = NOW()
                RETURNING id;
            """, (
                pattern_name,
                'fix_pattern',
                pattern_template,
                language,
                1,
                success_score,
                Json([{
                    'bug_description': bug_description,
                    'fix_strategy': fix_strategy,
                    'fix_code': fix_code[:500],
                    'success': success
                }]),
                Json(metadata or {}),
                success_score
            ))

            pattern_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                f"Learned fix pattern: {pattern_name} (ID: {pattern_id})"
            )
            return create_success({
                'pattern_id': pattern_id,
                'pattern_name': pattern_name
            })

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to learn fix pattern: {e}")
            return create_error(ErrorCode.KNOWLEDGE_GRAPH_ERROR, str(e))
        finally:
            if conn:
                self.kg._return_connection(conn)

    def get_similar_bug_patterns(
        self,
        bug_description: str,
        bug_type: Optional[str] = None,
        language: str = "python",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Find similar bug patterns."""
        if not self.kg.db_pool:
            return create_error(
                ErrorCode.KNOWLEDGE_GRAPH_ERROR,
                "Database not configured"
            )

        conn = None
        try:
            conn = self.kg._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if bug_type:
                cursor.execute("""
                    SELECT id, pattern_name, pattern_type, pattern_template,
                           frequency, confidence_score, examples, metadata
                    FROM code_patterns
                    WHERE pattern_type = 'bug_pattern'
                    AND language = %s
                    AND metadata->>'bug_type' = %s
                    ORDER BY frequency DESC, confidence_score DESC
                    LIMIT %s;
                """, (language, bug_type, top_k))
            else:
                cursor.execute("""
                    SELECT id, pattern_name, pattern_type, pattern_template,
                           frequency, confidence_score, examples, metadata
                    FROM code_patterns
                    WHERE pattern_type = 'bug_pattern'
                    AND language = %s
                    ORDER BY frequency DESC, confidence_score DESC
                    LIMIT %s;
                """, (language, top_k))

            results = cursor.fetchall()

            return create_success({
                'patterns': [dict(row) for row in results],
                'count': len(results)
            })

        except Exception as e:
            logger.error(f"Failed to get similar bug patterns: {e}")
            return create_error(ErrorCode.KNOWLEDGE_GRAPH_ERROR, str(e))
        finally:
            if conn:
                self.kg._return_connection(conn)

    def get_similar_fix_patterns(
        self,
        bug_description: str,
        min_success_rate: float = 0.7,
        language: str = "python",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Find similar fix patterns with high success rate."""
        if not self.kg.db_pool:
            return create_error(
                ErrorCode.KNOWLEDGE_GRAPH_ERROR,
                "Database not configured"
            )

        conn = None
        try:
            conn = self.kg._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT id, pattern_name, pattern_type, pattern_template,
                       frequency, confidence_score, examples, metadata
                FROM code_patterns
                WHERE pattern_type = 'fix_pattern'
                AND language = %s
                AND confidence_score >= %s
                ORDER BY confidence_score DESC, frequency DESC
                LIMIT %s;
            """, (language, min_success_rate, top_k))

            results = cursor.fetchall()

            return create_success({
                'patterns': [dict(row) for row in results],
                'count': len(results)
            })

        except Exception as e:
            logger.error(f"Failed to get similar fix patterns: {e}")
            return create_error(ErrorCode.KNOWLEDGE_GRAPH_ERROR, str(e))
        finally:
            if conn:
                self.kg._return_connection(conn)

    def record_bug_fix(
        self,
        issue_number: int,
        issue_title: str,
        bug_description: str,
        bug_type: str,
        affected_files: List[str],
        root_cause: str,
        fix_strategy: str,
        fix_code_diff: str,
        pr_number: Optional[int],
        pr_url: Optional[str],
        success: bool,
        execution_time_seconds: int,
        patterns_used: Optional[List[int]] = None,
        test_results: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Record a bug fix attempt in bug_fix_history table."""
        if not self.kg.db_pool:
            return create_error(
                ErrorCode.KNOWLEDGE_GRAPH_ERROR,
                "Database not configured"
            )

        conn = None
        try:
            conn = self.kg._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO bug_fix_history
                (issue_number, issue_title, bug_description, bug_type,
                 affected_files, root_cause, fix_strategy, fix_code_diff,
                 pr_number, pr_url, success, execution_time_seconds,
                 patterns_used, test_results)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                issue_number,
                issue_title,
                bug_description,
                bug_type,
                affected_files or [],
                root_cause,
                fix_strategy,
                fix_code_diff,
                pr_number,
                pr_url,
                success,
                execution_time_seconds,
                Json(patterns_used or []),
                Json(test_results or {})
            ))

            record_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                f"Recorded bug fix for issue #{issue_number} "
                f"(ID: {record_id})"
            )
            return create_success({'record_id': record_id})

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to record bug fix: {e}")
            return create_error(ErrorCode.KNOWLEDGE_GRAPH_ERROR, str(e))
        finally:
            if conn:
                self.kg._return_connection(conn)

    def get_bug_fix_history(
        self,
        issue_number: Optional[int] = None,
        bug_type: Optional[str] = None,
        success_only: bool = False,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get bug fix history records."""
        if not self.kg.db_pool:
            return create_error(
                ErrorCode.DATABASE_ERROR,
                "Database not configured"
            )

        conn = None
        try:
            conn = self.kg._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = "SELECT * FROM bug_fix_history WHERE 1=1"
            params = []

            if issue_number:
                query += " AND issue_number = %s"
                params.append(issue_number)

            if bug_type:
                query += " AND bug_type = %s"
                params.append(bug_type)

            if success_only:
                query += " AND success = true"

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()

            return create_success({
                'records': [dict(row) for row in results],
                'count': len(results)
            })

        except Exception as e:
            logger.error(f"Failed to get bug fix history: {e}")
            return create_error(ErrorCode.DATABASE_ERROR, str(e))
        finally:
            if conn:
                self.kg._return_connection(conn)
