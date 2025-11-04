#!/usr/bin/env python3
"""
Session State Management
Phase 1 Week 4: Persistent session state with Redis + PostgreSQL
"""
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from agents.dev_agent.persistence.upstash_redis_client import UpstashRedisClient
from agents.dev_agent.error_handler import ErrorCode, create_error, create_success

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """Session state structure"""
    session_id: str
    task: str
    priority: str
    created_at: str
    last_activity: str
    context_window: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    decision_trace: List[Dict[str, Any]]


class SessionStateManager:
    """Manages Dev_Agent session state with Redis caching"""

    CONTEXT_WINDOW_SIZE = 50
    SESSION_TTL = 3600
    OPERATION_TTL = 1800

    def __init__(self, redis_client: Optional[UpstashRedisClient] = None):
        self.redis = redis_client or UpstashRedisClient()
        logger.info("SessionStateManager initialized")

    def create_session(
        self,
        task: str,
        priority: str = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new session"""
        try:
            session_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            session = SessionState(
                session_id=session_id,
                task=task,
                priority=priority,
                created_at=now,
                last_activity=now,
                context_window=[],
                metadata=metadata or {},
                decision_trace=[]
            )

            session_key = f"session:{session_id}"
            if not self.redis.set_json(session_key, asdict(session), ex=self.SESSION_TTL):
                return create_error(
                    ErrorCode.STATE_PERSISTENCE_FAILED,
                    "Failed to create session in Redis",
                    hint="Check Redis connection and credentials"
                )

            logger.info(f"Created session {session_id} for task: {task}")
            return create_success({'session_id': session_id})

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return create_error(
                ErrorCode.STATE_PERSISTENCE_FAILED,
                f"Session creation failed: {str(e)}"
            )

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session state"""
        try:
            session_key = f"session:{session_id}"
            session_data = self.redis.get_json(session_key)

            if not session_data:
                logger.warning(f"Session {session_id} not found")
                return None

            self.redis.expire(session_key, self.SESSION_TTL)
            return session_data

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update session state"""
        try:
            session = self.get_session(session_id)
            if not session:
                return create_error(
                    ErrorCode.SESSION_NOT_FOUND,
                    f"Session {session_id} not found",
                    hint="Session may have expired or never existed"
                )

            session.update(updates)
            session['last_activity'] = datetime.now().isoformat()

            session_key = f"session:{session_id}"
            if not self.redis.set_json(session_key, session, ex=self.SESSION_TTL):
                return create_error(
                    ErrorCode.STATE_PERSISTENCE_FAILED,
                    "Failed to update session"
                )

            return create_success({'session_id': session_id})

        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return create_error(
                ErrorCode.STATE_PERSISTENCE_FAILED,
                f"Session update failed: {str(e)}"
            )

    def add_to_context_window(
        self,
        session_id: str,
        operation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add operation to context window (sliding window)"""
        try:
            operations_key = f"session:{session_id}:operations"

            operation['timestamp'] = datetime.now().isoformat()
            operation_json = json.dumps(operation)

            self.redis.lpush(operations_key, operation_json)

            self.redis.ltrim(operations_key, 0, self.CONTEXT_WINDOW_SIZE - 1)

            self.redis.expire(operations_key, self.OPERATION_TTL)

            return create_success()

        except Exception as e:
            logger.error(f"Failed to add operation to context window: {e}")
            return create_error(
                ErrorCode.CONTEXT_WINDOW_FULL,
                f"Context window update failed: {str(e)}"
            )

    def get_context_window(self, session_id: str) -> List[Dict[str, Any]]:
        """Get operations from context window"""
        try:
            operations_key = f"session:{session_id}:operations"
            operations_json = self.redis.lrange(operations_key, 0, -1)

            operations = []
            for op_json in operations_json:
                try:
                    operations.append(json.loads(op_json))
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode operation: {op_json}")
                    continue

            return operations

        except Exception as e:
            logger.error(f"Failed to get context window: {e}")
            return []

    def add_decision_trace(
        self,
        session_id: str,
        phase: str,
        decision_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add decision trace for debugging and analysis"""
        try:
            trace_key = f"session:{session_id}:trace"

            trace_entry = {
                'timestamp': datetime.now().isoformat(),
                'phase': phase,
                'data': decision_data
            }

            trace_json = json.dumps(trace_entry)
            self.redis.lpush(trace_key, trace_json)

            self.redis.ltrim(trace_key, 0, 99)

            self.redis.expire(trace_key, self.OPERATION_TTL)

            return create_success()

        except Exception as e:
            logger.error(f"Failed to add decision trace: {e}")
            return create_error(
                ErrorCode.STATE_PERSISTENCE_FAILED,
                f"Decision trace failed: {str(e)}"
            )

    def get_decision_trace(self, session_id: str) -> List[Dict[str, Any]]:
        """Get decision trace for session"""
        try:
            trace_key = f"session:{session_id}:trace"
            traces_json = self.redis.lrange(trace_key, 0, -1)

            traces = []
            for trace_json in traces_json:
                try:
                    traces.append(json.loads(trace_json))
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode trace: {trace_json}")
                    continue

            return traces

        except Exception as e:
            logger.error(f"Failed to get decision trace: {e}")
            return []

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete session and related data"""
        try:
            session_key = f"session:{session_id}"
            operations_key = f"session:{session_id}:operations"
            trace_key = f"session:{session_id}:trace"

            self.redis.delete(session_key)
            self.redis.delete(operations_key)
            self.redis.delete(trace_key)

            logger.info(f"Deleted session {session_id}")
            return create_success()

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return create_error(
                ErrorCode.STATE_PERSISTENCE_FAILED,
                f"Session deletion failed: {str(e)}"
            )

    def health_check(self) -> Dict[str, Any]:
        """Check Redis connection health"""
        try:
            if self.redis.ping():
                return create_success({'redis': 'healthy'})
            else:
                return create_error(
                    ErrorCode.NETWORK_ERROR,
                    "Redis ping failed"
                )
        except Exception as e:
            return create_error(
                ErrorCode.NETWORK_ERROR,
                f"Redis health check failed: {str(e)}"
            )


def get_session_manager() -> SessionStateManager:
    """Factory function to create session manager"""
    return SessionStateManager()
