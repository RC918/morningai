from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
from src.models.user import db, User

auth_bp = Blueprint('auth', __name__)

# 模擬用戶數據（實際應用中應該從數據庫讀取）
MOCK_USERS = {
    'admin': {
        'id': 1,
        'username': 'admin',
        'password_hash': generate_password_hash('admin123'),
        'name': '系統管理員',
        'role': '超級管理員',
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
        token = jwt.encode({
            'user_id': user_data['id'],
            'username': username,
            'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
        }, 'your-secret-key', algorithm='HS256')
        
        # 返回用戶信息和token
        return jsonify({
            'user': {
                'id': user_data['id'],
                'username': user_data['username'],
                'name': user_data['name'],
                'role': user_data['role'],
                'avatar': user_data['avatar']
            },
            'token': token
        })
        
    except Exception as e:
        return jsonify({'message': '登錄失敗，請稍後重試'}), 500

@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """驗證token有效性"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'message': '缺少認證頭'}), 401
        
        # 提取token
        try:
            token = auth_header.split(' ')[1]  # Bearer <token>
        except IndexError:
            return jsonify({'message': '無效的認證格式'}), 401
        
        # 驗證token
        try:
            payload = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
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
    # 在實際應用中，可以將token加入黑名單
    return jsonify({'message': '登出成功'})

