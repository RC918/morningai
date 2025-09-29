#!/usr/bin/env python3
"""
Persistent State Manager - Database-backed state persistence
Replaces in-memory state with persistent storage for Beta candidates and approval history
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sqlite3
import threading
from contextlib import contextmanager

@dataclass
class StateCheckpoint:
    """State checkpoint for recovery"""
    checkpoint_id: str
    component_name: str
    state_data: Dict
    created_at: datetime
    metadata: Dict = None

class PersistentStateManager:
    """Manages persistent state for all Phase 7 components"""
    
    def __init__(self, db_path: str = "phase7_state.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS beta_candidates (
                    user_id TEXT PRIMARY KEY,
                    activity_score REAL NOT NULL,
                    engagement_metrics TEXT NOT NULL,
                    qualification_reason TEXT NOT NULL,
                    invited_at TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS approval_requests (
                    request_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    context TEXT NOT NULL,
                    prompt_details TEXT NOT NULL,
                    requester_agent TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    approved_by TEXT,
                    approved_at TEXT,
                    approval_channel TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_stories (
                    story_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    estimated_effort INTEGER NOT NULL,
                    source_feedback TEXT NOT NULL,
                    status TEXT DEFAULT 'backlog',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS gamification_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    trigger_condition TEXT NOT NULL,
                    reward_type TEXT NOT NULL,
                    reward_amount INTEGER NOT NULL,
                    effectiveness_score REAL NOT NULL,
                    last_updated TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS state_checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    component_name TEXT NOT NULL,
                    state_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            
            conn.commit()
            
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def save_beta_candidate(self, candidate_data: Dict) -> bool:
        """Save Beta candidate to persistent storage"""
        try:
            with self._lock, self._get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO beta_candidates 
                    (user_id, activity_score, engagement_metrics, qualification_reason, 
                     invited_at, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    candidate_data['user_id'],
                    candidate_data['activity_score'],
                    json.dumps(candidate_data['engagement_metrics']),
                    candidate_data['qualification_reason'],
                    candidate_data.get('invited_at'),
                    candidate_data.get('status', 'pending'),
                    candidate_data.get('created_at', datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to save Beta candidate: {e}")
            return False
            
    def load_beta_candidates(self, status: Optional[str] = None) -> List[Dict]:
        """Load Beta candidates from persistent storage"""
        try:
            with self._get_connection() as conn:
                if status:
                    cursor = conn.execute(
                        'SELECT * FROM beta_candidates WHERE status = ? ORDER BY created_at DESC',
                        (status,)
                    )
                else:
                    cursor = conn.execute(
                        'SELECT * FROM beta_candidates ORDER BY created_at DESC'
                    )
                    
                candidates = []
                for row in cursor.fetchall():
                    candidate = dict(row)
                    candidate['engagement_metrics'] = json.loads(candidate['engagement_metrics'])
                    candidates.append(candidate)
                    
                return candidates
        except Exception as e:
            self.logger.error(f"Failed to load Beta candidates: {e}")
            return []
            
    def save_approval_request(self, request_data: Dict) -> bool:
        """Save approval request to persistent storage"""
        try:
            with self._lock, self._get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO approval_requests 
                    (request_id, trace_id, title, description, context, prompt_details,
                     requester_agent, priority, status, created_at, expires_at,
                     approved_by, approved_at, approval_channel)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request_data['request_id'],
                    request_data['trace_id'],
                    request_data['title'],
                    request_data['description'],
                    json.dumps(request_data['context']),
                    request_data['prompt_details'],
                    request_data['requester_agent'],
                    request_data['priority'],
                    request_data['status'],
                    request_data['created_at'],
                    request_data['expires_at'],
                    request_data.get('approved_by'),
                    request_data.get('approved_at'),
                    request_data.get('approval_channel')
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to save approval request: {e}")
            return False
            
    def load_approval_requests(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Load approval requests from persistent storage"""
        try:
            with self._get_connection() as conn:
                if status:
                    cursor = conn.execute(
                        'SELECT * FROM approval_requests WHERE status = ? ORDER BY created_at DESC LIMIT ?',
                        (status, limit)
                    )
                else:
                    cursor = conn.execute(
                        'SELECT * FROM approval_requests ORDER BY created_at DESC LIMIT ?',
                        (limit,)
                    )
                    
                requests = []
                for row in cursor.fetchall():
                    request = dict(row)
                    request['context'] = json.loads(request['context'])
                    requests.append(request)
                    
                return requests
        except Exception as e:
            self.logger.error(f"Failed to load approval requests: {e}")
            return []
            
    def save_user_story(self, story_data: Dict) -> bool:
        """Save user story to persistent storage"""
        try:
            with self._lock, self._get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO user_stories 
                    (story_id, title, description, priority, estimated_effort,
                     source_feedback, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    story_data['story_id'],
                    story_data['title'],
                    story_data['description'],
                    story_data['priority'],
                    story_data['estimated_effort'],
                    story_data['source_feedback'],
                    story_data.get('status', 'backlog'),
                    story_data.get('created_at', datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to save user story: {e}")
            return False
            
    def save_gamification_rule(self, rule_data: Dict) -> bool:
        """Save gamification rule to persistent storage"""
        try:
            with self._lock, self._get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO gamification_rules 
                    (rule_id, name, trigger_condition, reward_type, reward_amount,
                     effectiveness_score, last_updated, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule_data['rule_id'],
                    rule_data['name'],
                    rule_data['trigger_condition'],
                    rule_data['reward_type'],
                    rule_data['reward_amount'],
                    rule_data['effectiveness_score'],
                    rule_data['last_updated'],
                    rule_data.get('active', True)
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to save gamification rule: {e}")
            return False
            
    def create_checkpoint(self, component_name: str, state_data: Dict, metadata: Dict = None) -> str:
        """Create state checkpoint for recovery"""
        checkpoint_id = f"{component_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            with self._lock, self._get_connection() as conn:
                conn.execute('''
                    INSERT INTO state_checkpoints 
                    (checkpoint_id, component_name, state_data, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    checkpoint_id,
                    component_name,
                    json.dumps(state_data),
                    datetime.now().isoformat(),
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                
                conn.execute('''
                    DELETE FROM state_checkpoints 
                    WHERE component_name = ? AND checkpoint_id NOT IN (
                        SELECT checkpoint_id FROM state_checkpoints 
                        WHERE component_name = ? 
                        ORDER BY created_at DESC LIMIT 10
                    )
                ''', (component_name, component_name))
                conn.commit()
                
                return checkpoint_id
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {e}")
            return None
            
    def restore_from_checkpoint(self, component_name: str, checkpoint_id: Optional[str] = None) -> Optional[Dict]:
        """Restore state from checkpoint"""
        try:
            with self._get_connection() as conn:
                if checkpoint_id:
                    cursor = conn.execute(
                        'SELECT * FROM state_checkpoints WHERE checkpoint_id = ?',
                        (checkpoint_id,)
                    )
                else:
                    cursor = conn.execute(
                        'SELECT * FROM state_checkpoints WHERE component_name = ? ORDER BY created_at DESC LIMIT 1',
                        (component_name,)
                    )
                    
                row = cursor.fetchone()
                if row:
                    return {
                        'checkpoint_id': row['checkpoint_id'],
                        'component_name': row['component_name'],
                        'state': json.loads(row['state_data']),
                        'created_at': row['created_at'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else None
                    }
                    
                return None
        except Exception as e:
            self.logger.error(f"Failed to restore from checkpoint: {e}")
            return None
            
    def cleanup_expired_data(self, days: int = 30):
        """Clean up expired data older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            with self._lock, self._get_connection() as conn:
                conn.execute(
                    'DELETE FROM approval_requests WHERE expires_at < ?',
                    (cutoff_date,)
                )
                
                conn.execute(
                    'DELETE FROM state_checkpoints WHERE created_at < ?',
                    (cutoff_date,)
                )
                
                conn.commit()
                self.logger.info(f"Cleaned up data older than {days} days")
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired data: {e}")
            
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            with self._get_connection() as conn:
                stats = {}
                
                tables = ['beta_candidates', 'approval_requests', 'user_stories', 
                         'gamification_rules', 'state_checkpoints']
                
                for table in tables:
                    cursor = conn.execute(f'SELECT COUNT(*) as count FROM {table}')
                    stats[table] = cursor.fetchone()['count']
                    
                if os.path.exists(self.db_path):
                    stats['db_size_bytes'] = os.path.getsize(self.db_path)
                    
                return stats
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return {}

persistent_state_manager = PersistentStateManager()
