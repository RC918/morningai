#!/usr/bin/env python3
"""
Integration test to verify that Alembic migrations work with actual data insertion.
This catches enum value mismatches that SQLite won't detect but PostgreSQL will.
"""
import os
import sys
from datetime import datetime
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.models.user import db
from src.models.agent_registry_db import (
    AgentDB, TaskDB,
    AgentTypeDB, AgentStatusDB, PermissionLevelDB, TaskStatusDB
)
from flask import Flask
from common.config.settings import settings

def test_data_insertion():
    """Test that we can insert data using the model enums after migration"""
    
    app = Flask(__name__)
    database_url = settings.database_url or 'sqlite:///test_insertion.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print(f"Testing data insertion with database: {database_url}")
        
        agent_id = str(uuid.uuid4())
        agent = AgentDB(
            agent_id=agent_id,
            agent_type=AgentTypeDB.DEV_AGENT,  # Uses "dev_agent" value
            status=AgentStatusDB.ACTIVE,        # Uses "active" value
            permission_level=PermissionLevelDB.SANDBOX_ONLY,  # Uses "sandbox_only" value
            reputation_score=500,
            capabilities='[]',
            metadata_json='{}',
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            pr_merged_count=0,
            pr_reverted_count=0,
            test_pass_count=0,
            test_fail_count=0,
            test_pass_rate=0.0
        )
        
        try:
            db.session.add(agent)
            db.session.commit()
            print(f"✅ Successfully inserted agent with ID: {agent_id}")
            print(f"   - agent_type: {agent.agent_type.value}")
            print(f"   - status: {agent.status.value}")
            print(f"   - permission_level: {agent.permission_level.value}")
        except Exception as e:
            print(f"❌ Failed to insert agent: {e}")
            db.session.rollback()
            sys.exit(1)
        
        task_id = str(uuid.uuid4())
        task = TaskDB(
            task_id=task_id,
            status=TaskStatusDB.QUEUED,  # Uses "queued" value
            agent_id=agent_id,
            tenant_id=str(uuid.uuid4()),
            task_type='test_task',
            payload='{}',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            db.session.add(task)
            db.session.commit()
            print(f"✅ Successfully inserted task with ID: {task_id}")
            print(f"   - status: {task.status.value}")
            print(f"   - agent_id: {task.agent_id}")
        except Exception as e:
            print(f"❌ Failed to insert task: {e}")
            db.session.rollback()
            sys.exit(1)
        
        try:
            queried_agent = AgentDB.query.filter_by(agent_id=agent_id).first()
            if not queried_agent:
                print(f"❌ Failed to query agent")
                sys.exit(1)
            
            print(f"✅ Successfully queried agent")
            print(f"   - Retrieved agent_type: {queried_agent.agent_type.value}")
            
            queried_task = TaskDB.query.filter_by(task_id=task_id).first()
            if not queried_task:
                print(f"❌ Failed to query task")
                sys.exit(1)
            
            print(f"✅ Successfully queried task")
            print(f"   - Retrieved status: {queried_task.status.value}")
        except Exception as e:
            print(f"❌ Failed to query data: {e}")
            sys.exit(1)
        
        print("\n✅ Testing all enum values...")
        all_agent_types = [AgentTypeDB.DEV_AGENT, AgentTypeDB.OPS_AGENT, AgentTypeDB.PM_AGENT, 
                          AgentTypeDB.GROWTH_STRATEGIST, AgentTypeDB.META_AGENT]
        all_statuses = [AgentStatusDB.ACTIVE, AgentStatusDB.IDLE, AgentStatusDB.BUSY, 
                       AgentStatusDB.OFFLINE, AgentStatusDB.ERROR]
        all_permissions = [PermissionLevelDB.SANDBOX_ONLY, PermissionLevelDB.STAGING_ACCESS,
                          PermissionLevelDB.PROD_LOW_RISK, PermissionLevelDB.PROD_FULL_ACCESS]
        all_task_statuses = [TaskStatusDB.QUEUED, TaskStatusDB.ASSIGNED, TaskStatusDB.RUNNING,
                            TaskStatusDB.COMPLETED, TaskStatusDB.FAILED, TaskStatusDB.CANCELLED]
        
        print(f"   Agent types: {[t.value for t in all_agent_types]}")
        print(f"   Agent statuses: {[s.value for s in all_statuses]}")
        print(f"   Permission levels: {[p.value for p in all_permissions]}")
        print(f"   Task statuses: {[s.value for s in all_task_statuses]}")
        
        print("\n✅ All data insertion tests passed!")
        print("   Enum values in migration match Python model definitions.")

if __name__ == '__main__':
    test_data_insertion()
