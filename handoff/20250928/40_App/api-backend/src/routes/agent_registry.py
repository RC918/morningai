"""
Agent Registry & Task Router Routes
Issue #760 - Agent Registry & Task Router
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
from src.middleware.auth_middleware import jwt_required, roles_required
from src.middleware.rate_limit import rate_limit
from src.models.agent_registry import (
    Agent, AgentRegistrationRequest, AgentUpdateRequest,
    AgentHealth, AgentHealthReport, AgentListResponse,
    Task, TaskCreationRequest, TaskUpdateRequest, TaskListResponse,
    AgentType, AgentStatus, PermissionLevel, TaskStatus,
    Pagination, AgentStatistics
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

agents_store = {}
tasks_store = {}


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
        
        filtered_agents = list(agents_store.values())
        
        if agent_type_filter:
            try:
                agent_type = AgentType(agent_type_filter)
                filtered_agents = [a for a in filtered_agents if a.agent_type == agent_type]
            except ValueError:
                return jsonify({"error": {"code": "invalid_parameter", "message": f"Invalid agent_type: {agent_type_filter}"}}), 400
        
        if status_filter:
            try:
                status = AgentStatus(status_filter)
                filtered_agents = [a for a in filtered_agents if a.status == status]
            except ValueError:
                return jsonify({"error": {"code": "invalid_parameter", "message": f"Invalid status: {status_filter}"}}), 400
        
        if permission_level_filter:
            try:
                permission_level = PermissionLevel(permission_level_filter)
                filtered_agents = [a for a in filtered_agents if a.permission_level == permission_level]
            except ValueError:
                return jsonify({"error": {"code": "invalid_parameter", "message": f"Invalid permission_level: {permission_level_filter}"}}), 400
        
        total_items = len(filtered_agents)
        total_pages = (total_items + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_agents = filtered_agents[start_idx:end_idx]
        
        response = AgentListResponse(
            agents=paginated_agents,
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
@rate_limit
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
        
        agent = Agent(
            agent_id=agent_id,
            agent_type=validated_request.agent_type,
            status=AgentStatus.IDLE,
            permission_level=PermissionLevel.SANDBOX_ONLY,  # Start with lowest permission
            reputation_score=500,  # Start with neutral reputation
            capabilities=validated_request.capabilities,
            metadata=validated_request.metadata,
            statistics=AgentStatistics()
        )
        
        for existing_agent in agents_store.values():
            if (existing_agent.agent_type == agent.agent_type and 
                set(existing_agent.capabilities) == set(agent.capabilities)):
                return jsonify({
                    "error": {
                        "code": "agent_already_exists",
                        "message": f"Agent with type {agent.agent_type} and same capabilities already registered"
                    }
                }), 409
        
        agents_store[agent_id] = agent
        
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
        logger.error(f"Failed to register agent: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents/<agent_id>", methods=["GET"])
@jwt_required
def get_agent(agent_id):
    """Get agent details by ID"""
    try:
        agent = agents_store.get(agent_id)
        
        if not agent:
            return jsonify({"error": {"code": "not_found", "message": "Agent not found"}}), 404
        
        return jsonify(agent.model_dump(mode='json')), 200
    
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents/<agent_id>", methods=["PATCH"])
@rate_limit
@jwt_required
@roles_required("admin", "service")
def update_agent(agent_id):
    """Update agent configuration or status"""
    try:
        agent = agents_store.get(agent_id)
        
        if not agent:
            return jsonify({"error": {"code": "not_found", "message": "Agent not found"}}), 404
        
        payload = request.get_json(silent=True) or {}
        validated_request = AgentUpdateRequest(**payload)
        
        if validated_request.status is not None:
            agent.status = validated_request.status
        if validated_request.capabilities is not None:
            agent.capabilities = validated_request.capabilities
        if validated_request.metadata is not None:
            agent.metadata.update(validated_request.metadata)
        
        agent.last_activity = datetime.utcnow()
        
        logger.info(f"Updated agent {agent_id}")
        
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
        logger.error(f"Failed to update agent {agent_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents/<agent_id>", methods=["DELETE"])
@rate_limit
@jwt_required
@roles_required("admin")
def unregister_agent(agent_id):
    """Unregister an agent"""
    try:
        if agent_id not in agents_store:
            return jsonify({"error": {"code": "not_found", "message": "Agent not found"}}), 404
        
        del agents_store[agent_id]
        
        logger.info(f"Unregistered agent {agent_id}")
        
        return '', 204
    
    except Exception as e:
        logger.error(f"Failed to unregister agent {agent_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents/<agent_id>/health", methods=["GET"])
@jwt_required
def get_agent_health(agent_id):
    """Get agent health status"""
    try:
        agent = agents_store.get(agent_id)
        
        if not agent:
            return jsonify({"error": {"code": "not_found", "message": "Agent not found"}}), 404
        
        health = AgentHealth(
            agent_id=agent.agent_id,
            status=agent.status,
            last_heartbeat=agent.last_activity,
            errors=[]
        )
        
        return jsonify(health.model_dump(mode='json')), 200
    
    except Exception as e:
        logger.error(f"Failed to get agent health {agent_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/agents/<agent_id>/health", methods=["POST"])
@rate_limit
@jwt_required
def report_agent_health(agent_id):
    """Report agent health (heartbeat)"""
    try:
        agent = agents_store.get(agent_id)
        
        if not agent:
            return jsonify({"error": {"code": "not_found", "message": "Agent not found"}}), 404
        
        payload = request.get_json(silent=True) or {}
        validated_request = AgentHealthReport(**payload)
        
        agent.status = validated_request.status
        agent.last_activity = datetime.utcnow()
        
        health = AgentHealth(
            agent_id=agent.agent_id,
            status=agent.status,
            last_heartbeat=agent.last_activity,
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
        
        filtered_tasks = list(tasks_store.values())
        
        if status_filter:
            try:
                status = TaskStatus(status_filter)
                filtered_tasks = [t for t in filtered_tasks if t.status == status]
            except ValueError:
                return jsonify({"error": {"code": "invalid_parameter", "message": f"Invalid status: {status_filter}"}}), 400
        
        if agent_id_filter:
            filtered_tasks = [t for t in filtered_tasks if t.agent_id == agent_id_filter]
        
        if tenant_id_filter:
            filtered_tasks = [t for t in filtered_tasks if t.tenant_id == tenant_id_filter]
        
        total_items = len(filtered_tasks)
        total_pages = (total_items + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_tasks = filtered_tasks[start_idx:end_idx]
        
        response = TaskListResponse(
            tasks=paginated_tasks,
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
@rate_limit
@jwt_required
def create_task():
    """Create a new task and route to appropriate agent"""
    try:
        payload = request.get_json(silent=True) or {}
        validated_request = TaskCreationRequest(**payload)
        
        task_id = str(uuid.uuid4())
        
        tenant_id = validated_request.tenant_id or getattr(request, 'tenant_id', None)
        
        task = Task(
            task_id=task_id,
            status=TaskStatus.QUEUED,
            task_type=validated_request.task_type,
            payload=validated_request.payload,
            tenant_id=tenant_id
        )
        
        tasks_store[task_id] = task
        
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
        logger.error(f"Failed to create task: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/tasks/<task_id>", methods=["GET"])
@jwt_required
def get_task(task_id):
    """Get task details by ID"""
    try:
        task = tasks_store.get(task_id)
        
        if not task:
            return jsonify({"error": {"code": "not_found", "message": "Task not found"}}), 404
        
        return jsonify(task.model_dump(mode='json')), 200
    
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/tasks/<task_id>", methods=["PATCH"])
@rate_limit
@jwt_required
def update_task(task_id):
    """Update task status or metadata"""
    try:
        task = tasks_store.get(task_id)
        
        if not task:
            return jsonify({"error": {"code": "not_found", "message": "Task not found"}}), 404
        
        payload = request.get_json(silent=True) or {}
        validated_request = TaskUpdateRequest(**payload)
        
        if validated_request.status is not None:
            task.status = validated_request.status
            
            if validated_request.status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.utcnow()
            elif validated_request.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and not task.completed_at:
                task.completed_at = datetime.utcnow()
            elif validated_request.status == TaskStatus.CANCELLED and not task.cancelled_at:
                task.cancelled_at = datetime.utcnow()
        
        if validated_request.result is not None:
            task.result = validated_request.result
        
        if validated_request.error_message is not None:
            task.error_message = validated_request.error_message
        
        task.updated_at = datetime.utcnow()
        
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
        logger.error(f"Failed to update task {task_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


@bp.route("/tasks/<task_id>/cancel", methods=["POST"])
@rate_limit
@jwt_required
def cancel_task(task_id):
    """Cancel a running or queued task"""
    try:
        task = tasks_store.get(task_id)
        
        if not task:
            return jsonify({"error": {"code": "not_found", "message": "Task not found"}}), 404
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return jsonify({
                "error": {
                    "code": "cannot_cancel",
                    "message": f"Task cannot be cancelled (current status: {task.status.value})"
                }
            }), 409
        
        payload = request.get_json(silent=True) or {}
        reason = payload.get('reason', 'User requested cancellation')
        
        task.status = TaskStatus.CANCELLED
        task.cancelled_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        task.error_message = f"Cancelled: {reason}"
        
        logger.info(f"Cancelled task {task_id}: {reason}")
        
        return jsonify(task.model_dump(mode='json')), 200
    
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500
