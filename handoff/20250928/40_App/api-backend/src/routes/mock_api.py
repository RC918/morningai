from flask import Blueprint, jsonify, request
from datetime import datetime
import random

mock_api = Blueprint('mock_api', __name__)

@mock_api.route('/api/dashboard/mock', methods=['GET'])
def dashboard_mock():
    """Mock dashboard data for design team integration"""
    return jsonify({
        "widgets": [
            {
                "id": "cpu_usage",
                "value": random.randint(60, 85),
                "status": "normal",
                "trend": "stable"
            },
            {
                "id": "memory_usage", 
                "value": random.randint(55, 80),
                "status": "normal",
                "trend": "increasing"
            },
            {
                "id": "active_strategies",
                "value": random.randint(8, 15),
                "status": "active",
                "trend": "stable"
            },
            {
                "id": "pending_approvals",
                "value": random.randint(2, 8),
                "status": "pending",
                "trend": "decreasing"
            }
        ],
        "recent_decisions": [
            {
                "id": 1,
                "strategy": "CPU優化策略",
                "status": "executed",
                "confidence": 0.87,
                "timestamp": "2024-01-01T14:30:00Z",
                "impact": "+15% 性能提升"
            },
            {
                "id": 2,
                "strategy": "緩存優化",
                "status": "pending",
                "confidence": 0.92,
                "timestamp": "2024-01-01T14:15:00Z",
                "impact": "預計 +20% 響應速度"
            }
        ],
        "system_metrics": {
            "uptime": "99.7%",
            "response_time": f"{random.randint(120, 180)}ms",
            "error_rate": f"{random.uniform(0.01, 0.05):.3f}%",
            "throughput": f"{random.randint(800, 1200)} req/min"
        },
        "timestamp": datetime.now().isoformat()
    })

@mock_api.route('/api/checkout/mock', methods=['GET', 'POST'])
def checkout_mock():
    """Mock checkout data for design team integration"""
    if request.method == 'POST':
        return jsonify({
            "checkout_session": {
                "id": f"mock_session_{random.randint(1000, 9999)}",
                "status": "created",
                "payment_url": "https://checkout.stripe.com/mock",
                "expires_at": datetime.now().isoformat()
            },
            "success": True,
            "message": "Checkout session created successfully"
        })
    
    return jsonify({
        "payment_methods": [
            {
                "id": "credit_card",
                "name": "信用卡",
                "icon": "credit-card",
                "enabled": True
            },
            {
                "id": "paypal", 
                "name": "PayPal",
                "icon": "paypal",
                "enabled": True
            },
            {
                "id": "stripe",
                "name": "Stripe",
                "icon": "stripe", 
                "enabled": True
            }
        ],
        "pricing_tiers": [
            {
                "id": "basic",
                "name": "Basic",
                "price": 29,
                "currency": "USD",
                "billing": "monthly",
                "features": [
                    "基礎功能",
                    "5個策略",
                    "基本監控",
                    "郵件支援"
                ],
                "popular": False
            },
            {
                "id": "pro",
                "name": "Pro", 
                "price": 99,
                "currency": "USD",
                "billing": "monthly",
                "features": [
                    "進階功能",
                    "無限策略",
                    "即時監控",
                    "優先支援",
                    "API 存取"
                ],
                "popular": True
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": 299,
                "currency": "USD", 
                "billing": "monthly",
                "features": [
                    "企業級功能",
                    "客製化策略",
                    "專屬監控",
                    "24/7 支援",
                    "完整 API",
                    "SLA 保證"
                ],
                "popular": False
            }
        ],
        "discounts": [
            {
                "code": "EARLY2024",
                "discount": 20,
                "type": "percentage",
                "valid_until": "2024-12-31"
            }
        ]
    })

@mock_api.route('/api/settings/mock', methods=['GET', 'POST'])
def settings_mock():
    """Mock settings data for design team integration"""
    if request.method == 'POST':
        settings_data = request.get_json() or {}
        return jsonify({
            "success": True,
            "message": "Settings updated successfully",
            "updated_settings": settings_data,
            "timestamp": datetime.now().isoformat()
        })
    
    return jsonify({
        "user_preferences": {
            "theme": "light",
            "language": "zh-TW",
            "timezone": "Asia/Taipei",
            "notifications": {
                "email": True,
                "push": True,
                "sms": False,
                "slack": True
            },
            "dashboard_layout": "grid",
            "auto_refresh": 30
        },
        "system_config": {
            "auto_approval": False,
            "risk_threshold": 0.8,
            "monitoring_interval": 300,
            "backup_frequency": "daily",
            "log_retention": 30,
            "api_rate_limit": 1000
        },
        "security_settings": {
            "two_factor_enabled": True,
            "session_timeout": 3600,
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_numbers": True,
                "require_symbols": True
            },
            "ip_whitelist": [],
            "audit_logging": True
        },
        "integration_settings": {
            "slack_webhook": "https://hooks.slack.com/mock",
            "email_provider": "sendgrid",
            "monitoring_tools": ["prometheus", "grafana"],
            "backup_provider": "aws_s3"
        },
        "billing_info": {
            "current_plan": "pro",
            "billing_cycle": "monthly",
            "next_billing_date": "2024-02-01",
            "payment_method": "credit_card_****1234"
        }
    })

@mock_api.route('/api/phase9/stripe/mock', methods=['GET', 'POST'])
def phase9_stripe_mock():
    """Mock Phase 9 Stripe integration for research"""
    return jsonify({
        "stripe_config": {
            "publishable_key": "pk_test_mock_key",
            "webhook_endpoint": "/api/stripe/webhook",
            "supported_currencies": ["USD", "EUR", "TWD"],
            "payment_methods": ["card", "alipay", "wechat_pay"]
        },
        "subscription_flows": [
            {
                "flow_id": "trial_to_paid",
                "steps": ["trial_signup", "payment_method", "subscription_create"],
                "duration": "14_days"
            },
            {
                "flow_id": "freemium_upgrade", 
                "steps": ["feature_gate", "pricing_page", "checkout"],
                "conversion_rate": "12%"
            }
        ],
        "refund_policies": {
            "trial_period": "14_days",
            "refund_window": "30_days",
            "partial_refunds": True,
            "auto_refund_threshold": 100
        }
    })

@mock_api.route('/api/phase9/tappay/mock', methods=['GET', 'POST'])
def phase9_tappay_mock():
    """Mock Phase 9 TapPay integration for research"""
    return jsonify({
        "tappay_config": {
            "app_id": "mock_app_id",
            "app_key": "mock_app_key",
            "server_type": "sandbox",
            "supported_methods": ["credit_card", "line_pay", "jko_pay"]
        },
        "payment_flows": [
            {
                "method": "credit_card",
                "steps": ["card_input", "3d_secure", "payment_confirm"],
                "success_rate": "98.5%"
            },
            {
                "method": "line_pay",
                "steps": ["line_auth", "payment_confirm"],
                "success_rate": "99.2%"
            }
        ],
        "localization": {
            "supported_languages": ["zh-TW", "en-US"],
            "currency": "TWD",
            "tax_handling": "inclusive"
        }
    })
