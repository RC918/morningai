import os
import logging
from flask import Blueprint, jsonify, request
from src.middleware.auth_middleware import jwt_required, roles_required

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

bp = Blueprint("mcp", __name__, url_prefix="/api/mcp")

TOOL_REGISTRY = {
    "shell": {
        "name": "shell",
        "description": "Execute bash commands in sandbox",
        "permissions": ["execute_commands"],
        "approval_required_patterns": [
            "rm -rf", "dd if=", "mkfs", ":(){:|:&};:", "chmod 777", "chown root"
        ],
        "implementation": "handoff/20250928/40_App/orchestrator/mcp/tools/shell_tool.py"
    },
    "browser": {
        "name": "browser",
        "description": "Automated browser interactions via Playwright",
        "permissions": ["web_access", "browser_automation"],
        "approval_required_patterns": [],
        "implementation": "handoff/20250928/40_App/orchestrator/mcp/tools/browser_tool.py"
    },
    "render": {
        "name": "render",
        "description": "Interact with Render deployment API",
        "permissions": ["api_access", "deployment_control"],
        "approval_required_patterns": ["deploy", "restart", "scale"],
        "implementation": "handoff/20250928/40_App/orchestrator/mcp/tools/render_tool.py"
    },
    "sentry": {
        "name": "sentry",
        "description": "Query and manage Sentry error tracking",
        "permissions": ["api_access", "error_monitoring"],
        "approval_required_patterns": [],
        "implementation": "handoff/20250928/40_App/orchestrator/mcp/tools/sentry_tool.py"
    }
}

@bp.route("/tools", methods=["GET"])
def list_tools():
    """List all available MCP tools with their permissions"""
    return jsonify({
        "tools": list(TOOL_REGISTRY.values()),
        "total_count": len(TOOL_REGISTRY)
    }), 200

@bp.route("/tools/<tool_name>", methods=["GET"])
def get_tool(tool_name):
    """Get details for a specific tool"""
    if tool_name not in TOOL_REGISTRY:
        return jsonify({
            "error": {
                "code": "tool_not_found",
                "message": f"Tool '{tool_name}' not found"
            }
        }), 404
    
    return jsonify(TOOL_REGISTRY[tool_name]), 200

@bp.route("/tools/<tool_name>/validate", methods=["POST"])
def validate_tool_invocation(tool_name):
    """Validate if a tool invocation requires approval"""
    if tool_name not in TOOL_REGISTRY:
        return jsonify({
            "error": {
                "code": "tool_not_found",
                "message": f"Tool '{tool_name}' not found"
            }
        }), 404
    
    payload = request.get_json(silent=True) or {}
    tool_config = TOOL_REGISTRY[tool_name]
    
    requires_approval = False
    matched_pattern = None
    
    if tool_name == "shell":
        command = payload.get("command", "")
        for pattern in tool_config["approval_required_patterns"]:
            if pattern in command:
                requires_approval = True
                matched_pattern = pattern
                break
    elif tool_name == "render":
        action = payload.get("action", "")
        if action in tool_config["approval_required_patterns"]:
            requires_approval = True
            matched_pattern = action
    
    return jsonify({
        "tool_name": tool_name,
        "requires_approval": requires_approval,
        "matched_pattern": matched_pattern,
        "invocation": payload
    }), 200

@bp.route("/whitelist", methods=["GET"])
@jwt_required
@roles_required("analyst", "admin")
def get_whitelist():
    """Get permission whitelist configuration"""
    return jsonify({
        "whitelisted_tools": list(TOOL_REGISTRY.keys()),
        "total_tools": len(TOOL_REGISTRY),
        "permission_model": "explicit_whitelist",
        "approval_gate": "hitl_required_for_high_risk"
    }), 200

@bp.route("/register", methods=["POST"])
@jwt_required
@roles_required("admin")
def register_tool():
    """
    Document tool registration endpoint (future: dynamic tool registration)
    Currently returns existing tool registry
    """
    return jsonify({
        "message": "Tool registration endpoint - currently documenting existing tools",
        "registered_tools": list(TOOL_REGISTRY.keys()),
        "note": "Dynamic tool registration will be implemented in future sprint"
    }), 200
