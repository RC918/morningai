#!/usr/bin/env python3
"""
Morning AI - Meta-Agent 決策中樞
整合監控系統、AI Agent 協調和自主決策能力
基於 OODA 循環的決策引擎
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import statistics
from collections import defaultdict, deque
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DecisionPriority(Enum):
    """決策優先級"""
    CRITICAL = "critical"    # 系統穩定性相關
    HIGH = "high"           # 業務關鍵決策
    MEDIUM = "medium"       # 優化改進決策
    LOW = "low"            # 例行維護決策

class AgentRole(Enum):
    """AI Agent 角色定義"""
    CEO = "ceo_agent"
    PM = "pm_agent"
    DEV = "dev_agent"
    QA = "qa_agent"
    DESIGN = "design_agent"
    OPS = "ops_agent"
    SECURITY = "security_agent"
    SUPPORT = "support_agent"
    GROWTH = "growth_agent"
    CONTENT = "content_agent"
    BILLING = "billing_agent"
    LEGAL = "legal_agent"
    PRIVACY = "privacy_agent"
    KNOWLEDGE = "knowledge_agent"
    TRAINER = "trainer_agent"

@dataclass
class SystemMetrics:
    """系統監控指標"""
    timestamp: datetime
    api_latency_p95: float
    api_error_rate: float
    db_connection_pool_usage: float
    redis_hit_rate: float
    cpu_usage: float
    memory_usage: float
    active_users: int
    revenue_mrr: float
    
    def is_healthy(self) -> bool:
        """判斷系統是否健康"""
        return (
            self.api_latency_p95 < 500 and
            self.api_error_rate < 0.01 and
            self.db_connection_pool_usage < 0.8 and
            self.cpu_usage < 0.8 and
            self.memory_usage < 0.8
        )
    
    def health_score(self) -> float:
        """計算系統健康分數 (0-100)"""
        scores = []
        
        # API 延遲評分 (500ms 為滿分)
        latency_score = max(0, 100 - (self.api_latency_p95 / 500) * 100)
        scores.append(latency_score)
        
        # 錯誤率評分 (1% 為 0 分)
        error_score = max(0, 100 - (self.api_error_rate / 0.01) * 100)
        scores.append(error_score)
        
        # 資源使用率評分
        cpu_score = max(0, 100 - (self.cpu_usage / 0.8) * 100)
        memory_score = max(0, 100 - (self.memory_usage / 0.8) * 100)
        scores.extend([cpu_score, memory_score])
        
        return sum(scores) / len(scores)

@dataclass
class DecisionContext:
    """決策上下文"""
    decision_id: str
    timestamp: datetime
    priority: DecisionPriority
    trigger_event: str
    system_metrics: SystemMetrics
    business_context: Dict[str, Any]
    affected_agents: List[AgentRole]
    
@dataclass
class DecisionResult:
    """決策結果"""
    decision_id: str
    strategy: str
    actions: List[Dict[str, Any]]
    expected_outcome: str
    risk_assessment: float  # 0-1
    confidence: float       # 0-1
    execution_timeline: str
    rollback_plan: Optional[str] = None

class OODALoop:
    """OODA 循環實現 (Observe, Orient, Decide, Act)"""
    
    def __init__(self, redis_client: redis.Redis, db_connection):
        self.redis = redis_client
        self.db = db_connection
        self.observations = deque(maxlen=1000)
        self.orientations = deque(maxlen=100)
        self.decisions = deque(maxlen=100)
        self.actions = deque(maxlen=100)
    
    async def observe(self) -> SystemMetrics:
        """觀察階段：收集系統狀態和環境信息"""
        try:
            # 從 Redis 獲取實時指標
            metrics_data = self.redis.hgetall("system:metrics:current")
            
            if not metrics_data:
                metrics_data = {
                    'api_latency_p95': '200',
                    'api_error_rate': '0.001',
                    'db_pool_usage': '0.3',
                    'redis_hit_rate': '0.95',
                    'cpu_usage': '0.4',
                    'memory_usage': '0.5',
                    'active_users': '100',
                    'revenue_mrr': '10000'
                }
            
            # 構建 SystemMetrics 對象
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                api_latency_p95=float(metrics_data.get('api_latency_p95', 0)),
                api_error_rate=float(metrics_data.get('api_error_rate', 0)),
                db_connection_pool_usage=float(metrics_data.get('db_pool_usage', 0)),
                redis_hit_rate=float(metrics_data.get('redis_hit_rate', 0.95)),
                cpu_usage=float(metrics_data.get('cpu_usage', 0)),
                memory_usage=float(metrics_data.get('memory_usage', 0)),
                active_users=int(metrics_data.get('active_users', 0)),
                revenue_mrr=float(metrics_data.get('revenue_mrr', 0))
            )
            
            self.observations.append(metrics)
            logger.info(f"Observed system metrics: health_score={metrics.health_score():.2f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to observe system metrics: {e}")
            # 返回默認的健康指標
            return SystemMetrics(
                timestamp=datetime.now(),
                api_latency_p95=200,
                api_error_rate=0.001,
                db_connection_pool_usage=0.3,
                redis_hit_rate=0.95,
                cpu_usage=0.4,
                memory_usage=0.5,
                active_users=100,
                revenue_mrr=10000
            )
    
    def orient(self, current_metrics: SystemMetrics, trigger_event: str) -> Dict[str, Any]:
        """定向階段：分析觀察結果，理解當前情況"""
        orientation = {
            'timestamp': datetime.now(),
            'trigger_event': trigger_event,
            'system_health': current_metrics.health_score(),
            'anomalies': self._detect_anomalies(current_metrics),
            'trends': self._analyze_trends(),
            'threat_level': self._assess_threat_level(current_metrics, trigger_event)
        }
        
        self.orientations.append(orientation)
        logger.info(f"Oriented situation: health={orientation['system_health']:.2f}, threats={orientation['threat_level']}")
        return orientation
    
    def decide(self, context: DecisionContext, orientation: Dict[str, Any]) -> DecisionResult:
        """決策階段：基於定向結果制定行動策略"""
        strategies = self._generate_strategies(context, orientation)
        
        best_strategy = self._evaluate_strategies(strategies, context)
        
        decision = DecisionResult(
            decision_id=context.decision_id,
            strategy=best_strategy['name'],
            actions=best_strategy['actions'],
            expected_outcome=best_strategy['expected_outcome'],
            risk_assessment=best_strategy['risk'],
            confidence=best_strategy['confidence'],
            execution_timeline=best_strategy.get('timeline', 'immediate'),
            rollback_plan=best_strategy.get('rollback_plan')
        )
        
        self.decisions.append(decision)
        logger.info(f"Decision made: {decision.strategy} (confidence: {decision.confidence:.2f})")
        return decision
    
    async def act(self, decision: DecisionResult) -> bool:
        """行動階段：執行決策"""
        try:
            logger.info(f"Executing decision: {decision.decision_id}")
            
            # 執行具體行動
            execution_results = []
            for action in decision.actions:
                result = await self._execute_action(action)
                execution_results.append(result)
            
            action_record = {
                'decision_id': decision.decision_id,
                'timestamp': datetime.now(),
                'actions': decision.actions,
                'results': execution_results,
                'success': all(execution_results)
            }
            
            self.actions.append(action_record)
            return action_record['success']
            
        except Exception as e:
            logger.error(f"Failed to execute decision {decision.decision_id}: {e}")
            return False
    
    def _detect_anomalies(self, current_metrics: SystemMetrics) -> List[str]:
        """檢測系統異常"""
        anomalies = []
        
        if len(self.observations) < 10:
            return anomalies
        
        # 計算歷史平均值
        recent_metrics = list(self.observations)[-10:]
        avg_latency = statistics.mean([m.api_latency_p95 for m in recent_metrics])
        avg_error_rate = statistics.mean([m.api_error_rate for m in recent_metrics])
        
        # 檢測延遲異常
        if current_metrics.api_latency_p95 > avg_latency * 2:
            anomalies.append(f"API latency spike: {current_metrics.api_latency_p95:.2f}ms")
        
        # 檢測錯誤率異常
        if current_metrics.api_error_rate > avg_error_rate * 3:
            anomalies.append(f"Error rate spike: {current_metrics.api_error_rate:.4f}")
        
        # 檢測資源使用異常
        if current_metrics.cpu_usage > 0.9:
            anomalies.append(f"High CPU usage: {current_metrics.cpu_usage:.2f}")
        
        if current_metrics.memory_usage > 0.9:
            anomalies.append(f"High memory usage: {current_metrics.memory_usage:.2f}")
        
        return anomalies
    
    def _analyze_trends(self) -> Dict[str, str]:
        """分析趨勢"""
        if len(self.observations) < 5:
            return {'trend': 'insufficient_data'}
        
        recent_health_scores = [obs.health_score() for obs in list(self.observations)[-5:]]
        
        if len(recent_health_scores) >= 2:
            if recent_health_scores[-1] > recent_health_scores[0]:
                trend = 'improving'
            elif recent_health_scores[-1] < recent_health_scores[0]:
                trend = 'degrading'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {'trend': trend, 'recent_scores': recent_health_scores}
    
    def _assess_threat_level(self, metrics: SystemMetrics, trigger_event: str) -> str:
        """評估威脅等級"""
        if not metrics.is_healthy() or 'critical' in trigger_event.lower():
            return 'high'
        elif metrics.health_score() < 70 or 'error' in trigger_event.lower():
            return 'medium'
        else:
            return 'low'
    
    def _generate_strategies(self, context: DecisionContext, orientation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成候選策略"""
        strategies = []
        
        threat_level = orientation['threat_level']
        
        if threat_level == 'high':
            strategies.extend([
                {
                    'name': 'emergency_scale_up',
                    'actions': [
                        {'type': 'scale_resources', 'parameters': {'service': 'api', 'replicas': 5}},
                        {'type': 'send_notification', 'parameters': {'channel': 'slack', 'message': '緊急擴容執行中'}}
                    ],
                    'expected_outcome': '提高系統容量，緩解高負載',
                    'risk': 0.3,
                    'confidence': 0.8,
                    'timeline': 'immediate'
                },
                {
                    'name': 'restart_unhealthy_services',
                    'actions': [
                        {'type': 'restart_service', 'parameters': {'service_name': 'api-backend'}},
                        {'type': 'send_notification', 'parameters': {'channel': 'slack', 'message': '服務重啟完成'}}
                    ],
                    'expected_outcome': '恢復服務健康狀態',
                    'risk': 0.4,
                    'confidence': 0.7,
                    'timeline': 'immediate'
                }
            ])
        elif threat_level == 'medium':
            strategies.extend([
                {
                    'name': 'gradual_optimization',
                    'actions': [
                        {'type': 'update_configuration', 'parameters': {'key': 'cache_ttl', 'value': '300'}},
                        {'type': 'send_notification', 'parameters': {'channel': 'slack', 'message': '系統優化配置已更新'}}
                    ],
                    'expected_outcome': '改善系統性能',
                    'risk': 0.2,
                    'confidence': 0.6,
                    'timeline': '5 minutes'
                }
            ])
        else:
            strategies.extend([
                {
                    'name': 'routine_monitoring',
                    'actions': [
                        {'type': 'send_notification', 'parameters': {'channel': 'slack', 'message': '系統運行正常'}}
                    ],
                    'expected_outcome': '維持當前狀態',
                    'risk': 0.1,
                    'confidence': 0.9,
                    'timeline': 'immediate'
                }
            ])
        
        return strategies
    
    def _evaluate_strategies(self, strategies: List[Dict[str, Any]], context: DecisionContext) -> Dict[str, Any]:
        """評估策略"""
        best_strategy = None
        best_score = 0
        
        for strategy in strategies:
            score = strategy['confidence'] * (1 - strategy['risk'])
            
            health_score = context.system_metrics.health_score()
            if health_score < 50:
                score *= (1 - strategy['risk'])
            
            if score > best_score:
                best_score = score
                best_strategy = strategy
        
        return best_strategy or strategies[0]
    
    async def _execute_action(self, action: Dict[str, Any]) -> bool:
        """執行單個行動"""
        action_type = action.get('type')
        parameters = action.get('parameters', {})
        
        try:
            if action_type == 'restart_service':
                return await self._restart_service(parameters.get('service_name'))
            elif action_type == 'scale_resources':
                return await self._scale_resources(parameters)
            elif action_type == 'update_configuration':
                return await self._update_configuration(parameters)
            elif action_type == 'send_notification':
                return await self._send_notification(parameters)
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to execute action {action_type}: {e}")
            return False
    
    async def _restart_service(self, service_name: str) -> bool:
        """重啟服務"""
        logger.info(f"Restarting service: {service_name}")
        await asyncio.sleep(2)  # 模擬重啟時間
        return True
    
    async def _scale_resources(self, parameters: Dict[str, Any]) -> bool:
        """擴縮容資源"""
        service = parameters.get('service')
        replicas = parameters.get('replicas')
        logger.info(f"Scaling {service} to {replicas} replicas")
        await asyncio.sleep(1)
        return True
    
    async def _update_configuration(self, parameters: Dict[str, Any]) -> bool:
        """更新配置"""
        config_key = parameters.get('key')
        config_value = parameters.get('value')
        logger.info(f"Updating configuration: {config_key} = {config_value}")
        return True
    
    async def _send_notification(self, parameters: Dict[str, Any]) -> bool:
        """發送通知"""
        channel = parameters.get('channel')
        message = parameters.get('message')
        logger.info(f"Sending notification to {channel}: {message}")
        return True

class MetaAgentDecisionHub:
    """Meta-Agent 決策中樞"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", db_url: str = None):
        try:
            self.redis = redis.from_url(redis_url)
            self.db = None  # 暫時不使用數據庫連接
            self.ooda_loop = OODALoop(self.redis, self.db)
            self.decision_history = []
            logger.info("Meta-Agent Decision Hub initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Meta-Agent Decision Hub: {e}")
            self.redis = type('MockRedis', (), {
                'hgetall': lambda self, key: {},
                'set': lambda self, key, value: True,
                'get': lambda self, key: None
            })()
            self.db = None
            self.ooda_loop = OODALoop(self.redis, self.db)
            self.decision_history = []
    
    async def process_trigger_event(self, trigger_event: str, business_context: Dict[str, Any] = None) -> Optional[DecisionResult]:
        """處理觸發事件，執行完整的 OODA 循環"""
        try:
            logger.info(f"Processing trigger event: {trigger_event}")
            
            current_metrics = await self.ooda_loop.observe()
            
            orientation = self.ooda_loop.orient(current_metrics, trigger_event)
            
            context = DecisionContext(
                decision_id=f"decision_{int(time.time())}",
                timestamp=datetime.now(),
                priority=self._determine_priority(trigger_event, orientation['anomalies']),
                trigger_event=trigger_event,
                system_metrics=current_metrics,
                business_context=business_context or {},
                affected_agents=self._identify_affected_agents(trigger_event)
            )
            
            decision = self.ooda_loop.decide(context, orientation)
            
            success = await self.ooda_loop.act(decision)
            
            self.decision_history.append({
                'decision': decision,
                'success': success,
                'timestamp': datetime.now()
            })
            
            logger.info(f"OODA cycle completed for {trigger_event}: success={success}")
            return decision
            
        except Exception as e:
            logger.error(f"Failed to process trigger event {trigger_event}: {e}")
            return None
    
    def _determine_priority(self, trigger_event: str, anomalies: List[str]) -> DecisionPriority:
        """確定決策優先級"""
        if anomalies or 'critical' in trigger_event.lower():
            return DecisionPriority.CRITICAL
        elif 'error' in trigger_event.lower() or 'failure' in trigger_event.lower():
            return DecisionPriority.HIGH
        elif 'optimization' in trigger_event.lower():
            return DecisionPriority.MEDIUM
        else:
            return DecisionPriority.LOW
    
    def _identify_affected_agents(self, trigger_event: str) -> List[AgentRole]:
        """識別受影響的 Agent"""
        affected_agents = []
        
        if 'security' in trigger_event.lower():
            affected_agents.extend([AgentRole.SECURITY, AgentRole.OPS])
        elif 'performance' in trigger_event.lower():
            affected_agents.extend([AgentRole.OPS, AgentRole.DEV])
        elif 'user' in trigger_event.lower():
            affected_agents.extend([AgentRole.SUPPORT, AgentRole.PM])
        else:
            affected_agents.append(AgentRole.OPS)
        
        return affected_agents
    
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取決策歷史"""
        return self.decision_history[-limit:]
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_decisions': len(self.decision_history),
            'recent_decisions': len([d for d in self.decision_history if d['timestamp'] > datetime.now() - timedelta(hours=1)]),
            'success_rate': sum(1 for d in self.decision_history if d['success']) / len(self.decision_history) if self.decision_history else 0,
            'ooda_loop_status': 'active'
        }

async def main():
    """主函數"""
    hub = MetaAgentDecisionHub()
    
    logger.info("Starting Meta-Agent Decision Hub...")
    
    test_events = [
        "system_performance_degradation",
        "high_error_rate_detected",
        "user_complaint_received",
        "security_anomaly_detected"
    ]
    
    try:
        for event in test_events:
            logger.info(f"Testing event: {event}")
            decision = await hub.process_trigger_event(event)
            if decision:
                logger.info(f"Decision result: {decision.strategy}")
            
            await asyncio.sleep(5)
        
        status = hub.get_system_status()
        logger.info(f"System status: {json.dumps(status, indent=2)}")
        
    except KeyboardInterrupt:
        logger.info("Meta-Agent Decision Hub stopped by user")
    except Exception as e:
        logger.error(f"Meta-Agent Decision Hub error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
