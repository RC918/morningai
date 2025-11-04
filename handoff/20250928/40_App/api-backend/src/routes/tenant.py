"""
Tenant API Routes - Phase 3: RLS Full Tenant Isolation
Provides endpoints for tenant management and member access
"""
import os
import logging
from flask import Blueprint, jsonify, request
from src.middleware.auth_middleware import jwt_required
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

logger = logging.getLogger(__name__)

bp = Blueprint("tenant", __name__, url_prefix="/api/tenant")


class UpdateMemberRoleRequest(BaseModel):
    """Request model for updating member role"""
    role: str = Field(..., description="New role for the member")
    
    class Config:
        extra = "forbid"


def get_supabase_client():
    """Get Supabase client instance"""
    try:
        from orchestrator.persistence.db_client import get_client
        return get_client()
    except Exception as e:
        logger.error(f"Failed to get Supabase client: {e}")
        raise


@bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user_tenant():
    """
    Get current user's tenant information
    
    Returns:
        200: Tenant info (id, name)
        404: User profile not found
        500: Server error
    """
    try:
        user_id = request.user_id
        client = get_supabase_client()
        
        response = client.table("user_profiles") \
            .select("tenant_id, tenants(id, name, created_at)") \
            .eq("id", user_id) \
            .single() \
            .execute()
        
        if not response.data:
            return jsonify({
                "error": {
                    "code": "profile_not_found",
                    "message": "User profile not found. Please contact support."
                }
            }), 404
        
        tenant_data = response.data.get("tenants")
        
        if not tenant_data:
            return jsonify({
                "error": {
                    "code": "tenant_not_found",
                    "message": "Tenant information not found"
                }
            }), 404
        
        return jsonify({
            "tenant_id": tenant_data["id"],
            "tenant_name": tenant_data["name"],
            "created_at": tenant_data.get("created_at")
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to get tenant for user {request.user_id}: {e}")
        return jsonify({
            "error": {
                "code": "server_error",
                "message": "Failed to retrieve tenant information"
            }
        }), 500


@bp.route("/members", methods=["GET"])
@jwt_required
def get_tenant_members():
    """
    Get list of members in current user's tenant
    
    Query params:
        - limit: Max number of results (default 50)
        - offset: Pagination offset (default 0)
    
    Returns:
        200: List of members with profile info
        500: Server error
    """
    try:
        user_id = request.user_id
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
        
        limit = min(limit, 100)
        
        client = get_supabase_client()
        
        user_response = client.table("user_profiles") \
            .select("tenant_id") \
            .eq("id", user_id) \
            .single() \
            .execute()
        
        if not user_response.data:
            return jsonify({
                "error": {
                    "code": "profile_not_found",
                    "message": "User profile not found"
                }
            }), 404
        
        tenant_id = user_response.data["tenant_id"]
        
        members_response = client.table("user_profiles") \
            .select("id, display_name, role, created_at") \
            .eq("tenant_id", tenant_id) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        members = members_response.data or []
        
        for member in members:
            try:
                auth_response = client.auth.admin.get_user_by_id(member["id"])
                if auth_response and hasattr(auth_response, 'user'):
                    member["email"] = auth_response.user.email
                else:
                    member["email"] = None
            except Exception as e:
                logger.warning(f"Failed to fetch email for user {member['id']}: {e}")
                member["email"] = None
        
        count_response = client.table("user_profiles") \
            .select("id", count="exact") \
            .eq("tenant_id", tenant_id) \
            .execute()
        
        total_count = count_response.count if hasattr(count_response, 'count') else len(members)
        
        return jsonify({
            "members": members,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }), 200
    
    except ValueError as e:
        return jsonify({
            "error": {
                "code": "invalid_parameters",
                "message": "Invalid limit or offset parameter"
            }
        }), 400
    except Exception as e:
        logger.error(f"Failed to get tenant members for user {request.user_id}: {e}")
        return jsonify({
            "error": {
                "code": "server_error",
                "message": "Failed to retrieve tenant members"
            }
        }), 500


@bp.route("/members/<member_id>", methods=["PUT"])
@jwt_required
def update_member_role(member_id):
    """
    Update a member's role within the tenant
    
    Requires: Current user must be owner or admin
    
    Args:
        member_id: UUID of member to update
    
    Body:
        {
            "role": "owner" | "admin" | "member" | "viewer"
        }
    
    Returns:
        200: Member updated successfully
        400: Invalid request
        403: Insufficient permissions
        404: Member not found
        500: Server error
    """
    try:
        payload = request.get_json(silent=True) or {}
        validated_request = UpdateMemberRoleRequest(**payload)
        new_role = validated_request.role
        
        if new_role not in ["owner", "admin", "member", "viewer"]:
            return jsonify({
                "error": {
                    "code": "invalid_role",
                    "message": "Role must be one of: owner, admin, member, viewer"
                }
            }), 400
    
    except ValidationError as e:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "Invalid request body",
                "details": e.errors()
            }
        }), 400
    
    try:
        user_id = request.user_id
        client = get_supabase_client()
        
        current_user_response = client.table("user_profiles") \
            .select("tenant_id, role") \
            .eq("id", user_id) \
            .single() \
            .execute()
        
        if not current_user_response.data:
            return jsonify({
                "error": {
                    "code": "profile_not_found",
                    "message": "User profile not found"
                }
            }), 404
        
        current_user_role = current_user_response.data["role"]
        tenant_id = current_user_response.data["tenant_id"]
        
        if current_user_role not in ["owner", "admin"]:
            return jsonify({
                "error": {
                    "code": "insufficient_permissions",
                    "message": "Only owners and admins can update member roles"
                }
            }), 403
        
        member_response = client.table("user_profiles") \
            .select("tenant_id, role") \
            .eq("id", member_id) \
            .single() \
            .execute()
        
        if not member_response.data:
            return jsonify({
                "error": {
                    "code": "member_not_found",
                    "message": "Member not found"
                }
            }), 404
        
        if member_response.data["tenant_id"] != tenant_id:
            return jsonify({
                "error": {
                    "code": "member_not_in_tenant",
                    "message": "Member does not belong to your tenant"
                }
            }), 403
        
        update_response = client.table("user_profiles") \
            .update({"role": new_role}) \
            .eq("id", member_id) \
            .execute()
        
        if not update_response.data:
            raise Exception("Update failed - no data returned")
        
        return jsonify({
            "message": "Member role updated successfully",
            "member_id": member_id,
            "new_role": new_role
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to update member {member_id} role: {e}")
        return jsonify({
            "error": {
                "code": "server_error",
                "message": "Failed to update member role"
            }
        }), 500


@bp.route("/info", methods=["GET"])
@jwt_required
def get_tenant_info():
    """
    Get detailed tenant information
    
    Returns:
        200: Tenant details (id, name, member count, created_at)
        404: Tenant not found
        500: Server error
    """
    try:
        user_id = request.user_id
        client = get_supabase_client()
        
        user_response = client.table("user_profiles") \
            .select("tenant_id") \
            .eq("id", user_id) \
            .single() \
            .execute()
        
        if not user_response.data:
            return jsonify({
                "error": {
                    "code": "profile_not_found",
                    "message": "User profile not found"
                }
            }), 404
        
        tenant_id = user_response.data["tenant_id"]
        
        tenant_response = client.table("tenants") \
            .select("id, name, created_at, updated_at") \
            .eq("id", tenant_id) \
            .single() \
            .execute()
        
        if not tenant_response.data:
            return jsonify({
                "error": {
                    "code": "tenant_not_found",
                    "message": "Tenant not found"
                }
            }), 404
        
        member_count_response = client.table("user_profiles") \
            .select("id", count="exact") \
            .eq("tenant_id", tenant_id) \
            .execute()
        
        member_count = member_count_response.count if hasattr(member_count_response, 'count') else 0
        
        task_count_response = client.table("agent_tasks") \
            .select("task_id", count="exact") \
            .eq("tenant_id", tenant_id) \
            .execute()
        
        task_count = task_count_response.count if hasattr(task_count_response, 'count') else 0
        
        return jsonify({
            "tenant_id": tenant_response.data["id"],
            "tenant_name": tenant_response.data["name"],
            "member_count": member_count,
            "task_count": task_count,
            "created_at": tenant_response.data.get("created_at"),
            "updated_at": tenant_response.data.get("updated_at")
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to get tenant info for user {request.user_id}: {e}")
        return jsonify({
            "error": {
                "code": "server_error",
                "message": "Failed to retrieve tenant information"
            }
        }), 500
