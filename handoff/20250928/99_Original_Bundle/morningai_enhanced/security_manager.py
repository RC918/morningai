"""
安全管理器
提供密鑰管理、API安全、通信加密和審計日誌功能
"""

import os
import json
import hashlib
import hmac
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets
import jwt
from functools import wraps
from flask import request, jsonify, current_app

class KeyManagementService:
    """密鑰管理服務"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.environ.get('MASTER_KEY', self._generate_master_key())
        self.fernet = self._create_fernet_instance()
        self.keys_cache = {}
        
    def _generate_master_key(self) -> str:
        """生成主密鑰"""
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    def _create_fernet_instance(self) -> Fernet:
        """創建Fernet加密實例"""
        key = base64.urlsafe_b64encode(self.master_key.encode()[:32].ljust(32, b'\0'))
        return Fernet(key)
    
    def encrypt_secret(self, secret: str, key_id: str) -> str:
        """加密敏感信息"""
        try:
            encrypted_data = self.fernet.encrypt(secret.encode())
            self.keys_cache[key_id] = {
                'encrypted_data': encrypted_data,
                'created_at': datetime.now(),
                'access_count': 0
            }
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            raise Exception(f"加密失敗: {str(e)}")
    
    def decrypt_secret(self, encrypted_secret: str, key_id: str) -> str:
        """解密敏感信息"""
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_secret.encode())
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            # 更新訪問計數
            if key_id in self.keys_cache:
                self.keys_cache[key_id]['access_count'] += 1
                
            return decrypted_data.decode()
        except Exception as e:
            raise Exception(f"解密失敗: {str(e)}")
    
    def rotate_key(self, key_id: str) -> str:
        """輪換密鑰"""
        if key_id in self.keys_cache:
            old_data = self.keys_cache[key_id]
            # 生成新的加密密鑰
            new_master_key = self._generate_master_key()
            old_fernet = self.fernet
            
            # 創建新的Fernet實例
            self.master_key = new_master_key
            self.fernet = self._create_fernet_instance()
            
            # 重新加密數據
            try:
                decrypted_data = old_fernet.decrypt(old_data['encrypted_data'])
                new_encrypted_data = self.fernet.encrypt(decrypted_data)
                
                self.keys_cache[key_id] = {
                    'encrypted_data': new_encrypted_data,
                    'created_at': datetime.now(),
                    'access_count': old_data['access_count'],
                    'rotated_from': old_data['created_at']
                }
                
                return base64.urlsafe_b64encode(new_encrypted_data).decode()
            except Exception as e:
                # 恢復舊密鑰
                self.master_key = old_master_key
                self.fernet = old_fernet
                raise Exception(f"密鑰輪換失敗: {str(e)}")
        else:
            raise Exception(f"密鑰 {key_id} 不存在")
    
    def get_key_info(self, key_id: str) -> Dict[str, Any]:
        """獲取密鑰信息"""
        if key_id in self.keys_cache:
            info = self.keys_cache[key_id].copy()
            # 不返回實際的加密數據
            info.pop('encrypted_data', None)
            return info
        else:
            raise Exception(f"密鑰 {key_id} 不存在")

class APISecurityManager:
    """API安全管理器"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.rate_limits = {}
        self.blocked_ips = set()
        
    def generate_api_key(self, user_id: str, permissions: List[str]) -> str:
        """生成API密鑰"""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'issued_at': time.time(),
            'expires_at': time.time() + 86400 * 30,  # 30天過期
            'api_key_id': secrets.token_urlsafe(16)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """驗證API密鑰"""
        try:
            payload = jwt.decode(api_key, self.secret_key, algorithms=['HS256'])
            
            # 檢查過期時間
            if time.time() > payload['expires_at']:
                raise Exception("API密鑰已過期")
            
            return payload
        except jwt.InvalidTokenError as e:
            raise Exception(f"無效的API密鑰: {str(e)}")
    
    def check_rate_limit(self, client_id: str, limit: int = 100, window: int = 3600) -> bool:
        """檢查速率限制"""
        current_time = time.time()
        window_start = current_time - window
        
        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = []
        
        # 清除過期的請求記錄
        self.rate_limits[client_id] = [
            req_time for req_time in self.rate_limits[client_id] 
            if req_time > window_start
        ]
        
        # 檢查是否超過限制
        if len(self.rate_limits[client_id]) >= limit:
            return False
        
        # 記錄當前請求
        self.rate_limits[client_id].append(current_time)
        return True
    
    def validate_request_signature(self, request_data: str, signature: str, timestamp: str) -> bool:
        """驗證請求簽名"""
        try:
            # 檢查時間戳（防止重放攻擊）
            request_time = float(timestamp)
            current_time = time.time()
            
            if abs(current_time - request_time) > 300:  # 5分鐘內有效
                return False
            
            # 計算預期簽名
            message = f"{timestamp}.{request_data}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # 使用安全的字符串比較
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception:
            return False
    
    def block_ip(self, ip_address: str, duration: int = 3600):
        """封鎖IP地址"""
        self.blocked_ips.add(ip_address)
        # 在實際應用中，應該將封鎖信息存儲到數據庫，並設置過期時間
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """檢查IP是否被封鎖"""
        return ip_address in self.blocked_ips

class CommunicationSecurity:
    """通信安全管理"""
    
    def __init__(self):
        self.session_keys = {}
        
    def generate_session_key(self, agent_id: str) -> str:
        """為Agent生成會話密鑰"""
        session_key = secrets.token_urlsafe(32)
        self.session_keys[agent_id] = {
            'key': session_key,
            'created_at': datetime.now(),
            'last_used': datetime.now()
        }
        return session_key
    
    def encrypt_message(self, message: str, agent_id: str) -> str:
        """加密Agent間通信消息"""
        if agent_id not in self.session_keys:
            raise Exception(f"Agent {agent_id} 沒有有效的會話密鑰")
        
        session_key = self.session_keys[agent_id]['key']
        fernet = Fernet(base64.urlsafe_b64encode(session_key.encode()[:32].ljust(32, b'\0')))
        
        encrypted_message = fernet.encrypt(message.encode())
        self.session_keys[agent_id]['last_used'] = datetime.now()
        
        return base64.urlsafe_b64encode(encrypted_message).decode()
    
    def decrypt_message(self, encrypted_message: str, agent_id: str) -> str:
        """解密Agent間通信消息"""
        if agent_id not in self.session_keys:
            raise Exception(f"Agent {agent_id} 沒有有效的會話密鑰")
        
        session_key = self.session_keys[agent_id]['key']
        fernet = Fernet(base64.urlsafe_b64encode(session_key.encode()[:32].ljust(32, b'\0')))
        
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_message.encode())
            decrypted_message = fernet.decrypt(encrypted_data)
            self.session_keys[agent_id]['last_used'] = datetime.now()
            
            return decrypted_message.decode()
        except Exception as e:
            raise Exception(f"消息解密失敗: {str(e)}")
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """清理過期的會話密鑰"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        expired_agents = [
            agent_id for agent_id, session_info in self.session_keys.items()
            if session_info['last_used'] < cutoff_time
        ]
        
        for agent_id in expired_agents:
            del self.session_keys[agent_id]

class AuditLogger:
    """審計日誌管理器"""
    
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger('audit')
        logger.setLevel(logging.INFO)
        
        # 創建文件處理器
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)
        
        # 創建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def log_api_access(self, user_id: str, endpoint: str, method: str, 
                      ip_address: str, user_agent: str, status_code: int):
        """記錄API訪問"""
        self.logger.info(json.dumps({
            'event_type': 'api_access',
            'user_id': user_id,
            'endpoint': endpoint,
            'method': method,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }))
    
    def log_authentication(self, user_id: str, success: bool, ip_address: str, reason: str = None):
        """記錄認證事件"""
        self.logger.info(json.dumps({
            'event_type': 'authentication',
            'user_id': user_id,
            'success': success,
            'ip_address': ip_address,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }))
    
    def log_decision_execution(self, decision_id: str, strategy_name: str, 
                             user_id: str, approved: bool, reason: str = None):
        """記錄決策執行"""
        self.logger.info(json.dumps({
            'event_type': 'decision_execution',
            'decision_id': decision_id,
            'strategy_name': strategy_name,
            'user_id': user_id,
            'approved': approved,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }))
    
    def log_security_event(self, event_type: str, severity: str, description: str, 
                          ip_address: str = None, user_id: str = None):
        """記錄安全事件"""
        self.logger.warning(json.dumps({
            'event_type': 'security_event',
            'security_event_type': event_type,
            'severity': severity,
            'description': description,
            'ip_address': ip_address,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }))
    
    def log_system_change(self, change_type: str, description: str, user_id: str, 
                         old_value: Any = None, new_value: Any = None):
        """記錄系統變更"""
        self.logger.info(json.dumps({
            'event_type': 'system_change',
            'change_type': change_type,
            'description': description,
            'user_id': user_id,
            'old_value': str(old_value) if old_value is not None else None,
            'new_value': str(new_value) if new_value is not None else None,
            'timestamp': datetime.now().isoformat()
        }))

class SecurityManager:
    """統一安全管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.kms = KeyManagementService(config.get('master_key'))
        self.api_security = APISecurityManager(config.get('secret_key', 'default-secret'))
        self.comm_security = CommunicationSecurity()
        self.audit_logger = AuditLogger(config.get('audit_log_file', 'audit.log'))
        
    def require_auth(self, f):
        """認證裝飾器"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # 獲取認證頭
                auth_header = request.headers.get('Authorization')
                if not auth_header:
                    self.audit_logger.log_security_event(
                        'unauthorized_access', 'warning',
                        'Missing authorization header',
                        request.remote_addr
                    )
                    return jsonify({'error': '缺少認證頭'}), 401
                
                # 驗證token
                token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
                payload = self.api_security.validate_api_key(token)
                
                # 檢查IP封鎖
                if self.api_security.is_ip_blocked(request.remote_addr):
                    self.audit_logger.log_security_event(
                        'blocked_ip_access', 'high',
                        f'Blocked IP attempted access: {request.remote_addr}',
                        request.remote_addr
                    )
                    return jsonify({'error': 'IP地址已被封鎖'}), 403
                
                # 檢查速率限制
                if not self.api_security.check_rate_limit(payload['user_id']):
                    self.audit_logger.log_security_event(
                        'rate_limit_exceeded', 'medium',
                        f'Rate limit exceeded for user: {payload["user_id"]}',
                        request.remote_addr, payload['user_id']
                    )
                    return jsonify({'error': '請求頻率過高'}), 429
                
                # 記錄API訪問
                self.audit_logger.log_api_access(
                    payload['user_id'], request.endpoint, request.method,
                    request.remote_addr, request.headers.get('User-Agent', ''),
                    200
                )
                
                # 將用戶信息添加到請求上下文
                request.current_user = payload
                
                return f(*args, **kwargs)
                
            except Exception as e:
                self.audit_logger.log_security_event(
                    'authentication_failure', 'medium',
                    f'Authentication failed: {str(e)}',
                    request.remote_addr
                )
                return jsonify({'error': '認證失敗'}), 401
                
        return decorated_function
    
    def require_permission(self, permission: str):
        """權限檢查裝飾器"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(request, 'current_user'):
                    return jsonify({'error': '未認證'}), 401
                
                user_permissions = request.current_user.get('permissions', [])
                if permission not in user_permissions:
                    self.audit_logger.log_security_event(
                        'permission_denied', 'medium',
                        f'Permission denied: {permission} for user {request.current_user["user_id"]}',
                        request.remote_addr, request.current_user['user_id']
                    )
                    return jsonify({'error': '權限不足'}), 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def validate_input(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """輸入驗證"""
        try:
            for field, rules in schema.items():
                if field not in data and rules.get('required', False):
                    raise ValueError(f"缺少必需字段: {field}")
                
                if field in data:
                    value = data[field]
                    
                    # 類型檢查
                    if 'type' in rules and not isinstance(value, rules['type']):
                        raise ValueError(f"字段 {field} 類型錯誤")
                    
                    # 長度檢查
                    if 'max_length' in rules and len(str(value)) > rules['max_length']:
                        raise ValueError(f"字段 {field} 長度超過限制")
                    
                    # 正則表達式檢查
                    if 'pattern' in rules:
                        import re
                        if not re.match(rules['pattern'], str(value)):
                            raise ValueError(f"字段 {field} 格式不正確")
            
            return True
            
        except ValueError as e:
            self.audit_logger.log_security_event(
                'input_validation_failure', 'low',
                f'Input validation failed: {str(e)}',
                request.remote_addr if request else None
            )
            return False

