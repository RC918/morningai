"""
Meta Agent 集成測試
測試MetaAgent與其他組件的集成
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from meta_agent_implementation import MetaAgent, StrategyGenerator
from ai_service_gateway import AIServiceGateway
from strategy_learning_system import StrategyLearningSystem
from enhanced_decision_simulator import EnhancedDecisionSimulator

@pytest.mark.integration
class TestMetaAgentIntegration:
    
    @pytest.fixture
    def mock_components(self):
        """創建模擬的組件"""
        return {
            'ai_gateway': Mock(spec=AIServiceGateway),
            'learning_system': Mock(spec=StrategyLearningSystem),
            'decision_simulator': Mock(spec=EnhancedDecisionSimulator),
            'db_session': Mock()
        }
    
    @pytest.fixture
    def meta_agent(self, mock_components):
        """創建測試用的MetaAgent實例"""
        return MetaAgent(
            ai_gateway=mock_components['ai_gateway'],
            learning_system=mock_components['learning_system'],
            decision_simulator=mock_components['decision_simulator'],
            db_session=mock_components['db_session']
        )
    
    @pytest.mark.asyncio
    async def test_complete_decision_workflow(self, meta_agent, mock_components):
        """測試完整的決策工作流程"""
        # 模擬系統狀態
        system_state = {
            "cpu_usage": 85,
            "memory_usage": 70,
            "response_time": 200,
            "error_rate": 0.05,
            "active_connections": 1500
        }
        
        # 模擬學習系統返回候選策略
        mock_components['learning_system'].get_strategy_recommendations.return_value = [
            {
                "id": "strategy_001",
                "name": "CPU優化策略",
                "confidence_score": 0.85,
                "actions": [{"type": "scale_up", "parameters": {"instances": 2}}]
            }
        ]
        
        # 模擬決策模擬器返回影響預測
        mock_components['decision_simulator'].simulate_strategy_impact.return_value = {
            "predicted_improvement": 20,
            "estimated_cost": 15.50,
            "risk_score": 0.2,
            "confidence": 0.8
        }
        
        # 模擬AI網關生成新策略
        mock_components['ai_gateway'].generate_response.return_value = {
            "content": '{"strategy": {"name": "AI生成策略", "actions": [{"type": "optimize_cache"}]}}',
            "model": "gpt-4",
            "tokens_used": 150
        }
        
        # 執行決策流程
        decision = await meta_agent.make_decision(system_state)
        
        # 驗證決策結果
        assert decision is not None
        assert "recommended_strategy" in decision
        assert "confidence_score" in decision
        assert "predicted_impact" in decision
        
        # 驗證各組件被正確調用
        mock_components['learning_system'].get_strategy_recommendations.assert_called_once()
        mock_components['decision_simulator'].simulate_strategy_impact.assert_called()
    
    @pytest.mark.asyncio
    async def test_strategy_generation_integration(self, meta_agent, mock_components):
        """測試策略生成的集成"""
        problem_context = {
            "issue_type": "performance_degradation",
            "affected_metrics": ["response_time", "cpu_usage"],
            "severity": "high",
            "duration": "15_minutes"
        }
        
        # 模擬AI網關回應
        mock_components['ai_gateway'].generate_response.return_value = {
            "content": '''
            {
                "strategies": [
                    {
                        "name": "緊急性能優化",
                        "priority": "high",
                        "actions": [
                            {"type": "increase_cache_size", "parameters": {"size_mb": 512}},
                            {"type": "scale_up", "parameters": {"instances": 3}}
                        ],
                        "estimated_impact": {
                            "response_time_improvement": 30,
                            "cpu_reduction": 15
                        }
                    }
                ]
            }
            ''',
            "model": "gpt-4",
            "tokens_used": 200
        }
        
        # 模擬學習系統生成模板策略
        mock_components['learning_system'].generate_strategy_from_template.return_value = Mock(
            id="template_001",
            name="模板策略",
            confidence_score=0.75
        )
        
        strategy_generator = StrategyGenerator(
            ai_gateway=mock_components['ai_gateway'],
            learning_system=mock_components['learning_system']
        )
        
        strategies = await strategy_generator.generate_strategies(problem_context)
        
        # 驗證策略生成
        assert len(strategies) > 0
        assert any(s.get("source") == "ai_generated" for s in strategies)
        
        # 驗證AI網關被調用
        mock_components['ai_gateway'].generate_response.assert_called()
        mock_components['learning_system'].generate_strategy_from_template.assert_called()
    
    @pytest.mark.asyncio
    async def test_learning_feedback_loop(self, meta_agent, mock_components):
        """測試學習反饋循環"""
        strategy_id = "executed_strategy_001"
        execution_result = {
            "success": True,
            "metrics_before": {"cpu_usage": 85, "response_time": 200},
            "metrics_after": {"cpu_usage": 70, "response_time": 150},
            "execution_time": 45.2,
            "user_feedback": {
                "rating": 5,
                "comments": "策略執行完美，系統性能顯著改善"
            }
        }
        
        # 執行反饋處理
        await meta_agent.process_execution_feedback(strategy_id, execution_result)
        
        # 驗證學習系統記錄執行結果
        mock_components['learning_system'].record_strategy_execution.assert_called_once_with(
            strategy_id, execution_result
        )
        
        # 驗證用戶反饋被處理
        mock_components['learning_system'].learn_from_feedback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, meta_agent, mock_components):
        """測試錯誤處理集成"""
        system_state = {"cpu_usage": 95}  # 極高CPU使用率
        
        # 模擬AI網關失敗
        mock_components['ai_gateway'].generate_response.side_effect = Exception("API調用失敗")
        
        # 模擬學習系統提供備用策略
        mock_components['learning_system'].get_strategy_recommendations.return_value = [
            {
                "id": "fallback_001",
                "name": "緊急備用策略",
                "confidence_score": 0.6,
                "actions": [{"type": "emergency_scale_up"}]
            }
        ]
        
        # 執行決策（應該優雅地處理錯誤）
        decision = await meta_agent.make_decision(system_state)
        
        # 驗證即使AI網關失敗，仍能返回決策
        assert decision is not None
        assert decision["recommended_strategy"]["name"] == "緊急備用策略"
        
        # 驗證錯誤被記錄
        assert meta_agent.error_count > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_decision_making(self, meta_agent, mock_components):
        """測試並發決策處理"""
        # 模擬多個並發的系統狀態
        system_states = [
            {"cpu_usage": 85, "issue_id": "cpu_high_1"},
            {"memory_usage": 90, "issue_id": "memory_high_1"},
            {"response_time": 500, "issue_id": "latency_high_1"}
        ]
        
        # 為每個狀態配置模擬回應
        mock_components['learning_system'].get_strategy_recommendations.return_value = [
            {"id": "concurrent_strategy", "confidence_score": 0.8}
        ]
        
        mock_components['decision_simulator'].simulate_strategy_impact.return_value = {
            "predicted_improvement": 15,
            "confidence": 0.7
        }
        
        # 並發執行決策
        tasks = [
            meta_agent.make_decision(state) 
            for state in system_states
        ]
        
        decisions = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 驗證所有決策都成功完成
        assert len(decisions) == 3
        assert all(isinstance(d, dict) for d in decisions if not isinstance(d, Exception))
        
        # 驗證並發安全性（沒有競態條件）
        assert meta_agent.total_decisions >= 3
    
    @pytest.mark.asyncio
    async def test_decision_quality_metrics(self, meta_agent, mock_components):
        """測試決策質量指標"""
        # 執行多個決策
        for i in range(5):
            system_state = {"cpu_usage": 80 + i, "iteration": i}
            
            mock_components['learning_system'].get_strategy_recommendations.return_value = [
                {"id": f"strategy_{i}", "confidence_score": 0.7 + i * 0.05}
            ]
            
            await meta_agent.make_decision(system_state)
        
        # 獲取決策質量指標
        quality_metrics = meta_agent.get_decision_quality_metrics()
        
        assert quality_metrics["total_decisions"] == 5
        assert "average_confidence" in quality_metrics
        assert "decision_latency_avg" in quality_metrics
        assert quality_metrics["average_confidence"] > 0
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, meta_agent, mock_components):
        """測試系統健康監控集成"""
        # 模擬系統健康檢查
        health_status = await meta_agent.check_system_health()
        
        assert "components" in health_status
        assert "overall_status" in health_status
        assert "last_check_time" in health_status
        
        # 驗證各組件的健康狀態被檢查
        components = health_status["components"]
        assert "ai_gateway" in components
        assert "learning_system" in components
        assert "decision_simulator" in components
    
    @pytest.mark.asyncio
    async def test_configuration_updates(self, meta_agent):
        """測試配置更新的集成"""
        new_config = {
            "confidence_threshold": 0.9,
            "max_concurrent_decisions": 10,
            "learning_rate": 0.15
        }
        
        # 更新配置
        await meta_agent.update_configuration(new_config)
        
        # 驗證配置被正確應用
        assert meta_agent.config["confidence_threshold"] == 0.9
        assert meta_agent.config["max_concurrent_decisions"] == 10
        
        # 驗證配置變更被記錄
        assert len(meta_agent.config_history) > 0

