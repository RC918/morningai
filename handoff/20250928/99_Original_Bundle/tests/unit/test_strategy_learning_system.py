"""
策略學習系統單元測試
測試StrategyLearningSystem的核心功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from strategy_learning_system import StrategyLearningSystem, CandidateStrategy, StrategyTemplate

@pytest.mark.unit
class TestStrategyLearningSystem:
    
    @pytest.fixture
    def mock_db_session(self):
        """模擬資料庫會話"""
        return Mock()
    
    @pytest.fixture
    def learning_system(self, mock_db_session):
        """創建測試用的學習系統實例"""
        return StrategyLearningSystem(
            db_session=mock_db_session,
            learning_rate=0.1,
            confidence_threshold=0.8
        )
    
    def test_system_initialization(self, learning_system):
        """測試系統初始化"""
        assert learning_system.learning_rate == 0.1
        assert learning_system.confidence_threshold == 0.8
        assert len(learning_system.candidate_strategies) == 0
        assert len(learning_system.strategy_templates) > 0
    
    def test_candidate_strategy_creation(self):
        """測試候選策略創建"""
        strategy = CandidateStrategy(
            id="test_001",
            name="測試策略",
            conditions={"cpu_usage": {"operator": ">", "value": 80}},
            actions=[{"type": "scale_up", "parameters": {"instances": 2}}],
            confidence_score=0.75,
            source="llm_generated"
        )
        
        assert strategy.id == "test_001"
        assert strategy.confidence_score == 0.75
        assert strategy.execution_count == 0
        assert strategy.success_count == 0
    
    @pytest.mark.asyncio
    async def test_record_strategy_execution(self, learning_system):
        """測試策略執行記錄"""
        strategy_id = "test_001"
        execution_result = {
            "success": True,
            "metrics_before": {"cpu_usage": 85, "response_time": 200},
            "metrics_after": {"cpu_usage": 70, "response_time": 150},
            "execution_time": 30.5
        }
        
        with patch.object(learning_system.db_session, 'add') as mock_add:
            await learning_system.record_strategy_execution(
                strategy_id, execution_result
            )
            
            mock_add.assert_called_once()
            # 驗證記錄的數據
            recorded_log = mock_add.call_args[0][0]
            assert recorded_log.strategy_id == strategy_id
            assert recorded_log.success == True
            assert recorded_log.improvement_score > 0  # 應該有改善
    
    @pytest.mark.asyncio
    async def test_calculate_improvement_score(self, learning_system):
        """測試改善分數計算"""
        metrics_before = {
            "cpu_usage": 85,
            "memory_usage": 70,
            "response_time": 200,
            "error_rate": 0.05
        }
        
        metrics_after = {
            "cpu_usage": 70,  # 改善了15%
            "memory_usage": 65,  # 改善了5%
            "response_time": 150,  # 改善了25%
            "error_rate": 0.02  # 改善了60%
        }
        
        score = learning_system._calculate_improvement_score(
            metrics_before, metrics_after
        )
        
        # 分數應該是正數，表示有改善
        assert score > 0
        assert score <= 100  # 分數應該在合理範圍內
    
    @pytest.mark.asyncio
    async def test_update_strategy_confidence(self, learning_system):
        """測試策略信心度更新"""
        # 創建一個候選策略
        strategy = CandidateStrategy(
            id="test_001",
            name="測試策略",
            conditions={"cpu_usage": {"operator": ">", "value": 80}},
            actions=[{"type": "scale_up"}],
            confidence_score=0.6,
            source="llm_generated"
        )
        
        learning_system.candidate_strategies["test_001"] = strategy
        
        # 模擬成功執行
        improvement_score = 25.0
        await learning_system._update_strategy_confidence(
            "test_001", True, improvement_score
        )
        
        # 信心度應該增加
        updated_strategy = learning_system.candidate_strategies["test_001"]
        assert updated_strategy.confidence_score > 0.6
        assert updated_strategy.execution_count == 1
        assert updated_strategy.success_count == 1
    
    @pytest.mark.asyncio
    async def test_promote_candidate_strategy(self, learning_system):
        """測試候選策略晉升"""
        # 創建一個高信心度的候選策略
        strategy = CandidateStrategy(
            id="test_001",
            name="高效策略",
            conditions={"cpu_usage": {"operator": ">", "value": 80}},
            actions=[{"type": "scale_up"}],
            confidence_score=0.85,  # 超過閾值
            source="llm_generated"
        )
        strategy.execution_count = 10
        strategy.success_count = 9
        
        learning_system.candidate_strategies["test_001"] = strategy
        
        with patch.object(learning_system.db_session, 'add') as mock_add:
            promoted = await learning_system._promote_candidate_strategy("test_001")
            
            assert promoted == True
            mock_add.assert_called_once()
            
            # 驗證策略已從候選列表中移除
            assert "test_001" not in learning_system.candidate_strategies
    
    @pytest.mark.asyncio
    async def test_generate_strategy_from_template(self, learning_system):
        """測試從模板生成策略"""
        context = {
            "problem_type": "high_cpu_usage",
            "current_metrics": {"cpu_usage": 85, "memory_usage": 60},
            "system_constraints": {"max_instances": 10, "budget_limit": 100}
        }
        
        with patch.object(learning_system, '_select_best_template') as mock_select:
            mock_template = StrategyTemplate(
                id="cpu_optimization",
                name="CPU優化模板",
                conditions_template={"cpu_usage": {"operator": ">", "value": "{threshold}"}},
                actions_template=[{"type": "scale_up", "parameters": {"instances": "{scale_factor}"}}]
            )
            mock_select.return_value = mock_template
            
            strategy = await learning_system.generate_strategy_from_template(context)
            
            assert strategy is not None
            assert strategy.name.startswith("CPU優化")
            assert "cpu_usage" in strategy.conditions
    
    @pytest.mark.asyncio
    async def test_get_strategy_recommendations(self, learning_system):
        """測試策略推薦"""
        # 添加一些候選策略
        high_confidence_strategy = CandidateStrategy(
            id="high_conf",
            name="高信心策略",
            conditions={"cpu_usage": {"operator": ">", "value": 80}},
            actions=[{"type": "scale_up"}],
            confidence_score=0.9,
            source="template"
        )
        
        low_confidence_strategy = CandidateStrategy(
            id="low_conf",
            name="低信心策略",
            conditions={"memory_usage": {"operator": ">", "value": 90}},
            actions=[{"type": "restart_service"}],
            confidence_score=0.3,
            source="llm_generated"
        )
        
        learning_system.candidate_strategies["high_conf"] = high_confidence_strategy
        learning_system.candidate_strategies["low_conf"] = low_confidence_strategy
        
        current_context = {"cpu_usage": 85, "memory_usage": 60}
        
        recommendations = await learning_system.get_strategy_recommendations(
            current_context, limit=5
        )
        
        # 應該優先推薦高信心度且匹配條件的策略
        assert len(recommendations) > 0
        assert recommendations[0]["confidence_score"] >= recommendations[-1]["confidence_score"]
    
    @pytest.mark.asyncio
    async def test_learning_from_feedback(self, learning_system):
        """測試從反饋中學習"""
        strategy_id = "test_001"
        feedback = {
            "user_rating": 4,  # 1-5分
            "effectiveness": "high",
            "side_effects": "none",
            "comments": "策略執行順利，效果明顯"
        }
        
        # 創建策略
        strategy = CandidateStrategy(
            id=strategy_id,
            name="測試策略",
            conditions={"cpu_usage": {"operator": ">", "value": 80}},
            actions=[{"type": "scale_up"}],
            confidence_score=0.7,
            source="llm_generated"
        )
        learning_system.candidate_strategies[strategy_id] = strategy
        
        await learning_system.learn_from_feedback(strategy_id, feedback)
        
        # 信心度應該根據正面反饋而增加
        updated_strategy = learning_system.candidate_strategies[strategy_id]
        assert updated_strategy.confidence_score > 0.7
    
    def test_strategy_similarity_calculation(self, learning_system):
        """測試策略相似度計算"""
        strategy1 = {
            "conditions": {"cpu_usage": {"operator": ">", "value": 80}},
            "actions": [{"type": "scale_up", "parameters": {"instances": 2}}]
        }
        
        strategy2 = {
            "conditions": {"cpu_usage": {"operator": ">", "value": 85}},
            "actions": [{"type": "scale_up", "parameters": {"instances": 3}}]
        }
        
        strategy3 = {
            "conditions": {"memory_usage": {"operator": ">", "value": 90}},
            "actions": [{"type": "restart_service"}]
        }
        
        # 相似的策略應該有較高的相似度分數
        similarity_12 = learning_system._calculate_strategy_similarity(strategy1, strategy2)
        similarity_13 = learning_system._calculate_strategy_similarity(strategy1, strategy3)
        
        assert similarity_12 > similarity_13
        assert 0 <= similarity_12 <= 1
        assert 0 <= similarity_13 <= 1
    
    @pytest.mark.asyncio
    async def test_strategy_lifecycle_management(self, learning_system):
        """測試策略生命週期管理"""
        # 創建一個過期的策略
        old_strategy = CandidateStrategy(
            id="old_001",
            name="過期策略",
            conditions={"cpu_usage": {"operator": ">", "value": 80}},
            actions=[{"type": "scale_up"}],
            confidence_score=0.5,
            source="llm_generated"
        )
        old_strategy.created_at = datetime.now() - timedelta(days=60)  # 60天前創建
        old_strategy.last_used = datetime.now() - timedelta(days=30)  # 30天未使用
        
        learning_system.candidate_strategies["old_001"] = old_strategy
        
        # 執行清理
        cleaned_count = await learning_system.cleanup_obsolete_strategies()
        
        assert cleaned_count > 0
        assert "old_001" not in learning_system.candidate_strategies

