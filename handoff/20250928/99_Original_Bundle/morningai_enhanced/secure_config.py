"""
安全配置管理器
管理系統的安全配置和環境變量
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
import base64
import logging
from pathlib import Path

class SecureConfigManager:
    """安全配置管理器"""
    
    def __init__(self, config_file: str = "config.yaml", encryption_key: Optional[str] = None):
        self.config_file = config_file
        self.encryption_key = encryption_key or self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        self.config = {}
        self.logger = self._setup_logger()
        self._load_config()
    
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger('secure_config')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _get_or_create_encryption_key(self) -> bytes:
        """獲取或創建加密密鑰"""
        key_file = ".encryption_key"
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                self.logger.warning(f"無法讀取加密密鑰文件: {e}")
        
        # 生成新的加密密鑰
        key = Fernet.generate_key()
        
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # 設置文件權限（僅所有者可讀寫）
            os.chmod(key_file, 0o600)
            self.logger.info("已生成新的加密密鑰")
            
        except Exception as e:
            self.logger.error(f"無法保存加密密鑰: {e}")
        
        return key
    
    def _load_config(self):
        """加載配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                        self.config = yaml.safe_load(f) or {}
                    else:
                        self.config = json.load(f)
                
                self.logger.info(f"已加載配置文件: {self.config_file}")
            else:
                self.config = self._create_default_config()
                self._save_config()
                self.logger.info("已創建默認配置文件")
                
        except Exception as e:
            self.logger.error(f"加載配置文件失敗: {e}")
            self.config = self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """創建默認配置"""
        return {
            'security': {
                'secret_key': self._generate_secret_key(),
                'jwt_expiration_hours': 24,
                'max_login_attempts': 5,
                'lockout_duration_minutes': 30,
                'password_min_length': 8,
                'require_special_chars': True,
                'session_timeout_minutes': 60
            },
            'api': {
                'rate_limit_per_hour': 1000,
                'max_request_size_mb': 10,
                'allowed_origins': ['*'],
                'require_https': False  # 開發環境設為False
            },
            'database': {
                'connection_pool_size': 20,
                'connection_timeout_seconds': 30,
                'query_timeout_seconds': 300,
                'backup_enabled': True,
                'backup_interval_hours': 24
            },
            'ai_services': {
                'openai_api_key': '',  # 需要用戶設置
                'max_tokens_per_request': 4000,
                'request_timeout_seconds': 60,
                'retry_attempts': 3,
                'cost_limit_per_day': 100.0
            },
            'monitoring': {
                'log_level': 'INFO',
                'metrics_enabled': True,
                'alert_email': '',
                'health_check_interval_seconds': 60
            },
            'encryption': {
                'algorithm': 'AES-256',
                'key_rotation_days': 90,
                'encrypt_sensitive_data': True
            }
        }
    
    def _generate_secret_key(self) -> str:
        """生成安全密鑰"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            # 設置配置文件權限
            os.chmod(self.config_file, 0o600)
            
        except Exception as e:
            self.logger.error(f"保存配置文件失敗: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, encrypt: bool = False):
        """設置配置值"""
        keys = key.split('.')
        config = self.config
        
        # 導航到正確的嵌套位置
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 如果需要加密
        if encrypt and isinstance(value, str):
            value = self._encrypt_value(value)
        
        config[keys[-1]] = value
        self._save_config()
        
        self.logger.info(f"已更新配置: {key}")
    
    def get_secret(self, key: str, default: Any = None) -> Any:
        """獲取加密的敏感配置值"""
        encrypted_value = self.get(key, default)
        
        if encrypted_value and isinstance(encrypted_value, str):
            try:
                return self._decrypt_value(encrypted_value)
            except Exception as e:
                self.logger.warning(f"解密配置值失敗 {key}: {e}")
                return default
        
        return encrypted_value
    
    def set_secret(self, key: str, value: str):
        """設置加密的敏感配置值"""
        self.set(key, value, encrypt=True)
    
    def _encrypt_value(self, value: str) -> str:
        """加密值"""
        try:
            encrypted_bytes = self.fernet.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            self.logger.error(f"加密失敗: {e}")
            raise
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """解密值"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            self.logger.error(f"解密失敗: {e}")
            raise
    
    def validate_config(self) -> List[str]:
        """驗證配置的完整性和安全性"""
        issues = []
        
        # 檢查必需的配置項
        required_configs = [
            'security.secret_key',
            'database.connection_pool_size',
            'ai_services.max_tokens_per_request'
        ]
        
        for config_key in required_configs:
            if not self.get(config_key):
                issues.append(f"缺少必需配置: {config_key}")
        
        # 檢查安全配置
        secret_key = self.get('security.secret_key')
        if secret_key and len(secret_key) < 32:
            issues.append("安全密鑰長度不足（建議至少32字符）")
        
        # 檢查密碼策略
        min_length = self.get('security.password_min_length', 8)
        if min_length < 8:
            issues.append("密碼最小長度設置過低（建議至少8字符）")
        
        # 檢查API限制
        rate_limit = self.get('api.rate_limit_per_hour', 0)
        if rate_limit <= 0:
            issues.append("API速率限制未設置或設置不當")
        
        # 檢查生產環境安全設置
        if self.get('api.require_https') is False:
            issues.append("生產環境應啟用HTTPS要求")
        
        allowed_origins = self.get('api.allowed_origins', [])
        if '*' in allowed_origins:
            issues.append("CORS設置過於寬鬆，建議限制允許的來源")
        
        return issues
    
    def get_security_headers(self) -> Dict[str, str]:
        """獲取安全HTTP頭"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def export_config_template(self, output_file: str = "config_template.yaml"):
        """導出配置模板"""
        template = self._create_default_config()
        
        # 移除敏感信息
        template['security']['secret_key'] = '<GENERATE_NEW_SECRET_KEY>'
        template['ai_services']['openai_api_key'] = '<YOUR_OPENAI_API_KEY>'
        template['monitoring']['alert_email'] = '<YOUR_ALERT_EMAIL>'
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(template, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"配置模板已導出到: {output_file}")
            
        except Exception as e:
            self.logger.error(f"導出配置模板失敗: {e}")
    
    def backup_config(self, backup_dir: str = "config_backups"):
        """備份配置文件"""
        try:
            Path(backup_dir).mkdir(exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"config_backup_{timestamp}.yaml")
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            
            # 設置備份文件權限
            os.chmod(backup_file, 0o600)
            
            self.logger.info(f"配置已備份到: {backup_file}")
            return backup_file
            
        except Exception as e:
            self.logger.error(f"備份配置失敗: {e}")
            return None
    
    def restore_config(self, backup_file: str):
        """從備份恢復配置"""
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"備份文件不存在: {backup_file}")
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
            
            self._save_config()
            self.logger.info(f"已從備份恢復配置: {backup_file}")
            
        except Exception as e:
            self.logger.error(f"恢復配置失敗: {e}")
            raise
    
    def get_environment_config(self) -> Dict[str, str]:
        """獲取環境變量配置"""
        env_config = {}
        
        # 從配置中提取需要設置為環境變量的值
        mappings = {
            'FLASK_SECRET_KEY': 'security.secret_key',
            'DATABASE_URL': 'database.url',
            'OPENAI_API_KEY': 'ai_services.openai_api_key',
            'LOG_LEVEL': 'monitoring.log_level',
            'REDIS_URL': 'cache.redis_url'
        }
        
        for env_var, config_key in mappings.items():
            value = self.get(config_key)
            if value:
                env_config[env_var] = str(value)
        
        return env_config
    
    def apply_environment_overrides(self):
        """應用環境變量覆蓋"""
        overrides = {
            'FLASK_SECRET_KEY': 'security.secret_key',
            'DATABASE_URL': 'database.url',
            'OPENAI_API_KEY': 'ai_services.openai_api_key',
            'LOG_LEVEL': 'monitoring.log_level',
            'API_RATE_LIMIT': 'api.rate_limit_per_hour'
        }
        
        for env_var, config_key in overrides.items():
            env_value = os.environ.get(env_var)
            if env_value:
                # 嘗試轉換數據類型
                if env_var == 'API_RATE_LIMIT':
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        continue
                
                self.set(config_key, env_value)
                self.logger.info(f"已應用環境變量覆蓋: {env_var} -> {config_key}")

def create_production_config() -> SecureConfigManager:
    """創建生產環境配置"""
    config_manager = SecureConfigManager("production_config.yaml")
    
    # 設置生產環境特定配置
    config_manager.set('api.require_https', True)
    config_manager.set('api.allowed_origins', ['https://your-domain.com'])
    config_manager.set('monitoring.log_level', 'WARNING')
    config_manager.set('security.session_timeout_minutes', 30)
    config_manager.set('database.backup_enabled', True)
    
    return config_manager

def create_development_config() -> SecureConfigManager:
    """創建開發環境配置"""
    config_manager = SecureConfigManager("development_config.yaml")
    
    # 設置開發環境特定配置
    config_manager.set('api.require_https', False)
    config_manager.set('api.allowed_origins', ['*'])
    config_manager.set('monitoring.log_level', 'DEBUG')
    config_manager.set('security.session_timeout_minutes', 120)
    
    return config_manager

if __name__ == '__main__':
    # 示例用法
    config = SecureConfigManager()
    
    # 驗證配置
    issues = config.validate_config()
    if issues:
        print("配置問題:")
        for issue in issues:
            print(f"  - {issue}")
    
    # 導出模板
    config.export_config_template()
    
    print("安全配置管理器初始化完成")

