#!/usr/bin/env python3
"""
AI 治理模組
實現三層權限架構和治理規則管理
基於 Phase 6 PRD 規範
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from flask import Flask, request, jsonify, render_template_string
import jwt
import secrets

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """用戶角色定義"""
    PLATFORM_ADMIN = "platform_admin"    # 平台管理員
    TENANT_ADMIN = "tenant_admin"         # 租戶管理員
    TENANT_USER = "tenant_user"           # 租戶用戶

class GovernanceRuleType(Enum):
    """治理規則類型"""
    BLACKLIST = "blacklist"               # 黑名單
    WHITELIST = "whitelist"               # 白名單
    CONTENT_FILTER = "content_filter"     # 內容過濾
    USAGE_LIMIT = "usage_limit"           # 使用量限制

@dataclass
class GovernanceRule:
    """治理規則"""
    rule_id: str
    rule_type: GovernanceRuleType
    name: str
    description: str
    config: Dict[str, Any]
    enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class User:
    """用戶"""
    user_id: str
    username: str
    email: str
    role: UserRole
    tenant_id: Optional[str] = None
    permissions: List[str] = None
    created_at: datetime = None
    last_login: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.permissions is None:
            self.permissions = self._get_default_permissions()
    
    def _get_default_permissions(self) -> List[str]:
        """獲取角色默認權限"""
        if self.role == UserRole.PLATFORM_ADMIN:
            return [
                'manage_all_tenants',
                'manage_system_settings',
                'view_all_governance_rules',
                'manage_all_governance_rules',
                'view_system_analytics',
                'manage_users'
            ]
        elif self.role == UserRole.TENANT_ADMIN:
            return [
                'manage_tenant_settings',
                'view_tenant_governance_rules',
                'manage_tenant_governance_rules',
                'view_tenant_analytics',
                'manage_tenant_users'
            ]
        else:  # TENANT_USER
            return [
                'use_ai_features',
                'view_own_usage',
                'view_tenant_governance_rules'
            ]

class PermissionManager:
    """權限管理器"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, str] = {}  # session_token -> user_id
    
    def create_user(self, username: str, email: str, role: UserRole, tenant_id: Optional[str] = None) -> User:
        """創建用戶"""
        user_id = f"user_{secrets.token_urlsafe(8)}"
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            tenant_id=tenant_id
        )
        self.users[user_id] = user
        logger.info(f"Created user: {username} ({role.value})")
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """用戶認證，返回 session token"""
        for user in self.users.values():
            if user.username == username:
                session_token = secrets.token_urlsafe(32)
                self.sessions[session_token] = user.user_id
                user.last_login = datetime.now()
                logger.info(f"User authenticated: {username}")
                return session_token
        return None
    
    def get_user_from_session(self, session_token: str) -> Optional[User]:
        """從 session token 獲取用戶"""
        user_id = self.sessions.get(session_token)
        if user_id:
            return self.users.get(user_id)
        return None
    
    def check_permission(self, user: User, permission: str) -> bool:
        """檢查用戶權限"""
        return permission in user.permissions
    
    def get_accessible_tenants(self, user: User) -> List[str]:
        """獲取用戶可訪問的租戶列表"""
        if user.role == UserRole.PLATFORM_ADMIN:
            return list(set(u.tenant_id for u in self.users.values() if u.tenant_id))
        elif user.role == UserRole.TENANT_ADMIN or user.role == UserRole.TENANT_USER:
            return [user.tenant_id] if user.tenant_id else []
        return []

class GovernanceRuleManager:
    """治理規則管理器"""
    
    def __init__(self):
        self.rules: Dict[str, GovernanceRule] = {}
        self.tenant_rules: Dict[str, List[str]] = {}  # tenant_id -> rule_ids
    
    def create_rule(self, tenant_id: str, rule_type: GovernanceRuleType, name: str, 
                   description: str, config: Dict[str, Any]) -> GovernanceRule:
        """創建治理規則"""
        rule_id = f"rule_{secrets.token_urlsafe(8)}"
        rule = GovernanceRule(
            rule_id=rule_id,
            rule_type=rule_type,
            name=name,
            description=description,
            config=config
        )
        
        self.rules[rule_id] = rule
        
        if tenant_id not in self.tenant_rules:
            self.tenant_rules[tenant_id] = []
        self.tenant_rules[tenant_id].append(rule_id)
        
        logger.info(f"Created governance rule: {name} for tenant {tenant_id}")
        return rule
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """更新治理規則"""
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_at = datetime.now()
        logger.info(f"Updated governance rule: {rule_id}")
        return True
    
    def delete_rule(self, rule_id: str) -> bool:
        """刪除治理規則"""
        if rule_id not in self.rules:
            return False
        
        for tenant_id, rule_ids in self.tenant_rules.items():
            if rule_id in rule_ids:
                rule_ids.remove(rule_id)
        
        del self.rules[rule_id]
        logger.info(f"Deleted governance rule: {rule_id}")
        return True
    
    def get_tenant_rules(self, tenant_id: str) -> List[GovernanceRule]:
        """獲取租戶的治理規則"""
        rule_ids = self.tenant_rules.get(tenant_id, [])
        return [self.rules[rule_id] for rule_id in rule_ids if rule_id in self.rules]
    
    def validate_rule_config(self, rule_type: GovernanceRuleType, config: Dict[str, Any]) -> bool:
        """驗證規則配置"""
        if rule_type == GovernanceRuleType.BLACKLIST:
            return 'domains' in config and isinstance(config['domains'], list)
        elif rule_type == GovernanceRuleType.WHITELIST:
            return 'domains' in config and isinstance(config['domains'], list)
        elif rule_type == GovernanceRuleType.CONTENT_FILTER:
            return 'keywords' in config and isinstance(config['keywords'], list)
        elif rule_type == GovernanceRuleType.USAGE_LIMIT:
            return 'max_tokens' in config and isinstance(config['max_tokens'], int)
        return False
    
    def apply_rules(self, tenant_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """應用治理規則"""
        rules = self.get_tenant_rules(tenant_id)
        result = {
            'allowed': True,
            'blocked_by': [],
            'modified_request': request_data.copy()
        }
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            if rule.rule_type == GovernanceRuleType.BLACKLIST:
                if self._check_blacklist(rule.config, request_data):
                    result['allowed'] = False
                    result['blocked_by'].append(rule.name)
            
            elif rule.rule_type == GovernanceRuleType.WHITELIST:
                if not self._check_whitelist(rule.config, request_data):
                    result['allowed'] = False
                    result['blocked_by'].append(rule.name)
            
            elif rule.rule_type == GovernanceRuleType.CONTENT_FILTER:
                result['modified_request'] = self._apply_content_filter(rule.config, result['modified_request'])
            
            elif rule.rule_type == GovernanceRuleType.USAGE_LIMIT:
                if not self._check_usage_limit(rule.config, request_data):
                    result['allowed'] = False
                    result['blocked_by'].append(rule.name)
        
        return result
    
    def _check_blacklist(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        """檢查黑名單"""
        domains = config.get('domains', [])
        request_url = request_data.get('url', '')
        return any(domain in request_url for domain in domains)
    
    def _check_whitelist(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        """檢查白名單"""
        domains = config.get('domains', [])
        request_url = request_data.get('url', '')
        return any(domain in request_url for domain in domains)
    
    def _apply_content_filter(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """應用內容過濾"""
        keywords = config.get('keywords', [])
        content = request_data.get('content', '')
        
        for keyword in keywords:
            content = content.replace(keyword, '*' * len(keyword))
        
        request_data['content'] = content
        return request_data
    
    def _check_usage_limit(self, config: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        """檢查使用量限制"""
        max_tokens = config.get('max_tokens', float('inf'))
        request_tokens = request_data.get('estimated_tokens', 0)
        return request_tokens <= max_tokens

class AIGovernanceModule:
    """AI 治理模組主類"""
    
    def __init__(self):
        self.permission_manager = PermissionManager()
        self.rule_manager = GovernanceRuleManager()
        self.app = Flask(__name__)
        self._setup_routes()
        
        self.permission_manager.create_user(
            username="admin",
            email="admin@morningai.com",
            role=UserRole.PLATFORM_ADMIN
        )
        
        logger.info("AI Governance Module initialized")
    
    def _setup_routes(self):
        """設置路由"""
        
        @self.app.route('/governance/login', methods=['POST'])
        def login():
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            session_token = self.permission_manager.authenticate_user(username, password)
            if session_token:
                return jsonify({
                    'success': True,
                    'session_token': session_token
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid credentials'
                }), 401
        
        @self.app.route('/governance/rules', methods=['GET'])
        def get_rules():
            session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            user = self.permission_manager.get_user_from_session(session_token)
            
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401
            
            if user.role == UserRole.PLATFORM_ADMIN:
                rules = list(self.rule_manager.rules.values())
            else:
                rules = self.rule_manager.get_tenant_rules(user.tenant_id)
            
            return jsonify({
                'rules': [asdict(rule) for rule in rules]
            })
        
        @self.app.route('/governance/rules', methods=['POST'])
        def create_rule():
            session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            user = self.permission_manager.get_user_from_session(session_token)
            
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401
            
            if not self.permission_manager.check_permission(user, 'manage_tenant_governance_rules') and \
               not self.permission_manager.check_permission(user, 'manage_all_governance_rules'):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            data = request.get_json()
            rule_type = GovernanceRuleType(data.get('rule_type'))
            
            if not self.rule_manager.validate_rule_config(rule_type, data.get('config', {})):
                return jsonify({'error': 'Invalid rule configuration'}), 400
            
            tenant_id = data.get('tenant_id', user.tenant_id)
            
            rule = self.rule_manager.create_rule(
                tenant_id=tenant_id,
                rule_type=rule_type,
                name=data.get('name'),
                description=data.get('description'),
                config=data.get('config')
            )
            
            return jsonify({
                'success': True,
                'rule': asdict(rule)
            })
        
        @self.app.route('/governance/rules/<rule_id>', methods=['PUT'])
        def update_rule(rule_id):
            session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            user = self.permission_manager.get_user_from_session(session_token)
            
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401
            
            if not self.permission_manager.check_permission(user, 'manage_tenant_governance_rules') and \
               not self.permission_manager.check_permission(user, 'manage_all_governance_rules'):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            data = request.get_json()
            success = self.rule_manager.update_rule(rule_id, data)
            
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Rule not found'}), 404
        
        @self.app.route('/governance/rules/<rule_id>', methods=['DELETE'])
        def delete_rule(rule_id):
            session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            user = self.permission_manager.get_user_from_session(session_token)
            
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401
            
            if not self.permission_manager.check_permission(user, 'manage_tenant_governance_rules') and \
               not self.permission_manager.check_permission(user, 'manage_all_governance_rules'):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            success = self.rule_manager.delete_rule(rule_id)
            
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Rule not found'}), 404
        
        @self.app.route('/governance/apply', methods=['POST'])
        def apply_governance():
            """應用治理規則到請求"""
            session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            user = self.permission_manager.get_user_from_session(session_token)
            
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401
            
            data = request.get_json()
            tenant_id = user.tenant_id
            
            result = self.rule_manager.apply_rules(tenant_id, data)
            
            return jsonify(result)
        
        @self.app.route('/governance/dashboard')
        def dashboard():
            """治理主控台"""
            return render_template_string(GOVERNANCE_DASHBOARD_HTML)
    
    def run(self, host='0.0.0.0', port=5002, debug=False):
        """運行治理模組"""
        logger.info(f"Starting AI Governance Module on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

GOVERNANCE_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Morning AI - 治理主控台</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        .header {
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #333;
            margin: 0;
        }
        .header p {
            color: #666;
            margin: 5px 0 0 0;
        }
        .section {
            margin-bottom: 30px;
        }
        .section h2 {
            color: #333;
            border-left: 4px solid #007bff;
            padding-left: 15px;
            margin-bottom: 20px;
        }
        .card {
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 15px;
            background: #fafafa;
        }
        .card h3 {
            margin-top: 0;
            color: #333;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .badge.platform-admin {
            background: #dc3545;
            color: white;
        }
        .badge.tenant-admin {
            background: #ffc107;
            color: black;
        }
        .badge.tenant-user {
            background: #28a745;
            color: white;
        }
        .btn {
            display: inline-block;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            font-size: 14px;
            margin-right: 10px;
        }
        .btn-primary {
            background: #007bff;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .rule-config {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Morning AI 治理主控台</h1>
            <p>AI 治理模組與權限分層管理系統</p>
        </div>
        
        <div class="section">
            <h2>📊 系統概覽</h2>
            <div class="card">
                <h3>權限架構</h3>
                <p><span class="badge platform-admin">Platform Admin</span> 平台管理員 - 擁有最高權限，可管理所有租戶和系統設定</p>
                <p><span class="badge tenant-admin">Tenant Admin</span> 租戶管理員 - 管理單一租戶的權限，可管理該租戶的使用者和設定</p>
                <p><span class="badge tenant-user">Tenant User</span> 租戶用戶 - 擁有最基本權限，只能使用該租戶的 AI 功能</p>
            </div>
        </div>
        
        <div class="section">
            <h2>⚙️ 治理規則類型</h2>
            <div class="card">
                <h3>🚫 黑名單/白名單</h3>
                <p>限制 AI 能存取的網站或服務</p>
                <div class="rule-config">
                {
                  "rule_type": "blacklist",
                  "config": {
                    "domains": ["example.com", "blocked-site.com"]
                  }
                }
                </div>
            </div>
            
            <div class="card">
                <h3>🔍 內容過濾</h3>
                <p>過濾掉不適當的內容</p>
                <div class="rule-config">
                {
                  "rule_type": "content_filter",
                  "config": {
                    "keywords": ["敏感詞", "不當內容"]
                  }
                }
                </div>
            </div>
            
            <div class="card">
                <h3>📊 使用量限制</h3>
                <p>限制 AI 的 Token 使用量或排程時數</p>
                <div class="rule-config">
                {
                  "rule_type": "usage_limit",
                  "config": {
                    "max_tokens": 10000,
                    "time_window": "daily"
                  }
                }
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🎛️ 管理功能</h2>
            <div class="card">
                <h3>API 端點</h3>
                <p><strong>POST /governance/login</strong> - 用戶登入</p>
                <p><strong>GET /governance/rules</strong> - 獲取治理規則</p>
                <p><strong>POST /governance/rules</strong> - 創建治理規則</p>
                <p><strong>PUT /governance/rules/{rule_id}</strong> - 更新治理規則</p>
                <p><strong>DELETE /governance/rules/{rule_id}</strong> - 刪除治理規則</p>
                <p><strong>POST /governance/apply</strong> - 應用治理規則</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 使用說明</h2>
            <div class="card">
                <h3>快速開始</h3>
                <ol>
                    <li>使用 <code>admin</code> 用戶登入系統</li>
                    <li>創建租戶管理員和用戶</li>
                    <li>配置治理規則</li>
                    <li>測試規則應用效果</li>
                </ol>
                <button class="btn btn-primary">開始使用</button>
                <button class="btn btn-secondary">查看文檔</button>
            </div>
        </div>
    </div>
</body>
</html>
"""

def main():
    """主函數"""
    governance_module = AIGovernanceModule()
    
    tenant_admin = governance_module.permission_manager.create_user(
        username="tenant_admin",
        email="tenant@example.com",
        role=UserRole.TENANT_ADMIN,
        tenant_id="tenant_001"
    )
    
    tenant_user = governance_module.permission_manager.create_user(
        username="tenant_user",
        email="user@example.com",
        role=UserRole.TENANT_USER,
        tenant_id="tenant_001"
    )
    
    governance_module.rule_manager.create_rule(
        tenant_id="tenant_001",
        rule_type=GovernanceRuleType.BLACKLIST,
        name="禁止訪問社交媒體",
        description="禁止 AI 訪問社交媒體網站",
        config={
            "domains": ["facebook.com", "twitter.com", "instagram.com"]
        }
    )
    
    governance_module.rule_manager.create_rule(
        tenant_id="tenant_001",
        rule_type=GovernanceRuleType.USAGE_LIMIT,
        name="每日 Token 限制",
        description="限制每日最大 Token 使用量",
        config={
            "max_tokens": 10000,
            "time_window": "daily"
        }
    )
    
    governance_module.run(debug=True)

if __name__ == "__main__":
    main()
