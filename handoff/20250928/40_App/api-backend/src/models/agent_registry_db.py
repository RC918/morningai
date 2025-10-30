"""
SQLAlchemy Database Models for Agent Registry
Issue #960 - Replace Agent Registry in-memory storage with database
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from enum import Enum
from src.models.user import db

class AgentTypeDB(str, Enum):
    """Database enum for agent types"""
    DEV_AGENT = "dev_agent"
    OPS_AGENT = "ops_agent"
    PM_AGENT = "pm_agent"
    GROWTH_STRATEGIST = "growth_strategist"
    META_AGENT = "meta_agent"

class AgentStatusDB(str, Enum):
    """Database enum for agent status"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"

class PermissionLevelDB(str, Enum):
    """Database enum for permission levels"""
    SANDBOX_ONLY = "sandbox_only"
    STAGING_ACCESS = "staging_access"
    PROD_LOW_RISK = "prod_low_risk"
    PROD_FULL_ACCESS = "prod_full_access"

class TaskStatusDB(str, Enum):
    """Database enum for task status"""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentDB(db.Model):
    """SQLAlchemy model for agents"""
    __tablename__ = 'agents'
    
    agent_id = db.Column(db.String(36), primary_key=True)  # UUID
    agent_type = db.Column(db.Enum(AgentTypeDB), nullable=False)
    status = db.Column(db.Enum(AgentStatusDB), nullable=False, default=AgentStatusDB.IDLE)
    permission_level = db.Column(db.Enum(PermissionLevelDB), nullable=False, default=PermissionLevelDB.SANDBOX_ONLY)
    reputation_score = db.Column(db.Integer, nullable=False, default=500)
    capabilities = db.Column(db.Text, nullable=False, default='[]')  # JSON array
    metadata_json = db.Column('metadata', db.Text, nullable=False, default='{}')  # JSON object - DB column is 'metadata'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    pr_merged_count = db.Column(db.Integer, nullable=False, default=0)
    pr_reverted_count = db.Column(db.Integer, nullable=False, default=0)
    test_pass_count = db.Column(db.Integer, nullable=False, default=0)
    test_fail_count = db.Column(db.Integer, nullable=False, default=0)
    test_pass_rate = db.Column(db.Float, nullable=False, default=0.0)
    
    def __repr__(self):
        return f'<AgentDB {self.agent_id}>'
    
    def get_capabilities(self):
        """Get capabilities as a list"""
        try:
            return json.loads(self.capabilities) if self.capabilities else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_capabilities(self, capabilities_list):
        """Set capabilities from a list"""
        self.capabilities = json.dumps(capabilities_list)
    
    def get_metadata(self):
        """Get metadata as a dictionary"""
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_metadata(self, metadata_dict):
        """Set metadata from a dictionary"""
        self.metadata_json = json.dumps(metadata_dict)
    
    def to_pydantic_model(self):
        """Convert to Pydantic Agent model"""
        from src.models.agent_registry import Agent, AgentType, AgentStatus, PermissionLevel, AgentStatistics
        
        return Agent(
            agent_id=self.agent_id,
            agent_type=AgentType(self.agent_type.value),
            status=AgentStatus(self.status.value),
            permission_level=PermissionLevel(self.permission_level.value),
            reputation_score=self.reputation_score,
            capabilities=self.get_capabilities(),
            metadata=self.get_metadata(),
            created_at=self.created_at,
            last_activity=self.last_activity,
            statistics=AgentStatistics(
                pr_merged_count=self.pr_merged_count,
                pr_reverted_count=self.pr_reverted_count,
                test_pass_count=self.test_pass_count,
                test_fail_count=self.test_fail_count,
                test_pass_rate=self.test_pass_rate
            )
        )

class TaskDB(db.Model):
    """SQLAlchemy model for tasks"""
    __tablename__ = 'tasks'
    
    task_id = db.Column(db.String(36), primary_key=True)  # UUID
    status = db.Column(db.Enum(TaskStatusDB), nullable=False, default=TaskStatusDB.QUEUED)
    agent_id = db.Column(db.String(36), db.ForeignKey('agents.agent_id'), nullable=True)
    tenant_id = db.Column(db.String(36), nullable=True)  # UUID
    task_type = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.Text, nullable=False, default='{}')  # JSON object
    result = db.Column(db.Text, nullable=True)  # JSON object
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agent = db.relationship('AgentDB', backref='tasks')
    
    def __repr__(self):
        return f'<TaskDB {self.task_id}>'
    
    def get_payload(self):
        """Get payload as a dictionary"""
        try:
            return json.loads(self.payload) if self.payload else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_payload(self, payload_dict):
        """Set payload from a dictionary"""
        self.payload = json.dumps(payload_dict)
    
    def get_result(self):
        """Get result as a dictionary"""
        try:
            return json.loads(self.result) if self.result else None
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_result(self, result_dict):
        """Set result from a dictionary"""
        self.result = json.dumps(result_dict) if result_dict is not None else None
    
    def to_pydantic_model(self):
        """Convert to Pydantic Task model"""
        from src.models.agent_registry import Task, TaskStatus
        
        return Task(
            task_id=self.task_id,
            status=TaskStatus(self.status.value),
            agent_id=self.agent_id,
            tenant_id=self.tenant_id,
            task_type=self.task_type,
            payload=self.get_payload(),
            result=self.get_result(),
            error_message=self.error_message,
            created_at=self.created_at,
            assigned_at=self.assigned_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            cancelled_at=self.cancelled_at,
            updated_at=self.updated_at
        )
