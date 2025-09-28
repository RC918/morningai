"""
Meta-Agent 決策中樞 - 技術實現範例
版本: 1.0
日期: 2025-09-12
作者: Manus AI

這是 Morning AI Meta-Agent 決策中樞的核心實現代碼，
展示了 OODA 循環的完整技術實現。
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
from pydantic import BaseModel
import redis
import psycopg2
from sqlalchemy import create_engine
import openai
from langgraph import StateGraph, END
import boto3
import prometheus_client

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 數據模型定義 ====================

class AlertLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AgentType(Enum):
    CEO_AGENT = "ceo_agent"
    PM_AGENT = "pm_agent"
    DEV_AGENT = "dev_agent"
    QA_AGENT = "qa_agent"
    OPS_AGENT = "ops_agent"
    SECURITY_AGENT = "security_agent"

@dataclass
class SystemMetric:
    """系統指標數據結構"""
    name: str
    value: float
    timestamp: datetime
    source: str
    tags: Dict[str, str] = None

@dataclass
class BusinessMetric:
    """業務指標數據結構"""
    name: str
    value: float
    timestamp: datetime
    dimension: str  # daily, weekly, monthly
    tags: Dict[str, str] = None

@dataclass
class SituationAssessment:
    """態勢評估報告"""
    timestamp: datetime
    overall_health_score: float  # 0-100
    critical_issues: List[str]
    key_deviations: Dict[str, float]
    root_cause_analysis: Dict[str, str]
    confidence_level: float  # 0-1

@dataclass
class Strategy:
    """策略定義"""
    id: str
    name: str
    description: str
    expected_gain: float
    implementation_cost: float
    risk_level: AlertLevel
    success_probability: float
    tasks: List[Dict[str, Any]]

@dataclass
class Task:
    """任務定義"""
    id: str
    agent_type: AgentType
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    timeout: int = 300  # seconds

# ==================== 感知層 (Perception Layer) ====================

class MonitoringAdapter:
    """監控適配器 - 連接各種監控系統"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.prometheus_client = prometheus_client
        
    async def collect_system_metrics(self) -> List[SystemMetric]:
        """收集系統性能指標"""
        metrics = []
        
        # 模擬從 Prometheus 收集指標
        metric_queries = [
            ("api_request_duration_p95", "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"),
            ("cpu_usage_percent", "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"),
            ("memory_usage_percent", "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"),
            ("error_rate_5xx", "rate(http_requests_total{status=~\"5..\"}[5m])"),
        ]
        
        for name, query in metric_queries:
            # 實際實現中會調用 Prometheus API
            value = np.random.uniform(0, 100)  # 模擬數據
            metrics.append(SystemMetric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                source="prometheus"
            ))
            
        return metrics

class DatabaseConnector:
    """數據庫連接器 - 收集業務指標"""
    
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        
    async def collect_business_metrics(self) -> List[BusinessMetric]:
        """收集業務指標"""
        metrics = []
        
        # 模擬業務指標查詢
        business_queries = [
            ("daily_active_users", "SELECT COUNT(DISTINCT user_id) FROM user_sessions WHERE created_at >= CURRENT_DATE"),
            ("conversion_rate", "SELECT (COUNT(*) FILTER (WHERE subscription_id IS NOT NULL) * 100.0 / COUNT(*)) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"),
            ("churn_rate", "SELECT (COUNT(*) FILTER (WHERE cancelled_at IS NOT NULL) * 100.0 / COUNT(*)) FROM subscriptions WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'"),
        ]
        
        for name, query in business_queries:
            # 實際實現中會執行 SQL 查詢
            value = np.random.uniform(0, 100)  # 模擬數據
            metrics.append(BusinessMetric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                dimension="daily"
            ))
            
        return metrics

# ==================== 認知層 (Cognition Layer) ====================

class GlobalStateManager:
    """全局狀態管理器"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.state_key = "meta_agent:global_state"
        
    async def update_state(self, metrics: List[SystemMetric], business_metrics: List[BusinessMetric]):
        """更新全局狀態"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": [asdict(m) for m in metrics],
            "business_metrics": [asdict(m) for m in business_metrics],
        }
        
        await self.redis.set(self.state_key, json.dumps(state, default=str))
        logger.info(f"Global state updated with {len(metrics)} system metrics and {len(business_metrics)} business metrics")
        
    async def get_current_state(self) -> Dict[str, Any]:
        """獲取當前全局狀態"""
        state_json = await self.redis.get(self.state_key)
        if state_json:
            return json.loads(state_json)
        return {}

class WorldModel:
    """世界模型 - 用於預測和模擬"""
    
    def __init__(self):
        self.model_weights = {}  # 簡化的模型權重
        
    def predict_impact(self, strategy: Strategy, current_state: Dict[str, Any]) -> Dict[str, float]:
        """預測策略對系統的影響"""
        # 簡化的影響預測邏輯
        impact = {
            "performance_improvement": strategy.expected_gain * 0.8,
            "cost_increase": strategy.implementation_cost,
            "risk_factor": strategy.risk_level.value,
            "success_probability": strategy.success_probability
        }
        
        logger.info(f"Predicted impact for strategy {strategy.name}: {impact}")
        return impact
        
    def simulate_strategy(self, strategy: Strategy, current_state: Dict[str, Any], simulation_steps: int = 100) -> Dict[str, Any]:
        """模擬策略執行的結果"""
        # 蒙特卡羅模擬
        results = []
        
        for _ in range(simulation_steps):
            # 添加隨機性來模擬不確定性
            noise = np.random.normal(0, 0.1)
            simulated_gain = strategy.expected_gain * (1 + noise)
            simulated_cost = strategy.implementation_cost * (1 + abs(noise))
            
            results.append({
                "gain": simulated_gain,
                "cost": simulated_cost,
                "net_benefit": simulated_gain - simulated_cost
            })
        
        # 計算統計摘要
        gains = [r["gain"] for r in results]
        costs = [r["cost"] for r in results]
        net_benefits = [r["net_benefit"] for r in results]
        
        simulation_result = {
            "mean_gain": np.mean(gains),
            "std_gain": np.std(gains),
            "mean_cost": np.mean(costs),
            "std_cost": np.std(costs),
            "mean_net_benefit": np.mean(net_benefits),
            "success_rate": len([nb for nb in net_benefits if nb > 0]) / len(net_benefits),
            "confidence_interval_95": np.percentile(net_benefits, [2.5, 97.5])
        }
        
        logger.info(f"Simulation completed for strategy {strategy.name}: {simulation_result}")
        return simulation_result

class SituationAnalyzer:
    """態勢分析器"""
    
    def __init__(self, world_model: WorldModel):
        self.world_model = world_model
        self.thresholds = {
            "api_latency_critical": 1000,  # ms
            "error_rate_critical": 5.0,    # %
            "cpu_usage_critical": 90.0,    # %
            "churn_rate_critical": 10.0,   # %
        }
        
    async def analyze_situation(self, current_state: Dict[str, Any]) -> SituationAssessment:
        """分析當前態勢"""
        system_metrics = current_state.get("system_metrics", [])
        business_metrics = current_state.get("business_metrics", [])
        
        # 計算整體健康分數
        health_score = self._calculate_health_score(system_metrics, business_metrics)
        
        # 識別關鍵問題
        critical_issues = self._identify_critical_issues(system_metrics, business_metrics)
        
        # 計算關鍵偏差
        key_deviations = self._calculate_deviations(system_metrics, business_metrics)
        
        # 根本原因分析
        root_causes = self._analyze_root_causes(critical_issues, key_deviations)
        
        assessment = SituationAssessment(
            timestamp=datetime.now(),
            overall_health_score=health_score,
            critical_issues=critical_issues,
            key_deviations=key_deviations,
            root_cause_analysis=root_causes,
            confidence_level=0.85  # 簡化的信心分數
        )
        
        logger.info(f"Situation analysis completed. Health score: {health_score:.2f}")
        return assessment
        
    def _calculate_health_score(self, system_metrics: List[Dict], business_metrics: List[Dict]) -> float:
        """計算系統整體健康分數 (0-100)"""
        scores = []
        
        # 系統指標評分
        for metric in system_metrics:
            if metric["name"] == "api_request_duration_p95":
                score = max(0, 100 - (metric["value"] / 10))  # 延遲越低分數越高
            elif metric["name"] == "error_rate_5xx":
                score = max(0, 100 - (metric["value"] * 20))  # 錯誤率越低分數越高
            elif metric["name"] in ["cpu_usage_percent", "memory_usage_percent"]:
                score = max(0, 100 - metric["value"])  # 使用率越低分數越高
            else:
                score = 50  # 默認分數
            scores.append(score)
        
        # 業務指標評分
        for metric in business_metrics:
            if metric["name"] == "daily_active_users":
                score = min(100, metric["value"] / 10)  # DAU 越高分數越高
            elif metric["name"] == "conversion_rate":
                score = metric["value"] * 2  # 轉化率越高分數越高
            elif metric["name"] == "churn_rate":
                score = max(0, 100 - (metric["value"] * 10))  # 流失率越低分數越高
            else:
                score = 50
            scores.append(score)
        
        return np.mean(scores) if scores else 50.0
        
    def _identify_critical_issues(self, system_metrics: List[Dict], business_metrics: List[Dict]) -> List[str]:
        """識別關鍵問題"""
        issues = []
        
        for metric in system_metrics:
            if metric["name"] == "api_request_duration_p95" and metric["value"] > self.thresholds["api_latency_critical"]:
                issues.append(f"API latency critically high: {metric['value']:.2f}ms")
            elif metric["name"] == "error_rate_5xx" and metric["value"] > self.thresholds["error_rate_critical"]:
                issues.append(f"Error rate critically high: {metric['value']:.2f}%")
            elif metric["name"] == "cpu_usage_percent" and metric["value"] > self.thresholds["cpu_usage_critical"]:
                issues.append(f"CPU usage critically high: {metric['value']:.2f}%")
        
        for metric in business_metrics:
            if metric["name"] == "churn_rate" and metric["value"] > self.thresholds["churn_rate_critical"]:
                issues.append(f"Churn rate critically high: {metric['value']:.2f}%")
        
        return issues
        
    def _calculate_deviations(self, system_metrics: List[Dict], business_metrics: List[Dict]) -> Dict[str, float]:
        """計算關鍵偏差"""
        deviations = {}
        
        # 目標值（這些通常來自 OKR 設定）
        targets = {
            "api_request_duration_p95": 200,  # ms
            "error_rate_5xx": 1.0,            # %
            "cpu_usage_percent": 70.0,        # %
            "conversion_rate": 15.0,          # %
            "churn_rate": 5.0,                # %
        }
        
        all_metrics = system_metrics + business_metrics
        for metric in all_metrics:
            metric_name = metric["name"]
            if metric_name in targets:
                target = targets[metric_name]
                actual = metric["value"]
                deviation = ((actual - target) / target) * 100  # 百分比偏差
                deviations[metric_name] = deviation
        
        return deviations
        
    def _analyze_root_causes(self, critical_issues: List[str], deviations: Dict[str, float]) -> Dict[str, str]:
        """根本原因分析（簡化版）"""
        root_causes = {}
        
        # 簡化的因果推斷邏輯
        if any("API latency" in issue for issue in critical_issues):
            if deviations.get("cpu_usage_percent", 0) > 20:
                root_causes["high_api_latency"] = "High CPU usage causing performance bottleneck"
            else:
                root_causes["high_api_latency"] = "Possible database query optimization needed"
        
        if any("Error rate" in issue for issue in critical_issues):
            root_causes["high_error_rate"] = "Recent deployment may have introduced bugs"
        
        if any("Churn rate" in issue for issue in critical_issues):
            root_causes["high_churn_rate"] = "Competitor pricing or feature gap analysis needed"
        
        return root_causes

# ==================== 決策層 (Decision-Making Layer) ====================

class StrategyGenerator:
    """策略生成器"""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.strategy_templates = {
            "scale_up": {
                "name": "Horizontal Scale Up",
                "description": "Increase the number of application instances",
                "base_cost": 100,
                "base_gain": 30
            },
            "optimize_database": {
                "name": "Database Query Optimization",
                "description": "Optimize slow database queries",
                "base_cost": 50,
                "base_gain": 25
            },
            "cache_implementation": {
                "name": "Implement Redis Caching",
                "description": "Add caching layer to reduce database load",
                "base_cost": 75,
                "base_gain": 40
            }
        }
        
    async def generate_strategies(self, assessment: SituationAssessment) -> List[Strategy]:
        """根據態勢評估生成策略"""
        strategies = []
        
        # 基於規則的策略生成
        for issue in assessment.critical_issues:
            if "API latency" in issue:
                strategies.extend(self._generate_performance_strategies())
            elif "Error rate" in issue:
                strategies.extend(self._generate_reliability_strategies())
            elif "Churn rate" in issue:
                strategies.extend(self._generate_retention_strategies())
        
        # 如果沒有關鍵問題，生成優化策略
        if not assessment.critical_issues and assessment.overall_health_score < 90:
            strategies.extend(self._generate_optimization_strategies())
        
        # 使用 LLM 生成創新策略（針對複雜問題）
        if assessment.confidence_level < 0.7:
            llm_strategies = await self._generate_llm_strategies(assessment)
            strategies.extend(llm_strategies)
        
        return strategies
        
    def _generate_performance_strategies(self) -> List[Strategy]:
        """生成性能優化策略"""
        return [
            Strategy(
                id="perf_001",
                name="Horizontal Scale Up",
                description="Increase application instances to handle higher load",
                expected_gain=30.0,
                implementation_cost=100.0,
                risk_level=AlertLevel.LOW,
                success_probability=0.9,
                tasks=[
                    {"agent": "ops_agent", "action": "scale_instances", "params": {"count": 2}}
                ]
            ),
            Strategy(
                id="perf_002",
                name="Implement Redis Caching",
                description="Add Redis caching to reduce database load",
                expected_gain=40.0,
                implementation_cost=75.0,
                risk_level=AlertLevel.MEDIUM,
                success_probability=0.85,
                tasks=[
                    {"agent": "dev_agent", "action": "implement_caching", "params": {"type": "redis"}},
                    {"agent": "qa_agent", "action": "test_caching", "params": {}}
                ]
            )
        ]
        
    def _generate_reliability_strategies(self) -> List[Strategy]:
        """生成可靠性提升策略"""
        return [
            Strategy(
                id="rel_001",
                name="Rollback Recent Deployment",
                description="Rollback to previous stable version",
                expected_gain=50.0,
                implementation_cost=20.0,
                risk_level=AlertLevel.LOW,
                success_probability=0.95,
                tasks=[
                    {"agent": "ops_agent", "action": "rollback_deployment", "params": {"version": "previous"}}
                ]
            )
        ]
        
    def _generate_retention_strategies(self) -> List[Strategy]:
        """生成用戶留存策略"""
        return [
            Strategy(
                id="ret_001",
                name="Launch Retention Campaign",
                description="Send personalized retention offers to at-risk users",
                expected_gain=15.0,
                implementation_cost=50.0,
                risk_level=AlertLevel.LOW,
                success_probability=0.7,
                tasks=[
                    {"agent": "growth_agent", "action": "create_campaign", "params": {"type": "retention"}},
                    {"agent": "announcer_agent", "action": "send_notifications", "params": {}}
                ]
            )
        ]
        
    def _generate_optimization_strategies(self) -> List[Strategy]:
        """生成一般優化策略"""
        return [
            Strategy(
                id="opt_001",
                name="Database Query Optimization",
                description="Optimize slow database queries identified in logs",
                expected_gain=25.0,
                implementation_cost=40.0,
                risk_level=AlertLevel.LOW,
                success_probability=0.8,
                tasks=[
                    {"agent": "dev_agent", "action": "optimize_queries", "params": {}},
                    {"agent": "qa_agent", "action": "performance_test", "params": {}}
                ]
            )
        ]
        
    async def _generate_llm_strategies(self, assessment: SituationAssessment) -> List[Strategy]:
        """使用 LLM 生成創新策略"""
        prompt = f"""
        Based on the following system assessment, generate innovative strategies to improve the situation:
        
        Health Score: {assessment.overall_health_score}
        Critical Issues: {assessment.critical_issues}
        Key Deviations: {assessment.key_deviations}
        Root Causes: {assessment.root_cause_analysis}
        
        Please suggest 2-3 creative strategies that address the root causes.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            # 解析 LLM 回應並轉換為策略對象
            # 這裡簡化處理，實際實現需要更複雜的解析邏輯
            llm_content = response.choices[0].message.content
            
            return [
                Strategy(
                    id="llm_001",
                    name="LLM Generated Strategy",
                    description=llm_content[:100] + "...",
                    expected_gain=20.0,
                    implementation_cost=60.0,
                    risk_level=AlertLevel.MEDIUM,
                    success_probability=0.6,
                    tasks=[{"agent": "pm_agent", "action": "evaluate_llm_strategy", "params": {}}]
                )
            ]
        except Exception as e:
            logger.error(f"Failed to generate LLM strategies: {e}")
            return []

class DecisionSimulator:
    """決策模擬器"""
    
    def __init__(self, world_model: WorldModel):
        self.world_model = world_model
        
    async def simulate_strategies(self, strategies: List[Strategy], current_state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """模擬所有策略的執行結果"""
        simulation_results = {}
        
        for strategy in strategies:
            result = self.world_model.simulate_strategy(strategy, current_state)
            simulation_results[strategy.id] = result
            
        return simulation_results

class DecisionSelector:
    """決策選擇器"""
    
    def __init__(self):
        self.utility_weights = {
            "gain": 0.4,
            "cost": -0.3,
            "risk": -0.2,
            "success_probability": 0.1
        }
        
    async def select_optimal_strategy(self, strategies: List[Strategy], simulation_results: Dict[str, Dict[str, Any]]) -> Tuple[Strategy, bool]:
        """選擇最優策略"""
        best_strategy = None
        best_utility = float('-inf')
        requires_human_approval = False
        
        for strategy in strategies:
            simulation = simulation_results.get(strategy.id, {})
            
            # 計算效用分數
            utility = self._calculate_utility(strategy, simulation)
            
            if utility > best_utility:
                best_utility = utility
                best_strategy = strategy
                
        # 檢查是否需要人類審批
        if best_strategy:
            requires_human_approval = self._requires_human_approval(best_strategy)
            
        logger.info(f"Selected strategy: {best_strategy.name if best_strategy else 'None'}, Utility: {best_utility:.2f}, Requires approval: {requires_human_approval}")
        
        return best_strategy, requires_human_approval
        
    def _calculate_utility(self, strategy: Strategy, simulation: Dict[str, Any]) -> float:
        """計算策略的效用分數"""
        gain = simulation.get("mean_gain", strategy.expected_gain)
        cost = simulation.get("mean_cost", strategy.implementation_cost)
        risk_penalty = {"low": 0, "medium": 10, "high": 25, "critical": 50}[strategy.risk_level.value]
        success_prob = simulation.get("success_rate", strategy.success_probability)
        
        utility = (
            self.utility_weights["gain"] * gain +
            self.utility_weights["cost"] * cost +
            self.utility_weights["risk"] * risk_penalty +
            self.utility_weights["success_probability"] * success_prob * 100
        )
        
        return utility
        
    def _requires_human_approval(self, strategy: Strategy) -> bool:
        """判斷是否需要人類審批"""
        # 高風險或高成本策略需要人類審批
        return (
            strategy.risk_level in [AlertLevel.HIGH, AlertLevel.CRITICAL] or
            strategy.implementation_cost > 200 or
            strategy.success_probability < 0.7
        )

# ==================== 行動層 (Action Layer) ====================

class TaskOrchestrator:
    """任務編排器（基於 LangGraph）"""
    
    def __init__(self):
        self.graph = self._build_workflow_graph()
        
    def _build_workflow_graph(self) -> StateGraph:
        """構建工作流圖"""
        # 簡化的 LangGraph 工作流
        workflow = StateGraph(dict)
        
        workflow.add_node("validate_strategy", self._validate_strategy)
        workflow.add_node("decompose_tasks", self._decompose_tasks)
        workflow.add_node("execute_tasks", self._execute_tasks)
        workflow.add_node("monitor_execution", self._monitor_execution)
        workflow.add_node("report_results", self._report_results)
        
        workflow.add_edge("validate_strategy", "decompose_tasks")
        workflow.add_edge("decompose_tasks", "execute_tasks")
        workflow.add_edge("execute_tasks", "monitor_execution")
        workflow.add_edge("monitor_execution", "report_results")
        workflow.add_edge("report_results", END)
        
        workflow.set_entry_point("validate_strategy")
        
        return workflow.compile()
        
    async def execute_strategy(self, strategy: Strategy) -> Dict[str, Any]:
        """執行策略"""
        initial_state = {
            "strategy": strategy,
            "status": "started",
            "results": {},
            "errors": []
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        return final_state
        
    async def _validate_strategy(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """驗證策略"""
        strategy = state["strategy"]
        logger.info(f"Validating strategy: {strategy.name}")
        
        # 簡化的驗證邏輯
        if not strategy.tasks:
            state["errors"].append("Strategy has no tasks defined")
            state["status"] = "failed"
        else:
            state["status"] = "validated"
            
        return state
        
    async def _decompose_tasks(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """分解任務"""
        if state["status"] == "failed":
            return state
            
        strategy = state["strategy"]
        logger.info(f"Decomposing tasks for strategy: {strategy.name}")
        
        # 將策略任務轉換為可執行的任務對象
        executable_tasks = []
        for i, task_def in enumerate(strategy.tasks):
            task = Task(
                id=f"{strategy.id}_task_{i}",
                agent_type=AgentType(task_def["agent"]),
                action=task_def["action"],
                parameters=task_def.get("params", {})
            )
            executable_tasks.append(task)
            
        state["executable_tasks"] = executable_tasks
        state["status"] = "decomposed"
        return state
        
    async def _execute_tasks(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """執行任務"""
        if state["status"] == "failed":
            return state
            
        executable_tasks = state["executable_tasks"]
        logger.info(f"Executing {len(executable_tasks)} tasks")
        
        task_results = {}
        for task in executable_tasks:
            try:
                result = await self._execute_single_task(task)
                task_results[task.id] = result
            except Exception as e:
                logger.error(f"Task {task.id} failed: {e}")
                task_results[task.id] = {"status": "failed", "error": str(e)}
                
        state["task_results"] = task_results
        state["status"] = "executed"
        return state
        
    async def _execute_single_task(self, task: Task) -> Dict[str, Any]:
        """執行單個任務"""
        # 模擬任務執行
        logger.info(f"Executing task {task.id} for agent {task.agent_type.value}")
        
        # 實際實現中，這裡會通過消息隊列向對應的 Agent 發送任務
        await asyncio.sleep(1)  # 模擬執行時間
        
        return {
            "status": "completed",
            "execution_time": 1.0,
            "output": f"Task {task.action} completed successfully"
        }
        
    async def _monitor_execution(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """監控執行"""
        if state["status"] == "failed":
            return state
            
        task_results = state["task_results"]
        
        # 檢查所有任務的執行狀態
        failed_tasks = [task_id for task_id, result in task_results.items() if result.get("status") == "failed"]
        
        if failed_tasks:
            state["status"] = "partially_failed"
            state["failed_tasks"] = failed_tasks
        else:
            state["status"] = "completed"
            
        return state
        
    async def _report_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """報告結果"""
        strategy = state["strategy"]
        status = state["status"]
        
        logger.info(f"Strategy {strategy.name} execution completed with status: {status}")
        
        # 生成執行報告
        execution_report = {
            "strategy_id": strategy.id,
            "strategy_name": strategy.name,
            "execution_status": status,
            "total_tasks": len(state.get("executable_tasks", [])),
            "failed_tasks": len(state.get("failed_tasks", [])),
            "execution_time": time.time() - state.get("start_time", time.time()),
            "errors": state.get("errors", [])
        }
        
        state["execution_report"] = execution_report
        return state

# ==================== Meta-Agent 主控制器 ====================

class MetaAgent:
    """Meta-Agent 決策中樞主控制器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 初始化各層組件
        self.monitoring_adapter = MonitoringAdapter(config.get("monitoring", {}))
        self.db_connector = DatabaseConnector(config["database_url"])
        
        redis_client = redis.Redis.from_url(config["redis_url"])
        self.global_state_manager = GlobalStateManager(redis_client)
        
        self.world_model = WorldModel()
        self.situation_analyzer = SituationAnalyzer(self.world_model)
        
        openai.api_key = config["openai_api_key"]
        self.strategy_generator = StrategyGenerator(openai)
        self.decision_simulator = DecisionSimulator(self.world_model)
        self.decision_selector = DecisionSelector()
        
        self.task_orchestrator = TaskOrchestrator()
        
        # OODA 循環控制
        self.is_running = False
        self.cycle_interval = config.get("cycle_interval", 30)  # seconds
        
    async def start(self):
        """啟動 Meta-Agent"""
        logger.info("Starting Meta-Agent decision center...")
        self.is_running = True
        
        while self.is_running:
            try:
                await self._execute_ooda_cycle()
                await asyncio.sleep(self.cycle_interval)
            except Exception as e:
                logger.error(f"Error in OODA cycle: {e}")
                await asyncio.sleep(5)  # 短暫休息後重試
                
    async def stop(self):
        """停止 Meta-Agent"""
        logger.info("Stopping Meta-Agent decision center...")
        self.is_running = False
        
    async def _execute_ooda_cycle(self):
        """執行一次完整的 OODA 循環"""
        cycle_start_time = time.time()
        logger.info("Starting OODA cycle...")
        
        try:
            # 1. Observe - 觀察
            system_metrics = await self.monitoring_adapter.collect_system_metrics()
            business_metrics = await self.db_connector.collect_business_metrics()
            await self.global_state_manager.update_state(system_metrics, business_metrics)
            
            # 2. Orient - 定向
            current_state = await self.global_state_manager.get_current_state()
            situation_assessment = await self.situation_analyzer.analyze_situation(current_state)
            
            # 3. Decide - 決策
            if situation_assessment.critical_issues or situation_assessment.overall_health_score < 80:
                strategies = await self.strategy_generator.generate_strategies(situation_assessment)
                
                if strategies:
                    simulation_results = await self.decision_simulator.simulate_strategies(strategies, current_state)
                    optimal_strategy, requires_approval = await self.decision_selector.select_optimal_strategy(strategies, simulation_results)
                    
                    if optimal_strategy:
                        if requires_approval:
                            logger.info(f"Strategy {optimal_strategy.name} requires human approval")
                            # 實際實現中會觸發 HITL 流程
                        else:
                            # 4. Act - 行動
                            execution_result = await self.task_orchestrator.execute_strategy(optimal_strategy)
                            logger.info(f"Strategy execution completed: {execution_result['execution_report']}")
            else:
                logger.info("System is healthy, no action required")
                
        except Exception as e:
            logger.error(f"Error in OODA cycle: {e}")
            
        cycle_duration = time.time() - cycle_start_time
        logger.info(f"OODA cycle completed in {cycle_duration:.2f} seconds")

# ==================== 使用範例 ====================

async def main():
    """主函數 - 展示 Meta-Agent 的使用"""
    
    # 配置
    config = {
        "database_url": "postgresql://user:pass@localhost/morningai",
        "redis_url": "redis://localhost:6379",
        "openai_api_key": "your-openai-api-key",
        "cycle_interval": 30,
        "monitoring": {
            "prometheus_url": "http://localhost:9090"
        }
    }
    
    # 創建並啟動 Meta-Agent
    meta_agent = MetaAgent(config)
    
    try:
        await meta_agent.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await meta_agent.stop()

if __name__ == "__main__":
    asyncio.run(main())

