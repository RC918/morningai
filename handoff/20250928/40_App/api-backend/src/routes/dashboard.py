from flask import Blueprint, jsonify, request
import random
import datetime
import logging
from typing import Dict, List
from src.middleware.auth_middleware import jwt_required

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","operation":"%(name)s"}'
)
logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/metrics', methods=['GET'])
def get_system_metrics():
    """獲取系統指標"""
    try:
        # 模擬實時系統指標
        metrics = {
            'cpu_usage': round(random.uniform(60, 90), 1),
            'memory_usage': round(random.uniform(50, 80), 1),
            'response_time': round(random.uniform(100, 300), 0),
            'error_rate': round(random.uniform(0.01, 0.05), 3),
            'active_strategies': random.randint(8, 15),
            'pending_approvals': random.randint(1, 5),
            'cost_today': round(random.uniform(30, 60), 2),
            'cost_saved': round(random.uniform(100, 200), 2),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'error': '獲取系統指標失敗'}), 500

@dashboard_bp.route('/performance-history', methods=['GET'])
def get_performance_history():
    """獲取性能歷史數據"""
    try:
        # 生成過去24小時的模擬數據
        hours = int(request.args.get('hours', 6))
        data = []
        
        base_time = datetime.datetime.now()
        for i in range(hours * 2):  # 每30分鐘一個數據點
            time_point = base_time - datetime.timedelta(minutes=30 * i)
            data.append({
                'time': time_point.strftime('%H:%M'),
                'cpu': round(random.uniform(60, 85), 1),
                'memory': round(random.uniform(50, 75), 1),
                'response_time': round(random.uniform(100, 250), 0),
                'timestamp': time_point.isoformat()
            })
        
        # 按時間順序排序
        data.reverse()
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': '獲取性能歷史失敗'}), 500

@dashboard_bp.route('/recent-decisions', methods=['GET'])
def get_recent_decisions():
    """獲取最近的決策記錄"""
    try:
        limit = int(request.args.get('limit', 10))
        
        # 模擬最近的決策數據
        decisions = []
        strategies = [
            'CPU優化策略', '內存清理', '緩存優化', '自動擴容', 
            '負載均衡調整', '數據庫優化', '網絡優化', '存儲清理'
        ]
        
        statuses = ['executed', 'pending', 'failed']
        
        for i in range(limit):
            decision_time = datetime.datetime.now() - datetime.timedelta(minutes=random.randint(5, 300))
            
            decisions.append({
                'id': f'decision_{i+1:03d}',
                'timestamp': decision_time.isoformat(),
                'strategy': random.choice(strategies),
                'status': random.choice(statuses),
                'impact': f'+{random.randint(10, 30)}% 性能提升' if random.choice([True, False]) else f'預計 +{random.randint(15, 40)}% 響應速度',
                'confidence': round(random.uniform(0.7, 0.95), 2),
                'execution_time': round(random.uniform(30, 180), 1) if random.choice([True, False]) else None
            })
        
        # 按時間排序
        decisions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify(decisions)
        
    except Exception as e:
        return jsonify({'error': '獲取決策記錄失敗'}), 500

@dashboard_bp.route('/system-health', methods=['GET'])
def get_system_health():
    """獲取系統健康狀態"""
    try:
        from src.utils.redis_client import check_redis_security
        
        components = {
            'ai_gateway': {
                'status': 'healthy',
                'response_time': round(random.uniform(50, 150), 0),
                'last_check': datetime.datetime.now().isoformat()
            },
            'learning_system': {
                'status': 'healthy',
                'active_strategies': random.randint(10, 20),
                'last_check': datetime.datetime.now().isoformat()
            },
            'decision_simulator': {
                'status': 'healthy',
                'accuracy': round(random.uniform(0.85, 0.95), 2),
                'last_check': datetime.datetime.now().isoformat()
            },
            'database': {
                'status': 'healthy',
                'connections': random.randint(20, 50),
                'last_check': datetime.datetime.now().isoformat()
            }
        }
        
        redis_security = check_redis_security()
        redis_status = 'healthy'
        if redis_security['status'] == 'vulnerable':
            redis_status = 'degraded'
        elif redis_security['status'] == 'error':
            redis_status = 'unhealthy'
        
        components['redis'] = {
            'status': redis_status,
            'security_status': redis_security['status'],
            'cve_2025_49844_risk': redis_security['cve_2025_49844_risk'],
            'type': redis_security['type'],
            'message': redis_security['message'],
            'recommendations': redis_security.get('recommendations', []),
            'last_check': datetime.datetime.now().isoformat()
        }
        
        all_healthy = all(comp['status'] == 'healthy' for comp in components.values())
        overall_status = 'healthy' if all_healthy else 'degraded'
        
        return jsonify({
            'overall_status': overall_status,
            'components': components,
            'last_check_time': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': '獲取系統健康狀態失敗'}), 500

@dashboard_bp.route('/alerts', methods=['GET'])
def get_active_alerts():
    """獲取活躍告警"""
    try:
        # 模擬告警數據
        alerts = []
        
        if random.choice([True, False]):  # 50%概率有告警
            alert_types = [
                {'type': 'high_cpu', 'message': 'CPU使用率持續偏高', 'severity': 'warning'},
                {'type': 'memory_leak', 'message': '檢測到可能的內存洩漏', 'severity': 'error'},
                {'type': 'slow_response', 'message': '響應時間超過閾值', 'severity': 'warning'},
                {'type': 'high_error_rate', 'message': '錯誤率異常升高', 'severity': 'critical'}
            ]
            
            num_alerts = random.randint(0, 3)
            for i in range(num_alerts):
                alert = random.choice(alert_types)
                alerts.append({
                    'id': f'alert_{i+1}',
                    'type': alert['type'],
                    'message': alert['message'],
                    'severity': alert['severity'],
                    'timestamp': (datetime.datetime.now() - datetime.timedelta(minutes=random.randint(1, 60))).isoformat(),
                    'acknowledged': False
                })
        
        return jsonify(alerts)
        
    except Exception as e:
        return jsonify({'error': '獲取告警信息失敗'}), 500

@dashboard_bp.route('/cost-analysis', methods=['GET'])
def get_cost_analysis():
    """獲取成本分析數據"""
    try:
        period = request.args.get('period', 'today')  # today, week, month
        
        if period == 'today':
            # 今日成本分析
            data = {
                'total_cost': round(random.uniform(40, 80), 2),
                'ai_service_cost': round(random.uniform(20, 40), 2),
                'infrastructure_cost': round(random.uniform(15, 30), 2),
                'storage_cost': round(random.uniform(3, 8), 2),
                'savings': round(random.uniform(50, 150), 2),
                'breakdown': [
                    {'service': 'OpenAI API', 'cost': round(random.uniform(15, 25), 2)},
                    {'service': 'AWS EC2', 'cost': round(random.uniform(10, 20), 2)},
                    {'service': 'AWS RDS', 'cost': round(random.uniform(5, 10), 2)},
                    {'service': 'Redis Cache', 'cost': round(random.uniform(2, 5), 2)}
                ]
            }
        else:
            # 其他時間段的數據
            multiplier = 7 if period == 'week' else 30
            data = {
                'total_cost': round(random.uniform(40, 80) * multiplier, 2),
                'ai_service_cost': round(random.uniform(20, 40) * multiplier, 2),
                'infrastructure_cost': round(random.uniform(15, 30) * multiplier, 2),
                'storage_cost': round(random.uniform(3, 8) * multiplier, 2),
                'savings': round(random.uniform(50, 150) * multiplier, 2)
            }
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': '獲取成本分析失敗'}), 500

@dashboard_bp.route('/layouts', methods=['GET'])
@jwt_required
def get_dashboard_layout():
    """獲取用戶的 Dashboard 佈局"""
    try:
        user_id = request.user_id
        logger.info(f"Fetching dashboard layout for user_id={user_id}")
        
        default_layout = {
            'user_id': user_id,
            'widgets': [
                {'id': 'cpu_usage', 'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4}},
                {'id': 'memory_usage', 'position': {'x': 6, 'y': 0, 'w': 6, 'h': 4}},
                {'id': 'response_time', 'position': {'x': 0, 'y': 4, 'w': 6, 'h': 4}},
                {'id': 'error_rate', 'position': {'x': 6, 'y': 4, 'w': 6, 'h': 4}},
                {'id': 'active_strategies', 'position': {'x': 0, 'y': 8, 'w': 4, 'h': 3}},
                {'id': 'pending_approvals', 'position': {'x': 4, 'y': 8, 'w': 4, 'h': 3}},
                {'id': 'task_execution', 'position': {'x': 8, 'y': 8, 'w': 4, 'h': 6}}
            ],
            'updated_at': datetime.datetime.now().isoformat()
        }
        
        return jsonify(default_layout)
        
    except Exception as e:
        logger.error(f"Failed to fetch dashboard layout: {e}", extra={"user_id": getattr(request, 'user_id', None)})
        return jsonify({'error': '獲取佈局失敗'}), 500

@dashboard_bp.route('/layouts', methods=['POST'])
@jwt_required
def save_dashboard_layout():
    """儲存用戶的 Dashboard 佈局"""
    try:
        user_id = request.user_id
        data = request.get_json()
        
        if not data:
            logger.warning(f"Empty request body for save_dashboard_layout, user_id={user_id}")
            return jsonify({'error': '請求數據不能為空'}), 400
        
        layout = data.get('layout', {})
        logger.info(f"Saving dashboard layout for user_id={user_id}, widgets_count={len(layout.get('widgets', []))}")
        
        return jsonify({
            'status': 'success',
            'message': 'Dashboard layout saved successfully',
            'user_id': user_id,
            'updated_at': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to save dashboard layout: {e}", extra={"user_id": getattr(request, 'user_id', None)})
        return jsonify({'error': '儲存佈局失敗'}), 500

@dashboard_bp.route('/widgets', methods=['GET'])
@jwt_required
def get_available_widgets():
    """獲取可用的 Dashboard 小工具列表"""
    try:
        user_id = request.user_id
        logger.info(f"Fetching available widgets for user_id={user_id}")
        
        widgets = [
            {
                'id': 'cpu_usage',
                'name': 'CPU 使用率',
                'description': '實時 CPU 使用率監控',
                'category': 'system',
                'icon': 'cpu',
                'size': {'w': 6, 'h': 4}
            },
            {
                'id': 'memory_usage',
                'name': '內存使用率',
                'description': '實時內存使用率監控',
                'category': 'system',
                'icon': 'memory',
                'size': {'w': 6, 'h': 4}
            },
            {
                'id': 'response_time',
                'name': '響應時間',
                'description': '系統響應時間監控',
                'category': 'performance',
                'icon': 'clock',
                'size': {'w': 6, 'h': 4}
            },
            {
                'id': 'error_rate',
                'name': '錯誤率',
                'description': '系統錯誤率監控',
                'category': 'performance',
                'icon': 'alert',
                'size': {'w': 6, 'h': 4}
            },
            {
                'id': 'active_strategies',
                'name': '活躍策略',
                'description': '當前活躍的 AI 策略數量',
                'category': 'ai',
                'icon': 'zap',
                'size': {'w': 4, 'h': 3}
            },
            {
                'id': 'pending_approvals',
                'name': '待審批任務',
                'description': '需要人工審批的決策數量',
                'category': 'workflow',
                'icon': 'check-circle',
                'size': {'w': 4, 'h': 3}
            },
            {
                'id': 'cost_today',
                'name': '今日成本',
                'description': '今日累計成本',
                'category': 'cost',
                'icon': 'dollar-sign',
                'size': {'w': 4, 'h': 3}
            },
            {
                'id': 'cost_saved',
                'name': '成本節省',
                'description': '通過 AI 優化節省的成本',
                'category': 'cost',
                'icon': 'trending-down',
                'size': {'w': 4, 'h': 3}
            },
            {
                'id': 'task_execution',
                'name': '任務執行',
                'description': '任務執行狀態與統計',
                'category': 'workflow',
                'icon': 'activity',
                'size': {'w': 4, 'h': 6}
            }
        ]
        
        logger.info(f"Returning {len(widgets)} widgets for user_id={user_id}")
        return jsonify({'widgets': widgets})
        
    except Exception as e:
        logger.error(f"Failed to fetch available widgets: {e}", extra={"user_id": getattr(request, 'user_id', None)})
        return jsonify({'error': '獲取小工具列表失敗'}), 500

