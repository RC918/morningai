# Routing Policy v1.2 - Multi-Model LLM Selection

This document describes the routing policy for multi-model LLM selection in MorningAI (EPIC #2594). The routing engine dynamically selects the appropriate LLM model based on task type and risk level, with cross-generation fallback for resilience.

## Overview

MorningAI uses a tiered model selection system that balances capability, cost, and reliability. The routing engine (`core/routing/engine.py`) reads configuration from `core/routing/routing_policy.json` and selects models based on:

1. **Task Type**: The nature of the work being performed (planning, coding, review, etc.)
2. **Risk Level**: The criticality of the task (high, medium, low)
3. **Provider Availability**: Which LLM providers have valid API keys configured

## Tier System

The routing policy defines four tiers (0-3) with decreasing capability and cost:

### Tier 0 - Highest Capability

Used for complex reasoning, strategic planning, and critical decisions.

| Provider | Model | Context Limit |
|----------|-------|---------------|
| AliCloud DashScope | qwen-max | 128,000 tokens |
| SiliconFlow (fallback) | Qwen/Qwen2.5-72B-Instruct | 128,000 tokens |

Fallback strategy: Cross-generation (Qwen3 to Qwen2.5-72B)

### Tier 1 - High Capability

Used for code generation, detailed analysis, code review, and routing decisions.

| Provider | Model | Context Limit |
|----------|-------|---------------|
| AliCloud DashScope | qwen-plus | 128,000 tokens |
| SiliconFlow (fallback) | Qwen/Qwen2.5-32B-Instruct | 128,000 tokens |

Fallback strategy: Cross-generation (Qwen3 to Qwen2.5-32B)

### Tier 2 - Medium Capability

Used for standard tasks, translation, summarization, and general chat.

| Provider | Model | Context Limit |
|----------|-------|---------------|
| AliCloud DashScope | qwen-turbo | 32,000 tokens |
| SiliconFlow (fallback) | Qwen/Qwen2.5-32B-Instruct | 32,000 tokens |

### Tier 3 - Basic Capability

Used for simple tasks and UX copy generation.

| Provider | Model | Context Limit |
|----------|-------|---------------|
| SiliconFlow | Qwen/Qwen2.5-14B-Instruct | 8,000 tokens |
| SiliconFlow (fallback) | Qwen/Qwen2.5-7B-Instruct | 8,000 tokens |

## Task Type Mapping

Each task type is mapped to a default tier and fallback tier:

| Task Type | Default Tier | Fallback Tier | Description |
|-----------|--------------|---------------|-------------|
| `planning` | 0 | 1 | Complex reasoning, strategic planning, critical decisions |
| `coding` | 1 | 2 | Code generation, implementation, debugging |
| `review` | 1 | 2 | Code review, PR analysis, quality assessment |
| `routing` | 1 | 2 | Flow routing decisions, next-step determination (C-2 Hybrid Router) |
| `analysis` | 1 | 2 | Data analysis, pattern recognition, insights |
| `translation` | 2 | 3 | Language translation, localization |
| `summarization` | 2 | 3 | Document summarization, key point extraction |
| `chat` | 2 | 3 | General conversation, Q&A, support |
| `ux_copy` | 3 | 2 | UI text, button labels, simple user-facing content |

## Risk Level Adjustments

Risk level modifies the effective tier by adjusting up or down:

| Risk Level | Tier Adjustment | Effect |
|------------|-----------------|--------|
| `high` | -1 | Upgrades to higher capability tier |
| `medium` | 0 | No change |
| `low` | +1 | Downgrades to lower capability tier (cost optimization) |

### Example Calculations

1. **Planning task with high risk**: Tier 0 + (-1) = Tier 0 (capped at highest)
2. **Coding task with medium risk**: Tier 1 + 0 = Tier 1
3. **Chat task with low risk**: Tier 2 + 1 = Tier 3

## Cross-Generation Fallback Strategy

Tiers 0 and 1 implement cross-generation fallback for resilience:

1. **Primary**: AliCloud DashScope Qwen3 models (qwen-max, qwen-plus)
2. **Fallback**: SiliconFlow Qwen2.5 models (72B, 32B)

This strategy ensures service continuity even if the primary provider experiences issues. The fallback models are from a previous generation (Qwen2.5) but still provide acceptable quality for most tasks.

## Provider Selection Logic

The routing engine (`engine.py:216-299`) implements the following selection logic:

```python
def select_model(task_type: TaskType, risk_level: RiskLevel) -> ModelSelection:
    # 1. Get base tier from task_type
    base_tier = routing_policy["task_types"][task_type]["tier"]
    
    # 2. Apply risk adjustment
    adjustment = routing_policy["risk_adjustments"][risk_level]
    effective_tier = max(0, min(3, base_tier + adjustment))
    
    # 3. Get models for effective tier
    tier_config = routing_policy["tier_models"][str(effective_tier)]
    
    # 4. Select first available model with valid API key
    for model in tier_config["models"]:
        if has_valid_api_key(model["provider"]):
            return ModelSelection(
                provider=model["provider"],
                model=model["model"],
                tier=effective_tier
            )
    
    # 5. Fallback to next tier if no models available
    return select_model_from_fallback_tier(task_type)
```

## Supported Providers

The following LLM providers are supported (`settings.py:54`):

| Provider | Environment Variable | Description |
|----------|---------------------|-------------|
| `openai` | `OPENAI_API_KEY` | OpenAI GPT models |
| `gemini` | `GEMINI_API_KEY` | Google Gemini models |
| `alicloud` | `DASHSCOPE_API_KEY` | AliCloud DashScope Qwen models |
| `siliconflow` | `SILICONFLOW_API_KEY` | SiliconFlow hosted models |

## Governance Controls

### ROUTING_ALLOWED_PROVIDERS

This environment variable restricts which providers can be used:

- **Empty (default)**: All providers with valid API keys are available
- **Non-empty**: Only listed providers are allowed (comma-separated)

Example: `ROUTING_ALLOWED_PROVIDERS=alicloud,siliconflow`

## Usage in Code

### BaseAgent.call_llm()

All agents use the routing engine through `BaseAgent.call_llm()`:

```python
from core.agents.base import BaseAgent

class MyAgent(BaseAgent):
    async def execute(self, task):
        response = await self.call_llm(
            prompt=task.prompt,
            task_type="coding",
            risk_level="medium"
        )
        return response
```

### Direct RoutingEngine Usage

For advanced use cases:

```python
from core.routing.engine import RoutingEngine, TaskType, RiskLevel

engine = RoutingEngine()
selection = engine.select_model(
    task_type=TaskType.PLANNING,
    risk_level=RiskLevel.HIGH
)
print(f"Selected: {selection.provider}/{selection.model} (Tier {selection.tier})")
```

## Configuration File Location

The routing policy configuration is located at:

```
handoff/20250928/40_App/orchestrator/core/routing/routing_policy.json
```

## Related Documentation

- [ONBOARDING_GUIDE.md](./ONBOARDING_GUIDE.md) - Developer onboarding guide
- [ADR-005](./adr/005-deprecate-simple-orchestrator-mode.md) - Simple Mode deprecation
- EPIC #2594 - Multi-Model Routing implementation

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.2 | Dec 2025 | Cross-generation fallback strategy, Qwen3/Qwen2.5 model lineup |
| 1.1 | Nov 2025 | Added risk level adjustments |
| 1.0 | Oct 2025 | Initial routing policy with tier system |
