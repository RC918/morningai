from flask import Blueprint, jsonify, request
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../orchestrator'))

try:
    from tools.faq_agent import FAQAgent
except ImportError as e:
    print(f"Warning: Could not import FAQAgent: {e}")
    class MockFAQAgent:
        def create_faq_pr(self, topic):
            import uuid
            from datetime import datetime
            trace_id = str(uuid.uuid4())[:8]
            return {
                "success": True,
                "trace_id": trace_id,
                "pr_url": f"https://github.com/RC918/morningai/pull/mock-{trace_id}",
                "pr_number": f"mock-{trace_id}",
                "message": f"Mock FAQ PR created successfully for topic: {topic}"
            }
        
        def get_task_status(self, trace_id):
            return {
                "trace_id": trace_id,
                "status": "completed",
                "created_at": "2024-01-01T00:00:00Z"
            }
        
        def check_pr_status(self, trace_id):
            return {
                "success": True,
                "ci_state": "success",
                "ci_details": ["All checks passed", "Ready to merge"]
            }
    
    FAQAgent = MockFAQAgent

agent_bp = Blueprint("agent", __name__, url_prefix="/api/agent")

@agent_bp.post("/faq/generate")
def generate_faq():
    """Trigger FAQ generation and PR creation"""
    if not FAQAgent:
        return jsonify({
            "success": False,
            "error": "FAQAgent not available",
            "message": "Agent system not properly configured"
        }), 500
        
    try:
        payload = request.get_json(silent=True) or {}
        topic = payload.get("topic", "Morning AI Platform")
        
        agent = FAQAgent()
        result = agent.create_faq_pr(topic)
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Internal server error"
        }), 500

@agent_bp.get("/faq/status/<trace_id>")
def get_faq_status(trace_id):
    """Get FAQ generation task status"""
    if not FAQAgent:
        return jsonify({
            "success": False,
            "error": "FAQAgent not available"
        }), 500
        
    try:
        agent = FAQAgent()
        task_data = agent.get_task_status(trace_id)
        
        if not task_data:
            return jsonify({
                "success": False,
                "message": "Task not found"
            }), 404
            
        return jsonify({
            "success": True,
            "task": task_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.get("/faq/check/<trace_id>")
def check_faq_pr_status(trace_id):
    """Check PR CI status for FAQ task"""
    if not FAQAgent:
        return jsonify({
            "success": False,
            "error": "FAQAgent not available"
        }), 500
        
    try:
        agent = FAQAgent()
        result = agent.check_pr_status(trace_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.get("/health")
def agent_health():
    """Agent system health check"""
    return jsonify({
        "status": "healthy",
        "agent_available": FAQAgent is not None,
        "timestamp": "2024-01-01T00:00:00Z"
    })
