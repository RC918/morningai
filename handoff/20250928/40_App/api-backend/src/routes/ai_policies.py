"""
AI Policies API Routes - Phase 6 PR-1

Provides CRUD endpoints for tenant-specific AI usage policies:
- GET /api/ai-policies - List policies for current tenant
- GET /api/ai-policies/<id> - Get a specific policy
- POST /api/ai-policies - Create a new policy
- PUT /api/ai-policies/<id> - Update a policy
- DELETE /api/ai-policies/<id> - Delete a policy
- GET /api/ai-policies/templates - Get policy templates for guided editor
- POST /api/ai-policies/evaluate - Evaluate if a request is allowed
"""
import os
import sys
import logging
from flask import Blueprint, jsonify, request
from src.middleware.auth_middleware import jwt_required, admin_required

# Add 40_App directory to sys.path so that 'orchestrator' package can be imported
# Path: routes -> src -> api-backend -> 40_App (3 levels up)
# IMPORTANT: There's a conflicting 'orchestrator' package at the repo root that must be
# removed from sys.modules before importing the correct one from 40_App
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

# Remove any existing orchestrator module that might be from the wrong location
# This is needed because there's a conflicting orchestrator package at the repo root
for mod_name in list(sys.modules.keys()):
    if mod_name == 'orchestrator' or mod_name.startswith('orchestrator.'):
        del sys.modules[mod_name]

# Ensure app_dir is at the very beginning of sys.path
if app_dir in sys.path:
    sys.path.remove(app_dir)
sys.path.insert(0, app_dir)

try:
    from orchestrator.governance.ai_policy import (
        PolicyType,
        PolicyScope,
        PolicyStatus,
        get_ai_policy_manager,
    )
    AI_POLICY_AVAILABLE = True
except Exception as e:
    print(f"Warning: AI Policy module not available: {e}")
    AI_POLICY_AVAILABLE = False

logger = logging.getLogger(__name__)

bp = Blueprint('ai_policies', __name__, url_prefix='/api/ai-policies')


def get_user_profile(user_id: str):
    """
    Get tenant_id, role, and is_platform_admin for a user in a single query.

    Returns:
        tuple: (tenant_id, role, is_platform_admin) or (None, None, False) if not found

    Raises:
        Exception: Re-raises database/network errors after logging
    """
    try:
        from orchestrator.persistence.db_client import get_client
        client = get_client()
        response = client.table('user_profiles').select(
            'tenant_id, role, is_platform_admin'
        ).eq('id', user_id).single().execute()
        if response.data:
            return (
                response.data.get('tenant_id'),
                response.data.get('role'),
                response.data.get('is_platform_admin', False)
            )
        return None, None, False
    except Exception:
        logger.exception(f"Failed to get profile for user {user_id}")
        raise


def get_user_tenant_id(user_id: str):
    """Get tenant_id for a user (wrapper for backward compatibility)"""
    tenant_id, _, _ = get_user_profile(user_id)
    return tenant_id


def get_user_role(user_id: str):
    """Get role for a user (wrapper for backward compatibility)"""
    _, role, _ = get_user_profile(user_id)
    return role


def is_user_platform_admin(user_id: str):
    """Check if user is a platform admin"""
    _, _, is_platform_admin = get_user_profile(user_id)
    return is_platform_admin


def _parse_policy_type(policy_type_str):
    """Parse and validate policy type string"""
    if not policy_type_str:
        return None, None
    try:
        return PolicyType(policy_type_str), None
    except ValueError:
        return None, f"Invalid policy_type: {policy_type_str}"


def _parse_policy_scope(scope_str):
    """Parse and validate policy scope string"""
    if not scope_str:
        return PolicyScope.TENANT, None
    try:
        return PolicyScope(scope_str), None
    except ValueError:
        return None, f"Invalid scope: {scope_str}"


def _parse_policy_status(status_str):
    """Parse and validate policy status string"""
    if not status_str:
        return PolicyStatus.DRAFT, None
    try:
        return PolicyStatus(status_str), None
    except ValueError:
        return None, f"Invalid status: {status_str}"


def _validate_user_context(user_id, required_roles=None):
    """
    Validate user context and return tenant_id, role, is_platform_admin, and any error.

    Platform admins bypass role checks and can access any tenant's data.
    """
    tenant_id, user_role, is_platform_admin = get_user_profile(user_id)

    if is_platform_admin:
        return tenant_id, user_role, is_platform_admin, None

    if not tenant_id:
        return None, None, False, ('Tenant not found for user', 404)

    if required_roles and user_role not in required_roles:
        return None, None, False, (
            f'Only {", ".join(required_roles)} can perform this action', 403
        )

    return tenant_id, user_role, is_platform_admin, None


def _build_policy_updates(data):
    """Build updates dict from request data, returns error tuple if invalid"""
    updates = {}
    allowed_fields = ['name', 'description', 'rules', 'priority', 'metadata']

    for field in allowed_fields:
        if field in data:
            updates[field] = data[field]

    if 'policy_type' in data:
        policy_type, err = _parse_policy_type(data['policy_type'])
        if err:
            return (err, 400)
        updates['policy_type'] = policy_type

    if 'status' in data:
        status, err = _parse_policy_status(data['status'])
        if err:
            return (err, 400)
        updates['status'] = status

    return updates


@bp.route('', methods=['GET'])
@jwt_required
def list_policies():
    """
    List AI policies for current user's tenant

    Query parameters:
    - policy_type: Filter by policy type
    - status: Filter by status (active, inactive, draft)
    - limit: Max results (default 50)
    - offset: Pagination offset (default 0)

    Returns:
        200: List of policies
        503: AI Policy system not available
    """
    if not AI_POLICY_AVAILABLE:
        return jsonify({'error': 'AI Policy system not available'}), 503

    try:
        user_id = request.user_id
        tenant_id = get_user_tenant_id(user_id)

        if not tenant_id:
            return jsonify({
                'error': 'Tenant not found for user'
            }), 404

        policy_type_str = request.args.get('policy_type')
        status_str = request.args.get('status')
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))

        policy_type, err = _parse_policy_type(policy_type_str)
        if err:
            return jsonify({'error': err}), 400

        status, err = _parse_policy_status(status_str)
        if err:
            return jsonify({'error': err}), 400

        manager = get_ai_policy_manager()
        policies = manager.list_policies(
            tenant_id=tenant_id,
            policy_type=policy_type,
            status=status,
            limit=limit,
            offset=offset
        )

        return jsonify({
            'policies': [p.to_dict() for p in policies],
            'count': len(policies),
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        logger.exception("Failed to list policies")
        return jsonify({'error': str(e)}), 500


@bp.route('/<policy_id>', methods=['GET'])
@jwt_required
def get_policy(policy_id):
    """
    Get a specific AI policy

    Args:
        policy_id: UUID of the policy

    Returns:
        200: Policy details
        404: Policy not found
        503: AI Policy system not available
    """
    if not AI_POLICY_AVAILABLE:
        return jsonify({'error': 'AI Policy system not available'}), 503

    try:
        user_id = request.user_id
        tenant_id = get_user_tenant_id(user_id)

        if not tenant_id:
            return jsonify({'error': 'Tenant not found for user'}), 404

        manager = get_ai_policy_manager()
        policy = manager.get_policy(policy_id)

        if not policy:
            return jsonify({'error': 'Policy not found'}), 404

        if policy.tenant_id != tenant_id and policy.scope != PolicyScope.PLATFORM:
            return jsonify({'error': 'Policy not found'}), 404

        return jsonify(policy.to_dict())

    except Exception as e:
        logger.exception(f"Failed to get policy {policy_id}")
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['POST'])
@jwt_required
@admin_required
def create_policy():
    """
    Create a new AI policy

    Request body:
    {
        "name": "Policy Name",
        "policy_type": "capability_whitelist",
        "rules": {...},
        "description": "Optional description",
        "priority": 0,
        "status": "draft"
    }

    Returns:
        201: Created policy
        400: Invalid request
        403: Insufficient permissions
        503: AI Policy system not available
    """
    if not AI_POLICY_AVAILABLE:
        return jsonify({'error': 'AI Policy system not available'}), 503

    try:
        user_id = request.user_id
        tenant_id, _, is_platform_admin, error = _validate_user_context(
            user_id, required_roles=['owner', 'admin']
        )
        if error:
            return jsonify({'error': error[0]}), error[1]

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        for field in ['name', 'policy_type', 'rules']:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        policy_type, err = _parse_policy_type(data['policy_type'])
        if err:
            return jsonify({'error': err}), 400

        scope, err = _parse_policy_scope(data.get('scope'))
        if err:
            return jsonify({'error': err}), 400

        status, err = _parse_policy_status(data.get('status'))
        if err:
            return jsonify({'error': err}), 400

        target_tenant_id = data.get('tenant_id', tenant_id)
        if target_tenant_id != tenant_id and not is_platform_admin:
            return jsonify({
                'error': 'Only platform admins can create policies for other tenants'
            }), 403

        manager = get_ai_policy_manager()
        policy = manager.create_policy(
            tenant_id=target_tenant_id,
            name=data['name'],
            policy_type=policy_type,
            rules=data['rules'],
            created_by=user_id,
            description=data.get('description'),
            scope=scope,
            priority=data.get('priority', 0),
            status=status,
            metadata=data.get('metadata')
        )

        if not policy:
            return jsonify({
                'error': 'Failed to persist policy to database'
            }), 503

        return jsonify(policy.to_dict()), 201

    except Exception as e:
        logger.exception("Failed to create policy")
        return jsonify({'error': str(e)}), 500


@bp.route('/<policy_id>', methods=['PUT'])
@jwt_required
@admin_required
def update_policy(policy_id):
    """
    Update an existing AI policy

    Args:
        policy_id: UUID of the policy to update

    Request body:
    {
        "name": "Updated Name",
        "rules": {...},
        "status": "active"
    }

    Returns:
        200: Updated policy
        400: Invalid request
        403: Insufficient permissions
        404: Policy not found
        503: AI Policy system not available
    """
    if not AI_POLICY_AVAILABLE:
        return jsonify({'error': 'AI Policy system not available'}), 503

    try:
        user_id = request.user_id
        tenant_id, _, is_platform_admin, error = _validate_user_context(
            user_id, required_roles=['owner', 'admin']
        )
        if error:
            return jsonify({'error': error[0]}), error[1]

        manager = get_ai_policy_manager()
        existing_policy = manager.get_policy(policy_id)

        if not existing_policy:
            return jsonify({'error': 'Policy not found'}), 404

        if existing_policy.tenant_id != tenant_id and not is_platform_admin:
            return jsonify({'error': 'Policy not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        updates = _build_policy_updates(data)
        if isinstance(updates, tuple):
            return jsonify({'error': updates[0]}), updates[1]

        updated_policy = manager.update_policy(
            policy_id=policy_id,
            updates=updates,
            updated_by=user_id
        )

        if not updated_policy:
            return jsonify({'error': 'Failed to update policy'}), 500

        return jsonify(updated_policy.to_dict())

    except Exception as e:
        logger.exception(f"Failed to update policy {policy_id}")
        return jsonify({'error': str(e)}), 500


@bp.route('/<policy_id>', methods=['DELETE'])
@jwt_required
@admin_required
def delete_policy(policy_id):
    """
    Delete an AI policy

    Args:
        policy_id: UUID of the policy to delete

    Returns:
        200: Success message
        403: Insufficient permissions (only owners or platform admins can delete)
        404: Policy not found
        503: AI Policy system not available
    """
    if not AI_POLICY_AVAILABLE:
        return jsonify({'error': 'AI Policy system not available'}), 503

    try:
        user_id = request.user_id
        tenant_id, user_role, is_platform_admin = get_user_profile(user_id)

        if not tenant_id and not is_platform_admin:
            return jsonify({'error': 'Tenant not found for user'}), 404

        if user_role != 'owner' and not is_platform_admin:
            return jsonify({
                'error': 'Only owners or platform admins can delete policies'
            }), 403

        manager = get_ai_policy_manager()
        existing_policy = manager.get_policy(policy_id)

        if not existing_policy:
            return jsonify({'error': 'Policy not found'}), 404

        if existing_policy.tenant_id != tenant_id and not is_platform_admin:
            return jsonify({'error': 'Policy not found'}), 404

        success = manager.delete_policy(policy_id, deleted_by=user_id)

        if not success:
            return jsonify({'error': 'Failed to delete policy'}), 500

        return jsonify({
            'message': 'Policy deleted successfully',
            'policy_id': policy_id
        })

    except Exception as e:
        logger.exception(f"Failed to delete policy {policy_id}")
        return jsonify({'error': str(e)}), 500


@bp.route('/templates', methods=['GET'])
@jwt_required
def get_templates():
    """
    Get policy templates for guided editor

    Returns:
        200: Dictionary of policy templates
        503: AI Policy system not available
    """
    if not AI_POLICY_AVAILABLE:
        return jsonify({'error': 'AI Policy system not available'}), 503

    try:
        manager = get_ai_policy_manager()
        templates = manager.get_policy_templates()

        return jsonify({
            'templates': templates,
            'count': len(templates)
        })

    except Exception as e:
        logger.exception("Failed to get templates")
        return jsonify({'error': str(e)}), 500


@bp.route('/evaluate', methods=['POST'])
@jwt_required
def evaluate_request():
    """
    Evaluate if a request is allowed based on tenant policies

    Request body:
    {
        "capability": "code_generation",
        "context": {...}
    }

    Returns:
        200: Evaluation result with allowed/denied and reason
        400: Invalid request
        503: AI Policy system not available
    """
    if not AI_POLICY_AVAILABLE:
        return jsonify({'error': 'AI Policy system not available'}), 503

    try:
        user_id = request.user_id
        tenant_id = get_user_tenant_id(user_id)

        if not tenant_id:
            return jsonify({'error': 'Tenant not found for user'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        if 'capability' not in data:
            return jsonify({'error': 'Missing required field: capability'}), 400

        manager = get_ai_policy_manager()
        result = manager.evaluate_request(
            tenant_id=tenant_id,
            capability=data['capability'],
            context=data.get('context')
        )

        return jsonify(result)

    except Exception as e:
        logger.exception("Failed to evaluate request")
        return jsonify({'error': str(e)}), 500
