# EPIC E: Safety Governor v2 + Compliance Radar v2 Roadmap

**Issue**: [#3489](https://github.com/RC918/morningai/issues/3489)  
**Blueprint Reference**: Section 4.1 (Safety Governor v2) + Section 4.2 (Compliance Radar v2)  
**Status**: Planning  
**Last Updated**: 2026-01-02

## Executive Summary

EPIC E transforms MorningAI's safety infrastructure from a "gatekeeping" model to an "immune system" architecture. This roadmap integrates evidence-based analysis of existing components with strategic vision for systemic resilience.

## Architecture Vision

### From "Gatekeeping" to "Immune System"

| Layer | Current Component | Integrated Role | North Star Extension |
|-------|-------------------|-----------------|----------------------|
| Policy Source | PolicyGuard | Unified policy config source | Capability-Based Security |
| Enforcement | RuntimePolicyEnforcer | Resource/Cost/Tool Safety | Agent-Specific Sandboxing |
| Advisory | SecurityAgent | Risk Scan (secrets/injection) | Safety Judge-as-a-Service |
| Audit | (New) | Evidence Event Stream | Immutable Evidence Ledger |

### Existing Components Analysis

| Component | File | Lines | Current Coverage |
|-----------|------|-------|------------------|
| RuntimePolicyEnforcer | `governance/runtime_policy_enforcer.py` | 927 | Resource/Cost/Tool Safety |
| SecurityAgent | `security_agent/agent.py` | 610 | Advisory (secrets/injection/traversal) |
| PolicyGuard | `governance/policy_guard.py` | 218 | YAML-based policy config |

**Important Note**: `RuntimePolicyEnforcer` docstring labels itself "Safety Governor v2" but only covers resource/cost/tool safety subset, NOT content safety required by Blueprint.

## Phase Breakdown

### Phase E-0: Decision Contract + Evidence Schema

**Objective**: Define unified Decision schema and Evidence Event schema as the "API specification" for Safety Governor v2.

**Deliverables**:

1. **Unified Decision Schema** (JSON Schema):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SafetyDecision",
  "type": "object",
  "required": ["action", "category", "policy_id", "reason", "trace_id", "decision_version"],
  "properties": {
    "action": {
      "type": "string",
      "enum": ["allow", "block", "require_approval", "degrade_model", "log_only"]
    },
    "category": {
      "type": "string",
      "description": "Safety category (e.g., 'resource_access', 'content_safety', 'compliance')"
    },
    "policy_id": {
      "type": "string",
      "description": "Unique identifier for the policy that triggered this decision"
    },
    "reason": {
      "type": "string",
      "description": "Human-readable explanation of the decision"
    },
    "evidence": {
      "type": "object",
      "properties": {
        "hash": { "type": "string", "description": "SHA-256 hash of evidence data" },
        "summary": { "type": "string", "description": "Brief summary of evidence" },
        "raw_data_ref": { "type": "string", "description": "Reference to full evidence data" }
      }
    },
    "trace_id": {
      "type": "string",
      "description": "Correlation ID for end-to-end tracing"
    },
    "decision_version": {
      "type": "string",
      "description": "Version of decision schema (e.g., '1.0.0')"
    },
    "overrideable": {
      "type": "boolean",
      "default": false,
      "description": "Whether this decision can be overridden via HITL"
    },
    "principal": {
      "type": "object",
      "description": "Agent identity context (hook for sandboxing)",
      "properties": {
        "agent_id": { "type": "string" },
        "agent_type": { "type": "string" },
        "capability_set": { 
          "type": "array", 
          "items": { "type": "string" },
          "description": "Allowed capabilities for this agent"
        }
      }
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

2. **Evidence Event Schema** (append-only interface):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SafetyEvidenceEvent",
  "type": "object",
  "required": ["event_id", "event_type", "trace_id", "timestamp", "decision"],
  "properties": {
    "event_id": { "type": "string", "format": "uuid" },
    "event_type": { 
      "type": "string", 
      "enum": ["decision_made", "override_requested", "override_approved", "override_denied"]
    },
    "trace_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "decision": { "$ref": "#/definitions/SafetyDecision" },
    "context": {
      "type": "object",
      "properties": {
        "task_id": { "type": "string" },
        "repo": { "type": "string" },
        "user_id": { "type": "string" },
        "session_id": { "type": "string" }
      }
    }
  }
}
```

3. **Enforcement Points Documentation**:
   - LLM boundary (input/output)
   - Agent output boundary
   - Side-effect boundary (file write, shell, network, GitHub posting)

**Acceptance Criteria**:
- [ ] Decision schema defined and documented
- [ ] Evidence Event schema defined and documented
- [ ] All enforcement points listed with current coverage status
- [ ] Principal/capability fields included for future sandboxing

**North Star Hook**: `principal.capability_set` field enables future Agent-Specific Sandboxing.

---

### Phase E-1: Wiring & Coverage + Principal Context

**Objective**: Ensure all side-effects pass through RuntimePolicyEnforcer with consistent principal context.

**Deliverables**:

1. **Coverage Audit**:
   - Map all side-effect entry points in orchestrator
   - Verify RuntimePolicyEnforcer is called at each point
   - Document any gaps

2. **Principal Context Propagation**:
   - Add `principal` parameter to RuntimePolicyEnforcer methods
   - Propagate agent identity through call chain
   - Default to "unknown" for backward compatibility

3. **PolicyGuard as Single Source**:
   - Ensure all policy reads go through PolicyGuard
   - Remove any hardcoded policy logic
   - Add policy version tracking

4. **Integration Tests**:
   - Test coverage for file write operations
   - Test coverage for shell execution
   - Test coverage for network access
   - Test coverage for GitHub posting

**Acceptance Criteria**:
- [ ] All side-effect operations verified to pass through RuntimePolicyEnforcer
- [ ] Principal context available at enforcement points
- [ ] PolicyGuard is the only policy source
- [ ] Integration tests pass for all enforcement points

**North Star Hook**: `capability_set` structure enables future granular rules.

---

### Phase E-2: Risk Scan + Risk Override Framework

**Objective**: Implement pluggable RiskScan pipeline with Tier-0 critical task handling.

**Deliverables**:

1. **RiskScan Pipeline Interface**:

```python
class RiskScanner(Protocol):
    """Protocol for pluggable risk scanners"""
    
    def scan(self, content: str, context: ScanContext) -> RiskScanResult:
        """Scan content for risks"""
        ...

@dataclass
class RiskScanResult:
    risk_level: str  # "low", "medium", "high", "critical"
    findings: List[RiskFinding]
    confidence: float
    scanner_id: str
```

2. **Multi-Scanner Support** (ensemble architecture):
   - Primary scanner (rule-based baseline)
   - Secondary scanner slot (for future AI classifier)
   - Aggregation logic (worst-case or voting)

3. **Tier-0 Critical Task Handling**:
   - Define Tier-0 criteria (high-risk repo paths, specific operations, labels)
   - Force `require_approval` for Tier-0 tasks
   - Integrate with existing HITL mechanism

4. **Risk Override Flow**:
   - Override request → HITL queue
   - Override approval → Evidence Event logged
   - Override denial → Evidence Event logged

**Acceptance Criteria**:
- [ ] RiskScan pipeline interface defined
- [ ] Rule-based baseline scanner implemented
- [ ] Tier-0 criteria defined and enforced
- [ ] Override flow integrated with HITL
- [ ] All decisions logged as Evidence Events

**North Star Hook**: Pipeline plugin architecture enables future Safety Judge-as-a-Service.

---

### Phase E-3: Content Safety MVP

**Objective**: Implement heuristic-based content safety checks for prompt injection, jailbreak, and harmful content.

**Deliverables**:

1. **Prompt Injection Detection**:
   - Pattern-based detection (system prompt exfiltration, instruction override)
   - Confidence scoring
   - Evidence generation

2. **Jailbreak Detection**:
   - Known jailbreak pattern matching
   - Role-play detection
   - Evidence generation

3. **Harmful Content Detection**:
   - Category-based filtering (violence, hate, etc.)
   - Configurable thresholds via PolicyGuard
   - Evidence generation

4. **Content Safety Scanner** (implements RiskScanner):

```python
class ContentSafetyScanner:
    """Heuristic-based content safety scanner"""
    
    def __init__(self, policies: PolicyGuard):
        self.policies = policies
        self.injection_patterns = self._load_injection_patterns()
        self.jailbreak_patterns = self._load_jailbreak_patterns()
        self.harmful_patterns = self._load_harmful_patterns()
    
    def scan(self, content: str, context: ScanContext) -> RiskScanResult:
        findings = []
        findings.extend(self._check_injection(content))
        findings.extend(self._check_jailbreak(content))
        findings.extend(self._check_harmful(content))
        return RiskScanResult(
            risk_level=self._aggregate_risk(findings),
            findings=findings,
            confidence=self._calculate_confidence(findings),
            scanner_id="content_safety_v1"
        )
```

**Acceptance Criteria**:
- [ ] Prompt injection patterns defined and tested
- [ ] Jailbreak patterns defined and tested
- [ ] Harmful content patterns defined and tested
- [ ] All detections produce evidence with hash and summary
- [ ] False positive rate < 5% on test corpus

**North Star Hook**: Pluggable classifier interface enables future AI-supervising-AI.

---

### Phase E-4: Compliance Radar v2 MVP

**Objective**: Implement PII scanning, audit trail, and compliance category framework.

**Deliverables**:

1. **PII Scanner**:
   - Email detection
   - Phone number detection
   - SSN/ID number detection
   - Credit card detection
   - Name detection (with context)

2. **Compliance Category Framework**:

```python
class ComplianceCategory(Enum):
    PII = "pii"
    LEGAL = "legal"           # Placeholder
    MEDICAL = "medical"       # Placeholder
    FINANCIAL = "financial"   # Placeholder
    POLITICAL = "political"   # Placeholder
    COPYRIGHT = "copyright"   # Placeholder

@dataclass
class ComplianceCheckResult:
    category: ComplianceCategory
    detected: bool
    findings: List[ComplianceFinding]
    policy_id: str
    action: str  # "allow", "block", "redact", "require_approval"
```

3. **Audit Trail**:
   - All compliance decisions logged as Evidence Events
   - Queryable by trace_id, category, time range
   - Retention policy configuration

4. **Flow Transition Integration**:
   - Every Flow v3 transition triggers compliance check
   - Compliance decision attached to transition metadata

**Acceptance Criteria**:
- [ ] PII scanner implemented with >90% recall
- [ ] Compliance category framework defined
- [ ] Audit trail queryable via API
- [ ] Flow transitions trigger compliance checks
- [ ] Placeholder policies for non-MVP categories

**North Star Hook**: Retention policy configuration enables future Immutable Evidence Ledger.

---

### Phase E-5: Observability & Ops Readiness

**Objective**: Integrate with Owner Console and establish operational readiness.

**Deliverables**:

1. **Owner Console Dashboard Integration**:
   - Safety decision event stream
   - Filter by category, policy_id, action
   - Override request/approval tracking

2. **Metrics & Alerting**:
   - `safety_decisions_total` (by action, category)
   - `safety_scan_latency_seconds`
   - `safety_override_requests_total`
   - Alert on high block rate

3. **Test Matrix**:
   - Unit tests for each scanner
   - Integration tests for full pipeline
   - E2E tests for allow/block/require_approval paths
   - Fail-closed vs fail-open verification

4. **Runbook**:
   - Emergency override procedure
   - False positive handling
   - Policy update procedure

**Acceptance Criteria**:
- [ ] Owner Console shows safety decisions
- [ ] Metrics exported to monitoring system
- [ ] Alerts configured for anomalies
- [ ] Test coverage > 80%
- [ ] Runbook documented and reviewed

**Future Extensions**:
- Immutable Evidence Ledger (PostgreSQL Audit Table)
- Safety Judge-as-a-Service (red-team model)
- Full Capability-Based Security

---

## MVP Scope Guardrail (Non-Goals)

The following are explicitly OUT OF SCOPE for MVP:

- Full legal/medical/financial/political/copyright judgment (placeholder policies only)
- Safety Judge-as-a-Service (red-team model for second opinion)
- Immutable Evidence Ledger (PostgreSQL Audit Table with cryptographic guarantees)
- Complete Capability-Based Security (fine-grained per-agent permissions)
- Real-time adversarial defense training

These will be tracked as follow-up issues after MVP completion.

---

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| EPIC C (Flow Controller v3) | Integration | Completed |
| EPIC D (Autonomous Coder) | Integration | Completed |
| EPIC I (Governance Layer) | Future Integration | Placeholder |
| HITL Mechanism | Existing | Available |
| Owner Console | Existing | Available |

---

## Cross-EPIC Integration Points

### E + F + I Closed Loop

```
Detection (E) → Recording (I) → Adjustment (F)
```

**Integration Schema Fields**:
- `SafetyDecision.principal.trust_score_input` - Input from EPIC I
- `SafetyDecision.evidence` - Output to EPIC I audit
- `PlannerOutput.risk_metadata` - Consumed from EPIC E decisions

This closed loop will be fully activated when EPIC I reaches maturity.

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Enforcement Coverage | 100% | All side-effects pass through enforcer |
| Content Safety Recall | >90% | Test corpus evaluation |
| False Positive Rate | <5% | Production monitoring |
| Decision Latency P99 | <100ms | Metrics dashboard |
| Audit Trail Completeness | 100% | All decisions logged |

---

## Timeline Estimate

| Phase | Estimated Duration | Dependencies |
|-------|-------------------|--------------|
| E-0 | 1-2 days | None |
| E-1 | 3-5 days | E-0 |
| E-2 | 5-7 days | E-1 |
| E-3 | 5-7 days | E-2 |
| E-4 | 5-7 days | E-2 |
| E-5 | 3-5 days | E-3, E-4 |

**Total Estimated Duration**: 4-6 weeks

---

## References

- [Blueprint Section 4.1: Safety Governor v2](../north_star/MorningAI_Ecosystem_Blueprint_2025_Final.md)
- [Blueprint Section 4.2: Compliance Radar v2](../north_star/MorningAI_Ecosystem_Blueprint_2025_Final.md)
- [Wish Pool v2: EPIC E](../north_star/ECOSYSTEM_WISHPOOL_V2.md)
- [RuntimePolicyEnforcer](../../handoff/20250928/40_App/orchestrator/governance/runtime_policy_enforcer.py)
- [SecurityAgent](../../handoff/20250928/40_App/orchestrator/security_agent/agent.py)
- [PolicyGuard](../../handoff/20250928/40_App/orchestrator/governance/policy_guard.py)
