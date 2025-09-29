from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from datetime import datetime, timedelta
import jwt
import logging
import asyncio
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../99_Original_Bundle/morningai_enhanced'))

try:
    from secure_config import SecureConfigManager
    from monitoring_system import MonitoringSystem
    from ai_service_gateway import get_ai_gateway
except ImportError:
    SecureConfigManager = None
    MonitoringSystem = None
    get_ai_gateway = None

from cloud_health_checker import CloudResourceHealthChecker

app = Flask(__name__)
CORS(app)

if SecureConfigManager:
    try:
        config_manager = SecureConfigManager()
        config_manager.apply_environment_overrides()
        app.config['SECRET_KEY'] = config_manager.get('security.secret_key')
    except Exception:
        app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
else:
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

if MonitoringSystem:
    try:
        monitoring = MonitoringSystem(
            base_url=os.getenv('API_BASE_URL', 'http://localhost:8000'),
            auth_token=os.getenv('MONITOR_AUTH_TOKEN')
        )
    except Exception:
        monitoring = None
else:
    monitoring = None

cloud_checker = CloudResourceHealthChecker()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == 'admin' and password == 'admin123':
        token = jwt.encode({
            'user_id': 1,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'user': {
                'id': 1,
                'name': '系統管理員',
                'username': username,
                'role': '超級管理員'
            },
            'token': token
        })
    
    return jsonify({'message': '用戶名或密碼錯誤'}), 401

@app.route('/api/auth/verify', methods=['GET'])
def verify_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': '缺少認證令牌'}), 401
    
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({
            'id': payload['user_id'],
            'username': payload['username']
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'message': '令牌已過期'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': '無效令牌'}), 401

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Morning AI API'
    })

@app.route('/healthz', methods=['GET'])
def health_detailed():
    """Detailed health check including cloud resources"""
    try:
        cloud_status = asyncio.run(cloud_checker.check_all_services())
        
        overall_healthy = all(
            status.get('status') in ['healthy', 'not_configured'] 
            for status in cloud_status.values()
        )
        
        return jsonify({
            'status': 'healthy' if overall_healthy else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'cloud_resources': cloud_status,
            'service': 'Morning AI API'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'service': 'Morning AI API'
        }), 500

@app.route('/api/system/metrics', methods=['GET'])
def get_system_metrics():
    """Get system metrics for dashboard"""
    return jsonify({
        'cpu_usage': 72,
        'memory_usage': 68,
        'response_time': 145,
        'error_rate': 0.02,
        'active_strategies': 12,
        'pending_approvals': 3,
        'cost_today': 45.67,
        'cost_saved': 123.45
    })

@app.route('/api/cloud/status', methods=['GET'])
def get_cloud_status():
    """Get detailed cloud resource status"""
    try:
        cloud_status = asyncio.run(cloud_checker.check_all_services())
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'services': cloud_status
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/openapi.json', methods=['GET'])
def openapi_spec():
    """OpenAPI specification"""
    return jsonify({
        'openapi': '3.0.0',
        'info': {
            'title': 'Morning AI API',
            'version': '1.0.0'
        },
        'paths': {
            '/api/auth/login': {'post': {'summary': 'User login'}},
            '/api/auth/verify': {'get': {'summary': 'Verify token'}},
            '/health': {'get': {'summary': 'Basic health check'}},
            '/healthz': {'get': {'summary': 'Detailed health check'}},
            '/api/system/metrics': {'get': {'summary': 'System metrics'}},
            '/api/cloud/status': {'get': {'summary': 'Cloud resource status'}}
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=os.environ.get('FLASK_ENV') == 'development', host='0.0.0.0', port=port)
