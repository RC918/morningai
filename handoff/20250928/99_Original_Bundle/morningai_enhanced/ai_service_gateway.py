"""
AI Service Gateway - 統一的 AI 服務抽象層
版本: 1.0
日期: 2025-09-12
作者: Manus AI

這個模塊提供了一個統一的接口來調用各種 AI 服務，
包括 OpenAI、Google、Anthropic 等，以及本地部署的模型。
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import openai
import anthropic
import google.generativeai as genai
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# 配置日誌
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    AZURE_OPENAI = "azure_openai"

class ModelPreference(Enum):
    BEST_QUALITY = "best_quality"
    LOWEST_COST = "lowest_cost"
    FASTEST = "fastest"
    BALANCED = "balanced"
    PRIVACY_FIRST = "privacy_first"

@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider
    model_name: str
    cost_per_1k_tokens: float
    max_tokens: int
    supports_streaming: bool = True
    privacy_level: int = 1  # 1=public, 2=private, 3=local_only

@dataclass
class AIRequest:
    """AI 請求結構"""
    prompt: str
    model_preference: ModelPreference = ModelPreference.BALANCED
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    context: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class AIResponse:
    """AI 回應結構"""
    content: str
    provider: ModelProvider
    model_name: str
    tokens_used: int
    cost: float
    latency_ms: int
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = None

class AIServiceGateway:
    """AI 服務網關 - 統一管理所有 AI 服務調用"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.clients = {}
        self.model_configs = self._initialize_model_configs()
        self._initialize_clients()
        
        # 統計和監控
        self.request_count = 0
        self.total_cost = 0.0
        self.error_count = 0
        
    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """初始化模型配置"""
        return {
            # OpenAI 模型
            "gpt-4": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                cost_per_1k_tokens=0.03,
                max_tokens=8192,
                privacy_level=1
            ),
            "gpt-4-turbo": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4-turbo",
                cost_per_1k_tokens=0.01,
                max_tokens=128000,
                privacy_level=1
            ),
            "gpt-3.5-turbo": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                cost_per_1k_tokens=0.001,
                max_tokens=4096,
                privacy_level=1
            ),
            
            # Anthropic 模型
            "claude-3-opus": ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-opus-20240229",
                cost_per_1k_tokens=0.015,
                max_tokens=4096,
                privacy_level=1
            ),
            "claude-3-sonnet": ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                cost_per_1k_tokens=0.003,
                max_tokens=4096,
                privacy_level=1
            ),
            
            # Google 模型
            "gemini-pro": ModelConfig(
                provider=ModelProvider.GOOGLE,
                model_name="gemini-pro",
                cost_per_1k_tokens=0.0005,
                max_tokens=2048,
                privacy_level=1
            ),
            
            # 本地模型
            "llama-3-8b": ModelConfig(
                provider=ModelProvider.LOCAL,
                model_name="llama-3-8b",
                cost_per_1k_tokens=0.0,  # 本地部署無 API 成本
                max_tokens=4096,
                privacy_level=3
            ),
            "mistral-7b": ModelConfig(
                provider=ModelProvider.LOCAL,
                model_name="mistral-7b",
                cost_per_1k_tokens=0.0,
                max_tokens=4096,
                privacy_level=3
            )
        }
    
    def _initialize_clients(self):
        """初始化各個 AI 服務客戶端"""
        try:
            # OpenAI 客戶端
            if self.config.get("openai_api_key"):
                self.clients[ModelProvider.OPENAI] = openai.AsyncOpenAI(
                    api_key=self.config["openai_api_key"]
                )
                logger.info("OpenAI client initialized")
            
            # Anthropic 客戶端
            if self.config.get("anthropic_api_key"):
                self.clients[ModelProvider.ANTHROPIC] = anthropic.AsyncAnthropic(
                    api_key=self.config["anthropic_api_key"]
                )
                logger.info("Anthropic client initialized")
            
            # Google 客戶端
            if self.config.get("google_api_key"):
                genai.configure(api_key=self.config["google_api_key"])
                self.clients[ModelProvider.GOOGLE] = genai
                logger.info("Google AI client initialized")
            
            # 本地模型客戶端
            if self.config.get("local_model_endpoint"):
                self.clients[ModelProvider.LOCAL] = {
                    "endpoint": self.config["local_model_endpoint"],
                    "headers": {"Content-Type": "application/json"}
                }
                logger.info("Local model client initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize AI clients: {e}")
    
    def _select_best_model(self, preference: ModelPreference, context_length: int = 0) -> str:
        """根據偏好選擇最佳模型"""
        available_models = [
            model_name for model_name, config in self.model_configs.items()
            if config.provider in self.clients and config.max_tokens >= context_length
        ]
        
        if not available_models:
            raise ValueError("No available models for the given requirements")
        
        if preference == ModelPreference.BEST_QUALITY:
            # 優先選擇最強大的模型
            priority = ["gpt-4", "claude-3-opus", "gpt-4-turbo", "claude-3-sonnet"]
        elif preference == ModelPreference.LOWEST_COST:
            # 優先選擇最便宜的模型
            available_models.sort(key=lambda x: self.model_configs[x].cost_per_1k_tokens)
            return available_models[0]
        elif preference == ModelPreference.FASTEST:
            # 優先選擇本地模型或輕量級模型
            priority = ["llama-3-8b", "mistral-7b", "gpt-3.5-turbo", "gemini-pro"]
        elif preference == ModelPreference.PRIVACY_FIRST:
            # 優先選擇本地模型
            priority = ["llama-3-8b", "mistral-7b"]
        else:  # BALANCED
            # 平衡性能、成本和速度
            priority = ["gpt-4-turbo", "claude-3-sonnet", "gpt-3.5-turbo", "gemini-pro"]
        
        for model in priority:
            if model in available_models:
                return model
        
        return available_models[0]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _call_openai(self, model_name: str, messages: List[Dict], **kwargs) -> AIResponse:
        """調用 OpenAI API"""
        start_time = time.time()
        
        try:
            client = self.clients[ModelProvider.OPENAI]
            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                **kwargs
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            tokens_used = response.usage.total_tokens
            cost = tokens_used * self.model_configs[model_name].cost_per_1k_tokens / 1000
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=ModelProvider.OPENAI,
                model_name=model_name,
                tokens_used=tokens_used,
                cost=cost,
                latency_ms=latency_ms,
                confidence_score=0.9  # OpenAI 通常有較高的可信度
            )
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _call_anthropic(self, model_name: str, messages: List[Dict], **kwargs) -> AIResponse:
        """調用 Anthropic API"""
        start_time = time.time()
        
        try:
            client = self.clients[ModelProvider.ANTHROPIC]
            
            # 轉換消息格式
            system_msg = None
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = await client.messages.create(
                model=model_name,
                messages=user_messages,
                system=system_msg,
                max_tokens=kwargs.get("max_tokens", 1000)
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = tokens_used * self.model_configs[model_name].cost_per_1k_tokens / 1000
            
            return AIResponse(
                content=response.content[0].text,
                provider=ModelProvider.ANTHROPIC,
                model_name=model_name,
                tokens_used=tokens_used,
                cost=cost,
                latency_ms=latency_ms,
                confidence_score=0.9
            )
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _call_local_model(self, model_name: str, messages: List[Dict], **kwargs) -> AIResponse:
        """調用本地模型"""
        start_time = time.time()
        
        try:
            client_config = self.clients[ModelProvider.LOCAL]
            
            # 構建請求
            prompt = self._format_messages_for_local(messages)
            payload = {
                "model": model_name,
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7)
            }
            
            # 發送請求到本地模型服務
            async with asyncio.timeout(30):  # 30秒超時
                response = requests.post(
                    client_config["endpoint"],
                    headers=client_config["headers"],
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
            
            latency_ms = int((time.time() - start_time) * 1000)
            content = result.get("choices", [{}])[0].get("text", "")
            tokens_used = result.get("usage", {}).get("total_tokens", len(content.split()))
            
            return AIResponse(
                content=content,
                provider=ModelProvider.LOCAL,
                model_name=model_name,
                tokens_used=tokens_used,
                cost=0.0,  # 本地模型無 API 成本
                latency_ms=latency_ms,
                confidence_score=0.8  # 本地模型可信度稍低
            )
            
        except Exception as e:
            logger.error(f"Local model call failed: {e}")
            raise
    
    def _format_messages_for_local(self, messages: List[Dict]) -> str:
        """將消息格式化為本地模型可理解的格式"""
        formatted_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                formatted_parts.append(f"System: {content}")
            elif role == "user":
                formatted_parts.append(f"Human: {content}")
            elif role == "assistant":
                formatted_parts.append(f"Assistant: {content}")
        
        formatted_parts.append("Assistant:")
        return "\n\n".join(formatted_parts)
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """統一的文本生成接口"""
        self.request_count += 1
        
        try:
            # 選擇最佳模型
            context_length = len(request.prompt) + len(request.context or "") + len(request.system_prompt or "")
            selected_model = self._select_best_model(request.model_preference, context_length)
            model_config = self.model_configs[selected_model]
            
            # 構建消息
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            user_content = request.prompt
            if request.context:
                user_content = f"Context: {request.context}\n\nQuery: {request.prompt}"
            
            messages.append({"role": "user", "content": user_content})
            
            # 準備調用參數
            call_kwargs = {
                "max_tokens": request.max_tokens or min(1000, model_config.max_tokens),
                "temperature": request.temperature
            }
            
            # 根據提供商調用相應的方法
            if model_config.provider == ModelProvider.OPENAI:
                response = await self._call_openai(selected_model, messages, **call_kwargs)
            elif model_config.provider == ModelProvider.ANTHROPIC:
                response = await self._call_anthropic(selected_model, messages, **call_kwargs)
            elif model_config.provider == ModelProvider.LOCAL:
                response = await self._call_local_model(selected_model, messages, **call_kwargs)
            else:
                raise ValueError(f"Unsupported provider: {model_config.provider}")
            
            # 更新統計
            self.total_cost += response.cost
            
            # 記錄請求日誌
            logger.info(f"AI request completed: model={selected_model}, "
                       f"tokens={response.tokens_used}, cost=${response.cost:.4f}, "
                       f"latency={response.latency_ms}ms")
            
            return response
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"AI service call failed: {e}")
            raise
    
    async def generate_text_simple(
        self, 
        prompt: str, 
        model_preference: ModelPreference = ModelPreference.BALANCED,
        **kwargs
    ) -> str:
        """簡化的文本生成接口，直接返回文本內容"""
        request = AIRequest(
            prompt=prompt,
            model_preference=model_preference,
            **kwargs
        )
        response = await self.generate_text(request)
        return response.content
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取使用統計"""
        return {
            "total_requests": self.request_count,
            "total_cost": self.total_cost,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "available_providers": list(self.clients.keys()),
            "available_models": list(self.model_configs.keys())
        }
    
    async def health_check(self) -> Dict[str, bool]:
        """檢查各個服務的健康狀態"""
        health_status = {}
        
        for provider in self.clients.keys():
            try:
                # 發送簡單的測試請求
                test_request = AIRequest(
                    prompt="Hello",
                    model_preference=ModelPreference.FASTEST
                )
                await self.generate_text(test_request)
                health_status[provider.value] = True
            except Exception as e:
                logger.warning(f"Health check failed for {provider.value}: {e}")
                health_status[provider.value] = False
        
        return health_status

# 全局實例（單例模式）
_gateway_instance = None

def get_ai_gateway(config: Optional[Dict[str, Any]] = None) -> AIServiceGateway:
    """獲取 AI 服務網關實例（單例）"""
    global _gateway_instance
    
    if _gateway_instance is None:
        if config is None:
            # 使用默認配置
            config = {
                "openai_api_key": "your-openai-api-key",
                "anthropic_api_key": "your-anthropic-api-key",
                "google_api_key": "your-google-api-key",
                "local_model_endpoint": "http://localhost:8000/v1/completions"
            }
        _gateway_instance = AIServiceGateway(config)
    
    return _gateway_instance

# 便捷函數
async def generate_ai_text(
    prompt: str, 
    preference: ModelPreference = ModelPreference.BALANCED,
    **kwargs
) -> str:
    """便捷的 AI 文本生成函數"""
    gateway = get_ai_gateway()
    return await gateway.generate_text_simple(prompt, preference, **kwargs)

