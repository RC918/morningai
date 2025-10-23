"""Governance API Routes - Agent reputation, costs, and violations"""
from flask import Blueprint, jsonify, request
from functools import wraps
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(project_root, 'handoff/20250928/40_App/orchestrator'))

from governance import (
    get_reputation_engine,
    get_cost_tracker,
    get_permission_checker
)

governance_bp = Blueprint('governance', __name__, url_prefix='/api/governance')


def require_auth(f):
    """Simple auth decorator (placeholder)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@governance_bp.route('/agents', methods=['GET'])
def get_agents():
    """
    Get all agents with their reputation and permission levels
    
    Query params:
        - sort_by: score|level|type (default: score)
        - order: asc|desc (default: desc)
        - limit: int (default: 10)
    """
    try:
        reputation_engine = get_reputation_engine()
        
        sort_by = request.args.get('sort_by', 'score')
        order = request.args.get('order', 'desc')
        limit = int(request.args.get('limit', 10))
        
        if sort_by == 'score':
            agents = reputation_engine.get_leaderboard(limit=limit)
        else:
            supabase = reputation_engine._get_supabase()
            if not supabase:
                return jsonify({'error': 'Database unavailable'}), 503
            
            query = supabase.table('agent_reputation').select('*')
            
            if sort_by == 'level':
                query = query.order('permission_level', desc=(order == 'desc'))
            elif sort_by == 'type':
                query = query.order('agent_type', desc=(order == 'desc'))
            else:
                query = query.order('reputation_score', desc=(order == 'desc'))
            
            response = query.limit(limit).execute()
            agents = response.data if response.data else []
        
        for agent in agents:
            agent_id = agent['agent_id']
            summary = reputation_engine.get_reputation(agent_id)
            if summary:
                agent['summary'] = summary
        
        return jsonify({
            'success': True,
            'agents': agents,
            'count': len(agents)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@governance_bp.route('/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get detailed information about a specific agent"""
    try:
        reputation_engine = get_reputation_engine()
        permission_checker = get_permission_checker()
        
        summary = reputation_engine.get_reputation(agent_id)
        if not summary:
            return jsonify({'error': 'Agent not found'}), 404
        
        recent_events = reputation_engine.get_recent_events(agent_id, limit=20)
        
        permission_summary = permission_checker.get_permission_summary(agent_id)
        
        return jsonify({
            'success': True,
            'agent': {
                'summary': summary,
                'recent_events': recent_events,
                'permissions': permission_summary
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@governance_bp.route('/events', methods=['GET'])
def get_events():
    """
    Get reputation events
    
    Query params:
        - agent_id: filter by agent (optional)
        - event_type: filter by event type (optional)
        - limit: int (default: 50)
        - offset: int (default: 0)
    """
    try:
        reputation_engine = get_reputation_engine()
        supabase = reputation_engine._get_supabase()
        
        if not supabase:
            return jsonify({'error': 'Database unavailable'}), 503
        
        agent_id = request.args.get('agent_id')
        event_type = request.args.get('event_type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        query = supabase.table('reputation_events').select('*')
        
        if agent_id:
            query = query.eq('agent_id', agent_id)
        
        if event_type:
            query = query.eq('event_type', event_type)
        
        query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
        
        response = query.execute()
        events = response.data if response.data else []
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events),
            'limit': limit,
            'offset': offset
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@governance_bp.route('/costs', methods=['GET'])
def get_costs():
    """
    Get cost statistics
    
    Query params:
        - trace_id: specific trace (optional)
        - period: daily|hourly|task (default: daily)
    """
    try:
        cost_tracker = get_cost_tracker()
        
        trace_id = request.args.get('trace_id', 'global')
        period = request.args.get('period', 'daily')
        
        if period not in ['daily', 'hourly', 'task']:
            return jsonify({'error': 'Invalid period. Must be daily, hourly, or task'}), 400
        
        status = cost_tracker.get_budget_status(trace_id, period=period)
        
        return jsonify({
            'success': True,
            'cost_status': status
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@governance_bp.route('/violations', methods=['GET'])
def get_violations():
    """
    Get violation events
    
    Query params:
        - agent_id: filter by agent (optional)
        - limit: int (default: 50)
    """
    try:
        reputation_engine = get_reputation_engine()
        supabase = reputation_engine._get_supabase()
        
        if not supabase:
            return jsonify({'error': 'Database unavailable'}), 503
        
        agent_id = request.args.get('agent_id')
        limit = int(request.args.get('limit', 50))
        
        query = supabase.table('reputation_events').select('*').eq('event_type', 'violation_detected')
        
        if agent_id:
            query = query.eq('agent_id', agent_id)
        
        query = query.order('created_at', desc=True).limit(limit)
        
        response = query.execute()
        violations = response.data if response.data else []
        
        return jsonify({
            'success': True,
            'violations': violations,
            'count': len(violations)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@governance_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get overall governance statistics"""
    try:
        reputation_engine = get_reputation_engine()
        
        stats = reputation_engine.get_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@governance_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get agent reputation leaderboard"""
    try:
        reputation_engine = get_reputation_engine()
        
        limit = int(request.args.get('limit', 10))
        
        leaderboard = reputation_engine.get_leaderboard(limit=limit)
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard,
            'count': len(leaderboard)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def register_governance_routes(app):
    """Register governance blueprint with Flask app"""
    app.register_blueprint(governance_bp)
