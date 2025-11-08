from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
import secrets
import os
from src.models.user import db, User
from common.config.settings import get_settings

auth_bp = Blueprint('auth', __name__)


# 模擬用戶數據（實際應用中應該從數據庫讀取）
MOCK_USERS = {
    'admin': {
        'id': 1,
        'username': 'admin',
        'password_hash': generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123')),
        'name': '系統管理員',
        'role': 'admin',
        'avatar': None
    },
    'operator': {
        'id': 2,
        'username': 'operator',
        'password_hash': generate_password_hash('operator123'),
        'name': '操作員',
        'role': 'operator',
        'avatar': None
    },
    'viewer': {
        'id': 3,
        'username': 'viewer',
        'password_hash': generate_password_hash('viewer123'),
        'name': '查看者',
        'role': 'viewer',
        'avatar': None
    }
}

@auth_bp.route('/login', methods=['POST'])
def login():
    """用戶登錄"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': '用戶名和密碼不能為空'}), 400
        
        # 檢查用戶是否存在（這裡使用模擬數據）
        user_data = MOCK_USERS.get(username)
        if not user_data:
            return jsonify({'message': '用戶名或密碼錯誤'}), 401
        
        # 驗證密碼
        if not check_password_hash(user_data['password_hash'], password):
            return jsonify({'message': '用戶名或密碼錯誤'}), 401
        
        # 生成JWT token
        jwt_secret = get_settings().jwt_secret_key or 'your-secret-key'
        token = jwt.encode({
            'user_id': user_data['id'],
            'username': username,
            'role': user_data['role'],
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
        }, jwt_secret, algorithm='HS256')
        
        user_info = {
            'id': user_data['id'],
            'username': user_data['username'],
            'name': user_data['name'],
            'role': user_data['role'],
            'avatar': user_data['avatar']
        }
        
        use_cookie_auth = os.environ.get('FEATURE_COOKIE_AUTH', 'false').lower() == 'true'
        
        if use_cookie_auth:
            csrf_token = secrets.token_urlsafe(32)
            
            response = make_response(jsonify({
                'user': user_info,
                'token': token
            }))
            
            is_production = os.environ.get('ENVIRONMENT') == 'production'
            secure = is_production
            samesite = 'None' if is_production else 'Lax'
            
            response.set_cookie(
                'access_token',
                token,
                httponly=True,
                secure=secure,
                samesite=samesite,
                max_age=86400,
                path='/'
            )
            
            response.set_cookie(
                'csrf_token',
                csrf_token,
                httponly=False,
                secure=secure,
                samesite=samesite,
                max_age=86400,
                path='/'
            )
            
            return response
        else:
            return jsonify({
                'user': user_info,
                'token': token
            })
        
    except Exception as e:
        return jsonify({'message': '登錄失敗，請稍後重試'}), 500

@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """驗證token有效性"""
    try:
        token = None
        
        use_cookie_auth = os.environ.get('FEATURE_COOKIE_AUTH', 'false').lower() == 'true'
        if use_cookie_auth:
            token = request.cookies.get('access_token')
        
        if not token:
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'message': '缺少認證頭'}), 401
            
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'message': '無效的認證格式'}), 401
        
        # 驗證token
        try:
            jwt_secret = get_settings().jwt_secret_key or 'your-secret-key'
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            username = payload['username']
            
            # 獲取用戶信息
            user_data = MOCK_USERS.get(username)
            if not user_data:
                return jsonify({'message': '用戶不存在'}), 401
            
            return jsonify({
                'id': user_data['id'],
                'username': user_data['username'],
                'name': user_data['name'],
                'role': user_data['role'],
                'avatar': user_data['avatar']
            })
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token已過期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '無效的Token'}), 401
            
    except Exception as e:
        return jsonify({'message': '驗證失敗'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用戶登出"""
    use_cookie_auth = os.environ.get('FEATURE_COOKIE_AUTH', 'false').lower() == 'true'
    
    if use_cookie_auth:
        response = make_response(jsonify({'message': '登出成功'}))
        
        is_production = os.environ.get('ENVIRONMENT') == 'production'
        secure = is_production
        samesite = 'None' if is_production else 'Lax'
        
        response.set_cookie('access_token', '', expires=0, path='/', secure=secure, samesite=samesite)
        response.set_cookie('csrf_token', '', expires=0, path='/', secure=secure, samesite=samesite)
        
        return response
    else:
        return jsonify({'message': '登出成功'})

