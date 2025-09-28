#!/usr/bin/env python3
"""
Morning AI - 增強版決策引擎與策略執行器
整合監控系統、AI Agent 協調和自主決策能力

版本: 4.0
日期: 2025-09-12
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
import numpy as np
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

class MonitoringIntegration:
    """監控系統整合"""
    
    def __init__(self, redis_client: redis.Redis, db_connection):
        self.redis = redis_client
        self.db = db_connection
        self.metrics_history = deque(maxlen=1000)
    
    async def get_current_metrics(self) -> SystemMetrics:
        """獲取當前系統指標"""
        try:
            # 從 Redis 獲取實時指標
            metrics_data = self.redis.hgetall("system:metrics:current")
            
            if not metrics_data:
                # 如果 Redis 中沒有數據，從資料庫獲取最新指標
                with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM system_metrics 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if row:
                        metrics_data = dict(row)
            
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
            
            self.metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
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
    
    def detect_anomalies(self, current_metrics: SystemMetrics) -> List[str]:
        """檢測系統異常"""
        anomalies = []
        
        if len(self.metrics_history) < 10:
            return anomalies
        
        # 計算歷史平均值
        recent_metrics = list(self.metrics_history)[-10:]
        avg_latency = np.mean([m.api_latency_p95 for m in recent_metrics])
        avg_error_rate = np.mean([m.api_error_rate for m in recent_metrics])
        
        # 檢測延遲異常
        if current_metrics.api_latency_p95 > avg_latency * 2:
            anomalies.append(f"API latency spike: {current_metrics.api_latency_p95:.2f}ms (avg: {avg_latency:.2f}ms)")
        
        # 檢測錯誤率異常
        if current_metrics.api_error_rate > avg_error_rate * 3:
            anomalies.append(f"Error rate spike: {current_metrics.api_error_rate:.4f} (avg: {avg_error_rate:.4f})")
        
        # 檢測資源使用異常
        if current_metrics.cpu_usage > 0.9:
            anomalies.append(f"High CPU usage: {current_metrics.cpu_usage:.2f}")
        
        if current_metrics.memory_usage > 0.9:
            anomalies.append(f"High memory usage: {current_metrics.memory_usage:.2f}")
        
        return anomalies

class DecisionSimulator:
    """決策模擬器"""
    
    def __init__(self):
        self.historical_decisions = []
        self.success_patterns = defaultdict(list)
    
    async def simulate_strategy(self, context: DecisionContext, strategy: str) -> Tuple[float, float]:
        """
        模擬策略執行結果
        返回: (預期成功率, 風險評估)
        """
        # 基於歷史數據和當前上下文模擬策略效果
        base_success_rate = 0.7
        base_risk = 0.3
        
        # 根據系統健康狀況調整
        health_score = context.system_metrics.health_score()
        if health_score < 50:
            base_success_rate *= 0.6  # 系統不健康時降低成功率
            base_risk *= 1.5          # 增加風險
        elif health_score > 80:
            base_success_rate *= 1.2  # 系統健康時提高成功率
            base_risk *= 0.8          # 降低風險
        
        # 根據決策優先級調整
        if context.priority == DecisionPriority.CRITICAL:
            base_risk *= 1.3  # 關鍵決策風險更高
        elif context.priority == DecisionPriority.LOW:
            base_success_rate *= 1.1  # 低優先級決策通常更安全
        
        # 根據涉及的 Agent 數量調整
        agent_count = len(context.affected_agents)
        if agent_count > 5:
            base_risk *= 1.2  # 涉及更多 Agent 的決策風險更高
        
        # 確保值在合理範圍內
        success_rate = min(0.95, max(0.1, base_success_rate))
        risk = min(0.9, max(0.1, base_risk))
        
        return success_rate, risk
    
    def learn_from_outcome(self, decision_id: str, actual_outcome: str, success: bool):
        """從決策結果中學習"""
        self.historical_decisions.append({
            'decision_id': decision_id,
            'outcome': actual_outcome,
            'success': success,
            'timestamp': datetime.now()
        })
        
        # 更新成功模式
        if success:
            # 這裡可以實現更複雜的模式學習邏輯
            pass

class StrategyExecutor:
    """策略執行器"""
    
    def __init__(self, monitoring: MonitoringIntegration):
        self.monitoring = monitoring
        self.active_executions = {}
        self.agent_coordinators = {}
    
    async def execute_strategy(self, decision: DecisionResult) -> bool:
        """執行決策策略"""
        try:
            logger.info(f"Executing strategy for decision {decision.decision_id}: {decision.strategy}")
            
            # 檢查系統健康狀況
            current_metrics = await self.monitoring.get_current_metrics()
            if not current_metrics.is_healthy() and decision.risk_assessment > 0.7:
                logger.warning(f"System unhealthy, postponing high-risk decision {decision.decision_id}")
                return False
            
            # 執行具體行動
            execution_results = []
            for action in decision.actions:
                result = await self._execute_action(action)
                execution_results.append(result)
            
            # 記錄執行狀態
            self.active_executions[decision.decision_id] = {
                'start_time': datetime.now(),
                'actions': decision.actions,
                'results': execution_results,
                'status': 'executing'
            }
            
            return all(execution_results)
            
        except Exception as e:
            logger.error(f"Failed to execute strategy {decision.decision_id}: {e}")
            return False
    
    async def _execute_action(self, action: Dict[str, Any]) -> bool:
        """執行單個行動"""
        action_type = action.get('type')
        target_agent = action.get('agent')
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
        # 這裡實現實際的服務重啟邏輯
        # 例如：kubectl rollout restart deployment/{service_name}
        await asyncio.sleep(2)  # 模擬重啟時間
        return True
    
    async def _scale_resources(self, parameters: Dict[str, Any]) -> bool:
        """擴縮容資源"""
        service = parameters.get('service')
        replicas = parameters.get('replicas')
        logger.info(f"Scaling {service} to {replicas} replicas")
        # 實現實際的擴縮容邏輯
        await asyncio.sleep(1)
        return True
    
    async def _update_configuration(self, parameters: Dict[str, Any]) -> bool:
        """更新配置"""
        config_key = parameters.get('key')
        config_value = parameters.get('value')
        logger.info(f"Updating configuration: {config_key} = {config_value}")
        # 實現配置更新邏輯
        return True
    
    async def _send_notification(self, parameters: Dict[str, Any]) -> bool:
        """發送通知"""
        channel = parameters.get('channel')
        message = parameters.get('message')
        logger.info(f"Sending notification to {channel}: {message}")
        # 實現通知發送邏輯（Slack, Email 等）
        return True

class MetaAgent:
    """Meta-Agent 決策中樞"""
    
    def __init__(self, redis_client: redis.Redis, db_connection):
        self.monitoring = MonitoringIntegration(redis_client, db_connection)
        self.simulator = DecisionSimulator()
        self.executor = StrategyExecutor(self.monitoring)
        self.decision_history = []
        
    async def make_decision(self, trigger_event: str, business_context: Dict[str, Any] = None) -> Optional[DecisionResult]:
        """主決策流程"""
        try:
            # 1. 收集當前系統狀態
            current_metrics = await self.monitoring.get_current_metrics()
            anomalies = self.monitoring.detect_anomalies(current_metrics)
            
            # 2. 構建決策上下文
            context = DecisionContext(
                decision_id=f"decision_{int(time.time())}",
                timestamp=datetime.now(),
                priority=self._determine_priority(trigger_event, anomalies),
                trigger_event=trigger_event,
                system_metrics=current_metrics,
                business_context=business_context or {},
                affected_agents=self._identify_affected_agents(trigger_event)
            )
            
            # 3. 生成候選策略
            candidate_strategies = await self._generate_strategies(context)
            
            # 4. 模擬和評估策略
            best_strategy = None
            best_score = 0
            
            for strategy in candidate_strategies:
                success_rate, risk = await self.simulator.simulate_strategy(context, strategy['name'])
                score = success_rate * (1 - risk)  # 簡單的評分公式
                
                if score > best_score:
                    best_score = score
                    best_strategy = strategy
                    best_strategy['success_rate'] = success_rate
                    best_strategy['risk'] = risk
            
            if not best_strategy:
                logger.warning(f"No suitable strategy found for {trigger_event}")
                return None
            
            # 5. 創建決策結果
            decision = DecisionResult(
                decision_id=context.decision_id,
                strategy=best_strategy['name'],
                actions=best_strategy['actions'],
                expected_outcome=best_strategy['expected_outcome'],
                risk_assessment=best_strategy['risk'],
                confidence=best_strategy['success_rate'],
                execution_timeline=best_strategy.get('timeline', 'immediate'),
                rollback_plan=best_strategy.get('rollback_plan')
            )
            
            # 6. 記錄決策
            self.decision_history.append(decision)
            logger.info(f"Decision made: {decision.strategy} (confidence: {decision.confidence:.2f}, risk: {decision.risk_assessment:.2f})")
            
            return decision
            
        except Exception as e:
            logger.error(f"Failed to make decision for {trigger_event}: {e}")
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
        affected = []
        
        if 'api' in trigger_event.lower() or 'service' in trigger_event.lower():
            affected.extend([AgentRole.OPS, AgentRole.DEV])
        
        if 'security' in trigger_event.lower():
            affected.append(AgentRole.SECURITY)
        
        if 'user' in trigger_event.lower() or 'customer' in trigger_event.lower():
            affected.extend([AgentRole.SUPPORT, AgentRole.PM])
        
        if 'billing' in trigger_event.lower() or 'payment' in trigger_event.lower():
            affected.append(AgentRole.BILLING)
        
        # 默認包含 CEO Agent
        if AgentRole.CEO not in affected:
            affected.append(AgentRole.CEO)
        
        return affected
    
    async def _generate_strategies(self, context: DecisionContext) -> List[Dict[str, Any]]:
        """生成候選策略"""
        strategies = []
        
        # 基於觸發事件生成策略
        if 'high_latency' in context.trigger_event:
            strategies.extend([
                {
                    'name': 'restart_slow_services',
                    'actions': [
                        {'type': 'restart_service', 'agent': 'ops_agent', 'parameters': {'service_name': 'api-gateway'}},
                        {'type': 'send_notification', 'parameters': {'channel': 'slack', 'message': 'API services restarted due to high latency'}}
                    ],
                    'expected_outcome': 'Reduced API latency',
                    'timeline': 'immediate',
                    'rollback_plan': 'Monitor for 10 minutes, rollback if latency increases'
                },
                {
                    'name': 'scale_up_resources',
                    'actions': [
                        {'type': 'scale_resources', 'agent': 'ops_agent', 'parameters': {'service': 'api-gateway', 'replicas': 3}},
                        {'type': 'update_configuration', 'parameters': {'key': 'max_connections', 'value': '1000'}}
                    ],
                    'expected_outcome': 'Increased capacity to handle load',
                    'timeline': '5 minutes'
                }
            ])
        
        elif 'high_error_rate' in context.trigger_event:
            strategies.append({
                'name': 'investigate_and_fix_errors',
                'actions': [
                    {'type': 'send_notification', 'parameters': {'channel': 'slack', 'message': 'High error rate detected, investigating...'}},
                    {'type': 'restart_service', 'agent': 'ops_agent', 'parameters': {'service_name': 'backend-api'}}
                ],
                'expected_outcome': 'Reduced error rate',
                'timeline': 'immediate'
            })
        
        elif 'user_growth' in context.trigger_event:
            strategies.append({
                'name': 'optimize_for_growth',
                'actions': [
                    {'type': 'scale_resources', 'agent': 'ops_agent', 'parameters': {'service': 'all', 'replicas': 5}},
                    {'type': 'update_configuration', 'parameters': {'key': 'cache_ttl', 'value': '3600'}}
                ],
                'expected_outcome': 'Better performance for increased user load',
                'timeline': '10 minutes'
            })
        
        # 如果沒有特定策略，生成默認策略
        if not strategies:
            strategies.append({
                'name': 'monitor_and_alert',
                'actions': [
                    {'type': 'send_notification', 'parameters': {'channel': 'slack', 'message': f'Event detected: {context.trigger_event}'}}
                ],
                'expected_outcome': 'Team notified of event',
                'timeline': 'immediate'
            })
        
        return strategies
    
    async def execute_decision(self, decision: DecisionResult) -> bool:
        """執行決策"""
        return await self.executor.execute_strategy(decision)
    
    async def monitor_execution(self, decision_id: str) -> Dict[str, Any]:
        """監控決策執行狀態"""
        if decision_id in self.executor.active_executions:
            return self.executor.active_executions[decision_id]
        return {'status': 'not_found'}

# 使用示例
async def main():
    """主函數示例"""
    # 初始化 Redis 和資料庫連接
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    db_connection = psycopg2.connect(
        host='localhost',
        database='morningai',
        user='postgres',
        password='password'
    )
    
    # 創建 Meta-Agent
    meta_agent = MetaAgent(redis_client, db_connection)
    
    # 模擬觸發事件
    decision = await meta_agent.make_decision(
        trigger_event='high_latency_detected',
        business_context={'current_users': 1500, 'peak_hour': True}
    )
    
    if decision:
        print(f"Decision: {decision.strategy}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Risk: {decision.risk_assessment:.2f}")
        
        # 執行決策
        success = await meta_agent.execute_decision(decision)
        print(f"Execution success: {success}")
    
    # 清理資源
    redis_client.close()
    db_connection.close()

if __name__ == "__main__":
    asyncio.run(main())

