import jwt
import os
from functools import wraps
from flask import request, jsonify, current_app

def jwt_required(f):
    """JWT authentication decorator for protecting endpoints (supports both Supabase and custom JWT)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'Authorization header missing',
                'message': 'Access denied. Please provide a valid JWT token.'
            }), 401
        
        try:
            token = auth_header.split(' ')[1]
        except (IndexError, AttributeError):
            return jsonify({
                'error': 'Invalid authorization format',
                'message': 'Authorization header must be in format: Bearer <token>'
            }), 401
        
        try:
            jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            
            user_id = payload.get('sub') or payload.get('user_id')
            
            request.current_user = {
                'user_id': user_id,
                'username': payload.get('username') or payload.get('email'),
                'role': payload.get('role', 'user')
            }
            
            request.user_id = user_id
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'error': 'Token expired',
                'message': 'JWT token has expired. Please login again.'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'error': 'Invalid token',
                'message': 'JWT token is invalid or malformed.'
            }), 401
        except Exception as e:
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Unable to verify JWT token.'
            }), 401
    
    return decorated_function

def admin_required(f):
    """Decorator for endpoints requiring admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'Authorization header missing',
                'message': 'Access denied. Please provide a valid JWT token.'
            }), 401
        
        try:
            token = auth_header.split(' ')[1]
        except (IndexError, AttributeError):
            return jsonify({
                'error': 'Invalid authorization format',
                'message': 'Authorization header must be in format: Bearer <token>'
            }), 401
        
        try:
            jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            
            user_role = payload.get('role', 'user')
            if user_role not in ['admin', '超級管理員']:
                return jsonify({
                    'error': 'Insufficient privileges',
                    'message': 'Admin access required for this endpoint.'
                }), 403
            
            request.current_user = {
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'role': user_role
            }
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'error': 'Token expired',
                'message': 'JWT token has expired. Please login again.'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'error': 'Invalid token',
                'message': 'JWT token is invalid or malformed.'
            }), 401
        except Exception as e:
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Unable to verify JWT token.'
            }), 401
    
    return decorated_function

def analyst_required(f):
    """Decorator for endpoints requiring analyst role or higher"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'Authorization header missing',
                'message': 'Access denied. Please provide a valid JWT token.'
            }), 401
        
        try:
            token = auth_header.split(' ')[1]
        except (IndexError, AttributeError):
            return jsonify({
                'error': 'Invalid authorization format',
                'message': 'Authorization header must be in format: Bearer <token>'
            }), 401
        
        try:
            jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            
            user_role = payload.get('role', 'user')
            if user_role not in ['admin', 'analyst', '超級管理員', '分析師']:
                return jsonify({
                    'error': 'Insufficient privileges',
                    'message': 'Analyst access or higher required for this endpoint.'
                }), 403
            
            request.current_user = {
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'role': user_role
            }
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'error': 'Token expired',
                'message': 'JWT token has expired. Please login again.'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'error': 'Invalid token',
                'message': 'JWT token is invalid or malformed.'
            }), 401
        except Exception as e:
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Unable to verify JWT token.'
            }), 401
    
    return decorated_function

def normalize_role(role):
    """
    Normalize role names for backward compatibility.
    Maps legacy role names to current standard role names.
    
    Role mapping:
    - operator -> analyst
    - viewer -> user
    - admin -> admin (unchanged)
    
    Args:
        role (str): The role name to normalize
        
    Returns:
        str: The normalized role name
    """
    role_mapping = {
        'operator': 'analyst',
        'viewer': 'user',
        'admin': 'admin',
        'analyst': 'analyst',
        'user': 'user',
        '超級管理員': 'admin',
        '分析師': 'analyst',
        '操作員': 'analyst',
        '查看者': 'user'
    }
    
    normalized = role_mapping.get(role, role)
    return normalized

def generate_jwt_token(user_data, expires_hours=24):
    """Generate JWT token for user authentication"""
    import datetime
    
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    
    original_role = user_data.get('role')
    normalized_role = normalize_role(original_role)
    
    payload = {
        'user_id': user_data.get('id'),
        'username': user_data.get('username'),
        'role': normalized_role,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=expires_hours),
        'iat': datetime.datetime.now(datetime.UTC)
    }
    
    return jwt.encode(payload, jwt_secret, algorithm='HS256')

def create_admin_token(user_id=1, username='admin'):
    """Create admin JWT token for testing purposes"""
    admin_data = {
        'id': user_id,
        'username': username,
        'role': 'admin'
    }
    return generate_jwt_token(admin_data)

def create_analyst_token():
    """Create analyst JWT token for testing purposes"""
    analyst_data = {
        'id': 2,
        'username': 'analyst',
        'role': 'analyst'
    }
    return generate_jwt_token(analyst_data)

def create_user_token():
    """Create user JWT token for testing purposes"""
    user_data = {
        'id': 3,
        'username': 'user',
        'role': 'user'
    }
    return generate_jwt_token(user_data)

def roles_required(*allowed_roles):
    """Decorator for endpoints requiring specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({
                    'error': 'Authorization header missing',
                    'message': 'Access denied. Please provide a valid JWT token.'
                }), 401
            
            try:
                token = auth_header.split(' ')[1]
            except (IndexError, AttributeError):
                return jsonify({
                    'error': 'Invalid authorization format',
                    'message': 'Authorization header must be in format: Bearer <token>'
                }), 401
            
            try:
                jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
                payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
                
                user_role = payload.get('role', 'user')
                normalized_role = normalize_role(user_role)
                
                if normalized_role not in allowed_roles and normalized_role not in ['超級管理員']:
                    return jsonify({
                        'error': 'Insufficient privileges',
                        'message': f'Access denied. Required role(s): {", ".join(allowed_roles)}'
                    }), 403
                
                request.current_user = {
                    'user_id': payload.get('user_id'),
                    'username': payload.get('username'),
                    'role': normalized_role
                }
                
                return f(*args, **kwargs)
                
            except jwt.ExpiredSignatureError:
                return jsonify({
                    'error': 'Token expired',
                    'message': 'JWT token has expired. Please login again.'
                }), 401
            except jwt.InvalidTokenError:
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'JWT token is invalid or malformed.'
                }), 401
            except Exception as e:
                return jsonify({
                    'error': 'Authentication failed',
                    'message': 'Unable to verify JWT token.'
                }), 401
        
        return decorated_function
    return decorator
