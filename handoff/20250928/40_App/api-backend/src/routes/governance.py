"""Governance API - Agent reputation, cost tracking, and policy management"""
import os
import sys
from flask import Blueprint, jsonify, request
from functools import wraps

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

governance_path = os.path.join(project_root, 'handoff/20250928/40_App/orchestrator')
if governance_path not in sys.path:
    sys.path.insert(0, governance_path)

try:
    from governance import (
        get_cost_tracker,
        get_reputation_engine,
        get_permission_checker,
        get_violation_detector
    )
    GOVERNANCE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Governance modules not available: {e}")
    GOVERNANCE_AVAILABLE = False

bp = Blueprint('governance', __name__, url_prefix='/api/governance')


def require_auth(f):
    """Authentication decorator (placeholder - integrate with existing JWT middleware)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/agents', methods=['GET'])
def get_agents():
    """Get all agents with their reputation scores"""
    if not GOVERNANCE_AVAILABLE:
        return jsonify({'error': 'Governance system not available'}), 503
    
    try:
        reputation_engine = get_reputation_engine()
        agents = reputation_engine.get_leaderboard(limit=100)
        
        return jsonify({
            'agents': agents,
            'count': len(agents)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/agents/<agent_id>', methods=['GET'])
def get_agent_details(agent_id):
    """Get detailed information about a specific agent"""
    if not GOVERNANCE_AVAILABLE:
        return jsonify({'error': 'Governance system not available'}), 503
    
    try:
        reputation_engine = get_reputation_engine()
        permission_checker = get_permission_checker()
        
        reputation = reputation_engine.get_reputation(agent_id)
        if not reputation:
            return jsonify({'error': 'Agent not found'}), 404
        
        permission_summary = permission_checker.get_permission_summary(agent_id)
        recent_events = reputation_engine.get_recent_events(agent_id, limit=20)
        
        return jsonify({
            'agent_id': agent_id,
            'reputation': reputation,
            'permissions': permission_summary,
            'recent_events': recent_events
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/events', methods=['GET'])
def get_events():
    """Get reputation events history"""
    if not GOVERNANCE_AVAILABLE:
        return jsonify({'error': 'Governance system not available'}), 503
    
    try:
        agent_id = request.args.get('agent_id')
        limit = int(request.args.get('limit', 50))
        
        reputation_engine = get_reputation_engine()
        
        if agent_id:
            events = reputation_engine.get_recent_events(agent_id, limit=limit)
        else:
            supabase = reputation_engine._get_supabase()
            if not supabase:
                return jsonify({'error': 'Database not available'}), 503
            
            response = supabase.table('reputation_events') \
                .select('*') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            events = response.data if response.data else []
        
        return jsonify({
            'events': events,
            'count': len(events)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/costs', methods=['GET'])
def get_costs():
    """Get cost tracking statistics"""
    if not GOVERNANCE_AVAILABLE:
        return jsonify({'error': 'Governance system not available'}), 503
    
    try:
        trace_id = request.args.get('trace_id', 'system')
        period = request.args.get('period', 'daily')
        
        cost_tracker = get_cost_tracker()
        
        if period == 'all':
            cost_summary = cost_tracker.get_cost_summary(trace_id)
            return jsonify(cost_summary)
        else:
            budget_status = cost_tracker.get_budget_status(trace_id, period)
            return jsonify(budget_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/violations', methods=['GET'])
def get_violations():
    """Get policy violation records"""
    if not GOVERNANCE_AVAILABLE:
        return jsonify({'error': 'Governance system not available'}), 503
    
    try:
        violation_detector = get_violation_detector()
        
        agent_id = request.args.get('agent_id')
        limit = int(request.args.get('limit', 50))
        
        violations = violation_detector.get_recent_violations(
            agent_id=agent_id,
            limit=limit
        )
        
        return jsonify({
            'violations': violations,
            'count': len(violations)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get overall governance system statistics"""
    if not GOVERNANCE_AVAILABLE:
        return jsonify({'error': 'Governance system not available'}), 503
    
    try:
        reputation_engine = get_reputation_engine()
        cost_tracker = get_cost_tracker()
        
        reputation_stats = reputation_engine.get_statistics()
        cost_summary = cost_tracker.get_cost_summary('system')
        
        return jsonify({
            'reputation': reputation_stats,
            'costs': cost_summary,
            'timestamp': cost_summary.get('daily', {}).get('usage', {})
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get agent reputation leaderboard"""
    if not GOVERNANCE_AVAILABLE:
        return jsonify({'error': 'Governance system not available'}), 503
    
    try:
        limit = int(request.args.get('limit', 10))
        
        reputation_engine = get_reputation_engine()
        leaderboard = reputation_engine.get_leaderboard(limit=limit)
        
        return jsonify({
            'leaderboard': leaderboard,
            'count': len(leaderboard)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check for governance system"""
    try:
        status = {
            'governance_available': GOVERNANCE_AVAILABLE,
            'components': {}
        }
        
        if GOVERNANCE_AVAILABLE:
            try:
                cost_tracker = get_cost_tracker()
                status['components']['cost_tracker'] = 'available' if cost_tracker.redis else 'degraded'
            except:
                status['components']['cost_tracker'] = 'unavailable'
            
            try:
                reputation_engine = get_reputation_engine()
                supabase = reputation_engine._get_supabase()
                status['components']['reputation_engine'] = 'available' if supabase else 'degraded'
            except:
                status['components']['reputation_engine'] = 'unavailable'
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
