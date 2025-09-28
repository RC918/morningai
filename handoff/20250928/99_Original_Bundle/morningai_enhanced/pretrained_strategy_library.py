"""
預訓練策略庫 - 為系統提供初始智慧
版本: 1.0
日期: 2025-09-12
作者: Manus AI

這個模塊包含了一套精心設計的預訓練策略，
讓 Morning AI 系統在第一天就具備強大的決策能力。
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum

# 配置日誌
logger = logging.getLogger(__name__)

class StrategyCategory(Enum):
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    COST_OPTIMIZATION = "cost_optimization"
    SECURITY = "security"
    BUSINESS_GROWTH = "business_growth"
    GENERAL = "general"

@dataclass
class PretrainedStrategy:
    """預訓練策略模板"""
    template_id: str
    name: str
    description: str
    category: StrategyCategory
    trigger_conditions: Dict[str, Any]
    template_content: Dict[str, Any]
    success_rate: float  # 基於行業最佳實踐的預期成功率
    average_impact: float  # 預期影響分數
    confidence_level: float  # 策略信心度
    source: str  # 策略來源（如：AWS Well-Architected, Google SRE, etc.）

class PretrainedStrategyLibrary:
    """預訓練策略庫"""
    
    def __init__(self):
        self.strategies: List[PretrainedStrategy] = []
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """初始化預訓練策略"""
        
        # 性能優化策略
        self.strategies.extend([
            PretrainedStrategy(
                template_id="perf_horizontal_scale",
                name="水平擴展策略",
                description="通過增加應用實例數量來處理更高負載，適用於無狀態應用",
                category=StrategyCategory.PERFORMANCE,
                trigger_conditions={
                    "cpu_usage_percent": {"min": 70, "max": 100},
                    "memory_usage_percent": {"min": 70, "max": 100},
                    "api_request_duration_p95": {"min": 1000, "max": 10000}
                },
                template_content={
                    "name_template": "水平擴展 - 增加 {scale_factor}x 實例",
                    "description_template": "將應用實例數量從 {current_instances} 增加到 {target_instances}，以處理當前 {cpu_usage}% CPU 使用率",
                    "base_expected_gain": 40.0,
                    "base_implementation_cost": 80.0,
                    "risk_level": "low",
                    "base_success_probability": 0.9,
                    "tasks_template": [
                        {"agent": "ops_agent", "action": "scale_instances", "params": {"scale_factor": "{scale_factor}"}},
                        {"agent": "monitoring_agent", "action": "verify_scaling", "params": {"timeout": 300}}
                    ],
                    "parameters": {
                        "scale_factor": {"type": "float", "min": 1.5, "max": 3.0, "default": 2.0},
                        "max_instances": {"type": "int", "min": 5, "max": 20, "default": 10}
                    }
                },
                success_rate=0.9,
                average_impact=35.0,
                confidence_level=0.95,
                source="AWS Well-Architected Framework"
            ),
            
            PretrainedStrategy(
                template_id="perf_redis_cache",
                name="Redis 緩存實施策略",
                description="實施 Redis 緩存層以減少資料庫負載和提升響應速度",
                category=StrategyCategory.PERFORMANCE,
                trigger_conditions={
                    "database_query_duration_p95": {"min": 500, "max": 5000},
                    "database_connection_pool_usage": {"min": 60, "max": 100},
                    "cache_hit_rate": {"min": 0, "max": 50}
                },
                template_content={
                    "name_template": "實施 Redis 緩存 - {cache_type} 模式",
                    "description_template": "為 {target_queries} 查詢實施 Redis 緩存，預期提升 {expected_improvement}% 性能",
                    "base_expected_gain": 50.0,
                    "base_implementation_cost": 60.0,
                    "risk_level": "medium",
                    "base_success_probability": 0.85,
                    "tasks_template": [
                        {"agent": "ops_agent", "action": "deploy_redis", "params": {"memory_size": "{redis_memory}"}},
                        {"agent": "dev_agent", "action": "implement_cache_layer", "params": {"cache_type": "{cache_type}"}},
                        {"agent": "monitoring_agent", "action": "monitor_cache_performance", "params": {}}
                    ],
                    "parameters": {
                        "cache_type": {"type": "string", "options": ["read-through", "write-behind", "cache-aside"], "default": "cache-aside"},
                        "redis_memory": {"type": "string", "options": ["1GB", "2GB", "4GB"], "default": "2GB"},
                        "ttl_seconds": {"type": "int", "min": 300, "max": 3600, "default": 1800}
                    }
                },
                success_rate=0.85,
                average_impact=45.0,
                confidence_level=0.9,
                source="Redis Best Practices Guide"
            ),
            
            PretrainedStrategy(
                template_id="perf_database_optimization",
                name="資料庫查詢優化策略",
                description="通過索引優化、查詢重寫和連接池調整來提升資料庫性能",
                category=StrategyCategory.PERFORMANCE,
                trigger_conditions={
                    "slow_query_count": {"min": 10, "max": 1000},
                    "database_cpu_usage": {"min": 60, "max": 100},
                    "database_query_duration_p95": {"min": 1000, "max": 10000}
                },
                template_content={
                    "name_template": "資料庫優化 - {optimization_type}",
                    "description_template": "針對 {slow_query_count} 個慢查詢進行 {optimization_type} 優化",
                    "base_expected_gain": 35.0,
                    "base_implementation_cost": 40.0,
                    "risk_level": "medium",
                    "base_success_probability": 0.8,
                    "tasks_template": [
                        {"agent": "dba_agent", "action": "analyze_slow_queries", "params": {}},
                        {"agent": "dba_agent", "action": "create_indexes", "params": {"index_type": "{index_type}"}},
                        {"agent": "dba_agent", "action": "optimize_connection_pool", "params": {"pool_size": "{pool_size}"}}
                    ],
                    "parameters": {
                        "optimization_type": {"type": "string", "options": ["index_optimization", "query_rewrite", "connection_tuning"], "default": "index_optimization"},
                        "index_type": {"type": "string", "options": ["btree", "hash", "gin"], "default": "btree"},
                        "pool_size": {"type": "int", "min": 10, "max": 100, "default": 20}
                    }
                },
                success_rate=0.8,
                average_impact=30.0,
                confidence_level=0.85,
                source="PostgreSQL Performance Tuning Guide"
            )
        ])
        
        # 可靠性策略
        self.strategies.extend([
            PretrainedStrategy(
                template_id="rel_circuit_breaker",
                name="熔斷器實施策略",
                description="實施熔斷器模式以防止級聯故障和提升系統韌性",
                category=StrategyCategory.RELIABILITY,
                trigger_conditions={
                    "error_rate_5xx": {"min": 5, "max": 50},
                    "api_timeout_rate": {"min": 10, "max": 100},
                    "downstream_service_availability": {"min": 0, "max": 95}
                },
                template_content={
                    "name_template": "熔斷器保護 - {service_name}",
                    "description_template": "為 {service_name} 實施熔斷器，錯誤率閾值 {error_threshold}%",
                    "base_expected_gain": 60.0,
                    "base_implementation_cost": 50.0,
                    "risk_level": "low",
                    "base_success_probability": 0.9,
                    "tasks_template": [
                        {"agent": "dev_agent", "action": "implement_circuit_breaker", "params": {"error_threshold": "{error_threshold}"}},
                        {"agent": "ops_agent", "action": "configure_fallback", "params": {"fallback_type": "{fallback_type}"}},
                        {"agent": "monitoring_agent", "action": "setup_circuit_breaker_alerts", "params": {}}
                    ],
                    "parameters": {
                        "error_threshold": {"type": "float", "min": 5.0, "max": 20.0, "default": 10.0},
                        "timeout_ms": {"type": "int", "min": 1000, "max": 10000, "default": 5000},
                        "fallback_type": {"type": "string", "options": ["cached_response", "default_value", "graceful_degradation"], "default": "cached_response"}
                    }
                },
                success_rate=0.9,
                average_impact=55.0,
                confidence_level=0.95,
                source="Netflix Hystrix Documentation"
            ),
            
            PretrainedStrategy(
                template_id="rel_health_check",
                name="健康檢查增強策略",
                description="實施深度健康檢查和自動恢復機制",
                category=StrategyCategory.RELIABILITY,
                trigger_conditions={
                    "service_availability": {"min": 90, "max": 99},
                    "health_check_failure_rate": {"min": 5, "max": 50},
                    "mean_time_to_recovery": {"min": 300, "max": 3600}
                },
                template_content={
                    "name_template": "健康檢查增強 - {check_type}",
                    "description_template": "實施 {check_type} 健康檢查，檢查間隔 {interval} 秒",
                    "base_expected_gain": 25.0,
                    "base_implementation_cost": 30.0,
                    "risk_level": "low",
                    "base_success_probability": 0.95,
                    "tasks_template": [
                        {"agent": "dev_agent", "action": "implement_health_checks", "params": {"check_type": "{check_type}"}},
                        {"agent": "ops_agent", "action": "configure_auto_recovery", "params": {"recovery_strategy": "{recovery_strategy}"}},
                        {"agent": "monitoring_agent", "action": "setup_health_alerts", "params": {"interval": "{interval}"}}
                    ],
                    "parameters": {
                        "check_type": {"type": "string", "options": ["shallow", "deep", "dependency"], "default": "deep"},
                        "interval": {"type": "int", "min": 10, "max": 300, "default": 30},
                        "recovery_strategy": {"type": "string", "options": ["restart", "failover", "scale"], "default": "restart"}
                    }
                },
                success_rate=0.95,
                average_impact=20.0,
                confidence_level=0.9,
                source="Kubernetes Health Check Best Practices"
            )
        ])
        
        # 成本優化策略
        self.strategies.extend([
            PretrainedStrategy(
                template_id="cost_auto_scaling",
                name="自動縮放優化策略",
                description="實施智能自動縮放以優化資源使用和成本",
                category=StrategyCategory.COST_OPTIMIZATION,
                trigger_conditions={
                    "resource_utilization": {"min": 0, "max": 40},
                    "cost_per_request": {"min": 0.01, "max": 1.0},
                    "idle_instance_percentage": {"min": 20, "max": 80}
                },
                template_content={
                    "name_template": "自動縮放優化 - {scaling_policy}",
                    "description_template": "實施 {scaling_policy} 縮放策略，目標利用率 {target_utilization}%",
                    "base_expected_gain": 30.0,
                    "base_implementation_cost": 40.0,
                    "risk_level": "medium",
                    "base_success_probability": 0.85,
                    "tasks_template": [
                        {"agent": "ops_agent", "action": "configure_autoscaling", "params": {"policy": "{scaling_policy}"}},
                        {"agent": "ops_agent", "action": "set_scaling_thresholds", "params": {"target_utilization": "{target_utilization}"}},
                        {"agent": "monitoring_agent", "action": "monitor_scaling_events", "params": {}}
                    ],
                    "parameters": {
                        "scaling_policy": {"type": "string", "options": ["target_tracking", "step_scaling", "predictive"], "default": "target_tracking"},
                        "target_utilization": {"type": "float", "min": 50.0, "max": 80.0, "default": 70.0},
                        "min_instances": {"type": "int", "min": 1, "max": 5, "default": 2}
                    }
                },
                success_rate=0.85,
                average_impact=25.0,
                confidence_level=0.8,
                source="AWS Auto Scaling Best Practices"
            ),
            
            PretrainedStrategy(
                template_id="cost_resource_rightsizing",
                name="資源右調策略",
                description="根據實際使用情況調整資源配置以優化成本效益",
                category=StrategyCategory.COST_OPTIMIZATION,
                trigger_conditions={
                    "cpu_usage_average": {"min": 0, "max": 30},
                    "memory_usage_average": {"min": 0, "max": 40},
                    "cost_efficiency_score": {"min": 0, "max": 60}
                },
                template_content={
                    "name_template": "資源右調 - {adjustment_type}",
                    "description_template": "將 {resource_type} 從 {current_size} 調整為 {target_size}",
                    "base_expected_gain": 40.0,
                    "base_implementation_cost": 20.0,
                    "risk_level": "medium",
                    "base_success_probability": 0.8,
                    "tasks_template": [
                        {"agent": "ops_agent", "action": "analyze_resource_usage", "params": {}},
                        {"agent": "ops_agent", "action": "resize_instances", "params": {"target_size": "{target_size}"}},
                        {"agent": "monitoring_agent", "action": "validate_performance", "params": {"duration": 3600}}
                    ],
                    "parameters": {
                        "adjustment_type": {"type": "string", "options": ["downsize", "optimize", "consolidate"], "default": "optimize"},
                        "resource_type": {"type": "string", "options": ["compute", "memory", "storage"], "default": "compute"},
                        "size_reduction_percent": {"type": "float", "min": 10.0, "max": 50.0, "default": 25.0}
                    }
                },
                success_rate=0.8,
                average_impact=35.0,
                confidence_level=0.85,
                source="FinOps Foundation Guidelines"
            )
        ])
        
        # 安全策略
        self.strategies.extend([
            PretrainedStrategy(
                template_id="sec_rate_limiting",
                name="速率限制強化策略",
                description="實施智能速率限制以防止 DDoS 攻擊和資源濫用",
                category=StrategyCategory.SECURITY,
                trigger_conditions={
                    "request_rate_per_ip": {"min": 100, "max": 10000},
                    "suspicious_traffic_percentage": {"min": 5, "max": 50},
                    "api_abuse_incidents": {"min": 1, "max": 100}
                },
                template_content={
                    "name_template": "速率限制 - {limiting_strategy}",
                    "description_template": "實施 {limiting_strategy} 速率限制，每 IP 每分鐘 {rate_limit} 請求",
                    "base_expected_gain": 70.0,
                    "base_implementation_cost": 35.0,
                    "risk_level": "low",
                    "base_success_probability": 0.9,
                    "tasks_template": [
                        {"agent": "security_agent", "action": "configure_rate_limiting", "params": {"strategy": "{limiting_strategy}"}},
                        {"agent": "security_agent", "action": "setup_ip_whitelist", "params": {}},
                        {"agent": "monitoring_agent", "action": "monitor_blocked_requests", "params": {}}
                    ],
                    "parameters": {
                        "limiting_strategy": {"type": "string", "options": ["fixed_window", "sliding_window", "token_bucket"], "default": "sliding_window"},
                        "rate_limit": {"type": "int", "min": 60, "max": 1000, "default": 300},
                        "burst_allowance": {"type": "int", "min": 10, "max": 100, "default": 50}
                    }
                },
                success_rate=0.9,
                average_impact=65.0,
                confidence_level=0.95,
                source="OWASP API Security Guidelines"
            )
        ])
        
        # 業務增長策略
        self.strategies.extend([
            PretrainedStrategy(
                template_id="growth_user_retention",
                name="用戶留存優化策略",
                description="通過個性化體驗和性能優化提升用戶留存率",
                category=StrategyCategory.BUSINESS_GROWTH,
                trigger_conditions={
                    "user_churn_rate": {"min": 5, "max": 30},
                    "session_duration_average": {"min": 0, "max": 300},
                    "user_engagement_score": {"min": 0, "max": 60}
                },
                template_content={
                    "name_template": "用戶留存優化 - {optimization_focus}",
                    "description_template": "針對 {user_segment} 用戶實施 {optimization_focus} 優化",
                    "base_expected_gain": 25.0,
                    "base_implementation_cost": 60.0,
                    "risk_level": "low",
                    "base_success_probability": 0.75,
                    "tasks_template": [
                        {"agent": "analytics_agent", "action": "analyze_user_behavior", "params": {"segment": "{user_segment}"}},
                        {"agent": "product_agent", "action": "implement_personalization", "params": {"focus": "{optimization_focus}"}},
                        {"agent": "monitoring_agent", "action": "track_retention_metrics", "params": {}}
                    ],
                    "parameters": {
                        "optimization_focus": {"type": "string", "options": ["onboarding", "engagement", "performance"], "default": "engagement"},
                        "user_segment": {"type": "string", "options": ["new_users", "power_users", "at_risk"], "default": "new_users"},
                        "personalization_level": {"type": "string", "options": ["basic", "advanced", "ai_driven"], "default": "basic"}
                    }
                },
                success_rate=0.75,
                average_impact=20.0,
                confidence_level=0.7,
                source="Product Growth Best Practices"
            )
        ])
        
        logger.info(f"Initialized {len(self.strategies)} pretrained strategies")
    
    def get_strategies_by_category(self, category: StrategyCategory) -> List[PretrainedStrategy]:
        """根據類別獲取策略"""
        return [s for s in self.strategies if s.category == category]
    
    def get_strategy_by_id(self, template_id: str) -> PretrainedStrategy:
        """根據 ID 獲取策略"""
        for strategy in self.strategies:
            if strategy.template_id == template_id:
                return strategy
        return None
    
    def get_all_strategies(self) -> List[PretrainedStrategy]:
        """獲取所有策略"""
        return self.strategies.copy()
    
    def export_to_json(self, file_path: str):
        """導出策略庫到 JSON 文件"""
        try:
            strategies_data = []
            for strategy in self.strategies:
                strategy_dict = asdict(strategy)
                strategy_dict['category'] = strategy.category.value
                strategies_data.append(strategy_dict)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(strategies_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Exported {len(strategies_data)} strategies to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export strategies: {e}")
    
    def import_from_json(self, file_path: str):
        """從 JSON 文件導入策略庫"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                strategies_data = json.load(f)
            
            imported_strategies = []
            for strategy_dict in strategies_data:
                strategy_dict['category'] = StrategyCategory(strategy_dict['category'])
                strategy = PretrainedStrategy(**strategy_dict)
                imported_strategies.append(strategy)
            
            self.strategies = imported_strategies
            logger.info(f"Imported {len(imported_strategies)} strategies from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to import strategies: {e}")

# 全局實例
_pretrained_library_instance = None

def get_pretrained_strategy_library() -> PretrainedStrategyLibrary:
    """獲取預訓練策略庫實例（單例）"""
    global _pretrained_library_instance
    
    if _pretrained_library_instance is None:
        _pretrained_library_instance = PretrainedStrategyLibrary()
    
    return _pretrained_library_instance

