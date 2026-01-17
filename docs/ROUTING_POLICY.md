# Routing Policy v1.3 - Multi-Model LLM Selection

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
| Google Gemini (primary) | gemini-3-pro-preview | 1,048,576 tokens |
| AliCloud DashScope (fallback) | qwen-max | 128,000 tokens |
| OpenAI (fallback) | gpt-4o | 128,000 tokens |

### Tier 1 - High Capability

Used for code generation, detailed analysis, code review, and routing decisions.

| Provider | Model | Context Limit |
|----------|-------|---------------|
| Google Gemini (primary) | gemini-3-flash-preview | 1,048,576 tokens |
| AliCloud DashScope (fallback) | qwen-plus | 128,000 tokens |
| OpenAI (fallback) | gpt-4o-mini | 128,000 tokens |

### Tier 2 - Medium Capability

Used for standard tasks, translation, summarization, and general chat.

| Provider | Model | Context Limit |
|----------|-------|---------------|
| Google Gemini (primary) | gemini-2.5-pro | 1,048,576 tokens |
| AliCloud DashScope (fallback) | qwen-turbo | 32,000 tokens |
| OpenAI (fallback) | gpt-4o-mini | 128,000 tokens |

### Tier 3 - Basic Capability

Used for simple tasks and UX copy generation.

| Provider | Model | Context Limit |
|----------|-------|---------------|
| Google Gemini (primary) | gemini-2.5-pro | 1,048,576 tokens |
| AliCloud DashScope (fallback) | qwen-turbo | 32,000 tokens |
| OpenAI (fallback) | gpt-4o-mini | 128,000 tokens |

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

## Provider Fallback Strategy

All tiers implement a consistent fallback strategy for resilience:

1. **Primary**: Google Gemini (gemini-2.0-flash)
2. **Secondary**: AliCloud DashScope Qwen models (qwen-max, qwen-plus, qwen-turbo)
3. **Tertiary**: OpenAI models (gpt-4o, gpt-4o-mini)

This strategy ensures service continuity even if the primary provider experiences issues. The routing engine automatically selects the next available provider if the primary is unavailable.

## Provider Selection Logic

The routing engine (see `RoutingEngine.select_model()` in `core/routing/engine.py`) implements the following selection logic:

```python
# Simplified illustration of select_model() logic
# See engine.py for exact implementation

def select_model(task_type: TaskType, risk_level: RiskLevel) -> ModelInfo:
    # 1. Get base tier from task_type (from routing_policy.json)
    routing_config = task_routing.get(task_type.value, {"tier": 2, "fallback": 3})
    target_tier = routing_config["tier"]
    
    # 2. Apply risk adjustment (hardcoded logic, not from config)
    if risk_level == RiskLevel.HIGH:
        target_tier = max(0, target_tier - 1)  # Upgrade tier
    elif risk_level == RiskLevel.LOW:
        target_tier = min(3, target_tier + 1)  # Downgrade tier
    
    # 3. Find available model in target tier
    model_info = find_available_model(Tier(target_tier))
    if model_info:
        return model_info
    
    # 4. Fallback to fallback tier if no models available
    fallback_tier = routing_config["fallback"]
    return find_available_model(Tier(fallback_tier))
```

Note: The risk adjustment values in `routing_policy.json` (`risk_adjustments` section) document the intended behavior but the actual implementation uses hardcoded if/else logic in `RoutingEngine.select_model()` (see risk level adjustment section in `core/routing/engine.py`).

## Supported Providers

The following LLM providers are supported (see `VALID_PROVIDERS` in `common/config/settings.py`):

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
    def execute(self, input: AgentInput) -> AgentOutput:
        # call_llm is synchronous (not async)
        response = self.call_llm(
            prompt=input.task_description,
            task_type="coding",
            risk_level="medium"
        )
        return AgentOutput(
            task_id=input.task_id,
            success=True,
            result=response["content"]
        )
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
| 1.4 | Jan 2026 | Upgraded Gemini models: Tier 0 to gemini-3-pro-preview, Tier 1 to gemini-3-flash-preview, Tier 2-3 to gemini-2.5-pro |
| 1.3 | Jan 2026 | Changed provider order to Gemini-first, removed SiliconFlow |
| 1.2 | Dec 2025 | Cross-generation fallback strategy, Qwen3/Qwen2.5 model lineup |
| 1.1 | Nov 2025 | Added risk level adjustments |
| 1.0 | Oct 2025 | Initial routing policy with tier system |
