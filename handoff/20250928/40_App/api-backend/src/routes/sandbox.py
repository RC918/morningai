import os
import sys
import logging
import uuid
import subprocess
from datetime import datetime
from flask import Blueprint, jsonify, request
from src.middleware.auth_middleware import jwt_required, roles_required

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

bp = Blueprint("sandbox", __name__, url_prefix="/api/sandbox")

sandbox_processes = {}
sandbox_logs = {}

@bp.route("/run", methods=["POST"])
def run_sandbox_task():
    """
    Start a sandbox task using subprocess (MVP implementation)
    Future: will use Docker containers when SANDBOX_ENABLED=true
    """
    payload = request.get_json(silent=True) or {}
    
    agent_id = payload.get("agent_id")
    agent_type = payload.get("agent_type", "ops_agent")
    command = payload.get("command")
    
    if not agent_id or not command:
        return jsonify({
            "error": {
                "code": "invalid_input",
                "message": "agent_id and command are required"
            }
        }), 400
    
    sandbox_id = str(uuid.uuid4())
    
    try:
        cpu_limit = payload.get("cpu_limit", 1.0)
        memory_limit_mb = payload.get("memory_limit_mb", 2048)
        timeout_seconds = payload.get("timeout_seconds", 300)
        
        logger.info(f"Starting sandbox {sandbox_id} for agent {agent_id}")
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        sandbox_processes[sandbox_id] = {
            "process": process,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "command": command,
            "started_at": datetime.utcnow().isoformat(),
            "timeout": timeout_seconds,
            "status": "running"
        }
        
        sandbox_logs[sandbox_id] = {
            "stdout": "",
            "stderr": "",
            "trace_id": sandbox_id
        }
        
        return jsonify({
            "sandbox_id": sandbox_id,
            "status": "running",
            "agent_id": agent_id,
            "started_at": sandbox_processes[sandbox_id]["started_at"],
            "timeout_seconds": timeout_seconds
        }), 202
        
    except Exception as e:
        logger.error(f"Failed to start sandbox {sandbox_id}: {e}")
        return jsonify({
            "error": {
                "code": "sandbox_start_failed",
                "message": str(e)
            }
        }), 500

@bp.route("/stop/<sandbox_id>", methods=["POST"])
def stop_sandbox_task(sandbox_id):
    """Stop a running sandbox task"""
    if sandbox_id not in sandbox_processes:
        return jsonify({
            "error": {
                "code": "sandbox_not_found",
                "message": f"Sandbox {sandbox_id} not found"
            }
        }), 404
    
    try:
        sandbox = sandbox_processes[sandbox_id]
        process = sandbox["process"]
        
        if sandbox["status"] == "stopped":
            return jsonify({
                "sandbox_id": sandbox_id,
                "status": "already_stopped"
            }), 200
        
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        sandbox["status"] = "stopped"
        sandbox["stopped_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Stopped sandbox {sandbox_id}")
        
        return jsonify({
            "sandbox_id": sandbox_id,
            "status": "stopped",
            "stopped_at": sandbox["stopped_at"]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to stop sandbox {sandbox_id}: {e}")
        return jsonify({
            "error": {
                "code": "sandbox_stop_failed",
                "message": str(e)
            }
        }), 500

@bp.route("/logs/<sandbox_id>", methods=["GET"])
def get_sandbox_logs(sandbox_id):
    """Get logs from a sandbox task"""
    if sandbox_id not in sandbox_processes:
        return jsonify({
            "error": {
                "code": "sandbox_not_found",
                "message": f"Sandbox {sandbox_id} not found"
            }
        }), 404
    
    try:
        sandbox = sandbox_processes[sandbox_id]
        process = sandbox["process"]
        
        stdout_data = ""
        stderr_data = ""
        
        if process.poll() is not None:
            if process.stdout:
                stdout_data = process.stdout.read()
            if process.stderr:
                stderr_data = process.stderr.read()
        
        if sandbox_id in sandbox_logs:
            sandbox_logs[sandbox_id]["stdout"] += stdout_data
            sandbox_logs[sandbox_id]["stderr"] += stderr_data
        
        return_code = process.poll()
        
        return jsonify({
            "sandbox_id": sandbox_id,
            "status": "running" if return_code is None else "completed",
            "return_code": return_code,
            "stdout": sandbox_logs.get(sandbox_id, {}).get("stdout", ""),
            "stderr": sandbox_logs.get(sandbox_id, {}).get("stderr", ""),
            "trace_id": sandbox_id
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get logs for sandbox {sandbox_id}: {e}")
        return jsonify({
            "error": {
                "code": "log_retrieval_failed",
                "message": str(e)
            }
        }), 500

@bp.route("/status/<sandbox_id>", methods=["GET"])
def get_sandbox_status(sandbox_id):
    """Get status of a sandbox task"""
    if sandbox_id not in sandbox_processes:
        return jsonify({
            "error": {
                "code": "sandbox_not_found",
                "message": f"Sandbox {sandbox_id} not found"
            }
        }), 404
    
    sandbox = sandbox_processes[sandbox_id]
    process = sandbox["process"]
    return_code = process.poll()
    
    return jsonify({
        "sandbox_id": sandbox_id,
        "agent_id": sandbox["agent_id"],
        "agent_type": sandbox["agent_type"],
        "status": "running" if return_code is None else "completed",
        "return_code": return_code,
        "started_at": sandbox["started_at"],
        "stopped_at": sandbox.get("stopped_at")
    }), 200

@bp.route("/list", methods=["GET"])
@jwt_required
@roles_required("analyst", "admin")
def list_sandboxes():
    """List all sandbox tasks (requires auth)"""
    sandboxes = []
    for sandbox_id, sandbox in sandbox_processes.items():
        process = sandbox["process"]
        return_code = process.poll()
        
        sandboxes.append({
            "sandbox_id": sandbox_id,
            "agent_id": sandbox["agent_id"],
            "agent_type": sandbox["agent_type"],
            "status": "running" if return_code is None else "completed",
            "return_code": return_code,
            "started_at": sandbox["started_at"]
        })
    
    return jsonify({
        "sandboxes": sandboxes,
        "total_count": len(sandboxes)
    }), 200
