"""
Pattern Learner for Dev_Agent

Learns coding patterns, bug patterns, and fix patterns from history.
Enables Dev_Agent to improve over time and suggest better solutions.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from psycopg2.extras import RealDictCursor, Json


class PatternLearner:
    """
    Learn and match coding patterns.
    
    Pattern Types:
    - bug_pattern: Common bugs and their characteristics
    - fix_pattern: Successful fixes and their strategies
    - coding_style: Coding conventions and best practices
    """
    
    def __init__(self, knowledge_graph_manager):
        """
        Initialize Pattern Learner.
        
        Args:
            knowledge_graph_manager: KnowledgeGraphManager instance
        """
        self.kg = knowledge_graph_manager
    
    def learn_bug_pattern(
        self,
        bug_description: str,
        root_cause: str,
        affected_code: str,
        bug_type: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Learn a new bug pattern from a fixed bug.
        
        Args:
            bug_description: Description of the bug
            root_cause: Root cause analysis
            affected_code: Code that had the bug
            bug_type: Type of bug (syntax, logic, type, etc.)
            metadata: Additional metadata
            
        Returns:
            Pattern ID
        """
        self.kg.connect()
        
        pattern_name = f"{bug_type}: {bug_description[:50]}"
        pattern_data = {
            "description": bug_description,
            "root_cause": root_cause,
            "affected_code": affected_code,
            "bug_type": bug_type,
            "metadata": metadata or {}
        }
        
        existing = self._find_similar_pattern("bug_pattern", pattern_data)
        
        if existing:
            return self._update_pattern_frequency(existing["id"])
        
        with self.kg.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO learned_patterns
                (pattern_type, pattern_name, pattern_data, frequency, last_used)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                "bug_pattern",
                pattern_name,
                Json(pattern_data),
                1,
                datetime.now()
            ))
            
            pattern_id = cur.fetchone()[0]
            self.kg.db_conn.commit()
            return pattern_id
    
    def learn_fix_pattern(
        self,
        bug_description: str,
        fix_strategy: str,
        fix_code: str,
        success: bool,
        execution_time_seconds: int,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Learn a new fix pattern from a successful (or failed) fix.
        
        Args:
            bug_description: Description of the bug that was fixed
            fix_strategy: Strategy used to fix
            fix_code: Code changes that fixed the bug
            success: Whether the fix was successful
            execution_time_seconds: Time taken to fix
            metadata: Additional metadata
            
        Returns:
            Pattern ID
        """
        self.kg.connect()
        
        pattern_name = f"Fix: {bug_description[:50]}"
        pattern_data = {
            "bug_description": bug_description,
            "fix_strategy": fix_strategy,
            "fix_code": fix_code,
            "execution_time_seconds": execution_time_seconds,
            "metadata": metadata or {}
        }
        
        existing = self._find_similar_pattern("fix_pattern", pattern_data)
        
        if existing:
            return self._update_pattern_success(existing["id"], success)
        
        success_rate = 1.0 if success else 0.0
        
        with self.kg.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO learned_patterns
                (pattern_type, pattern_name, pattern_data, frequency, success_rate, last_used)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                "fix_pattern",
                pattern_name,
                Json(pattern_data),
                1,
                success_rate,
                datetime.now()
            ))
            
            pattern_id = cur.fetchone()[0]
            self.kg.db_conn.commit()
            return pattern_id
    
    def learn_coding_style(
        self,
        style_name: str,
        style_description: str,
        example_code: str,
        language: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Learn a coding style pattern.
        
        Args:
            style_name: Name of the style
            style_description: Description
            example_code: Example code
            language: Programming language
            metadata: Additional metadata
            
        Returns:
            Pattern ID
        """
        self.kg.connect()
        
        pattern_data = {
            "description": style_description,
            "example_code": example_code,
            "language": language,
            "metadata": metadata or {}
        }
        
        with self.kg.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO learned_patterns
                (pattern_type, pattern_name, pattern_data, frequency, last_used)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                "coding_style",
                style_name,
                Json(pattern_data),
                1,
                datetime.now()
            ))
            
            pattern_id = cur.fetchone()[0]
            self.kg.db_conn.commit()
            return pattern_id
    
    def get_similar_bug_patterns(
        self,
        bug_description: str,
        bug_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar bug patterns.
        
        Args:
            bug_description: Description of current bug
            bug_type: Type of bug to filter by
            top_k: Number of results
            
        Returns:
            List of similar bug patterns
        """
        self.kg.connect()
        
        conditions = ["pattern_type = 'bug_pattern'"]
        params = []
        
        if bug_type:
            conditions.append("pattern_data->>'bug_type' = %s")
            params.append(bug_type)
        
        params.append(top_k)
        
        with self.kg.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT 
                    id, pattern_name, pattern_data, 
                    frequency, success_rate, last_used
                FROM learned_patterns
                WHERE {' AND '.join(conditions)}
                ORDER BY frequency DESC, last_used DESC
                LIMIT %s;
            """, params)
            
            return [dict(row) for row in cur.fetchall()]
    
    def get_similar_fix_patterns(
        self,
        bug_description: str,
        min_success_rate: float = 0.7,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar fix patterns with high success rate.
        
        Args:
            bug_description: Description of current bug
            min_success_rate: Minimum success rate filter
            top_k: Number of results
            
        Returns:
            List of similar fix patterns
        """
        self.kg.connect()
        
        with self.kg.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    id, pattern_name, pattern_data, 
                    frequency, success_rate, last_used
                FROM learned_patterns
                WHERE 
                    pattern_type = 'fix_pattern'
                    AND success_rate >= %s
                ORDER BY 
                    success_rate DESC,
                    frequency DESC,
                    last_used DESC
                LIMIT %s;
            """, (min_success_rate, top_k))
            
            return [dict(row) for row in cur.fetchall()]
    
    def get_coding_styles(
        self,
        language: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get coding style patterns.
        
        Args:
            language: Filter by programming language
            top_k: Number of results
            
        Returns:
            List of coding style patterns
        """
        self.kg.connect()
        
        conditions = ["pattern_type = 'coding_style'"]
        params = []
        
        if language:
            conditions.append("pattern_data->>'language' = %s")
            params.append(language)
        
        params.append(top_k)
        
        with self.kg.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT 
                    id, pattern_name, pattern_data, 
                    frequency, last_used
                FROM learned_patterns
                WHERE {' AND '.join(conditions)}
                ORDER BY frequency DESC, last_used DESC
                LIMIT %s;
            """, params)
            
            return [dict(row) for row in cur.fetchall()]
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """
        Get statistics about learned patterns.
        
        Returns:
            Statistics dictionary
        """
        self.kg.connect()
        
        with self.kg.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    pattern_type,
                    COUNT(*) as count,
                    AVG(frequency) as avg_frequency,
                    AVG(success_rate) as avg_success_rate
                FROM learned_patterns
                GROUP BY pattern_type;
            """)
            
            stats_by_type = {
                row["pattern_type"]: {
                    "count": row["count"],
                    "avg_frequency": float(row["avg_frequency"]) if row["avg_frequency"] else 0,
                    "avg_success_rate": float(row["avg_success_rate"]) if row["avg_success_rate"] else 0
                }
                for row in cur.fetchall()
            }
            
            cur.execute("""
                SELECT 
                    COUNT(*) as total_patterns,
                    SUM(frequency) as total_uses,
                    AVG(success_rate) as overall_success_rate
                FROM learned_patterns;
            """)
            
            overall = dict(cur.fetchone())
            
            return {
                "total_patterns": overall["total_patterns"],
                "total_uses": overall["total_uses"],
                "overall_success_rate": float(overall["overall_success_rate"]) if overall["overall_success_rate"] else 0,
                "by_type": stats_by_type
            }
    
    def _find_similar_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict
    ) -> Optional[Dict[str, Any]]:
        """Find existing similar pattern (simple matching for now)."""
        self.kg.connect()
        
        with self.kg.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, pattern_name, pattern_data, frequency, success_rate
                FROM learned_patterns
                WHERE pattern_type = %s
                ORDER BY frequency DESC
                LIMIT 10;
            """, (pattern_type,))
            
            for row in cur.fetchall():
                existing_data = row["pattern_data"]
                
                if pattern_type == "bug_pattern":
                    if (existing_data.get("bug_type") == pattern_data.get("bug_type") and
                        existing_data.get("root_cause") == pattern_data.get("root_cause")):
                        return dict(row)
                
                elif pattern_type == "fix_pattern":
                    if (existing_data.get("fix_strategy") == pattern_data.get("fix_strategy")):
                        return dict(row)
        
        return None
    
    def _update_pattern_frequency(self, pattern_id: int) -> int:
        """Update pattern frequency when encountered again."""
        self.kg.connect()
        
        with self.kg.db_conn.cursor() as cur:
            cur.execute("""
                UPDATE learned_patterns
                SET 
                    frequency = frequency + 1,
                    last_used = %s
                WHERE id = %s;
            """, (datetime.now(), pattern_id))
            
            self.kg.db_conn.commit()
        
        return pattern_id
    
    def _update_pattern_success(self, pattern_id: int, success: bool) -> int:
        """Update pattern success rate."""
        self.kg.connect()
        
        with self.kg.db_conn.cursor() as cur:
            cur.execute("""
                SELECT frequency, success_rate
                FROM learned_patterns
                WHERE id = %s;
            """, (pattern_id,))
            
            row = cur.fetchone()
            if not row:
                return pattern_id
            
            current_frequency = row[0]
            current_success_rate = row[1]
            
            new_frequency = current_frequency + 1
            new_success_rate = (
                (current_success_rate * current_frequency + (1.0 if success else 0.0))
                / new_frequency
            )
            
            cur.execute("""
                UPDATE learned_patterns
                SET 
                    frequency = %s,
                    success_rate = %s,
                    last_used = %s
                WHERE id = %s;
            """, (new_frequency, new_success_rate, datetime.now(), pattern_id))
            
            self.kg.db_conn.commit()
        
        return pattern_id
    
    def record_bug_fix(
        self,
        github_issue_id: int,
        issue_title: str,
        issue_description: str,
        bug_type: str,
        root_cause: str,
        fix_strategy: str,
        pr_number: Optional[int],
        success: bool,
        execution_time_seconds: int,
        patterns_used: Optional[List[int]] = None
    ) -> int:
        """
        Record a bug fix attempt in history.
        
        Args:
            github_issue_id: GitHub Issue ID
            issue_title: Issue title
            issue_description: Issue description
            bug_type: Type of bug
            root_cause: Root cause analysis
            fix_strategy: Strategy used to fix
            pr_number: PR number if created
            success: Whether fix was successful
            execution_time_seconds: Time taken
            patterns_used: List of pattern IDs used
            
        Returns:
            Record ID
        """
        self.kg.connect()
        
        with self.kg.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO bug_fix_history
                (github_issue_id, issue_title, issue_description, bug_type,
                 root_cause, fix_strategy, pr_number, success, 
                 execution_time_seconds, patterns_used)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                github_issue_id, issue_title, issue_description, bug_type,
                root_cause, fix_strategy, pr_number, success,
                execution_time_seconds, Json(patterns_used or [])
            ))
            
            record_id = cur.fetchone()[0]
            self.kg.db_conn.commit()
            return record_id
    
    def get_bug_fix_history(
        self,
        github_issue_id: Optional[int] = None,
        success_only: bool = False,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get bug fix history.
        
        Args:
            github_issue_id: Filter by GitHub Issue ID
            success_only: Only return successful fixes
            limit: Maximum number of results
            
        Returns:
            List of bug fix records
        """
        self.kg.connect()
        
        conditions = []
        params = []
        
        if github_issue_id:
            conditions.append("github_issue_id = %s")
            params.append(github_issue_id)
        
        if success_only:
            conditions.append("success = true")
        
        params.append(limit)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        with self.kg.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT *
                FROM bug_fix_history
                {where_clause}
                ORDER BY created_at DESC
                LIMIT %s;
            """, params)
            
            return [dict(row) for row in cur.fetchall()]
    
    def get_success_metrics(self) -> Dict[str, Any]:
        """
        Get success metrics for bug fixes.
        
        Returns:
            Success metrics
        """
        self.kg.connect()
        
        with self.kg.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_fixes,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_fixes,
                    AVG(CASE WHEN success THEN execution_time_seconds ELSE NULL END) as avg_fix_time,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
                FROM bug_fix_history;
            """)
            
            overall = dict(cur.fetchone())
            
            cur.execute("""
                SELECT 
                    bug_type,
                    COUNT(*) as count,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate
                FROM bug_fix_history
                GROUP BY bug_type
                ORDER BY count DESC;
            """)
            
            by_type = [dict(row) for row in cur.fetchall()]
            
            return {
                "total_fixes": overall["total_fixes"],
                "successful_fixes": overall["successful_fixes"],
                "success_rate": float(overall["success_rate"]) if overall["success_rate"] else 0,
                "avg_fix_time_seconds": float(overall["avg_fix_time"]) if overall["avg_fix_time"] else 0,
                "by_bug_type": by_type
            }
