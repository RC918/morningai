# Gemini 3 Integration Design Document

> **Status**: Phase 0 - Design & Planning  
> **Created**: 2025-11-30  
> **Author**: CTO Analysis

## Executive Summary

This document outlines the integration plan for Google Gemini 3 Pro into the MorningAI orchestrator. The integration leverages our existing `LLMClient` abstraction and `ExperimentManager` infrastructure to enable safe, experiment-driven rollout.

**Critical Finding**: The legacy `google-generativeai` SDK (currently used by MorningAI) reached end-of-support on November 30th, 2025. Migration to the new `google-genai` SDK is required.

---

## 1. Gemini 3 API Overview

### 1.1 Model Information

| Property | Value |
|----------|-------|
| **Model ID** | `gemini-3-pro-preview` |
| **Context Window** | 1M input tokens / 64k output tokens |
| **Knowledge Cutoff** | January 2025 |
| **Pricing (<200k tokens)** | $2 / 1M input, $12 / 1M output |
| **Pricing (>200k tokens)** | $4 / 1M input, $18 / 1M output |

### 1.2 New API Features

#### 1.2.1 Thinking Level

Controls the depth of reasoning for complex tasks.

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents="Analyze this code for security vulnerabilities",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="high")
    ),
)
```

| Level | Description | Use Case |
|-------|-------------|----------|
| `low` | Minimizes latency and cost | Simple tasks, quick responses |
| `high` (default) | Maximizes reasoning depth | Complex analysis, code review |

> **Note**: `medium` is not currently supported. Cannot use both `thinking_level` and legacy `thinking_budget` in the same request.

#### 1.2.2 Media Resolution

Controls multimodal vision processing quality.

| Media Type | Recommended Setting | Max Tokens | Guidance |
|------------|---------------------|------------|----------|
| Images | `media_resolution_high` | 1120 | Best for image analysis |
| PDFs | `media_resolution_medium` | 560 | Quality saturates at medium |
| Video (General) | `media_resolution_low` | 70/frame | Sufficient for action recognition |
| Video (Text-heavy) | `media_resolution_high` | 280/frame | Required for OCR in video |

> **Note**: Requires `api_version: 'v1alpha'` in client configuration.

#### 1.2.3 Temperature

**Important**: Gemini 3 recommends keeping temperature at default `1.0`. Changing it may cause:
- Looping behavior
- Degraded performance in mathematical/reasoning tasks

#### 1.2.4 Thought Signatures

Encrypted representations of the model's internal thought process for maintaining reasoning context across API calls.

| Mode | Validation | Impact |
|------|------------|--------|
| Function Calling | **Strict** | Missing signatures = 400 error |
| Text/Chat | Not strict | Omitting degrades quality |
| Image Generation | **Strict** | Missing signatures = 400 error |

> **Good News**: Official SDKs handle Thought Signatures automatically!

#### 1.2.5 Structured Outputs with Tools

Gemini 3 supports combining structured outputs with built-in tools:
- Google Search (grounding)
- URL Context
- Code Execution

```python
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class ReviewResult(BaseModel):
    severity: str = Field(description="Issue severity level")
    issues: list[str] = Field(description="List of identified issues")
    recommendations: list[str] = Field(description="Suggested fixes")

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents="Review this code for security issues: ...",
    config={
        "response_mime_type": "application/json",
        "response_json_schema": ReviewResult.model_json_schema(),
    },
)

result = ReviewResult.model_validate_json(response.text)
```

---

## 2. SDK Migration Requirements

### 2.1 Current State

| Component | Current | Required |
|-----------|---------|----------|
| **SDK** | `google-generativeai~=0.8.0` | `google-genai>=1.50.0` |
| **API Style** | `genai.GenerativeModel()` | `genai.Client()` |
| **Import** | `import google.generativeai as genai` | `from google import genai` |

### 2.2 Migration Timeline

| Date | Event |
|------|-------|
| Late 2024 | Google GenAI SDK launched with Gemini 2.0 |
| May 2025 | Google GenAI SDK reached General Availability |
| **Nov 30, 2025** | Legacy `google-generativeai` stops receiving updates |
| Dec 2025+ | Feature gaps will grow, bugs may not be fixed |

### 2.3 API Changes

#### Old API (google-generativeai)
```python
import google.generativeai as genai

genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config={"temperature": 0.7, "max_output_tokens": 1000}
)
response = model.generate_content(prompt)
```

#### New API (google-genai)
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        temperature=1.0,  # Keep at default for Gemini 3
        max_output_tokens=1000,
        thinking_config=types.ThinkingConfig(thinking_level="high"),
    ),
)
```

---

## 3. MorningAI Integration Plan

### 3.1 Architecture Compatibility

MorningAI's existing architecture is **highly compatible** with Gemini 3:

| Component | Current Implementation | Gemini 3 Fit |
|-----------|----------------------|--------------|
| `LLMClient` | Provider abstraction | Add Gemini3Provider |
| `ExperimentManager` | Hash-based A/B testing | Add gemini3 experiments |
| `GeminiProvider` | Legacy SDK wrapper | Migrate to new SDK |
| Planner/Reviewer Adapters | Use `get_client_for_component()` | No changes needed |

### 3.2 Files to Modify

#### Phase 1: SDK Migration (Required)

| File | Changes |
|------|---------|
| `orchestrator/requirements.txt` | Replace `google-generativeai~=0.8.0` with `google-genai>=1.50.0` |
| `orchestrator/llm/providers/gemini_provider.py` | Rewrite to use new `genai.Client()` API |
| `orchestrator/llm/providers/base.py` | Add `thinking_level` parameter to `LLMResponse` |

#### Phase 2: Gemini 3 Features (Optional)

| File | Changes |
|------|---------|
| `orchestrator/experiment_manager.py` | Add `gemini3_planner_10pct_staging` experiment |
| `orchestrator/llm/client.py` | Add `thinking_level` parameter support |
| `orchestrator/llm_planner_adapter.py` | Use `thinking_level="high"` for complex plans |
| `orchestrator/llm_reviewer_adapter.py` | Use structured outputs for review results |

### 3.3 New GeminiProvider Implementation

```python
"""
Google Gemini 3 LLM Provider implementation

Supports:
- gemini-3-pro-preview (default for Gemini 3)
- gemini-pro (legacy, for backward compatibility)

Uses the new google-genai SDK (GA since May 2025).
"""
import logging
from typing import Optional, Literal

from common.config.settings import settings
from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)

ThinkingLevel = Literal["low", "high"]


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini provider using the new google-genai SDK
    """

    provider_name = "gemini"
    default_model = "gemini-3-pro-preview"

    def __init__(self, model: Optional[str] = None):
        self.model = model or self.default_model
        self._client = None

    def _get_client(self):
        """Lazy initialization of Gemini client"""
        if self._client is None:
            try:
                from google import genai
                self._genai = genai
            except ImportError:
                raise NotImplementedError(
                    "Google GenAI SDK not installed. "
                    "Install with: pip install google-genai"
                )

            api_key = getattr(settings, 'gemini_api_key', None)
            if not api_key:
                raise ValueError(
                    "Gemini API key not configured. "
                    "Set GEMINI_API_KEY environment variable."
                )

            self._client = genai.Client(api_key=api_key)

        return self._client

    def is_available(self) -> bool:
        """Check if Gemini API key is configured"""
        return bool(getattr(settings, 'gemini_api_key', None))

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,  # Gemini 3 default
        max_tokens: int = 1000,
        json_mode: bool = False,
        thinking_level: ThinkingLevel = "high",
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using Google Gemini 3

        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (recommend 1.0 for Gemini 3)
            max_tokens: Maximum tokens to generate
            json_mode: If True, request JSON-formatted response
            thinking_level: "low" for speed, "high" for depth
            model: Override default model
        """
        from google.genai import types

        use_model = model or self.model
        client = self._get_client()

        # Build generation config
        config_dict = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Add thinking config for Gemini 3 models
        if "gemini-3" in use_model:
            config_dict["thinking_config"] = types.ThinkingConfig(
                thinking_level=thinking_level
            )

        if json_mode:
            config_dict["response_mime_type"] = "application/json"

        # Combine system prompt with user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        logger.debug(
            f"[Gemini] Calling API with model={use_model}, "
            f"thinking_level={thinking_level}, json_mode={json_mode}"
        )

        try:
            response = client.models.generate_content(
                model=use_model,
                contents=full_prompt,
                config=types.GenerateContentConfig(**config_dict),
            )

            content = response.text if response.text else ""

            # Extract usage metadata
            usage = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(
                        response.usage_metadata, 'prompt_token_count', 0
                    ),
                    "completion_tokens": getattr(
                        response.usage_metadata, 'candidates_token_count', 0
                    ),
                    "total_tokens": getattr(
                        response.usage_metadata, 'total_token_count', 0
                    )
                }

            return LLMResponse(
                content=content,
                model=use_model,
                provider=self.provider_name,
                usage=usage,
                raw_response=response
            )

        except Exception as e:
            logger.error(
                f"[Gemini] API call failed: {e}",
                extra={
                    "operation": "llm_generate",
                    "provider": self.provider_name,
                    "model": use_model,
                    "error": str(e)
                }
            )
            raise
```

### 3.4 New Experiment Configuration

```python
# Add to experiment_manager.py EXPERIMENT_CONFIGS

"gemini3_planner_10pct_staging": ExperimentConfig(
    name="gemini3_planner_10pct_staging",
    description="Test Gemini 3 Pro as planner LLM on 10% of staging traffic",
    treatment_percent=10,
    enabled_environments=["staging"],
    treatment_provider="gemini",  # Uses gemini-3-pro-preview
    control_provider="openai",
    target_component="planner",
    enabled=True
),

"gemini3_reviewer_5pct_staging": ExperimentConfig(
    name="gemini3_reviewer_5pct_staging",
    description="Test Gemini 3 Pro as reviewer LLM on 5% of staging traffic",
    treatment_percent=5,
    enabled_environments=["staging"],
    treatment_provider="gemini",
    control_provider="openai",
    target_component="reviewer",
    enabled=True
),
```

---

## 4. Implementation Roadmap

### Phase 1: SDK Migration (Priority: Critical)

**Timeline**: 1-2 days  
**Risk**: Medium (breaking change)

| Task | Effort | Owner |
|------|--------|-------|
| Update `requirements.txt` to use `google-genai>=1.50.0` | 5 min | - |
| Rewrite `GeminiProvider` to use new SDK | 2-3 hours | - |
| Update unit tests for new API | 1-2 hours | - |
| Test in staging environment | 1 hour | - |

### Phase 2: Gemini 3 Features (Priority: High)

**Timeline**: 3-5 days  
**Risk**: Low (additive changes)

| Task | Effort | Owner |
|------|--------|-------|
| Add `thinking_level` parameter to `LLMClient` | 1 hour | - |
| Add Gemini 3 experiments to `ExperimentManager` | 30 min | - |
| Update planner adapter for `thinking_level="high"` | 1 hour | - |
| Update reviewer adapter for structured outputs | 2-3 hours | - |
| Add metrics for thinking_level usage | 1 hour | - |

### Phase 3: Staging Validation (Priority: High)

**Timeline**: 1-2 weeks  
**Risk**: Low (controlled rollout)

| Task | Effort | Owner |
|------|--------|-------|
| Enable `gemini3_planner_10pct_staging` experiment | 5 min | - |
| Monitor latency, cost, error rate metrics | Ongoing | - |
| Compare plan quality vs OpenAI baseline | 1 week | - |
| Tune prompts for Gemini 3 behavior | 2-3 days | - |

### Phase 4: Production Rollout (Priority: Medium)

**Timeline**: 2-4 weeks  
**Risk**: Medium (production traffic)

| Task | Effort | Owner |
|------|--------|-------|
| Gradually increase experiment percentages | Ongoing | - |
| Add kill switch env var `DISABLE_GEMINI3` | 30 min | - |
| Update AI Policies to support provider selection | 2-3 hours | - |
| Document Gemini 3 behavior differences | 1-2 hours | - |

---

## 5. Risk Assessment

### 5.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SDK migration breaks existing Gemini calls | Medium | High | Comprehensive testing, staged rollout |
| Prompt behavior differs from OpenAI | High | Medium | A/B testing, prompt tuning |
| Thought signatures cause 400 errors | Low | High | Use official SDK (handles automatically) |
| Temperature=1.0 causes unexpected behavior | Low | Medium | Monitor output quality |

### 5.2 Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Cost increase from Gemini 3 pricing | Medium | Medium | Budget alerts, cost tracking per trace |
| Latency increase from `thinking_level="high"` | High | Low | Use `thinking_level="low"` for simple tasks |
| API rate limits | Low | Medium | Implement retry with backoff |

---

## 6. Success Metrics

### 6.1 Phase 1 (SDK Migration)

- [ ] All existing Gemini tests pass with new SDK
- [ ] No regression in staging Gemini experiments
- [ ] Zero 400 errors from thought signature issues

### 6.2 Phase 2 (Gemini 3 Features)

- [ ] `thinking_level` parameter available in `LLMClient`
- [ ] Gemini 3 experiments registered and activatable
- [ ] Metrics dashboard shows provider breakdown

### 6.3 Phase 3 (Staging Validation)

- [ ] Gemini 3 planner latency within 2x of OpenAI
- [ ] Gemini 3 plan quality >= OpenAI (subjective review)
- [ ] Error rate < 1% for Gemini 3 calls

### 6.4 Phase 4 (Production Rollout)

- [ ] 50%+ traffic on Gemini 3 for planner
- [ ] Cost per task within budget
- [ ] No critical incidents from Gemini 3

---

## 7. References

- [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3)
- [Google GenAI SDK Documentation](https://ai.google.dev/gemini-api/docs/libraries)
- [SDK Migration Guide](https://ai.google.dev/gemini-api/docs/migrate)
- [Gemini API Pricing](https://ai.google.dev/pricing)

---

## Appendix A: Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google AI API key | Required |
| `LLM_PROVIDER` | Default LLM provider | `openai` |
| `DISABLE_GEMINI3` | Kill switch for Gemini 3 | `false` |
| `GEMINI3_THINKING_LEVEL` | Default thinking level | `high` |

## Appendix B: Backward Compatibility

The new `GeminiProvider` maintains backward compatibility:

1. **Model fallback**: If `gemini-3-pro-preview` is unavailable, falls back to `gemini-pro`
2. **API key**: Uses same `GEMINI_API_KEY` environment variable
3. **Interface**: Same `generate()` method signature with optional new parameters
4. **Experiments**: Existing `gemini_planner_10pct_staging` continues to work

## Appendix C: Testing Checklist

- [ ] Unit tests for new `GeminiProvider`
- [ ] Integration tests with real Gemini 3 API
- [ ] A/B test comparison: Gemini 3 vs OpenAI
- [ ] Load test for latency under concurrent requests
- [ ] Error handling for API failures
- [ ] Thought signature handling verification

---

## Appendix D: Troubleshooting

### D.1 OpenAI SDK `proxies` Compatibility Issue

**Symptom**: After deploying, you see errors like:
```
TypeError: Client.__init__() got an unexpected keyword argument 'proxies'
```

**Root Cause**: The `openai` SDK version 1.57.0+ removed support for the `proxies` parameter, which was previously passed through to `httpx`. This is due to `httpx` 0.28.0 removing the deprecated `proxies` argument.

**Solution**: Upgrade `openai` SDK to version `>=1.57.0` which properly handles the httpx 0.28 compatibility:

```bash
# In requirements.txt
openai>=1.57.0

# In setup.py
install_requires=[
    "openai>=1.57.0",
    # ... other dependencies
]
```

**Important**: After updating dependencies, you must also remove stale `.egg-info` directories that may cache old dependency versions:

```bash
# Remove stale egg-info
rm -rf handoff/20250928/40_App/orchestrator/morningai_orchestrator.egg-info/

# Reinstall package
pip install -e handoff/20250928/40_App/orchestrator/
```

**Verification**: After deployment, check worker logs for successful LLM calls without `proxies` errors.

### D.2 Stale egg-info Caching Old Dependencies

**Symptom**: Even after updating `requirements.txt` and `setup.py`, the deployed application still uses old dependency versions.

**Root Cause**: Python's `pip install -e .` (editable install) creates a `.egg-info` directory that caches dependency information. If this directory exists from a previous install, pip may not re-read the updated `setup.py`.

**Solution**:
1. Add `.egg-info/` directories to `.gitignore`
2. Remove existing `.egg-info` directories before deployment
3. Use `pip install --no-cache-dir -e .` for fresh installs

**Prevention**: The `.gitignore` should include:
```
*.egg-info/
```

---

## Appendix E: Experiment Operations Guide

### E.1 Changing Treatment Percentage

To adjust the percentage of traffic receiving the treatment (Gemini 3):

1. **Edit `experiment_manager.py`**:
```python
# Find the experiment configuration
"gemini3_planner_10pct_staging": ExperimentConfig(
    name="gemini3_planner_10pct_staging",
    treatment_percent=10,  # Change this value (0-100)
    # ...
),
```

2. **Commit and deploy** the change
3. **Verify** in logs that the new percentage is active

**Recommended rollout schedule**:
- Start: 10% (initial validation)
- Week 1: 25% (if metrics look good)
- Week 2: 50% (broader validation)
- Week 3+: 100% (full rollout)

### E.2 Pausing an Experiment

To temporarily pause an experiment without removing it:

**Option 1: Set treatment_percent to 0**
```python
"gemini3_planner_10pct_staging": ExperimentConfig(
    treatment_percent=0,  # Effectively pauses the experiment
    # ...
),
```

**Option 2: Disable the experiment**
```python
"gemini3_planner_10pct_staging": ExperimentConfig(
    enabled=False,  # Disables the experiment
    # ...
),
```

**Option 3: Remove from enabled_environments**
```python
"gemini3_planner_10pct_staging": ExperimentConfig(
    enabled_environments=[],  # No environments enabled
    # ...
),
```

### E.3 Emergency Rollback

If Gemini 3 causes issues in production:

1. **Immediate**: Set `treatment_percent=0` or `enabled=False`
2. **Deploy** the change immediately
3. **Verify** in logs that all traffic is going to control (OpenAI)

**Rollback checklist**:
- [ ] Update experiment config
- [ ] Commit and push
- [ ] Trigger deployment
- [ ] Verify in worker logs: no `thinking_level=high` entries
- [ ] Monitor error rates return to baseline

### E.4 Monitoring Experiment Metrics

**API Endpoint**: `GET /api/experiments/comparison`

Query parameters:
- `days`: Number of days to look back (default: 7)

**Response includes**:
```json
{
  "comparisons": [
    {
      "experiment_name": "gemini3_planner_10pct_staging",
      "metrics": {
        "control": {
          "success_rate": 0.95,
          "avg_latency_ms": 1250,
          "total_requests": 100,
          "error_rate": 0.05
        },
        "treatment": {
          "success_rate": 0.92,
          "avg_latency_ms": 980,
          "total_requests": 10,
          "error_rate": 0.08
        }
      }
    }
  ],
  "metrics_source": "planner_events",
  "metrics_period_days": 7
}
```

**Key metrics to monitor**:
- `success_rate`: Should be >= control
- `avg_latency_ms`: Gemini 3 with `thinking_level=high` may be slower
- `error_rate`: Should be < 5%
- `total_requests`: Verify expected traffic split

### E.5 Database Schema for Metrics

The `planner_events` table stores metrics for experiment analysis:

```sql
-- Key columns for experiment metrics
SELECT 
    provider,           -- 'openai' or 'gemini'
    COUNT(*) as total_requests,
    AVG(planning_time_ms) as avg_latency_ms,
    COUNT(CASE WHEN jsonb_array_length(actual_plan_steps) > 0 THEN 1 END)::float / COUNT(*) as success_rate,
    COUNT(CASE WHEN actual_plan_steps IS NULL OR jsonb_array_length(actual_plan_steps) = 0 THEN 1 END)::float / COUNT(*) as error_rate
FROM planner_events
WHERE provider IS NOT NULL
  AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY provider;
```

**Required migration**: Migration 027 adds the `provider` column:
```sql
ALTER TABLE planner_events
ADD COLUMN IF NOT EXISTS provider VARCHAR(50);

CREATE INDEX IF NOT EXISTS idx_planner_events_provider
    ON planner_events(provider);
```
