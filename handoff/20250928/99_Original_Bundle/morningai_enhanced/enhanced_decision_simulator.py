"""
增強版決策模擬器 - 基於歷史數據和機器學習的數字孿生
版本: 1.0
日期: 2025-09-12
作者: Manus AI

這個模塊實現了增強版的決策模擬器，
使用歷史數據、時序預測和機器學習來提高決策準確性。
"""

import asyncio
import json
import logging
import time
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from prophet import Prophet
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import warnings
warnings.filterwarnings('ignore')

# 配置日誌
logger = logging.getLogger(__name__)

Base = declarative_base()

class HistoricalMetric(Base):
    """歷史指標數據表"""
    __tablename__ = 'historical_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_category = Column(String(50), nullable=False)  # system, business, user
    timestamp = Column(DateTime, nullable=False)
    context_data = Column(Text, nullable=True)  # JSON 格式的上下文信息

class StrategyImpact(Base):
    """策略影響記錄表"""
    __tablename__ = 'strategy_impacts'
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(String(50), nullable=False)
    strategy_type = Column(String(50), nullable=False)
    execution_timestamp = Column(DateTime, nullable=False)
    
    # 執行前後的指標
    before_metrics = Column(Text, nullable=False)  # JSON
    after_metrics = Column(Text, nullable=False)   # JSON
    
    # 影響分析
    impact_duration_hours = Column(Float, nullable=False)
    primary_impact_metric = Column(String(100), nullable=False)
    impact_magnitude = Column(Float, nullable=False)  # 正負值表示改善/惡化
    confidence_score = Column(Float, nullable=False)  # 0-1

@dataclass
class PredictionResult:
    """預測結果"""
    metric_name: str
    predicted_value: float
    confidence_interval: Tuple[float, float]
    prediction_horizon_hours: int
    model_confidence: float
    contributing_factors: Dict[str, float]

@dataclass
class SimulationResult:
    """模擬結果"""
    strategy_id: str
    predicted_impacts: Dict[str, PredictionResult]
    overall_score: float
    risk_assessment: Dict[str, float]
    execution_recommendation: str
    simulation_confidence: float

class TimeSeriesPredictor:
    """時序預測器"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.is_trained = False
    
    def train(self, historical_data: pd.DataFrame):
        """訓練時序預測模型"""
        try:
            logger.info("Training time series prediction models...")
            
            # 為每個指標訓練 Prophet 模型
            metrics = historical_data['metric_name'].unique()
            
            for metric in metrics:
                metric_data = historical_data[historical_data['metric_name'] == metric].copy()
                
                if len(metric_data) < 10:  # 數據不足，跳過
                    continue
                
                # 準備 Prophet 數據格式
                prophet_data = pd.DataFrame({
                    'ds': metric_data['timestamp'],
                    'y': metric_data['metric_value']
                })
                
                # 創建和訓練 Prophet 模型
                model = Prophet(
                    daily_seasonality=True,
                    weekly_seasonality=True,
                    yearly_seasonality=False,
                    changepoint_prior_scale=0.05
                )
                
                model.fit(prophet_data)
                self.models[metric] = model
                
                logger.info(f"Trained Prophet model for metric: {metric}")
            
            self.is_trained = True
            logger.info(f"Time series training completed for {len(self.models)} metrics")
            
        except Exception as e:
            logger.error(f"Failed to train time series models: {e}")
    
    def predict(self, metric_name: str, hours_ahead: int = 24) -> Optional[PredictionResult]:
        """預測指標未來值"""
        if not self.is_trained or metric_name not in self.models:
            return None
        
        try:
            model = self.models[metric_name]
            
            # 創建未來時間點
            future = model.make_future_dataframe(periods=hours_ahead, freq='H')
            
            # 進行預測
            forecast = model.predict(future)
            
            # 獲取最後一個預測點
            last_prediction = forecast.iloc[-1]
            
            return PredictionResult(
                metric_name=metric_name,
                predicted_value=last_prediction['yhat'],
                confidence_interval=(last_prediction['yhat_lower'], last_prediction['yhat_upper']),
                prediction_horizon_hours=hours_ahead,
                model_confidence=0.8,  # 簡化的信心分數
                contributing_factors={}  # Prophet 不直接提供特徵重要性
            )
            
        except Exception as e:
            logger.error(f"Failed to predict {metric_name}: {e}")
            return None

class ImpactLearner:
    """影響學習器 - 學習策略對指標的影響"""
    
    def __init__(self):
        self.impact_models: Dict[str, Any] = {}
        self.feature_scalers: Dict[str, StandardScaler] = {}
        self.is_trained = False
    
    def train(self, impact_data: pd.DataFrame):
        """訓練影響預測模型"""
        try:
            logger.info("Training impact prediction models...")
            
            if len(impact_data) < 20:
                logger.warning("Insufficient impact data for training")
                return
            
            # 準備特徵和目標變量
            features = self._extract_features(impact_data)
            
            # 為每個主要影響指標訓練模型
            impact_metrics = impact_data['primary_impact_metric'].unique()
            
            for metric in impact_metrics:
                metric_data = impact_data[impact_data['primary_impact_metric'] == metric]
                
                if len(metric_data) < 10:
                    continue
                
                # 準備訓練數據
                X = features.loc[metric_data.index]
                y = metric_data['impact_magnitude']
                
                # 標準化特徵
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                # 訓練隨機森林模型
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                model.fit(X_scaled, y)
                
                # 保存模型和標準化器
                self.impact_models[metric] = model
                self.feature_scalers[metric] = scaler
                
                # 評估模型
                y_pred = model.predict(X_scaled)
                r2 = r2_score(y, y_pred)
                logger.info(f"Trained impact model for {metric}, R² score: {r2:.3f}")
            
            self.is_trained = True
            logger.info(f"Impact learning completed for {len(self.impact_models)} metrics")
            
        except Exception as e:
            logger.error(f"Failed to train impact models: {e}")
    
    def _extract_features(self, impact_data: pd.DataFrame) -> pd.DataFrame:
        """從影響數據中提取特徵"""
        features = []
        
        for _, row in impact_data.iterrows():
            try:
                before_metrics = json.loads(row['before_metrics'])
                strategy_type = row['strategy_type']
                
                # 基本特徵
                feature_dict = {
                    'hour_of_day': row['execution_timestamp'].hour,
                    'day_of_week': row['execution_timestamp'].weekday(),
                    'impact_duration': row['impact_duration_hours']
                }
                
                # 策略類型特徵（one-hot encoding）
                strategy_types = ['scale_up', 'optimize', 'rollback', 'cache', 'other']
                for st in strategy_types:
                    feature_dict[f'strategy_{st}'] = 1 if st in strategy_type.lower() else 0
                
                # 執行前指標特徵
                for metric_name, value in before_metrics.items():
                    if isinstance(value, (int, float)):
                        feature_dict[f'before_{metric_name}'] = value
                
                features.append(feature_dict)
                
            except Exception as e:
                logger.warning(f"Failed to extract features from row: {e}")
                continue
        
        return pd.DataFrame(features).fillna(0)
    
    def predict_impact(self, strategy_type: str, current_metrics: Dict[str, float], 
                      execution_context: Dict[str, Any]) -> Dict[str, PredictionResult]:
        """預測策略影響"""
        if not self.is_trained:
            return {}
        
        predictions = {}
        
        try:
            # 構建特徵向量
            feature_dict = {
                'hour_of_day': datetime.now().hour,
                'day_of_week': datetime.now().weekday(),
                'impact_duration': execution_context.get('expected_duration', 1.0)
            }
            
            # 策略類型特徵
            strategy_types = ['scale_up', 'optimize', 'rollback', 'cache', 'other']
            for st in strategy_types:
                feature_dict[f'strategy_{st}'] = 1 if st in strategy_type.lower() else 0
            
            # 當前指標特徵
            for metric_name, value in current_metrics.items():
                feature_dict[f'before_{metric_name}'] = value
            
            # 為每個訓練過的指標進行預測
            for metric, model in self.impact_models.items():
                try:
                    # 準備特徵向量
                    feature_df = pd.DataFrame([feature_dict])
                    
                    # 確保所有必要的特徵都存在
                    scaler = self.feature_scalers[metric]
                    expected_features = scaler.feature_names_in_ if hasattr(scaler, 'feature_names_in_') else range(scaler.n_features_in_)
                    
                    # 填充缺失特徵
                    for feature in expected_features:
                        if feature not in feature_df.columns:
                            feature_df[feature] = 0
                    
                    # 選擇和排序特徵
                    feature_df = feature_df[expected_features]
                    
                    # 標準化和預測
                    X_scaled = scaler.transform(feature_df)
                    predicted_impact = model.predict(X_scaled)[0]
                    
                    # 計算信心區間（基於模型的預測方差）
                    if hasattr(model, 'predict'):
                        # 對於隨機森林，使用樹的預測方差
                        tree_predictions = np.array([tree.predict(X_scaled)[0] for tree in model.estimators_])
                        std = np.std(tree_predictions)
                        confidence_interval = (predicted_impact - 1.96 * std, predicted_impact + 1.96 * std)
                    else:
                        confidence_interval = (predicted_impact * 0.8, predicted_impact * 1.2)
                    
                    # 計算特徵重要性
                    feature_importance = dict(zip(expected_features, model.feature_importances_))
                    
                    predictions[metric] = PredictionResult(
                        metric_name=metric,
                        predicted_value=predicted_impact,
                        confidence_interval=confidence_interval,
                        prediction_horizon_hours=execution_context.get('expected_duration', 1),
                        model_confidence=0.8,  # 簡化的信心分數
                        contributing_factors=feature_importance
                    )
                    
                except Exception as e:
                    logger.warning(f"Failed to predict impact for {metric}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to predict strategy impact: {e}")
        
        return predictions

class EnhancedDecisionSimulator:
    """增強版決策模擬器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # 預測組件
        self.time_series_predictor = TimeSeriesPredictor()
        self.impact_learner = ImpactLearner()
        
        # 模型狀態
        self.last_training_time = None
        self.training_interval_hours = 24  # 每24小時重新訓練
        
        # 初始化時嘗試加載已訓練的模型
        self._load_models()
    
    async def initialize(self):
        """初始化模擬器"""
        await self._train_models()
    
    async def _train_models(self):
        """訓練預測模型"""
        try:
            logger.info("Training enhanced decision simulator models...")
            
            # 加載歷史數據
            historical_data = self._load_historical_data()
            impact_data = self._load_impact_data()
            
            # 訓練時序預測模型
            if len(historical_data) > 0:
                self.time_series_predictor.train(historical_data)
            
            # 訓練影響學習模型
            if len(impact_data) > 0:
                self.impact_learner.train(impact_data)
            
            self.last_training_time = datetime.utcnow()
            
            # 保存模型
            self._save_models()
            
            logger.info("Enhanced decision simulator training completed")
            
        except Exception as e:
            logger.error(f"Failed to train enhanced decision simulator: {e}")
    
    def _load_historical_data(self) -> pd.DataFrame:
        """加載歷史指標數據"""
        try:
            query = """
            SELECT metric_name, metric_value, metric_category, timestamp, context_data
            FROM historical_metrics
            WHERE timestamp >= %s
            ORDER BY timestamp
            """
            
            # 加載最近30天的數據
            start_date = datetime.utcnow() - timedelta(days=30)
            
            return pd.read_sql(query, self.engine, params=[start_date])
            
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
            return pd.DataFrame()
    
    def _load_impact_data(self) -> pd.DataFrame:
        """加載策略影響數據"""
        try:
            query = """
            SELECT strategy_id, strategy_type, execution_timestamp, before_metrics,
                   after_metrics, impact_duration_hours, primary_impact_metric,
                   impact_magnitude, confidence_score
            FROM strategy_impacts
            WHERE execution_timestamp >= %s
            ORDER BY execution_timestamp
            """
            
            # 加載最近60天的數據
            start_date = datetime.utcnow() - timedelta(days=60)
            
            return pd.read_sql(query, self.engine, params=[start_date])
            
        except Exception as e:
            logger.error(f"Failed to load impact data: {e}")
            return pd.DataFrame()
    
    def _save_models(self):
        """保存訓練好的模型"""
        try:
            model_dir = "/tmp/morningai_models"
            os.makedirs(model_dir, exist_ok=True)
            
            # 保存時序預測模型
            with open(f"{model_dir}/time_series_models.pkl", "wb") as f:
                pickle.dump(self.time_series_predictor.models, f)
            
            # 保存影響學習模型
            with open(f"{model_dir}/impact_models.pkl", "wb") as f:
                pickle.dump(self.impact_learner.impact_models, f)
            
            with open(f"{model_dir}/feature_scalers.pkl", "wb") as f:
                pickle.dump(self.impact_learner.feature_scalers, f)
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def _load_models(self):
        """加載已訓練的模型"""
        try:
            model_dir = "/tmp/morningai_models"
            
            # 加載時序預測模型
            ts_model_path = f"{model_dir}/time_series_models.pkl"
            if os.path.exists(ts_model_path):
                with open(ts_model_path, "rb") as f:
                    self.time_series_predictor.models = pickle.load(f)
                    self.time_series_predictor.is_trained = True
            
            # 加載影響學習模型
            impact_model_path = f"{model_dir}/impact_models.pkl"
            scaler_path = f"{model_dir}/feature_scalers.pkl"
            
            if os.path.exists(impact_model_path) and os.path.exists(scaler_path):
                with open(impact_model_path, "rb") as f:
                    self.impact_learner.impact_models = pickle.load(f)
                
                with open(scaler_path, "rb") as f:
                    self.impact_learner.feature_scalers = pickle.load(f)
                
                self.impact_learner.is_trained = True
            
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load existing models: {e}")
    
    async def simulate_strategy(self, strategy: Any, current_state: Dict[str, Any]) -> SimulationResult:
        """模擬策略執行結果"""
        try:
            # 檢查是否需要重新訓練模型
            if (self.last_training_time is None or 
                datetime.utcnow() - self.last_training_time > timedelta(hours=self.training_interval_hours)):
                await self._train_models()
            
            # 提取當前指標
            current_metrics = self._extract_current_metrics(current_state)
            
            # 預測策略影響
            impact_predictions = self.impact_learner.predict_impact(
                strategy_type=strategy.name,
                current_metrics=current_metrics,
                execution_context={
                    'expected_duration': 2.0,  # 假設2小時影響期
                    'strategy_complexity': len(strategy.tasks)
                }
            )
            
            # 預測基線趨勢（無策略執行的情況）
            baseline_predictions = {}
            for metric_name in current_metrics.keys():
                baseline_pred = self.time_series_predictor.predict(metric_name, hours_ahead=24)
                if baseline_pred:
                    baseline_predictions[metric_name] = baseline_pred
            
            # 計算綜合影響
            combined_predictions = self._combine_predictions(impact_predictions, baseline_predictions)
            
            # 風險評估
            risk_assessment = self._assess_risks(strategy, combined_predictions, current_metrics)
            
            # 計算整體分數
            overall_score = self._calculate_overall_score(combined_predictions, risk_assessment)
            
            # 生成執行建議
            recommendation = self._generate_recommendation(overall_score, risk_assessment, strategy)
            
            # 計算模擬信心度
            simulation_confidence = self._calculate_simulation_confidence(
                impact_predictions, baseline_predictions, len(current_metrics)
            )
            
            return SimulationResult(
                strategy_id=strategy.id,
                predicted_impacts=combined_predictions,
                overall_score=overall_score,
                risk_assessment=risk_assessment,
                execution_recommendation=recommendation,
                simulation_confidence=simulation_confidence
            )
            
        except Exception as e:
            logger.error(f"Failed to simulate strategy {strategy.id}: {e}")
            
            # 返回默認結果
            return SimulationResult(
                strategy_id=strategy.id,
                predicted_impacts={},
                overall_score=50.0,  # 中性分數
                risk_assessment={"unknown_risk": 0.5},
                execution_recommendation="Insufficient data for accurate simulation",
                simulation_confidence=0.1
            )
    
    def _extract_current_metrics(self, current_state: Dict[str, Any]) -> Dict[str, float]:
        """從當前狀態提取指標"""
        metrics = {}
        
        # 從系統指標中提取
        system_metrics = current_state.get("system_metrics", [])
        for metric in system_metrics:
            if isinstance(metric, dict) and "name" in metric and "value" in metric:
                metrics[metric["name"]] = float(metric["value"])
        
        # 從業務指標中提取
        business_metrics = current_state.get("business_metrics", [])
        for metric in business_metrics:
            if isinstance(metric, dict) and "name" in metric and "value" in metric:
                metrics[metric["name"]] = float(metric["value"])
        
        return metrics
    
    def _combine_predictions(self, impact_predictions: Dict[str, PredictionResult], 
                           baseline_predictions: Dict[str, PredictionResult]) -> Dict[str, PredictionResult]:
        """結合影響預測和基線預測"""
        combined = {}
        
        # 對於有影響預測的指標，結合基線趨勢
        for metric_name, impact_pred in impact_predictions.items():
            baseline_pred = baseline_predictions.get(metric_name)
            
            if baseline_pred:
                # 將影響疊加到基線預測上
                combined_value = baseline_pred.predicted_value + impact_pred.predicted_value
                
                # 結合信心區間
                lower_bound = (baseline_pred.confidence_interval[0] + 
                              impact_pred.confidence_interval[0])
                upper_bound = (baseline_pred.confidence_interval[1] + 
                              impact_pred.confidence_interval[1])
                
                combined[metric_name] = PredictionResult(
                    metric_name=metric_name,
                    predicted_value=combined_value,
                    confidence_interval=(lower_bound, upper_bound),
                    prediction_horizon_hours=24,
                    model_confidence=min(baseline_pred.model_confidence, impact_pred.model_confidence),
                    contributing_factors=impact_pred.contributing_factors
                )
            else:
                combined[metric_name] = impact_pred
        
        # 添加只有基線預測的指標
        for metric_name, baseline_pred in baseline_predictions.items():
            if metric_name not in combined:
                combined[metric_name] = baseline_pred
        
        return combined
    
    def _assess_risks(self, strategy: Any, predictions: Dict[str, PredictionResult], 
                     current_metrics: Dict[str, float]) -> Dict[str, float]:
        """評估策略風險"""
        risks = {}
        
        # 性能風險
        performance_metrics = ["api_request_duration_p95", "cpu_usage_percent", "memory_usage_percent"]
        performance_risk = 0.0
        
        for metric in performance_metrics:
            if metric in predictions:
                pred = predictions[metric]
                current_value = current_metrics.get(metric, 0)
                
                # 如果預測值顯著惡化，增加風險
                if pred.predicted_value > current_value * 1.2:
                    performance_risk += 0.3
        
        risks["performance_degradation"] = min(performance_risk, 1.0)
        
        # 可用性風險
        error_metrics = ["error_rate_5xx"]
        availability_risk = 0.0
        
        for metric in error_metrics:
            if metric in predictions:
                pred = predictions[metric]
                if pred.predicted_value > 5.0:  # 錯誤率超過5%
                    availability_risk += 0.5
        
        risks["availability_impact"] = min(availability_risk, 1.0)
        
        # 成本風險
        cost_risk = strategy.implementation_cost / 1000.0  # 標準化成本
        risks["cost_overrun"] = min(cost_risk, 1.0)
        
        # 不確定性風險
        uncertainty_risk = 0.0
        for pred in predictions.values():
            interval_width = pred.confidence_interval[1] - pred.confidence_interval[0]
            relative_uncertainty = interval_width / max(abs(pred.predicted_value), 1.0)
            uncertainty_risk += relative_uncertainty
        
        if predictions:
            uncertainty_risk /= len(predictions)
        
        risks["prediction_uncertainty"] = min(uncertainty_risk, 1.0)
        
        return risks
    
    def _calculate_overall_score(self, predictions: Dict[str, PredictionResult], 
                               risks: Dict[str, float]) -> float:
        """計算整體分數"""
        # 基礎分數
        base_score = 50.0
        
        # 根據預測的改善程度調整分數
        improvement_score = 0.0
        for pred in predictions.values():
            if pred.predicted_value > 0:  # 假設正值表示改善
                improvement_score += pred.predicted_value * pred.model_confidence
        
        # 根據風險調整分數
        risk_penalty = sum(risks.values()) * 10  # 風險懲罰
        
        final_score = base_score + improvement_score - risk_penalty
        return max(0.0, min(100.0, final_score))
    
    def _generate_recommendation(self, overall_score: float, risks: Dict[str, float], 
                               strategy: Any) -> str:
        """生成執行建議"""
        if overall_score >= 80:
            return "Highly recommended - Low risk, high expected benefit"
        elif overall_score >= 60:
            return "Recommended with monitoring - Moderate benefit expected"
        elif overall_score >= 40:
            return "Proceed with caution - Mixed risk/benefit profile"
        elif overall_score >= 20:
            return "Not recommended - High risk, low expected benefit"
        else:
            return "Strongly discouraged - Very high risk"
    
    def _calculate_simulation_confidence(self, impact_predictions: Dict[str, PredictionResult],
                                       baseline_predictions: Dict[str, PredictionResult],
                                       total_metrics: int) -> float:
        """計算模擬信心度"""
        if total_metrics == 0:
            return 0.0
        
        # 基於可預測指標的比例
        predictable_ratio = len(impact_predictions) / total_metrics
        
        # 基於模型信心度
        avg_model_confidence = 0.0
        if impact_predictions:
            avg_model_confidence = np.mean([pred.model_confidence for pred in impact_predictions.values()])
        
        # 基於歷史數據量（簡化假設）
        data_confidence = 0.8 if self.impact_learner.is_trained else 0.3
        
        # 綜合信心度
        overall_confidence = (predictable_ratio * 0.4 + 
                            avg_model_confidence * 0.4 + 
                            data_confidence * 0.2)
        
        return min(1.0, overall_confidence)
    
    async def record_strategy_impact(self, strategy: Any, before_metrics: Dict[str, float],
                                   after_metrics: Dict[str, float], execution_duration_hours: float):
        """記錄策略執行的實際影響"""
        try:
            # 計算主要影響指標和影響幅度
            primary_metric, impact_magnitude = self._calculate_primary_impact(before_metrics, after_metrics)
            
            # 創建影響記錄
            impact_record = StrategyImpact(
                strategy_id=strategy.id,
                strategy_type=strategy.name,
                execution_timestamp=datetime.utcnow(),
                before_metrics=json.dumps(before_metrics, default=str),
                after_metrics=json.dumps(after_metrics, default=str),
                impact_duration_hours=execution_duration_hours,
                primary_impact_metric=primary_metric,
                impact_magnitude=impact_magnitude,
                confidence_score=0.9  # 實際數據的信心度較高
            )
            
            self.session.add(impact_record)
            self.session.commit()
            
            logger.info(f"Recorded strategy impact: {strategy.id} -> {primary_metric}: {impact_magnitude}")
            
        except Exception as e:
            logger.error(f"Failed to record strategy impact: {e}")
            self.session.rollback()
    
    def _calculate_primary_impact(self, before_metrics: Dict[str, float], 
                                after_metrics: Dict[str, float]) -> Tuple[str, float]:
        """計算主要影響指標和影響幅度"""
        max_impact = 0.0
        primary_metric = "unknown"
        
        for metric_name in before_metrics.keys():
            if metric_name in after_metrics:
                before_value = before_metrics[metric_name]
                after_value = after_metrics[metric_name]
                
                # 計算相對變化
                if before_value != 0:
                    relative_change = (after_value - before_value) / abs(before_value)
                else:
                    relative_change = after_value
                
                # 選擇變化最大的指標作為主要影響
                if abs(relative_change) > abs(max_impact):
                    max_impact = relative_change
                    primary_metric = metric_name
        
        return primary_metric, max_impact

# 全局實例
_enhanced_simulator_instance = None

def get_enhanced_decision_simulator(database_url: Optional[str] = None) -> EnhancedDecisionSimulator:
    """獲取增強版決策模擬器實例（單例）"""
    global _enhanced_simulator_instance
    
    if _enhanced_simulator_instance is None:
        if database_url is None:
            database_url = "postgresql://user:password@localhost/morningai"
        _enhanced_simulator_instance = EnhancedDecisionSimulator(database_url)
    
    return _enhanced_simulator_instance

