"""Admin API - System monitoring and management endpoints for Owner Console"""
import os
import psutil
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from src.middleware.auth_middleware import jwt_required, admin_required
from src.models.agent_registry_db import TaskDB, AgentDB, TaskStatusDB, db
from sqlalchemy import and_, or_, func
from common.config.settings import settings
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

APP_START_TIME = time.time()


@bp.route('/system/health', methods=['GET'])
@jwt_required
@admin_required
def get_system_health():
    """
    Get system health status
    
    Returns overall system health including:
    - System status (healthy/degraded/unhealthy)
    - Uptime
    - Service status checks
    
    Requires: Owner role
    """
    try:
        uptime_seconds = time.time() - APP_START_TIME
        uptime_hours = uptime_seconds / 3600
        
        services_status = {
            'database': _check_database_status(),
            'redis': _check_redis_status(),
            'api': 'healthy'  # If we're responding, API is healthy
        }
        
        unhealthy_services = [name for name, status in services_status.items() if status == 'unhealthy']
        degraded_services = [name for name, status in services_status.items() if status == 'degraded']
        
        if unhealthy_services:
            overall_status = 'unhealthy'
        elif degraded_services:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        return jsonify({
            'status': overall_status,
            'uptime_seconds': int(uptime_seconds),
            'uptime_hours': round(uptime_hours, 2),
            'services': services_status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({
            'error': 'Failed to get system health',
            'message': str(e)
        }), 500


@bp.route('/system/metrics', methods=['GET'])
@jwt_required
@admin_required
def get_system_metrics():
    """
    Get system metrics
    
    Returns system resource usage metrics:
    - CPU usage (percentage)
    - Memory usage (percentage and bytes)
    - Disk usage (percentage and bytes)
    - Request metrics (if available)
    
    Requires: Owner role
    """
    try:
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)
            
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024 ** 3)
            disk_total_gb = disk.total / (1024 ** 3)
        except (PermissionError, OSError) as e:
            logger.warning(f"psutil access restricted: {e}")
            return jsonify({
                'error': 'System metrics unavailable',
                'message': 'Insufficient permissions to access system metrics',
                'status': 'degraded'
            }), 503
        
        request_metrics = _get_request_metrics()
        
        return jsonify({
            'cpu': {
                'usage_percent': round(cpu_percent, 2),
                'count': cpu_count
            },
            'memory': {
                'usage_percent': round(memory_percent, 2),
                'used_gb': round(memory_used_gb, 2),
                'total_gb': round(memory_total_gb, 2)
            },
            'disk': {
                'usage_percent': round(disk_percent, 2),
                'used_gb': round(disk_used_gb, 2),
                'total_gb': round(disk_total_gb, 2)
            },
            'requests': request_metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return jsonify({
            'error': 'Failed to get system metrics',
            'message': str(e)
        }), 500


@bp.route('/system/logs', methods=['GET'])
@jwt_required
@admin_required
def get_system_logs():
    """
    Get system logs
    
    Query parameters:
    - level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - limit: Number of logs to return (default: 100, max: 1000)
    - since: ISO timestamp to get logs since (optional)
    
    Returns recent system logs with filtering options
    
    Requires: Owner role
    """
    try:
        level = request.args.get('level', '').upper()
        limit = min(int(request.args.get('limit', 100)), 1000)
        since = request.args.get('since')
        
        logs = _get_recent_logs(level=level, limit=limit, since=since)
        
        return jsonify({
            'logs': logs,
            'count': len(logs),
            'filters': {
                'level': level if level else 'ALL',
                'limit': limit,
                'since': since
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        return jsonify({
            'error': 'Failed to get system logs',
            'message': str(e)
        }), 500



def _check_database_status():
    """Check database connectivity status"""
    try:
        from src.models.user import db
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return 'unhealthy'


def _check_redis_status():
    """Check Redis connectivity status"""
    try:
        from src.utils.redis_config import get_secure_redis_url
        from redis import Redis
        
        redis_url = get_secure_redis_url(allow_local=settings.testing)
        redis_client = Redis.from_url(redis_url, socket_connect_timeout=2)
        redis_client.ping()
        return 'healthy'
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return 'degraded'  # Redis is optional for core functionality


def _get_request_metrics():
    """Get request metrics from the last hour"""
    return {
        'total_requests_1h': 0,
        'avg_response_time_ms': 0,
        'error_rate_percent': 0,
        'note': 'Request metrics tracking not yet implemented'
    }


def _get_recent_logs(level=None, limit=100, since=None):
    """Get recent logs with filtering"""
    
    logs = []
    
    logs.append({
        'timestamp': datetime.utcnow().isoformat(),
        'level': 'INFO',
        'message': 'System logs endpoint accessed',
        'source': 'admin.py',
        'metadata': {
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'ip': request.remote_addr
        }
    })
    
    return logs


@bp.route('/agent-execution-logs', methods=['GET'])
@jwt_required
@admin_required
def get_agent_execution_logs():
    """
    Get comprehensive agent execution logs for Owner Console
    
    Query parameters:
    - status: Filter by task status (queued, assigned, running, completed, failed, cancelled)
    - agent_id: Filter by specific agent ID
    - agent_type: Filter by agent type (dev_agent, ops_agent, pm_agent, growth_strategist, meta_agent)
    - tenant_id: Filter by specific tenant ID
    - task_type: Filter by task type (e.g., 'faq', 'bug_fix')
    - start_date: Filter tasks created after this date (ISO format)
    - end_date: Filter tasks created before this date (ISO format)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 200)
    - sort_by: Sort field (created_at, updated_at, completed_at) - default: created_at
    - sort_order: Sort order (asc, desc) - default: desc
    
    Returns enriched task execution logs with agent information
    
    Requires: Owner role
    """
    try:
        status_filter = request.args.get('status')
        agent_id_filter = request.args.get('agent_id')
        agent_type_filter = request.args.get('agent_type')
        tenant_id_filter = request.args.get('tenant_id')
        task_type_filter = request.args.get('task_type')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        page = max(int(request.args.get('page', 1)), 1)
        page_size = min(max(int(request.args.get('page_size', 50)), 1), 200)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        valid_sort_fields = ['created_at', 'updated_at', 'completed_at', 'started_at']
        if sort_by not in valid_sort_fields:
            return jsonify({
                'error': 'Invalid sort_by parameter',
                'message': f'sort_by must be one of: {", ".join(valid_sort_fields)}'
            }), 400
        
        if sort_order not in ['asc', 'desc']:
            return jsonify({
                'error': 'Invalid sort_order parameter',
                'message': 'sort_order must be either "asc" or "desc"'
            }), 400
        
        query = db.session.query(TaskDB, AgentDB).outerjoin(
            AgentDB, TaskDB.agent_id == AgentDB.agent_id
        )
        
        filters = []
        
        if status_filter:
            try:
                status = TaskStatusDB(status_filter)
                filters.append(TaskDB.status == status)
            except ValueError:
                return jsonify({
                    'error': 'Invalid status parameter',
                    'message': f'status must be one of: queued, assigned, running, completed, failed, cancelled'
                }), 400
        
        if agent_id_filter:
            filters.append(TaskDB.agent_id == agent_id_filter)
        
        if agent_type_filter:
            try:
                from src.models.agent_registry_db import AgentTypeDB
                agent_type = AgentTypeDB(agent_type_filter)
                filters.append(AgentDB.agent_type == agent_type)
            except ValueError:
                return jsonify({
                    'error': 'Invalid agent_type parameter',
                    'message': f'agent_type must be one of: dev_agent, ops_agent, pm_agent, growth_strategist, meta_agent'
                }), 400
        
        if tenant_id_filter:
            filters.append(TaskDB.tenant_id == tenant_id_filter)
        
        if task_type_filter:
            filters.append(TaskDB.task_type == task_type_filter)
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                filters.append(TaskDB.created_at >= start_date)
            except ValueError:
                return jsonify({
                    'error': 'Invalid start_date parameter',
                    'message': 'start_date must be in ISO format (e.g., 2025-11-01T00:00:00Z)'
                }), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                filters.append(TaskDB.created_at <= end_date)
            except ValueError:
                return jsonify({
                    'error': 'Invalid end_date parameter',
                    'message': 'end_date must be in ISO format (e.g., 2025-11-01T23:59:59Z)'
                }), 400
        
        if filters:
            query = query.filter(and_(*filters))
        
        total_items = query.count()
        total_pages = (total_items + page_size - 1) // page_size
        
        sort_field = getattr(TaskDB, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        results = query.all()
        
        execution_logs = []
        for task_db, agent_db in results:
            duration_ms = None
            if task_db.started_at and task_db.completed_at:
                duration = task_db.completed_at - task_db.started_at
                duration_ms = int(duration.total_seconds() * 1000)
            
            log_entry = {
                'task_id': task_db.task_id,
                'status': task_db.status.value,
                'task_type': task_db.task_type,
                'tenant_id': task_db.tenant_id,
                'agent': {
                    'agent_id': agent_db.agent_id if agent_db else task_db.agent_id,
                    'agent_type': agent_db.agent_type.value if agent_db else None,
                    'status': agent_db.status.value if agent_db else None,
                    'reputation_score': agent_db.reputation_score if agent_db else None
                } if task_db.agent_id else None,
                'timestamps': {
                    'created_at': task_db.created_at.isoformat() if task_db.created_at else None,
                    'assigned_at': task_db.assigned_at.isoformat() if task_db.assigned_at else None,
                    'started_at': task_db.started_at.isoformat() if task_db.started_at else None,
                    'completed_at': task_db.completed_at.isoformat() if task_db.completed_at else None,
                    'cancelled_at': task_db.cancelled_at.isoformat() if task_db.cancelled_at else None,
                    'updated_at': task_db.updated_at.isoformat() if task_db.updated_at else None
                },
                'duration_ms': duration_ms,
                'payload': task_db.get_payload(),
                'result': task_db.get_result(),
                'error_message': task_db.error_message
            }
            execution_logs.append(log_entry)
        
        summary_stats = _get_execution_summary_stats(filters)
        
        return jsonify({
            'execution_logs': execution_logs,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_items': total_items,
                'total_pages': total_pages
            },
            'filters': {
                'status': status_filter,
                'agent_id': agent_id_filter,
                'agent_type': agent_type_filter,
                'tenant_id': tenant_id_filter,
                'task_type': task_type_filter,
                'start_date': start_date_str,
                'end_date': end_date_str,
                'sort_by': sort_by,
                'sort_order': sort_order
            },
            'summary': summary_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting agent execution logs: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to get agent execution logs',
            'message': str(e)
        }), 500


def _get_execution_summary_stats(filters=None):
    """Get summary statistics for execution logs"""
    try:
        query = db.session.query(TaskDB)
        
        if filters:
            query = query.filter(and_(*filters))
        
        status_counts = {}
        for status in TaskStatusDB:
            count = query.filter(TaskDB.status == status).count()
            status_counts[status.value] = count
        
        total_count = query.count()
        
        completed_count = status_counts.get('completed', 0)
        failed_count = status_counts.get('failed', 0)
        success_rate = 0.0
        if (completed_count + failed_count) > 0:
            success_rate = completed_count / (completed_count + failed_count)
        
        completed_tasks = query.filter(
            and_(
                TaskDB.status == TaskStatusDB.COMPLETED,
                TaskDB.started_at.isnot(None),
                TaskDB.completed_at.isnot(None)
            )
        ).all()
        
        avg_duration_ms = None
        if completed_tasks:
            durations = []
            for task in completed_tasks:
                duration = task.completed_at - task.started_at
                durations.append(duration.total_seconds() * 1000)
            avg_duration_ms = int(sum(durations) / len(durations))
        
        return {
            'total_executions': total_count,
            'status_counts': status_counts,
            'success_rate': round(success_rate, 4),
            'avg_duration_ms': avg_duration_ms
        }
    
    except Exception as e:
        logger.error(f"Error calculating execution summary stats: {e}")
        return {
            'total_executions': 0,
            'status_counts': {},
            'success_rate': 0.0,
            'avg_duration_ms': None
        }
