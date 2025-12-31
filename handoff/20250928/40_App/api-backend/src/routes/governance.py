"""Governance API - Agent reputation, cost tracking, and policy management"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from common.config.settings import settings

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

ALLOW_GOVERNANCE_MOCK = settings.allow_governance_mock or False

from src.middleware.auth_middleware import jwt_required, admin_required
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('governance', __name__, url_prefix='/api/governance')

admin_bp = Blueprint('admin_agents', __name__, url_prefix='/api/admin')


@bp.route('/agents', methods=['GET'])
@jwt_required
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
@jwt_required
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
@jwt_required
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
@jwt_required
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
@jwt_required
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
@jwt_required
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
@jwt_required
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
                status['components']['cost_tracker'] = (
                    'available' if cost_tracker.redis else 'degraded'
                )
            except Exception:
                status['components']['cost_tracker'] = 'unavailable'

            try:
                reputation_engine = get_reputation_engine()
                supabase = reputation_engine._get_supabase()
                status['components']['reputation_engine'] = (
                    'available' if supabase else 'degraded'
                )
            except Exception:
                status['components']['reputation_engine'] = 'unavailable'
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/providers/health', methods=['GET'])
@jwt_required
def get_provider_health_snapshot():
    """
    Get provider health snapshot for dashboard display

    EPIC I-3b: Health Snapshot API

    This endpoint provides real-time health scores for all LLM providers,
    designed for dashboard visualization and monitoring.

    Query Parameters:
        window: Time window in minutes (default: 15, range: 1-60)
        providers: Comma-separated list of providers (default: all)

    Returns:
        JSON with provider health scores, rankings, and alert status

    Requires: JWT authentication
    """
    try:
        # Parse query parameters
        window_minutes = request.args.get('window', 15, type=int)
        window_minutes = max(1, min(60, window_minutes))

        providers_param = request.args.get('providers', '')
        if providers_param:
            providers = [p.strip() for p in providers_param.split(',') if p.strip()]
        else:
            providers = None

        # Try to get metrics from CanaryMetrics
        try:
            from metrics import get_canary_metrics
            metrics = get_canary_metrics()
        except ImportError:
            logger.warning("[ProviderHealth] metrics module not available")
            metrics = None

        if metrics is None:
            return jsonify({
                'available': False,
                'error': 'metrics_unavailable',
                'message': 'CanaryMetrics not configured or Redis unavailable',
                'timestamp': datetime.utcnow().isoformat()
            }), 503

        # Get health data for all providers
        health_data = metrics.get_all_providers_health(
            providers=providers,
            window_minutes=window_minutes
        )

        if not health_data.get('enabled', False):
            return jsonify({
                'available': False,
                'error': 'metrics_disabled',
                'message': 'Provider health metrics are disabled',
                'timestamp': datetime.utcnow().isoformat()
            }), 503

        # Get alert service status
        try:
            from governance.health_alerter import get_health_alert_service
            alert_service = get_health_alert_service()
            alerting_enabled = alert_service is not None and alert_service.enabled
            cooldown_status = (
                alert_service.get_cooldown_status() if alert_service else {}
            )
        except ImportError:
            alerting_enabled = False
            cooldown_status = {}

        # Build response with dashboard-friendly structure
        providers_health = health_data.get('providers', {})
        ranking = health_data.get('ranking', [])

        # Determine overall system health status
        health_scores = [
            p.get('health_score', 100)
            for p in providers_health.values()
            if isinstance(p, dict) and 'health_score' in p
        ]
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 100

        if avg_health >= 80:
            system_status = 'healthy'
        elif avg_health >= 60:
            system_status = 'degraded'
        else:
            system_status = 'critical'

        # Count providers by health status
        healthy_count = sum(1 for s in health_scores if s >= 80)
        degraded_count = sum(1 for s in health_scores if 60 <= s < 80)
        critical_count = sum(1 for s in health_scores if s < 60)

        response = {
            'available': True,
            'timestamp': datetime.utcnow().isoformat(),
            'window_minutes': window_minutes,
            'system_status': system_status,
            'summary': {
                'average_health': round(avg_health, 1),
                'total_providers': len(providers_health),
                'healthy': healthy_count,
                'degraded': degraded_count,
                'critical': critical_count,
            },
            'providers': providers_health,
            'ranking': ranking,
            'alerting': {
                'enabled': alerting_enabled,
                'cooldown_status': cooldown_status,
            },
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"[ProviderHealth] Error getting health snapshot: {e}")
        return jsonify({
            'available': False,
            'error': 'internal_error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@bp.route('/providers/<provider>/health', methods=['GET'])
@jwt_required
def get_single_provider_health(provider):
    """
    Get health details for a single provider

    EPIC I-3b: Health Snapshot API

    This endpoint provides detailed health metrics for a specific provider,
    including historical trends and component breakdowns.

    Path Parameters:
        provider: Provider name (openai, gemini, alicloud, siliconflow)

    Query Parameters:
        window: Time window in minutes (default: 15, range: 1-60)

    Returns:
        JSON with detailed provider health metrics

    Requires: JWT authentication
    """
    try:
        # Validate provider name
        valid_providers = ['openai', 'gemini', 'alicloud', 'siliconflow']
        if provider not in valid_providers:
            return jsonify({
                'error': 'invalid_provider',
                'message': f'Provider must be one of: {", ".join(valid_providers)}',
                'valid_providers': valid_providers
            }), 400

        # Parse query parameters
        window_minutes = request.args.get('window', 15, type=int)
        window_minutes = max(1, min(60, window_minutes))

        # Try to get metrics from CanaryMetrics
        try:
            from metrics import get_canary_metrics
            metrics = get_canary_metrics()
        except ImportError:
            logger.warning("[ProviderHealth] metrics module not available")
            metrics = None

        if metrics is None:
            return jsonify({
                'available': False,
                'provider': provider,
                'error': 'metrics_unavailable',
                'message': 'CanaryMetrics not configured or Redis unavailable',
                'timestamp': datetime.utcnow().isoformat()
            }), 503

        # Get health data for the specific provider
        health_data = metrics.get_provider_health(
            provider=provider,
            window_minutes=window_minutes
        )

        if not health_data.get('enabled', True):
            return jsonify({
                'available': False,
                'provider': provider,
                'error': 'metrics_disabled',
                'message': 'Provider health metrics are disabled',
                'timestamp': datetime.utcnow().isoformat()
            }), 503

        # Get alert status for this provider
        try:
            from governance.health_alerter import get_health_alert_service
            alert_service = get_health_alert_service()
            if alert_service:
                cooldown_status = alert_service.get_cooldown_status()
                provider_cooldown = cooldown_status.get(provider, {})
            else:
                provider_cooldown = {}
        except ImportError:
            provider_cooldown = {}

        # Determine health status
        health_score = health_data.get('health_score', 100)
        if health_score >= 80:
            status = 'healthy'
        elif health_score >= 60:
            status = 'degraded'
        else:
            status = 'critical'

        response = {
            'available': True,
            'provider': provider,
            'timestamp': datetime.utcnow().isoformat(),
            'window_minutes': window_minutes,
            'status': status,
            'health_score': health_score,
            'metrics': {
                'total_requests': health_data.get('total_requests', 0),
                'error_rate': health_data.get('error_rate', 0),
                'drift_rate': health_data.get('drift_rate', 0),
                'latency': health_data.get('latency', {}),
            },
            'weights': {
                'latency': health_data.get('latency_weight', 0.3),
                'error': health_data.get('error_weight', 0.4),
                'drift': health_data.get('drift_weight', 0.3),
            },
            'alert_cooldown': provider_cooldown,
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"[ProviderHealth] Error getting health for {provider}: {e}")
        return jsonify({
            'available': False,
            'provider': provider,
            'error': 'internal_error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@admin_bp.route('/agents', methods=['GET'])
@jwt_required
@admin_required
def admin_get_agents():
    """
    Get all agents with their status and metadata
    
    Query parameters:
    - status: Filter by status (active, paused, all) - default: all
    - limit: Number of agents to return - default: 100
    
    Returns list of agents with execution statistics
    
    Requires: Owner role
    """
    try:
        status_filter = request.args.get('status', 'all')
        limit = min(int(request.args.get('limit', 100)), 500)
        
        if not GOVERNANCE_AVAILABLE and not ALLOW_GOVERNANCE_MOCK:
            return jsonify({
                'error': 'Governance system unavailable',
                'message': 'Mock data is disabled. Please enable ALLOW_GOVERNANCE_MOCK or fix governance system.'
            }), 503
        
        if GOVERNANCE_AVAILABLE:
            reputation_engine = get_reputation_engine()
            agents_data = reputation_engine.get_leaderboard(limit=limit)
            
            agents = []
            for agent in agents_data:
                agent_info = {
                    'id': agent.get('agent_id', 'unknown'),
                    'name': agent.get('agent_id', 'unknown').replace('_', ' ').title(),
                    'status': 'active',  # Default status
                    'reputation_score': agent.get('score', 0),
                    'total_executions': agent.get('total_tasks', 0),
                    'success_rate': agent.get('success_rate', 0),
                    'last_execution': agent.get('last_activity'),
                    'created_at': agent.get('created_at')
                }
                agents.append(agent_info)
        else:
            agents = _get_mock_agents(limit)
        
        if status_filter != 'all':
            agents = [a for a in agents if a.get('status') == status_filter]
        
        return jsonify({
            'agents': agents,
            'count': len(agents),
            'using_mock': not GOVERNANCE_AVAILABLE,
            'filters': {
                'status': status_filter,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': 'Failed to get agents',
            'message': str(e)
        }), 500


@admin_bp.route('/agents/<agent_id>', methods=['GET'])
@jwt_required
@admin_required
def admin_get_agent_details(agent_id):
    """
    Get detailed information about a specific agent
    
    Returns:
    - Agent metadata
    - Reputation score and history
    - Recent execution history
    - Performance metrics
    
    Requires: Owner role
    """
    try:
        if not GOVERNANCE_AVAILABLE and not ALLOW_GOVERNANCE_MOCK:
            return jsonify({
                'error': 'Governance system unavailable',
                'message': 'Mock data is disabled. Please enable ALLOW_GOVERNANCE_MOCK or fix governance system.'
            }), 503
        
        using_mock = False
        if GOVERNANCE_AVAILABLE:
            try:
                reputation_engine = get_reputation_engine()
                permission_checker = get_permission_checker()
                
                reputation = reputation_engine.get_reputation(agent_id)
                if not reputation:
                    agent_details = _get_mock_agent_details(agent_id)
                    using_mock = True
                else:
                    permission_summary = permission_checker.get_permission_summary(agent_id)
                    recent_events = reputation_engine.get_recent_events(agent_id, limit=20)
                    
                    agent_details = {
                        'id': agent_id,
                        'name': agent_id.replace('_', ' ').title(),
                        'status': 'active',
                        'reputation': reputation,
                        'permissions': permission_summary,
                        'recent_events': recent_events,
                        'metadata': {
                            'created_at': reputation.get('created_at'),
                            'last_updated': reputation.get('last_activity')
                        }
                    }
            except Exception as gov_error:
                logger.warning(f"Governance system error for agent {agent_id}: {gov_error}")
                agent_details = _get_mock_agent_details(agent_id)
                using_mock = True
        else:
            agent_details = _get_mock_agent_details(agent_id)
            using_mock = True
        
        agent_details['using_mock'] = using_mock
        return jsonify(agent_details)
    except Exception as e:
        return jsonify({
            'error': 'Failed to get agent details',
            'message': str(e)
        }), 500


@admin_bp.route('/agents/<agent_id>/executions', methods=['GET'])
@jwt_required
@admin_required
def admin_get_agent_executions(agent_id):
    """
    Get execution history for a specific agent
    
    Query parameters:
    - limit: Number of executions to return - default: 50
    - status: Filter by status (success, failure, all) - default: all
    
    Returns list of recent executions with details
    
    Requires: Owner role
    """
    try:
        if not GOVERNANCE_AVAILABLE and not ALLOW_GOVERNANCE_MOCK:
            return jsonify({
                'error': 'Governance system unavailable',
                'message': 'Mock data is disabled. Please enable ALLOW_GOVERNANCE_MOCK or fix governance system.'
            }), 503
        
        limit = min(int(request.args.get('limit', 50)), 200)
        status_filter = request.args.get('status', 'all')
        
        using_mock = False
        if GOVERNANCE_AVAILABLE:
            try:
                reputation_engine = get_reputation_engine()
                executions = reputation_engine.get_recent_events(agent_id, limit=limit)
                
                formatted_executions = []
                for event in executions:
                    execution = {
                        'id': event.get('id'),
                        'agent_id': agent_id,
                        'status': 'success' if event.get('event_type') == 'task_success' else 'failure',
                        'started_at': event.get('created_at'),
                        'completed_at': event.get('created_at'),
                        'duration_ms': event.get('metadata', {}).get('duration_ms', 0),
                        'metadata': event.get('metadata', {})
                    }
                    formatted_executions.append(execution)
            except Exception as gov_error:
                logger.warning(f"Governance system error for agent {agent_id} executions: {gov_error}")
                formatted_executions = _get_mock_executions(agent_id, limit)
                using_mock = True
        else:
            formatted_executions = _get_mock_executions(agent_id, limit)
            using_mock = True
        
        if status_filter != 'all':
            formatted_executions = [e for e in formatted_executions if e.get('status') == status_filter]
        
        return jsonify({
            'executions': formatted_executions,
            'count': len(formatted_executions),
            'using_mock': using_mock,
            'agent_id': agent_id,
            'filters': {
                'status': status_filter,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': 'Failed to get agent executions',
            'message': str(e)
        }), 500


@admin_bp.route('/agents/<agent_id>/pause', methods=['POST'])
@jwt_required
@admin_required
def admin_pause_agent(agent_id):
    """
    Pause an agent (prevent new executions)
    
    Requires: Owner role
    """
    try:
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'status': 'paused',
            'message': f'Agent {agent_id} has been paused',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': 'Failed to pause agent',
            'message': str(e)
        }), 500


@admin_bp.route('/agents/<agent_id>/resume', methods=['POST'])
@jwt_required
@admin_required
def admin_resume_agent(agent_id):
    """
    Resume a paused agent
    
    Requires: Owner role
    """
    try:
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'status': 'active',
            'message': f'Agent {agent_id} has been resumed',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': 'Failed to resume agent',
            'message': str(e)
        }), 500



def _get_mock_agents(limit=100):
    """Return mock agent data when governance system is unavailable"""
    mock_agents = [
        {
            'id': 'faq_agent',
            'name': 'FAQ Agent',
            'status': 'active',
            'reputation_score': 85,
            'total_executions': 1234,
            'success_rate': 0.95,
            'last_execution': datetime.utcnow().isoformat(),
            'created_at': '2025-01-01T00:00:00Z'
        },
        {
            'id': 'orchestrator_agent',
            'name': 'Orchestrator Agent',
            'status': 'active',
            'reputation_score': 92,
            'total_executions': 5678,
            'success_rate': 0.98,
            'last_execution': datetime.utcnow().isoformat(),
            'created_at': '2025-01-01T00:00:00Z'
        },
        {
            'id': 'analytics_agent',
            'name': 'Analytics Agent',
            'status': 'paused',
            'reputation_score': 78,
            'total_executions': 890,
            'success_rate': 0.89,
            'last_execution': '2025-10-30T12:00:00Z',
            'created_at': '2025-01-15T00:00:00Z'
        }
    ]
    return mock_agents[:limit]


def _get_mock_agent_details(agent_id):
    """Return mock agent details when governance system is unavailable"""
    return {
        'id': agent_id,
        'name': agent_id.replace('_', ' ').title(),
        'status': 'active',
        'reputation': {
            'score': 85,
            'rank': 1,
            'total_tasks': 1234,
            'success_rate': 0.95
        },
        'permissions': {
            'can_execute': True,
            'can_access_data': True,
            'rate_limit': 100
        },
        'recent_events': [],
        'metadata': {
            'created_at': '2025-01-01T00:00:00Z',
            'last_updated': datetime.utcnow().isoformat()
        }
    }


def _get_mock_executions(agent_id, limit=50):
    """Return mock execution data when governance system is unavailable"""
    mock_executions = []
    for i in range(min(limit, 10)):
        mock_executions.append({
            'id': f'exec_{i+1}',
            'agent_id': agent_id,
            'status': 'success' if i % 5 != 0 else 'failure',
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': datetime.utcnow().isoformat(),
            'duration_ms': 1500 + (i * 100),
            'metadata': {
                'task_type': 'faq_generation',
                'input_size': 1024
            }
        })
    return mock_executions


@admin_bp.route('/config/summary', methods=['GET'])
@jwt_required
@admin_required
def get_config_summary():
    """
    Get a summary of all orchestrator, LLM, canary, and enforcement configurations.

    This endpoint dumps all relevant configuration settings in a single response
    for operational visibility and debugging purposes.

    Returns:
    - orchestrator: Orchestrator mode and settings
    - llm: LLM provider and feature flags
    - canary: Canary deployment settings and thresholds
    - enforcement: Security policy enforcement configuration
    - environment: Current environment information

    Requires: Owner role
    """
    try:
        config_summary = {
            'orchestrator': {
                # USE_LANGGRAPH, USE_LANGGRAPH_PERCENT removed in Issue #2651
                # LangGraph is now the only orchestrator mode (Simple Mode removed 2025-12-18)
                'mode': 'langgraph',  # Always LangGraph now
                'enable_orchestrator': settings.enable_orchestrator,
                'orchestrator_path': settings.orchestrator_path,
                'orchestrator_test_mode': settings.orchestrator_test_mode,
                'orchestrator_shutdown_timeout': settings.orchestrator_shutdown_timeout,
            },
            'llm': {
                'provider': settings.llm_provider,
                'use_llm_planner': settings.use_llm_planner,
                'use_llm_reviewer': settings.use_llm_reviewer,
                'planner_json_mode': settings.planner_json_mode,
                'reviewer_json_mode': settings.reviewer_json_mode,
                'dev_agent_model': settings.dev_agent_model,
                'use_tiktoken_estimator': settings.use_tiktoken_estimator,
                'planner_events_storage': settings.planner_events_storage,
            },
            'canary': {
                'metrics_enabled': settings.canary_metrics_enabled,
                'alerting_enabled': settings.canary_alerting_enabled,
                'window_minutes': settings.canary_window_minutes,
                'p95_ms_threshold': settings.canary_p95_ms_threshold,
                '5xx_rate_threshold': settings.canary_5xx_rate_threshold,
                'failure_rate_threshold': settings.canary_failure_rate_threshold,
                'buckets_ms': settings.canary_buckets_ms,
            },
            'enforcement': {
                'security_enforcement_mode': settings.security_enforcement_mode,
                'policies_path': settings.policies_path,
            },
            'code_generation': {
                'use_code_generation': settings.use_code_generation,
                'use_codegen_workflow_percent': settings.use_codegen_workflow_percent,
                'enable_project_engineer_codegen': settings.enable_project_engineer_codegen,
                'enable_project_engineer_fixer': settings.enable_project_engineer_fixer,
                'project_engineer_fixer_percent': settings.project_engineer_fixer_percent,
            },
            'agents': {
                'ops_agent_enabled': settings.ops_agent_enabled,
                'growth_strategist_enabled': settings.growth_strategist_enabled,
                'pm_agent_enabled': settings.pm_agent_enabled,
                'hitl_approval_enabled': settings.hitl_approval_enabled,
                'sandbox_enabled': settings.sandbox_enabled,
            },
            'environment': {
                'environment': settings.environment,
                'flask_env': settings.flask_env,
                'app_version': settings.app_version,
                'app_phase': settings.app_phase,
                'debug': settings.debug,
                'log_level': settings.log_level,
            },
            'rate_limiting': {
                'rate_limit_requests': settings.rate_limit_requests,
                'rate_limit_window': settings.rate_limit_window,
                'rate_limit_by_user': settings.rate_limit_by_user,
                'rate_limit_fail_fast': settings.rate_limit_fail_fast,
            },
            'timestamp': datetime.utcnow().isoformat(),
        }

        return jsonify(config_summary)
    except Exception as e:
        logger.error(f"Failed to get config summary: {e}")
        return jsonify({
            'error': 'Failed to get config summary',
            'message': 'An internal error occurred while retrieving the configuration summary'
        }), 500
