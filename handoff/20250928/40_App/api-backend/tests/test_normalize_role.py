import pytest
from src.middleware.auth_middleware import normalize_role, generate_jwt_token
import jwt
import os


def test_normalize_role_operator_to_analyst():
    """Test that operator is normalized to analyst"""
    assert normalize_role('operator') == 'analyst'


def test_normalize_role_viewer_to_user():
    """Test that viewer is normalized to user"""
    assert normalize_role('viewer') == 'user'


def test_normalize_role_admin_unchanged():
    """Test that admin remains admin"""
    assert normalize_role('admin') == 'admin'


def test_normalize_role_analyst_unchanged():
    """Test that analyst remains analyst"""
    assert normalize_role('analyst') == 'analyst'


def test_normalize_role_user_unchanged():
    """Test that user remains user"""
    assert normalize_role('user') == 'user'


def test_normalize_role_chinese_admin():
    """Test Chinese admin role mapping"""
    assert normalize_role('超級管理員') == 'admin'


def test_normalize_role_chinese_analyst():
    """Test Chinese analyst role mapping"""
    assert normalize_role('分析師') == 'analyst'


def test_normalize_role_chinese_operator():
    """Test Chinese operator role mapping"""
    assert normalize_role('操作員') == 'analyst'


def test_normalize_role_chinese_viewer():
    """Test Chinese viewer role mapping"""
    assert normalize_role('查看者') == 'user'


def test_normalize_role_unknown_passthrough():
    """Test that unknown roles pass through unchanged"""
    unknown_role = 'unknown_role'
    assert normalize_role(unknown_role) == unknown_role


def test_normalize_role_empty_string():
    """Test handling of empty string"""
    assert normalize_role('') == ''


def test_normalize_role_none_passthrough():
    """Test handling of None value"""
    assert normalize_role(None) == None


def test_jwt_token_generation_with_operator_role():
    """Test JWT token generation normalizes operator to analyst"""
    user_data = {
        'id': 2,
        'username': 'operator_user',
        'role': 'operator'
    }
    
    token = generate_jwt_token(user_data)
    
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
    
    assert payload['role'] == 'analyst'
    assert payload['username'] == 'operator_user'


def test_jwt_token_generation_with_viewer_role():
    """Test JWT token generation normalizes viewer to user"""
    user_data = {
        'id': 3,
        'username': 'viewer_user',
        'role': 'viewer'
    }
    
    token = generate_jwt_token(user_data)
    
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
    
    assert payload['role'] == 'user'
    assert payload['username'] == 'viewer_user'


def test_jwt_token_generation_with_admin_role():
    """Test JWT token generation keeps admin unchanged"""
    user_data = {
        'id': 1,
        'username': 'admin_user',
        'role': 'admin'
    }
    
    token = generate_jwt_token(user_data)
    
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
    
    assert payload['role'] == 'admin'
    assert payload['username'] == 'admin_user'


def test_backward_compatibility_operator_login():
    """Integration test: operator user can login and get normalized token"""
    from src.middleware import generate_jwt_token
    
    operator_data = {
        'id': 2,
        'username': 'operator',
        'role': 'operator'
    }
    
    token = generate_jwt_token(operator_data)
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    decoded = jwt.decode(token, jwt_secret, algorithms=['HS256'])
    
    assert decoded['role'] == 'analyst'


def test_backward_compatibility_viewer_login():
    """Integration test: viewer user can login and get normalized token"""
    from src.middleware import generate_jwt_token
    
    viewer_data = {
        'id': 3,
        'username': 'viewer',
        'role': 'viewer'
    }
    
    token = generate_jwt_token(viewer_data)
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    decoded = jwt.decode(token, jwt_secret, algorithms=['HS256'])
    
    assert decoded['role'] == 'user'


def test_roles_required_decorator_with_operator_token():
    """Integration test: operator token can access analyst-required endpoint"""
    from src.middleware import roles_required
    from flask import Flask, jsonify
    import jwt as jwt_lib
    import datetime
    
    app = Flask(__name__)
    
    @app.route('/test-endpoint')
    @roles_required("analyst", "admin")
    def test_endpoint():
        return jsonify({"message": "success"})
    
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    payload = {
        'user_id': 2,
        'username': 'operator',
        'role': 'operator',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()
    }
    operator_token = jwt_lib.encode(payload, jwt_secret, algorithm='HS256')
    
    with app.test_client() as client:
        response = client.get(
            '/test-endpoint',
            headers={'Authorization': f'Bearer {operator_token}'}
        )
        
        assert response.status_code == 200
        assert response.json['message'] == 'success'


def test_roles_required_decorator_with_viewer_token():
    """Integration test: viewer token cannot access analyst-required endpoint"""
    from src.middleware import roles_required
    from flask import Flask, jsonify
    import jwt as jwt_lib
    import datetime
    
    app = Flask(__name__)
    
    @app.route('/test-endpoint')
    @roles_required("analyst", "admin")
    def test_endpoint():
        return jsonify({"message": "success"})
    
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    payload = {
        'user_id': 3,
        'username': 'viewer',
        'role': 'viewer',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        'iat': datetime.datetime.utcnow()
    }
    viewer_token = jwt_lib.encode(payload, jwt_secret, algorithm='HS256')
    
    with app.test_client() as client:
        response = client.get(
            '/test-endpoint',
            headers={'Authorization': f'Bearer {viewer_token}'}
        )
        
        assert response.status_code == 403
        assert 'Insufficient privileges' in response.json['error']
