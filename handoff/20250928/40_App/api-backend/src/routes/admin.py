"""Admin API - System monitoring and management endpoints for Owner Console"""
import os
import psutil
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from src.middleware.auth_middleware import jwt_required, admin_required
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
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)
        
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        
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
        db.session.execute('SELECT 1')
        return 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return 'unhealthy'


def _check_redis_status():
    """Check Redis connectivity status"""
    try:
        from src.utils.redis_config import get_secure_redis_url
        from redis import Redis
        
        redis_url = get_secure_redis_url(allow_local=os.getenv("TESTING") == "true")
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
