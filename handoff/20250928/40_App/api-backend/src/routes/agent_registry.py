"""
Agent Registry & Task Router Routes
Issue #760 - Agent Registry & Task Router
Issue #960 - Replace in-memory storage with database
Feature Flag: MVP_AGENT_REGISTRY

Implements OpenAPI spec: agent-registry-v1.yaml
"""
import os
import uuid
import logging
from datetime import datetime
from typing import Optional
from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy import or_
from src.middleware.auth_middleware import jwt_required, roles_required
from src.models.agent_registry import (
    Agent, AgentRegistrationRequest, AgentUpdateRequest,
    AgentHealth, AgentHealthReport, AgentListResponse,
    Task, TaskCreationRequest, TaskUpdateRequest, TaskListResponse,
    AgentType, AgentStatus, PermissionLevel, TaskStatus,
    Pagination, AgentStatistics
)
from src.models.agent_registry_db import (
    AgentDB, TaskDB, AgentTypeDB, AgentStatusDB, 
    PermissionLevelDB, TaskStatusDB, db
)

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN and SENTRY_DSN.strip():
    import sentry_sdk
else:
    sentry_sdk = None

bp = Blueprint("agent_registry", __name__, url_prefix="/api/v1")


@bp.route("/agents", methods=["GET"])
@jwt_required
def list_agents():
    """
    List all registered agents
    Supports filtering by agent_type, status, permission_level
    """
    try:
        agent_type_filter = request.args.get('agent_type')
        status_filter = request.args.get('status')
        permission_level_filter = request.args.get('permission_level')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        if page < 1:
            return jsonify({"error": {"code": "invalid_parameter", "message": "page must be >= 1"}}), 400
        if page_size < 1 or page_size > 100:
            return jsonify({"error": {"code": "invalid_parameter", "message": "page_size must be between 1 and 100"}}), 400
        
        query = AgentDB.query
        
        if agent_type_filter:
            try:
                agent_type = AgentTypeDB(agent_type_filter)
                query = query.filter(AgentDB.agent_type == agent_type)
            except ValueError:
                return jsonify({"error": {"code": "invalid_parameter", "message": f"Invalid agent_type: {agent_type_filter}"}}), 400
        
        if status_filter:
            try:
                status = AgentStatusDB(status_filter)
                query = query.filter(AgentDB.status == status)
            except ValueError:
                return jsonify({"error": {"code": "invalid_parameter", "message": f"Invalid status: {status_filter}"}}), 400
        
        if permission_level_filter:
            try:
                permission_level = PermissionLevelDB(permission_level_filter)
                query = query.filter(AgentDB.permission_level == permission_level)
            except ValueError:
                return jsonify({"error": {"code": "invalid_parameter", "message": f"Invalid permission_level: {permission_level_filter}"}}), 400
        
        total_items = query.count()
        total_pages = (total_items + page_size - 1) // page_size
        
        agents_db = query.order_by(AgentDB.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        agents = [agent_db.to_pydantic_model() for agent_db in agents_db]
        
        response = AgentListResponse(
            agents=agents,
            pagination=Pagination(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages
            )
        )
        
        return jsonify(response.model_dump(mode='json')), 200
    
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents", methods=["POST"])
@jwt_required
@roles_required("admin", "service")
def register_agent():
    """
    Register a new agent
    Requires admin or service role permissions
    """
    try:
        payload = request.get_json(silent=True) or {}
        validated_request = AgentRegistrationRequest(**payload)
        
        agent_id = str(uuid.uuid4())
        
        existing_agent = AgentDB.query.filter_by(agent_type=AgentTypeDB(validated_request.agent_type.value)).first()
        if existing_agent:
            existing_caps = set(existing_agent.get_capabilities())
            new_caps = set(validated_request.capabilities)
            if existing_caps == new_caps:
                return jsonify({
                    "error": {
                        "code": "agent_already_exists",
                        "message": f"Agent with type {validated_request.agent_type} and same capabilities already registered"
                    }
                }), 409
        
        agent_db = AgentDB(
            agent_id=agent_id,
            agent_type=AgentTypeDB(validated_request.agent_type.value),
            status=AgentStatusDB.IDLE,
            permission_level=PermissionLevelDB.SANDBOX_ONLY,
            reputation_score=500
        )
        agent_db.set_capabilities(validated_request.capabilities)
        agent_db.set_metadata(validated_request.metadata)
        
        db.session.add(agent_db)
        db.session.commit()
        
        agent = agent_db.to_pydantic_model()
        
        logger.info(f"Registered agent {agent_id} of type {agent.agent_type}")
        
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='agent_registry',
                message='Agent registered',
                level='info',
                data={'agent_id': agent_id, 'agent_type': agent.agent_type.value}
            )
        
        return jsonify(agent.model_dump(mode='json')), 201
    
    except ValidationError as e:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "Invalid request parameters",
                "details": e.errors()
            }
        }), 400
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to register agent: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents/<agent_id>", methods=["GET"])
@jwt_required
def get_agent(agent_id):
    """Get agent details by ID"""
    try:
        agent_db = AgentDB.query.get(agent_id)
        
        if not agent_db:
            return jsonify({"error": {"code": "not_found", "message": "Agent not found"}}), 404
        
        agent = agent_db.to_pydantic_model()
        return jsonify(agent.model_dump(mode='json')), 200
    
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents/<agent_id>", methods=["PATCH"])
@jwt_required
@roles_required("admin", "service")
def update_agent(agent_id):
    """Update agent configuration or status"""
    try:
        agent_db = AgentDB.query.get(agent_id)
        
        if not agent_db:
            return jsonify({"error": {"code": "not_found", "message": "Agent not found"}}), 404
        
        payload = request.get_json(silent=True) or {}
        validated_request = AgentUpdateRequest(**payload)
        
        if validated_request.status is not None:
            agent_db.status = AgentStatusDB(validated_request.status.value)
        if validated_request.capabilities is not None:
            agent_db.set_capabilities(validated_request.capabilities)
        if validated_request.metadata is not None:
            current_metadata = agent_db.get_metadata()
            current_metadata.update(validated_request.metadata)
            agent_db.set_metadata(current_metadata)
        
        agent_db.last_activity = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Updated agent {agent_id}")
        
        agent = agent_db.to_pydantic_model()
        return jsonify(agent.model_dump(mode='json')), 200
    
    except ValidationError as e:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "Invalid request parameters",
                "details": e.errors()
            }
        }), 400
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update agent {agent_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents/<agent_id>", methods=["DELETE"])
@jwt_required
@roles_required("admin")
def unregister_agent(agent_id):
    """Unregister an agent"""
    try:
        agent_db = AgentDB.query.get(agent_id)
        
        if not agent_db:
            return jsonify({"error": {"code": "not_found", "message": "Agent not found"}}), 404
        
        db.session.delete(agent_db)
        db.session.commit()
        
        logger.info(f"Unregistered agent {agent_id}")
        
        return '', 204
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to unregister agent {agent_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents/<agent_id>/health", methods=["GET"])
@jwt_required
def get_agent_health(agent_id):
    """Get agent health status"""
    try:
        agent_db = AgentDB.query.get(agent_id)
        
        if not agent_db:
            return jsonify({"error": {"code": "not_found", "message": "Agent not found"}}), 404
        
        health = AgentHealth(
            agent_id=agent_db.agent_id,
            status=AgentStatus(agent_db.status.value),
            last_heartbeat=agent_db.last_activity,
            errors=[]
        )
        
        return jsonify(health.model_dump(mode='json')), 200
    
    except Exception as e:
        logger.error(f"Failed to get agent health {agent_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents/<agent_id>/health", methods=["POST"])
@jwt_required
def report_agent_health(agent_id):
    """Report agent health (heartbeat)"""
    try:
        agent_db = AgentDB.query.get(agent_id)
        
        if not agent_db:
            return jsonify({"error": {"code": "not_found", "message": "Agent not found"}}), 404
        
        payload = request.get_json(silent=True) or {}
        validated_request = AgentHealthReport(**payload)
        
        agent_db.status = AgentStatusDB(validated_request.status.value)
        agent_db.last_activity = datetime.utcnow()
        
        db.session.commit()
        
        health = AgentHealth(
            agent_id=agent_db.agent_id,
            status=AgentStatus(agent_db.status.value),
            last_heartbeat=agent_db.last_activity,
            metrics=validated_request.metrics,
            errors=[]
        )
        
        return jsonify(health.model_dump(mode='json')), 200
    
    except ValidationError as e:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "Invalid request parameters",
                "details": e.errors()
            }
        }), 400
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to report agent health {agent_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/tasks", methods=["GET"])
@jwt_required
def list_tasks():
    """List tasks with optional filtering"""
    try:
        status_filter = request.args.get('status')
        agent_id_filter = request.args.get('agent_id')
        tenant_id_filter = request.args.get('tenant_id')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        if page < 1:
            return jsonify({"error": {"code": "invalid_parameter", "message": "page must be >= 1"}}), 400
        if page_size < 1 or page_size > 100:
            return jsonify({"error": {"code": "invalid_parameter", "message": "page_size must be between 1 and 100"}}), 400
        
        query = TaskDB.query
        
        if status_filter:
            try:
                status = TaskStatusDB(status_filter)
                query = query.filter(TaskDB.status == status)
            except ValueError:
                return jsonify({"error": {"code": "invalid_parameter", "message": f"Invalid status: {status_filter}"}}), 400
        
        if agent_id_filter:
            query = query.filter(TaskDB.agent_id == agent_id_filter)
        
        if tenant_id_filter:
            query = query.filter(TaskDB.tenant_id == tenant_id_filter)
        
        total_items = query.count()
        total_pages = (total_items + page_size - 1) // page_size
        
        tasks_db = query.order_by(TaskDB.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        tasks = [task_db.to_pydantic_model() for task_db in tasks_db]
        
        response = TaskListResponse(
            tasks=tasks,
            pagination=Pagination(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages
            )
        )
        
        return jsonify(response.model_dump(mode='json')), 200
    
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/tasks", methods=["POST"])
@jwt_required
def create_task():
    """Create a new task and route to appropriate agent"""
    try:
        payload = request.get_json(silent=True) or {}
        validated_request = TaskCreationRequest(**payload)
        
        task_id = str(uuid.uuid4())
        
        tenant_id = validated_request.tenant_id or getattr(request, 'tenant_id', None)
        
        task_db = TaskDB(
            task_id=task_id,
            status=TaskStatusDB.QUEUED,
            task_type=validated_request.task_type,
            tenant_id=tenant_id
        )
        task_db.set_payload(validated_request.payload)
        
        db.session.add(task_db)
        db.session.commit()
        
        task = task_db.to_pydantic_model()
        
        logger.info(f"Created task {task_id} of type {task.task_type}")
        
        if sentry_sdk:
            sentry_sdk.add_breadcrumb(
                category='task_router',
                message='Task created',
                level='info',
                data={'task_id': task_id, 'task_type': task.task_type}
            )
        
        return jsonify(task.model_dump(mode='json')), 202
    
    except ValidationError as e:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "Invalid request parameters",
                "details": e.errors()
            }
        }), 400
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create task: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/tasks/<task_id>", methods=["GET"])
@jwt_required
def get_task(task_id):
    """Get task details by ID"""
    try:
        task_db = TaskDB.query.get(task_id)
        
        if not task_db:
            return jsonify({"error": {"code": "not_found", "message": "Task not found"}}), 404
        
        task = task_db.to_pydantic_model()
        return jsonify(task.model_dump(mode='json')), 200
    
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/tasks/<task_id>", methods=["PATCH"])
@jwt_required
def update_task(task_id):
    """Update task status or metadata"""
    try:
        task_db = TaskDB.query.get(task_id)
        
        if not task_db:
            return jsonify({"error": {"code": "not_found", "message": "Task not found"}}), 404
        
        payload = request.get_json(silent=True) or {}
        validated_request = TaskUpdateRequest(**payload)
        
        if validated_request.status is not None:
            task_db.status = TaskStatusDB(validated_request.status.value)
            
            if validated_request.status == TaskStatus.RUNNING and not task_db.started_at:
                task_db.started_at = datetime.utcnow()
            elif validated_request.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and not task_db.completed_at:
                task_db.completed_at = datetime.utcnow()
            elif validated_request.status == TaskStatus.CANCELLED and not task_db.cancelled_at:
                task_db.cancelled_at = datetime.utcnow()
        
        if validated_request.result is not None:
            task_db.set_result(validated_request.result)
        
        if validated_request.error_message is not None:
            task_db.error_message = validated_request.error_message
        
        task_db.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        task = task_db.to_pydantic_model()
        
        logger.info(f"Updated task {task_id} to status {task.status}")
        
        return jsonify(task.model_dump(mode='json')), 200
    
    except ValidationError as e:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "Invalid request parameters",
                "details": e.errors()
            }
        }), 400
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update task {task_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/tasks/<task_id>/cancel", methods=["POST"])
@jwt_required
def cancel_task(task_id):
    """Cancel a running or queued task"""
    try:
        task_db = TaskDB.query.get(task_id)
        
        if not task_db:
            return jsonify({"error": {"code": "not_found", "message": "Task not found"}}), 404
        
        if task_db.status in [TaskStatusDB.COMPLETED, TaskStatusDB.FAILED, TaskStatusDB.CANCELLED]:
            return jsonify({
                "error": {
                    "code": "cannot_cancel",
                    "message": f"Task cannot be cancelled (current status: {task_db.status.value})"
                }
            }), 409
        
        payload = request.get_json(silent=True) or {}
        reason = payload.get('reason', 'User requested cancellation')
        
        task_db.status = TaskStatusDB.CANCELLED
        task_db.cancelled_at = datetime.utcnow()
        task_db.updated_at = datetime.utcnow()
        task_db.error_message = f"Cancelled: {reason}"
        
        db.session.commit()
        
        task = task_db.to_pydantic_model()
        
        logger.info(f"Cancelled task {task_id}: {reason}")
        
        return jsonify(task.model_dump(mode='json')), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to cancel task {task_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500
