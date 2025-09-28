"""
策略學習系統 - 策略沉澱與模型反哺機制
版本: 1.0
日期: 2025-09-12
作者: Manus AI

這個模塊實現了策略的學習、沉澱和反哺機制，
讓系統能夠從成功的策略中學習，逐步減少對外部 AI 服務的依賴。
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pickle
import hashlib

# 配置日誌
logger = logging.getLogger(__name__)

Base = declarative_base()

class StrategyExecutionLog(Base):
    """策略執行日誌表"""
    __tablename__ = 'strategy_execution_logs'
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(String(50), nullable=False)
    strategy_name = Column(String(200), nullable=False)
    strategy_content = Column(Text, nullable=False)  # JSON 格式的策略內容
    trigger_context = Column(Text, nullable=False)   # 觸發背景
    execution_status = Column(String(20), nullable=False)  # success, failed, partial
    execution_time = Column(Float, nullable=False)   # 執行時間（秒）
    
    # 效果指標
    before_metrics = Column(Text, nullable=True)     # 執行前的系統指標
    after_metrics = Column(Text, nullable=True)      # 執行後的系統指標
    impact_score = Column(Float, nullable=True)      # 影響分數 (-100 to 100)
    
    # 評分
    human_rating = Column(Float, nullable=True)      # 人工評分 (1-5)
    auto_rating = Column(Float, nullable=True)       # 自動評分 (1-5)
    confidence_score = Column(Float, nullable=True)  # 信心分數 (0-1)
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CandidateStrategy(Base):
    """候選策略庫表"""
    __tablename__ = 'candidate_strategies'
    
    id = Column(Integer, primary_key=True)
    strategy_template_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)    # performance, reliability, cost, etc.
    
    # 策略模板
    template_content = Column(Text, nullable=False)  # JSON 格式的參數化模板
    trigger_conditions = Column(Text, nullable=False) # 觸發條件
    
    # 統計數據
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    total_executions = Column(Integer, default=0)
    average_impact = Column(Float, default=0.0)
    average_rating = Column(Float, default=0.0)
    
    # 狀態
    is_active = Column(Boolean, default=True)
    confidence_level = Column(Float, default=0.0)    # 0-1
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@dataclass
class StrategyEvaluation:
    """策略評估結果"""
    strategy_id: str
    execution_status: str
    impact_score: float
    human_rating: Optional[float] = None
    auto_rating: Optional[float] = None
    confidence_score: float = 0.0
    execution_time: float = 0.0
    before_metrics: Dict[str, Any] = None
    after_metrics: Dict[str, Any] = None

class StrategyLearningSystem:
    """策略學習系統"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # 學習參數
        self.min_success_count = 3      # 最少成功次數才能成為候選策略
        self.min_success_rate = 0.7     # 最低成功率
        self.min_average_rating = 3.5   # 最低平均評分
        self.promotion_threshold = 0.8  # 提升為內部規則的閾值
        
    async def log_strategy_execution(
        self, 
        strategy: Any,  # Strategy 對象
        trigger_context: Dict[str, Any],
        evaluation: StrategyEvaluation
    ):
        """記錄策略執行日誌"""
        try:
            log_entry = StrategyExecutionLog(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                strategy_content=json.dumps(asdict(strategy), default=str),
                trigger_context=json.dumps(trigger_context, default=str),
                execution_status=evaluation.execution_status,
                execution_time=evaluation.execution_time,
                before_metrics=json.dumps(evaluation.before_metrics or {}, default=str),
                after_metrics=json.dumps(evaluation.after_metrics or {}, default=str),
                impact_score=evaluation.impact_score,
                human_rating=evaluation.human_rating,
                auto_rating=evaluation.auto_rating,
                confidence_score=evaluation.confidence_score
            )
            
            self.session.add(log_entry)
            self.session.commit()
            
            logger.info(f"Strategy execution logged: {strategy.id} - {evaluation.execution_status}")
            
            # 如果是成功的策略，檢查是否可以成為候選策略
            if evaluation.execution_status == "success":
                await self._evaluate_for_candidacy(strategy, evaluation)
                
        except Exception as e:
            logger.error(f"Failed to log strategy execution: {e}")
            self.session.rollback()
    
    async def _evaluate_for_candidacy(self, strategy: Any, evaluation: StrategyEvaluation):
        """評估策略是否可以成為候選策略"""
        try:
            # 計算策略的特徵哈希，用於識別相似策略
            strategy_hash = self._calculate_strategy_hash(strategy)
            
            # 查詢歷史執行記錄
            similar_executions = self.session.query(StrategyExecutionLog).filter(
                StrategyExecutionLog.strategy_name == strategy.name
            ).all()
            
            if len(similar_executions) < self.min_success_count:
                return  # 執行次數不足
            
            # 計算成功率和平均評分
            success_count = len([e for e in similar_executions if e.execution_status == "success"])
            success_rate = success_count / len(similar_executions)
            
            ratings = [e.auto_rating or e.human_rating for e in similar_executions if e.auto_rating or e.human_rating]
            average_rating = np.mean(ratings) if ratings else 0
            
            # 檢查是否滿足候選條件
            if success_rate >= self.min_success_rate and average_rating >= self.min_average_rating:
                await self._promote_to_candidate(strategy, similar_executions, strategy_hash)
                
        except Exception as e:
            logger.error(f"Failed to evaluate strategy for candidacy: {e}")
    
    def _calculate_strategy_hash(self, strategy: Any) -> str:
        """計算策略的特徵哈希"""
        # 提取策略的關鍵特徵
        features = {
            "name": strategy.name,
            "description": strategy.description[:100],  # 只取前100字符
            "tasks": [task.get("action") for task in strategy.tasks if isinstance(task, dict)]
        }
        
        feature_string = json.dumps(features, sort_keys=True)
        return hashlib.md5(feature_string.encode()).hexdigest()
    
    async def _promote_to_candidate(self, strategy: Any, executions: List[StrategyExecutionLog], strategy_hash: str):
        """將策略提升為候選策略"""
        try:
            # 檢查是否已經存在
            existing = self.session.query(CandidateStrategy).filter(
                CandidateStrategy.strategy_template_id == strategy_hash
            ).first()
            
            if existing:
                # 更新統計數據
                await self._update_candidate_statistics(existing, executions)
                return
            
            # 創建新的候選策略
            success_count = len([e for e in executions if e.execution_status == "success"])
            total_count = len(executions)
            
            impact_scores = [e.impact_score for e in executions if e.impact_score is not None]
            average_impact = np.mean(impact_scores) if impact_scores else 0
            
            ratings = [e.auto_rating or e.human_rating for e in executions if e.auto_rating or e.human_rating]
            average_rating = np.mean(ratings) if ratings else 0
            
            # 生成參數化模板
            template = self._generate_strategy_template(strategy, executions)
            
            candidate = CandidateStrategy(
                strategy_template_id=strategy_hash,
                name=strategy.name,
                description=strategy.description,
                category=self._categorize_strategy(strategy),
                template_content=json.dumps(template, default=str),
                trigger_conditions=json.dumps(self._extract_trigger_conditions(executions), default=str),
                success_count=success_count,
                failure_count=total_count - success_count,
                total_executions=total_count,
                average_impact=average_impact,
                average_rating=average_rating,
                confidence_level=success_count / total_count
            )
            
            self.session.add(candidate)
            self.session.commit()
            
            logger.info(f"Strategy promoted to candidate: {strategy.name} (hash: {strategy_hash})")
            
        except Exception as e:
            logger.error(f"Failed to promote strategy to candidate: {e}")
            self.session.rollback()
    
    def _generate_strategy_template(self, strategy: Any, executions: List[StrategyExecutionLog]) -> Dict[str, Any]:
        """生成參數化的策略模板"""
        # 分析執行歷史，提取可變參數
        template = {
            "name_template": strategy.name,
            "description_template": strategy.description,
            "base_expected_gain": strategy.expected_gain,
            "base_implementation_cost": strategy.implementation_cost,
            "risk_level": strategy.risk_level.value,
            "base_success_probability": strategy.success_probability,
            "tasks_template": strategy.tasks,
            "parameters": {
                # 可以根據具體情況動態調整的參數
                "scale_factor": {"type": "float", "min": 0.5, "max": 2.0, "default": 1.0},
                "urgency_multiplier": {"type": "float", "min": 0.8, "max": 1.5, "default": 1.0}
            }
        }
        
        return template
    
    def _categorize_strategy(self, strategy: Any) -> str:
        """對策略進行分類"""
        name_lower = strategy.name.lower()
        description_lower = strategy.description.lower()
        
        if any(keyword in name_lower or keyword in description_lower 
               for keyword in ["scale", "performance", "latency", "speed"]):
            return "performance"
        elif any(keyword in name_lower or keyword in description_lower 
                 for keyword in ["error", "reliability", "stability", "rollback"]):
            return "reliability"
        elif any(keyword in name_lower or keyword in description_lower 
                 for keyword in ["cost", "optimize", "efficiency"]):
            return "cost_optimization"
        elif any(keyword in name_lower or keyword in description_lower 
                 for keyword in ["security", "auth", "permission"]):
            return "security"
        elif any(keyword in name_lower or keyword in description_lower 
                 for keyword in ["user", "retention", "growth"]):
            return "business_growth"
        else:
            return "general"
    
    def _extract_trigger_conditions(self, executions: List[StrategyExecutionLog]) -> Dict[str, Any]:
        """從執行歷史中提取觸發條件"""
        # 分析觸發背景，提取共同模式
        trigger_patterns = {
            "common_metrics": [],
            "threshold_ranges": {},
            "context_patterns": []
        }
        
        for execution in executions:
            try:
                context = json.loads(execution.trigger_context)
                # 這裡可以添加更複雜的模式識別邏輯
                trigger_patterns["context_patterns"].append(context)
            except:
                continue
        
        return trigger_patterns
    
    async def _update_candidate_statistics(self, candidate: CandidateStrategy, executions: List[StrategyExecutionLog]):
        """更新候選策略的統計數據"""
        try:
            success_count = len([e for e in executions if e.execution_status == "success"])
            total_count = len(executions)
            
            impact_scores = [e.impact_score for e in executions if e.impact_score is not None]
            average_impact = np.mean(impact_scores) if impact_scores else candidate.average_impact
            
            ratings = [e.auto_rating or e.human_rating for e in executions if e.auto_rating or e.human_rating]
            average_rating = np.mean(ratings) if ratings else candidate.average_rating
            
            candidate.success_count = success_count
            candidate.failure_count = total_count - success_count
            candidate.total_executions = total_count
            candidate.average_impact = average_impact
            candidate.average_rating = average_rating
            candidate.confidence_level = success_count / total_count
            candidate.updated_at = datetime.utcnow()
            
            self.session.commit()
            
            # 檢查是否可以提升為內部規則
            if candidate.confidence_level >= self.promotion_threshold:
                await self._promote_to_internal_rule(candidate)
                
        except Exception as e:
            logger.error(f"Failed to update candidate statistics: {e}")
            self.session.rollback()
    
    async def _promote_to_internal_rule(self, candidate: CandidateStrategy):
        """將候選策略提升為內部規則"""
        try:
            logger.info(f"Promoting candidate strategy to internal rule: {candidate.name}")
            
            # 這裡可以實現將策略集成到 StrategyGenerator 的內部規則中
            # 例如，更新策略模板庫，或者生成新的規則代碼
            
            # 標記為已提升
            candidate.is_active = False  # 不再作為候選策略，已成為內部規則
            candidate.updated_at = datetime.utcnow()
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to promote candidate to internal rule: {e}")
            self.session.rollback()
    
    async def get_candidate_strategies(self, category: Optional[str] = None, min_confidence: float = 0.0) -> List[CandidateStrategy]:
        """獲取候選策略列表"""
        query = self.session.query(CandidateStrategy).filter(
            CandidateStrategy.is_active == True,
            CandidateStrategy.confidence_level >= min_confidence
        )
        
        if category:
            query = query.filter(CandidateStrategy.category == category)
        
        return query.order_by(CandidateStrategy.confidence_level.desc()).all()
    
    async def generate_strategy_from_template(self, template_id: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """從模板生成具體的策略"""
        try:
            candidate = self.session.query(CandidateStrategy).filter(
                CandidateStrategy.strategy_template_id == template_id
            ).first()
            
            if not candidate:
                return None
            
            template = json.loads(candidate.template_content)
            
            # 根據上下文調整參數
            strategy = {
                "id": f"template_{template_id}_{int(time.time())}",
                "name": template["name_template"],
                "description": template["description_template"],
                "expected_gain": template["base_expected_gain"],
                "implementation_cost": template["base_implementation_cost"],
                "risk_level": template["risk_level"],
                "success_probability": template["base_success_probability"],
                "tasks": template["tasks_template"],
                "source": "internal_template",
                "template_id": template_id,
                "confidence": candidate.confidence_level
            }
            
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to generate strategy from template: {e}")
            return None
    
    async def get_learning_statistics(self) -> Dict[str, Any]:
        """獲取學習系統統計數據"""
        try:
            total_executions = self.session.query(StrategyExecutionLog).count()
            successful_executions = self.session.query(StrategyExecutionLog).filter(
                StrategyExecutionLog.execution_status == "success"
            ).count()
            
            total_candidates = self.session.query(CandidateStrategy).filter(
                CandidateStrategy.is_active == True
            ).count()
            
            promoted_strategies = self.session.query(CandidateStrategy).filter(
                CandidateStrategy.is_active == False
            ).count()
            
            return {
                "total_strategy_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": successful_executions / max(total_executions, 1),
                "active_candidate_strategies": total_candidates,
                "promoted_to_internal_rules": promoted_strategies,
                "learning_efficiency": total_candidates / max(total_executions, 1)
            }
            
        except Exception as e:
            logger.error(f"Failed to get learning statistics: {e}")
            return {}

# 全局實例
_learning_system_instance = None

def get_strategy_learning_system(database_url: Optional[str] = None) -> StrategyLearningSystem:
    """獲取策略學習系統實例（單例）"""
    global _learning_system_instance
    
    if _learning_system_instance is None:
        if database_url is None:
            database_url = "postgresql://user:password@localhost/morningai"
        _learning_system_instance = StrategyLearningSystem(database_url)
    
    return _learning_system_instance

