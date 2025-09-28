"""
智能初始化機制 - 讓系統從第一天就聰明
版本: 1.0
日期: 2025-09-12
作者: Manus AI

這個模塊實現了智能初始化機制，
在系統首次啟動時自動注入預訓練策略和知識。
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from pretrained_strategy_library import get_pretrained_strategy_library, StrategyCategory
from strategy_learning_system import get_strategy_learning_system, CandidateStrategy

# 配置日誌
logger = logging.getLogger(__name__)

class SmartInitializer:
    """智能初始化器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pretrained_library = get_pretrained_strategy_library()
        self.learning_system = get_strategy_learning_system(database_url)
        self.initialization_complete = False
    
    async def initialize_system(self, force_reinit: bool = False) -> bool:
        """初始化系統，注入預訓練知識"""
        try:
            logger.info("Starting smart system initialization...")
            
            # 檢查是否已經初始化過
            if not force_reinit and await self._check_initialization_status():
                logger.info("System already initialized, skipping...")
                return True
            
            # 步驟 1: 注入預訓練策略到候選策略庫
            await self._inject_pretrained_strategies()
            
            # 步驟 2: 創建模擬歷史數據
            await self._create_synthetic_history()
            
            # 步驟 3: 初始化決策模擬器
            await self._initialize_decision_simulator()
            
            # 步驟 4: 設置系統配置
            await self._setup_system_configuration()
            
            # 步驟 5: 標記初始化完成
            await self._mark_initialization_complete()
            
            logger.info("Smart system initialization completed successfully")
            self.initialization_complete = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            return False
    
    async def _check_initialization_status(self) -> bool:
        """檢查系統是否已經初始化"""
        try:
            # 檢查候選策略庫是否有預訓練策略
            candidates = await self.learning_system.get_candidate_strategies()
            
            # 如果有候選策略且包含預訓練策略，認為已初始化
            pretrained_count = len([c for c in candidates if c.strategy_template_id.startswith('pretrained_')])
            
            return pretrained_count > 0
            
        except Exception as e:
            logger.warning(f"Failed to check initialization status: {e}")
            return False
    
    async def _inject_pretrained_strategies(self):
        """注入預訓練策略到候選策略庫"""
        try:
            logger.info("Injecting pretrained strategies...")
            
            pretrained_strategies = self.pretrained_library.get_all_strategies()
            injected_count = 0
            
            for pretrained in pretrained_strategies:
                # 轉換為候選策略格式
                candidate = CandidateStrategy(
                    strategy_template_id=f"pretrained_{pretrained.template_id}",
                    name=pretrained.name,
                    description=pretrained.description,
                    category=pretrained.category.value,
                    template_content=json.dumps(pretrained.template_content, default=str),
                    trigger_conditions=json.dumps(pretrained.trigger_conditions, default=str),
                    success_count=int(pretrained.success_rate * 100),  # 模擬成功次數
                    failure_count=int((1 - pretrained.success_rate) * 20),  # 模擬失敗次數
                    total_executions=int(pretrained.success_rate * 100) + int((1 - pretrained.success_rate) * 20),
                    average_impact=pretrained.average_impact,
                    average_rating=4.0 + pretrained.confidence_level,  # 轉換為 1-5 評分
                    is_active=True,
                    confidence_level=pretrained.confidence_level,
                    created_at=datetime.utcnow()
                )
                
                # 檢查是否已存在
                existing = self.learning_system.session.query(CandidateStrategy).filter(
                    CandidateStrategy.strategy_template_id == candidate.strategy_template_id
                ).first()
                
                if not existing:
                    self.learning_system.session.add(candidate)
                    injected_count += 1
                else:
                    logger.debug(f"Strategy {candidate.strategy_template_id} already exists, skipping")
            
            self.learning_system.session.commit()
            logger.info(f"Injected {injected_count} pretrained strategies")
            
        except Exception as e:
            logger.error(f"Failed to inject pretrained strategies: {e}")
            self.learning_system.session.rollback()
            raise
    
    async def _create_synthetic_history(self):
        """創建合成歷史數據以訓練模型"""
        try:
            logger.info("Creating synthetic historical data...")
            
            # 為增強版決策模擬器創建一些基礎歷史數據
            from enhanced_decision_simulator import HistoricalMetric, StrategyImpact
            
            # 創建歷史指標數據
            base_time = datetime.utcnow() - timedelta(days=30)
            metrics_data = []
            
            # 生成系統指標的歷史數據
            system_metrics = [
                "cpu_usage_percent", "memory_usage_percent", "api_request_duration_p95",
                "error_rate_5xx", "database_query_duration_p95", "cache_hit_rate"
            ]
            
            for i in range(30 * 24):  # 30天，每小時一個數據點
                timestamp = base_time + timedelta(hours=i)
                
                for metric_name in system_metrics:
                    # 生成合理的模擬數據
                    if metric_name == "cpu_usage_percent":
                        value = 30 + 40 * (0.5 + 0.3 * np.sin(i * 2 * np.pi / 24))  # 日週期
                    elif metric_name == "memory_usage_percent":
                        value = 40 + 30 * (0.5 + 0.2 * np.sin(i * 2 * np.pi / 24))
                    elif metric_name == "api_request_duration_p95":
                        value = 200 + 300 * (0.5 + 0.4 * np.sin(i * 2 * np.pi / 24))
                    elif metric_name == "error_rate_5xx":
                        value = 1 + 4 * np.random.random()
                    elif metric_name == "database_query_duration_p95":
                        value = 100 + 200 * (0.5 + 0.3 * np.sin(i * 2 * np.pi / 24))
                    elif metric_name == "cache_hit_rate":
                        value = 70 + 25 * np.random.random()
                    else:
                        value = 50 + 30 * np.random.random()
                    
                    metric = HistoricalMetric(
                        metric_name=metric_name,
                        metric_value=value,
                        metric_category="system",
                        timestamp=timestamp,
                        context_data=json.dumps({"synthetic": True})
                    )
                    metrics_data.append(metric)
            
            # 批量插入歷史指標
            enhanced_simulator = get_enhanced_decision_simulator(self.database_url)
            enhanced_simulator.session.bulk_save_objects(metrics_data)
            
            # 創建策略影響數據
            impact_data = []
            pretrained_strategies = self.pretrained_library.get_all_strategies()
            
            for i, strategy in enumerate(pretrained_strategies[:10]):  # 只為前10個策略創建歷史
                for execution in range(int(strategy.success_rate * 10)):  # 根據成功率創建執行記錄
                    execution_time = base_time + timedelta(days=i, hours=execution * 2)
                    
                    # 模擬執行前後的指標
                    before_metrics = {
                        "cpu_usage_percent": 70 + 20 * np.random.random(),
                        "memory_usage_percent": 60 + 30 * np.random.random(),
                        "api_request_duration_p95": 800 + 400 * np.random.random()
                    }
                    
                    # 根據策略類型模擬改善效果
                    improvement_factor = strategy.average_impact / 100.0
                    after_metrics = {}
                    
                    for metric, value in before_metrics.items():
                        if strategy.category == StrategyCategory.PERFORMANCE:
                            # 性能策略應該改善響應時間和資源使用
                            after_metrics[metric] = value * (1 - improvement_factor * 0.5)
                        else:
                            after_metrics[metric] = value * (1 - improvement_factor * 0.3)
                    
                    impact = StrategyImpact(
                        strategy_id=f"pretrained_{strategy.template_id}_{execution}",
                        strategy_type=strategy.name,
                        execution_timestamp=execution_time,
                        before_metrics=json.dumps(before_metrics, default=str),
                        after_metrics=json.dumps(after_metrics, default=str),
                        impact_duration_hours=2.0,
                        primary_impact_metric="api_request_duration_p95",
                        impact_magnitude=improvement_factor,
                        confidence_score=strategy.confidence_level
                    )
                    impact_data.append(impact)
            
            enhanced_simulator.session.bulk_save_objects(impact_data)
            enhanced_simulator.session.commit()
            
            logger.info(f"Created {len(metrics_data)} historical metrics and {len(impact_data)} strategy impacts")
            
        except Exception as e:
            logger.error(f"Failed to create synthetic history: {e}")
            raise
    
    async def _initialize_decision_simulator(self):
        """初始化決策模擬器"""
        try:
            logger.info("Initializing enhanced decision simulator...")
            
            from enhanced_decision_simulator import get_enhanced_decision_simulator
            
            enhanced_simulator = get_enhanced_decision_simulator(self.database_url)
            await enhanced_simulator.initialize()
            
            logger.info("Enhanced decision simulator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize decision simulator: {e}")
            raise
    
    async def _setup_system_configuration(self):
        """設置系統配置"""
        try:
            logger.info("Setting up system configuration...")
            
            # 創建配置文件
            config = {
                "initialization": {
                    "completed": True,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "pretrained_strategies_count": len(self.pretrained_library.get_all_strategies())
                },
                "learning_system": {
                    "min_success_count": 2,  # 降低門檻，因為有預訓練數據
                    "min_success_rate": 0.6,
                    "min_average_rating": 3.0,
                    "promotion_threshold": 0.75
                },
                "ai_gateway": {
                    "default_preference": "cost_effective",  # 優先使用成本效益高的模型
                    "fallback_enabled": True,
                    "cache_enabled": True
                },
                "hybrid_deployment": {
                    "prefer_local": True,  # 優先使用本地模型
                    "auto_deploy_threshold": 0.8
                }
            }
            
            # 保存配置
            config_path = "/tmp/morningai_init_config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            logger.info(f"System configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to setup system configuration: {e}")
            raise
    
    async def _mark_initialization_complete(self):
        """標記初始化完成"""
        try:
            # 在資料庫中創建初始化標記
            from strategy_learning_system import StrategyExecutionLog
            
            init_log = StrategyExecutionLog(
                strategy_id="system_initialization",
                strategy_name="Smart System Initialization",
                strategy_content=json.dumps({"type": "system_initialization", "version": "1.0"}),
                trigger_context=json.dumps({"automated": True, "timestamp": datetime.utcnow().isoformat()}),
                execution_status="success",
                execution_time=0.0,
                impact_score=100.0,
                auto_rating=5.0,
                confidence_score=1.0,
                created_at=datetime.utcnow()
            )
            
            self.learning_system.session.add(init_log)
            self.learning_system.session.commit()
            
            logger.info("Initialization completion marked in database")
            
        except Exception as e:
            logger.error(f"Failed to mark initialization complete: {e}")
            raise
    
    async def get_initialization_status(self) -> Dict[str, Any]:
        """獲取初始化狀態"""
        try:
            # 檢查候選策略數量
            candidates = await self.learning_system.get_candidate_strategies()
            pretrained_count = len([c for c in candidates if c.strategy_template_id.startswith('pretrained_')])
            
            # 檢查歷史數據
            from enhanced_decision_simulator import get_enhanced_decision_simulator
            enhanced_simulator = get_enhanced_decision_simulator(self.database_url)
            
            historical_metrics_count = enhanced_simulator.session.query(
                enhanced_simulator.HistoricalMetric
            ).count()
            
            strategy_impacts_count = enhanced_simulator.session.query(
                enhanced_simulator.StrategyImpact
            ).count()
            
            # 檢查學習統計
            learning_stats = await self.learning_system.get_learning_statistics()
            
            return {
                "initialization_complete": self.initialization_complete or pretrained_count > 0,
                "pretrained_strategies_count": pretrained_count,
                "total_candidate_strategies": len(candidates),
                "historical_metrics_count": historical_metrics_count,
                "strategy_impacts_count": strategy_impacts_count,
                "learning_statistics": learning_stats,
                "system_readiness_score": min(100, (pretrained_count * 5) + (historical_metrics_count / 100))
            }
            
        except Exception as e:
            logger.error(f"Failed to get initialization status: {e}")
            return {"error": str(e)}
    
    async def export_initialization_report(self, file_path: str):
        """導出初始化報告"""
        try:
            status = await self.get_initialization_status()
            
            report = {
                "report_title": "Morning AI Smart Initialization Report",
                "generated_at": datetime.utcnow().isoformat(),
                "system_status": status,
                "pretrained_strategies": [
                    {
                        "id": s.template_id,
                        "name": s.name,
                        "category": s.category.value,
                        "confidence": s.confidence_level,
                        "expected_impact": s.average_impact
                    }
                    for s in self.pretrained_library.get_all_strategies()
                ],
                "recommendations": [
                    "系統已完成智能初始化，具備強大的初始決策能力",
                    "建議開始正常運行，系統將在實際使用中持續學習和優化",
                    "監控系統性能指標，確保預訓練策略的有效性",
                    "定期檢查學習系統統計數據，評估自學習進展"
                ]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Initialization report exported to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export initialization report: {e}")

# 導入必要的 numpy
import numpy as np

# 全局實例
_smart_initializer_instance = None

def get_smart_initializer(database_url: Optional[str] = None) -> SmartInitializer:
    """獲取智能初始化器實例（單例）"""
    global _smart_initializer_instance
    
    if _smart_initializer_instance is None:
        if database_url is None:
            database_url = "postgresql://user:password@localhost/morningai"
        _smart_initializer_instance = SmartInitializer(database_url)
    
    return _smart_initializer_instance

async def quick_initialize_system(database_url: Optional[str] = None, force_reinit: bool = False) -> bool:
    """快速初始化系統的便捷函數"""
    initializer = get_smart_initializer(database_url)
    return await initializer.initialize_system(force_reinit)

