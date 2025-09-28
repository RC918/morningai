"""
混合模型部署策略 - 本地+雲端模型管理
版本: 1.0
日期: 2025-09-12
作者: Manus AI

這個模塊實現了混合模型部署策略，
支持本地模型和雲端模型的智能路由和管理。
"""

import asyncio
import json
import logging
import time
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import requests
import docker
import boto3
from pathlib import Path

# 配置日誌
logger = logging.getLogger(__name__)

class ModelType(Enum):
    EMBEDDING = "embedding"
    CHAT = "chat"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    CODE_GENERATION = "code_generation"

class DeploymentStatus(Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class LocalModelConfig:
    """本地模型配置"""
    model_id: str
    model_name: str
    model_type: ModelType
    model_path: str
    container_image: str
    port: int
    gpu_required: bool = False
    memory_limit: str = "4g"
    cpu_limit: str = "2"
    environment_vars: Dict[str, str] = None
    health_check_endpoint: str = "/health"

@dataclass
class ModelDeployment:
    """模型部署信息"""
    model_id: str
    deployment_id: str
    status: DeploymentStatus
    endpoint_url: str
    container_id: Optional[str] = None
    sagemaker_endpoint: Optional[str] = None
    created_at: datetime = None
    last_health_check: datetime = None
    error_message: Optional[str] = None

class LocalModelManager:
    """本地模型管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.docker_client = docker.from_env()
        self.deployments: Dict[str, ModelDeployment] = {}
        self.model_configs: Dict[str, LocalModelConfig] = {}
        
        # 預定義的本地模型配置
        self._initialize_model_configs()
    
    def _initialize_model_configs(self):
        """初始化預定義的模型配置"""
        self.model_configs = {
            "llama-3-8b": LocalModelConfig(
                model_id="llama-3-8b",
                model_name="Meta Llama 3 8B",
                model_type=ModelType.CHAT,
                model_path="/models/llama-3-8b",
                container_image="ollama/ollama:latest",
                port=11434,
                gpu_required=True,
                memory_limit="8g",
                cpu_limit="4",
                environment_vars={"OLLAMA_MODEL": "llama3:8b"}
            ),
            "mistral-7b": LocalModelConfig(
                model_id="mistral-7b",
                model_name="Mistral 7B",
                model_type=ModelType.CHAT,
                model_path="/models/mistral-7b",
                container_image="ollama/ollama:latest",
                port=11435,
                gpu_required=True,
                memory_limit="6g",
                cpu_limit="4",
                environment_vars={"OLLAMA_MODEL": "mistral:7b"}
            ),
            "bge-large": LocalModelConfig(
                model_id="bge-large",
                model_name="BGE Large Embedding",
                model_type=ModelType.EMBEDDING,
                model_path="/models/bge-large",
                container_image="sentence-transformers/all-MiniLM-L6-v2:latest",
                port=8080,
                gpu_required=False,
                memory_limit="2g",
                cpu_limit="2"
            ),
            "phi-3-mini": LocalModelConfig(
                model_id="phi-3-mini",
                model_name="Microsoft Phi-3 Mini",
                model_type=ModelType.CHAT,
                model_path="/models/phi-3-mini",
                container_image="ollama/ollama:latest",
                port=11436,
                gpu_required=False,
                memory_limit="4g",
                cpu_limit="2",
                environment_vars={"OLLAMA_MODEL": "phi3:mini"}
            )
        }
    
    async def deploy_model(self, model_id: str) -> ModelDeployment:
        """部署本地模型"""
        if model_id not in self.model_configs:
            raise ValueError(f"Unknown model: {model_id}")
        
        config = self.model_configs[model_id]
        deployment_id = f"{model_id}_{int(time.time())}"
        
        try:
            logger.info(f"Deploying local model: {model_id}")
            
            # 檢查是否已經部署
            if model_id in self.deployments and self.deployments[model_id].status == DeploymentStatus.RUNNING:
                logger.info(f"Model {model_id} is already running")
                return self.deployments[model_id]
            
            # 創建部署記錄
            deployment = ModelDeployment(
                model_id=model_id,
                deployment_id=deployment_id,
                status=DeploymentStatus.DEPLOYING,
                endpoint_url=f"http://localhost:{config.port}",
                created_at=datetime.utcnow()
            )
            self.deployments[model_id] = deployment
            
            # 檢查 GPU 可用性
            if config.gpu_required and not self._check_gpu_available():
                logger.warning(f"GPU required for {model_id} but not available, deploying on CPU")
            
            # 啟動 Docker 容器
            container = await self._start_container(config, deployment_id)
            deployment.container_id = container.id
            
            # 等待模型啟動
            await self._wait_for_model_ready(deployment, config)
            
            deployment.status = DeploymentStatus.RUNNING
            logger.info(f"Model {model_id} deployed successfully")
            
            return deployment
            
        except Exception as e:
            logger.error(f"Failed to deploy model {model_id}: {e}")
            deployment.status = DeploymentStatus.ERROR
            deployment.error_message = str(e)
            return deployment
    
    def _check_gpu_available(self) -> bool:
        """檢查 GPU 是否可用"""
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    async def _start_container(self, config: LocalModelConfig, deployment_id: str) -> Any:
        """啟動 Docker 容器"""
        try:
            # 準備容器配置
            container_config = {
                "image": config.container_image,
                "name": f"morningai_{config.model_id}_{deployment_id}",
                "ports": {f"{config.port}/tcp": config.port},
                "environment": config.environment_vars or {},
                "mem_limit": config.memory_limit,
                "cpu_count": int(config.cpu_limit),
                "detach": True,
                "remove": True  # 容器停止時自動刪除
            }
            
            # 如果需要 GPU 且可用，添加 GPU 支持
            if config.gpu_required and self._check_gpu_available():
                container_config["device_requests"] = [
                    docker.types.DeviceRequest(count=-1, capabilities=[["gpu"]])
                ]
            
            # 掛載模型文件（如果存在）
            if os.path.exists(config.model_path):
                container_config["volumes"] = {
                    config.model_path: {"bind": "/app/models", "mode": "ro"}
                }
            
            # 啟動容器
            container = self.docker_client.containers.run(**container_config)
            logger.info(f"Container started: {container.id}")
            
            return container
            
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            raise
    
    async def _wait_for_model_ready(self, deployment: ModelDeployment, config: LocalModelConfig, timeout: int = 300):
        """等待模型準備就緒"""
        start_time = time.time()
        health_url = f"{deployment.endpoint_url}{config.health_check_endpoint}"
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    deployment.last_health_check = datetime.utcnow()
                    logger.info(f"Model {config.model_id} is ready")
                    return
            except requests.RequestException:
                pass
            
            await asyncio.sleep(5)
        
        raise TimeoutError(f"Model {config.model_id} failed to become ready within {timeout} seconds")
    
    async def stop_model(self, model_id: str) -> bool:
        """停止本地模型"""
        if model_id not in self.deployments:
            logger.warning(f"Model {model_id} is not deployed")
            return False
        
        deployment = self.deployments[model_id]
        
        try:
            if deployment.container_id:
                container = self.docker_client.containers.get(deployment.container_id)
                container.stop()
                logger.info(f"Container {deployment.container_id} stopped")
            
            deployment.status = DeploymentStatus.STOPPED
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop model {model_id}: {e}")
            return False
    
    async def health_check(self, model_id: str) -> bool:
        """檢查模型健康狀態"""
        if model_id not in self.deployments:
            return False
        
        deployment = self.deployments[model_id]
        config = self.model_configs[model_id]
        
        try:
            health_url = f"{deployment.endpoint_url}{config.health_check_endpoint}"
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                deployment.last_health_check = datetime.utcnow()
                return True
            else:
                return False
                
        except requests.RequestException:
            return False
    
    def get_deployment_status(self, model_id: str) -> Optional[ModelDeployment]:
        """獲取模型部署狀態"""
        return self.deployments.get(model_id)
    
    def list_available_models(self) -> List[LocalModelConfig]:
        """列出可用的本地模型"""
        return list(self.model_configs.values())
    
    def list_running_models(self) -> List[ModelDeployment]:
        """列出正在運行的模型"""
        return [d for d in self.deployments.values() if d.status == DeploymentStatus.RUNNING]

class SageMakerModelManager:
    """AWS SageMaker 模型管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sagemaker_client = boto3.client(
            'sagemaker',
            region_name=config.get('aws_region', 'us-east-1'),
            aws_access_key_id=config.get('aws_access_key_id'),
            aws_secret_access_key=config.get('aws_secret_access_key')
        )
        self.sagemaker_runtime = boto3.client(
            'sagemaker-runtime',
            region_name=config.get('aws_region', 'us-east-1'),
            aws_access_key_id=config.get('aws_access_key_id'),
            aws_secret_access_key=config.get('aws_secret_access_key')
        )
        self.deployments: Dict[str, ModelDeployment] = {}
    
    async def deploy_model(self, model_name: str, model_data_url: str, instance_type: str = "ml.m5.large") -> ModelDeployment:
        """部署模型到 SageMaker"""
        deployment_id = f"morningai-{model_name}-{int(time.time())}"
        endpoint_name = f"morningai-{model_name}-endpoint"
        
        try:
            logger.info(f"Deploying model to SageMaker: {model_name}")
            
            # 創建模型
            model_response = self.sagemaker_client.create_model(
                ModelName=deployment_id,
                PrimaryContainer={
                    'Image': self._get_inference_image(instance_type),
                    'ModelDataUrl': model_data_url,
                    'Environment': {
                        'SAGEMAKER_PROGRAM': 'inference.py',
                        'SAGEMAKER_SUBMIT_DIRECTORY': '/opt/ml/code'
                    }
                },
                ExecutionRoleArn=self.config['sagemaker_execution_role']
            )
            
            # 創建端點配置
            endpoint_config_response = self.sagemaker_client.create_endpoint_config(
                EndpointConfigName=f"{deployment_id}-config",
                ProductionVariants=[
                    {
                        'VariantName': 'primary',
                        'ModelName': deployment_id,
                        'InitialInstanceCount': 1,
                        'InstanceType': instance_type,
                        'InitialVariantWeight': 1
                    }
                ]
            )
            
            # 創建端點
            endpoint_response = self.sagemaker_client.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=f"{deployment_id}-config"
            )
            
            # 創建部署記錄
            deployment = ModelDeployment(
                model_id=model_name,
                deployment_id=deployment_id,
                status=DeploymentStatus.DEPLOYING,
                endpoint_url=f"https://runtime.sagemaker.{self.config.get('aws_region', 'us-east-1')}.amazonaws.com/endpoints/{endpoint_name}/invocations",
                sagemaker_endpoint=endpoint_name,
                created_at=datetime.utcnow()
            )
            self.deployments[model_name] = deployment
            
            # 等待端點就緒
            await self._wait_for_endpoint_ready(endpoint_name)
            deployment.status = DeploymentStatus.RUNNING
            
            logger.info(f"Model {model_name} deployed to SageMaker successfully")
            return deployment
            
        except Exception as e:
            logger.error(f"Failed to deploy model to SageMaker: {e}")
            deployment.status = DeploymentStatus.ERROR
            deployment.error_message = str(e)
            return deployment
    
    def _get_inference_image(self, instance_type: str) -> str:
        """獲取推理容器鏡像"""
        # 這裡應該根據模型類型和實例類型選擇合適的容器鏡像
        # 簡化示例，實際應用中需要更複雜的邏輯
        region = self.config.get('aws_region', 'us-east-1')
        account_id = "763104351884"  # AWS Deep Learning Containers account
        return f"{account_id}.dkr.ecr.{region}.amazonaws.com/pytorch-inference:1.12.0-gpu-py38-cu113-ubuntu20.04-sagemaker"
    
    async def _wait_for_endpoint_ready(self, endpoint_name: str, timeout: int = 600):
        """等待 SageMaker 端點就緒"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
                status = response['EndpointStatus']
                
                if status == 'InService':
                    logger.info(f"SageMaker endpoint {endpoint_name} is ready")
                    return
                elif status == 'Failed':
                    raise Exception(f"SageMaker endpoint {endpoint_name} failed to deploy")
                
            except Exception as e:
                logger.error(f"Error checking endpoint status: {e}")
            
            await asyncio.sleep(30)
        
        raise TimeoutError(f"SageMaker endpoint {endpoint_name} failed to become ready within {timeout} seconds")

class HybridModelRouter:
    """混合模型路由器"""
    
    def __init__(self, local_manager: LocalModelManager, sagemaker_manager: SageMakerModelManager):
        self.local_manager = local_manager
        self.sagemaker_manager = sagemaker_manager
        
        # 路由策略配置
        self.routing_rules = {
            "privacy_sensitive": "local",      # 隱私敏感任務優先本地
            "low_latency": "local",           # 低延遲需求優先本地
            "high_complexity": "cloud",       # 高複雜度任務優先雲端
            "cost_sensitive": "local",        # 成本敏感優先本地
            "high_availability": "cloud"      # 高可用性需求優先雲端
        }
    
    async def route_request(self, task_type: str, requirements: Dict[str, Any]) -> str:
        """根據任務類型和需求路由請求"""
        
        # 檢查隱私要求
        if requirements.get("privacy_level", 1) >= 3:
            return await self._route_to_local(task_type, requirements)
        
        # 檢查延遲要求
        if requirements.get("max_latency_ms", 10000) < 1000:
            return await self._route_to_local(task_type, requirements)
        
        # 檢查複雜度
        if requirements.get("complexity_score", 1) > 8:
            return await self._route_to_cloud(task_type, requirements)
        
        # 檢查成本敏感度
        if requirements.get("cost_priority", "balanced") == "lowest":
            return await self._route_to_local(task_type, requirements)
        
        # 默認策略：平衡路由
        return await self._balanced_routing(task_type, requirements)
    
    async def _route_to_local(self, task_type: str, requirements: Dict[str, Any]) -> str:
        """路由到本地模型"""
        # 選擇最適合的本地模型
        suitable_models = self._find_suitable_local_models(task_type, requirements)
        
        if not suitable_models:
            logger.warning(f"No suitable local models for task {task_type}, falling back to cloud")
            return await self._route_to_cloud(task_type, requirements)
        
        # 選擇最佳模型
        best_model = suitable_models[0]
        
        # 確保模型已部署
        deployment = await self.local_manager.deploy_model(best_model)
        if deployment.status == DeploymentStatus.RUNNING:
            return deployment.endpoint_url
        else:
            logger.error(f"Failed to deploy local model {best_model}")
            return await self._route_to_cloud(task_type, requirements)
    
    async def _route_to_cloud(self, task_type: str, requirements: Dict[str, Any]) -> str:
        """路由到雲端模型"""
        # 這裡可以實現更複雜的雲端模型選擇邏輯
        # 簡化示例：返回 OpenAI API
        return "openai"
    
    async def _balanced_routing(self, task_type: str, requirements: Dict[str, Any]) -> str:
        """平衡路由策略"""
        # 檢查本地模型可用性
        local_models = self._find_suitable_local_models(task_type, requirements)
        
        if local_models:
            # 檢查本地模型負載
            local_load = await self._check_local_load()
            if local_load < 0.8:  # 負載低於80%時使用本地模型
                return await self._route_to_local(task_type, requirements)
        
        # 否則使用雲端模型
        return await self._route_to_cloud(task_type, requirements)
    
    def _find_suitable_local_models(self, task_type: str, requirements: Dict[str, Any]) -> List[str]:
        """查找適合的本地模型"""
        suitable_models = []
        
        for model_id, config in self.local_manager.model_configs.items():
            # 根據任務類型匹配模型
            if self._is_model_suitable(config, task_type, requirements):
                suitable_models.append(model_id)
        
        # 按優先級排序（這裡簡化為按模型名稱排序）
        return sorted(suitable_models)
    
    def _is_model_suitable(self, config: LocalModelConfig, task_type: str, requirements: Dict[str, Any]) -> bool:
        """檢查模型是否適合任務"""
        # 簡化的匹配邏輯
        if task_type == "chat" and config.model_type == ModelType.CHAT:
            return True
        elif task_type == "embedding" and config.model_type == ModelType.EMBEDDING:
            return True
        elif task_type == "classification" and config.model_type == ModelType.CLASSIFICATION:
            return True
        
        return False
    
    async def _check_local_load(self) -> float:
        """檢查本地模型負載"""
        # 簡化的負載檢查，實際應用中需要更複雜的監控
        running_models = self.local_manager.list_running_models()
        max_models = 3  # 假設最多同時運行3個模型
        return len(running_models) / max_models

# 全局實例
_hybrid_deployment_instance = None

def get_hybrid_deployment_manager(config: Optional[Dict[str, Any]] = None) -> HybridModelRouter:
    """獲取混合部署管理器實例（單例）"""
    global _hybrid_deployment_instance
    
    if _hybrid_deployment_instance is None:
        if config is None:
            config = {
                "aws_region": "us-east-1",
                "aws_access_key_id": "your-access-key",
                "aws_secret_access_key": "your-secret-key",
                "sagemaker_execution_role": "arn:aws:iam::account:role/SageMakerExecutionRole"
            }
        
        local_manager = LocalModelManager(config)
        sagemaker_manager = SageMakerModelManager(config)
        _hybrid_deployment_instance = HybridModelRouter(local_manager, sagemaker_manager)
    
    return _hybrid_deployment_instance

