"""
Tests for Evidence Ledger - Blueprint Section 4.6

Issue: #4095 - [Phase 2] Evidence Ledger: Complete Decision Record + Reasoning Chain
"""

import pytest

from governance.evidence_ledger import (
    EvidenceLedger,
    DecisionRecord,
    DecisionType,
    DecisionOutcome,
    ReasoningChain,
    ReasoningStepType,
    AuditQuery,
    RetentionPolicy,
    get_evidence_ledger,
    reset_evidence_ledger,
)


class TestDecisionRecord:
    """Tests for DecisionRecord dataclass"""

    def test_create_decision_record(self):
        """Test creating a basic decision record"""
        record = DecisionRecord(
            decision_id="dec:test123",
            decision_type=DecisionType.ROUTING,
            component="FlowController",
            agent_id="agent:planner",
            trace_id="trace:abc123",
            span_id="span:def456",
            input_summary="Route task to appropriate agent",
            output_summary="Selected ReviewerAgent",
            outcome=DecisionOutcome.APPROVED,
            confidence=0.95,
        )

        assert record.decision_id == "dec:test123"
        assert record.decision_type == DecisionType.ROUTING
        assert record.outcome == DecisionOutcome.APPROVED
        assert record.confidence == 0.95

    def test_decision_record_to_dict(self):
        """Test serialization to dictionary"""
        record = DecisionRecord(
            decision_id="dec:test123",
            decision_type=DecisionType.SAFETY,
            component="SafetyGovernor",
            agent_id=None,
            trace_id="trace:abc123",
            span_id="span:def456",
            input_summary="Check content safety",
            output_summary="Content approved",
            outcome=DecisionOutcome.APPROVED,
        )

        data = record.to_dict()

        assert data["decision_id"] == "dec:test123"
        assert data["decision_type"] == "safety"
        assert data["outcome"] == "approved"
        assert data["component"] == "SafetyGovernor"

    def test_decision_record_from_dict(self):
        """Test deserialization from dictionary"""
        data = {
            "decision_id": "dec:test123",
            "decision_type": "governance",
            "component": "PolicyEnforcer",
            "agent_id": "agent:enforcer",
            "trace_id": "trace:abc123",
            "span_id": "span:def456",
            "input_summary": "Enforce policy",
            "output_summary": "Policy enforced",
            "outcome": "approved",
            "confidence": 0.99,
        }

        record = DecisionRecord.from_dict(data)

        assert record.decision_id == "dec:test123"
        assert record.decision_type == DecisionType.GOVERNANCE
        assert record.outcome == DecisionOutcome.APPROVED
        assert record.confidence == 0.99


class TestReasoningChain:
    """Tests for ReasoningChain"""

    def test_create_reasoning_chain(self):
        """Test creating a reasoning chain"""
        chain = ReasoningChain(
            chain_id="chain:test123",
            decision_id="dec:test456",
        )

        assert chain.chain_id == "chain:test123"
        assert chain.decision_id == "dec:test456"
        assert len(chain.steps) == 0
        assert chain.total_confidence == 1.0

    def test_add_reasoning_steps(self):
        """Test adding steps to a reasoning chain"""
        chain = ReasoningChain(
            chain_id="chain:test123",
            decision_id="dec:test456",
        )

        step1 = chain.add_step(
            step_type=ReasoningStepType.OBSERVATION,
            description="Observed user request for code review",
            confidence=1.0,
        )

        step2 = chain.add_step(
            step_type=ReasoningStepType.ANALYSIS,
            description="Analyzed code complexity and risk level",
            confidence=0.9,
        )

        step3 = chain.add_step(
            step_type=ReasoningStepType.CONCLUSION,
            description="Concluded: Route to ReviewerAgent",
            confidence=0.85,
        )

        assert len(chain.steps) == 3
        assert chain.total_confidence == 0.85  # Minimum confidence
        assert step1.step_type == ReasoningStepType.OBSERVATION
        assert step2.step_type == ReasoningStepType.ANALYSIS
        assert step3.step_type == ReasoningStepType.CONCLUSION

    def test_reasoning_chain_complete(self):
        """Test completing a reasoning chain"""
        chain = ReasoningChain(
            chain_id="chain:test123",
            decision_id="dec:test456",
        )

        assert chain.completed_at is None

        chain.complete()

        assert chain.completed_at is not None

    def test_reasoning_chain_serialization(self):
        """Test serialization and deserialization"""
        chain = ReasoningChain(
            chain_id="chain:test123",
            decision_id="dec:test456",
        )

        chain.add_step(
            step_type=ReasoningStepType.OBSERVATION,
            description="Test observation",
        )

        chain.add_step(
            step_type=ReasoningStepType.CONCLUSION,
            description="Test conclusion",
            confidence=0.9,
        )

        chain.complete()

        # Serialize
        data = chain.to_dict()

        # Deserialize
        restored = ReasoningChain.from_dict(data)

        assert restored.chain_id == chain.chain_id
        assert restored.decision_id == chain.decision_id
        assert len(restored.steps) == 2
        assert restored.total_confidence == 0.9
        assert restored.completed_at is not None


class TestEvidenceLedger:
    """Tests for EvidenceLedger"""

    @pytest.fixture
    def ledger(self):
        """Create a fresh Evidence Ledger for each test"""
        reset_evidence_ledger()
        return EvidenceLedger(enabled=True)

    def test_record_decision(self, ledger):
        """Test recording a decision"""
        record = ledger.record_decision(
            decision_type=DecisionType.ROUTING,
            component="FlowController",
            trace_id="trace:abc123",
            span_id="span:def456",
            input_summary="Route task",
            output_summary="Selected agent",
            outcome=DecisionOutcome.APPROVED,
        )

        assert record.decision_id.startswith("dec:")
        assert record.decision_type == DecisionType.ROUTING
        assert record.outcome == DecisionOutcome.APPROVED

    def test_record_decision_with_reasoning_chain(self, ledger):
        """Test recording a decision with reasoning chain"""
        chain = ledger.create_reasoning_chain()

        chain.add_step(
            step_type=ReasoningStepType.OBSERVATION,
            description="Observed request",
        )

        chain.add_step(
            step_type=ReasoningStepType.CONCLUSION,
            description="Made decision",
            confidence=0.9,
        )

        record = ledger.record_decision(
            decision_type=DecisionType.AGENT,
            component="AgentSelector",
            trace_id="trace:abc123",
            span_id="span:def456",
            input_summary="Select agent",
            output_summary="Selected PlannerAgent",
            outcome=DecisionOutcome.APPROVED,
            reasoning_chain=chain,
        )

        assert record.reasoning_chain_id == chain.chain_id

        # Verify chain was stored
        retrieved_chain = ledger.get_reasoning_chain(chain.chain_id)
        assert retrieved_chain is not None
        assert len(retrieved_chain.steps) == 2

    def test_get_decision(self, ledger):
        """Test retrieving a decision by ID"""
        record = ledger.record_decision(
            decision_type=DecisionType.SAFETY,
            component="SafetyGovernor",
            trace_id="trace:abc123",
            span_id="span:def456",
            input_summary="Check safety",
            output_summary="Approved",
            outcome=DecisionOutcome.APPROVED,
        )

        retrieved = ledger.get_decision(record.decision_id)

        assert retrieved is not None
        assert retrieved.decision_id == record.decision_id
        assert retrieved.decision_type == DecisionType.SAFETY

    def test_query_decisions_by_type(self, ledger):
        """Test querying decisions by type"""
        # Record multiple decisions
        ledger.record_decision(
            decision_type=DecisionType.ROUTING,
            component="FlowController",
            trace_id="trace:1",
            span_id="span:1",
            input_summary="Route 1",
            output_summary="Result 1",
            outcome=DecisionOutcome.APPROVED,
        )

        ledger.record_decision(
            decision_type=DecisionType.SAFETY,
            component="SafetyGovernor",
            trace_id="trace:2",
            span_id="span:2",
            input_summary="Safety 1",
            output_summary="Result 2",
            outcome=DecisionOutcome.REJECTED,
        )

        ledger.record_decision(
            decision_type=DecisionType.ROUTING,
            component="FlowController",
            trace_id="trace:3",
            span_id="span:3",
            input_summary="Route 2",
            output_summary="Result 3",
            outcome=DecisionOutcome.APPROVED,
        )

        # Query routing decisions
        query = AuditQuery(decision_type=DecisionType.ROUTING)
        results = ledger.query_decisions(query)

        assert len(results) == 2
        assert all(r.decision_type == DecisionType.ROUTING for r in results)

    def test_query_decisions_by_outcome(self, ledger):
        """Test querying decisions by outcome"""
        ledger.record_decision(
            decision_type=DecisionType.SAFETY,
            component="SafetyGovernor",
            trace_id="trace:1",
            span_id="span:1",
            input_summary="Check 1",
            output_summary="Approved",
            outcome=DecisionOutcome.APPROVED,
        )

        ledger.record_decision(
            decision_type=DecisionType.SAFETY,
            component="SafetyGovernor",
            trace_id="trace:2",
            span_id="span:2",
            input_summary="Check 2",
            output_summary="Rejected",
            outcome=DecisionOutcome.REJECTED,
        )

        query = AuditQuery(outcome=DecisionOutcome.REJECTED)
        results = ledger.query_decisions(query)

        assert len(results) == 1
        assert results[0].outcome == DecisionOutcome.REJECTED

    def test_query_decisions_by_confidence(self, ledger):
        """Test querying decisions by minimum confidence"""
        ledger.record_decision(
            decision_type=DecisionType.ROUTING,
            component="FlowController",
            trace_id="trace:1",
            span_id="span:1",
            input_summary="Route 1",
            output_summary="Result 1",
            outcome=DecisionOutcome.APPROVED,
            confidence=0.5,
        )

        ledger.record_decision(
            decision_type=DecisionType.ROUTING,
            component="FlowController",
            trace_id="trace:2",
            span_id="span:2",
            input_summary="Route 2",
            output_summary="Result 2",
            outcome=DecisionOutcome.APPROVED,
            confidence=0.9,
        )

        query = AuditQuery(min_confidence=0.8)
        results = ledger.query_decisions(query)

        assert len(results) == 1
        assert results[0].confidence >= 0.8

    def test_rollback_decision(self, ledger):
        """Test rolling back a decision"""
        record = ledger.record_decision(
            decision_type=DecisionType.GOVERNANCE,
            component="PolicyEnforcer",
            trace_id="trace:abc123",
            span_id="span:def456",
            input_summary="Enforce policy",
            output_summary="Policy applied",
            outcome=DecisionOutcome.APPROVED,
            rollback_data={"previous_state": "inactive"},
        )

        assert record.rollback_available is True

        rolled_back = ledger.rollback_decision(
            decision_id=record.decision_id,
            rolled_back_by="admin:user123",
            reason="Policy was incorrect",
        )

        assert rolled_back is not None
        assert rolled_back.rolled_back_at is not None
        assert rolled_back.rolled_back_by == "admin:user123"
        assert rolled_back.metadata.get("rollback_reason") == "Policy was incorrect"

    def test_rollback_unavailable(self, ledger):
        """Test rollback when not available"""
        record = ledger.record_decision(
            decision_type=DecisionType.ROUTING,
            component="FlowController",
            trace_id="trace:abc123",
            span_id="span:def456",
            input_summary="Route task",
            output_summary="Selected agent",
            outcome=DecisionOutcome.APPROVED,
            # No rollback_data provided
        )

        assert record.rollback_available is False

        result = ledger.rollback_decision(
            decision_id=record.decision_id,
            rolled_back_by="admin:user123",
        )

        assert result is None

    def test_verify_evidence_hash(self, ledger):
        """Test evidence hash verification"""
        record = ledger.record_decision(
            decision_type=DecisionType.SAFETY,
            component="SafetyGovernor",
            trace_id="trace:abc123",
            span_id="span:def456",
            input_summary="Check content",
            output_summary="Content safe",
            outcome=DecisionOutcome.APPROVED,
            evidence_hashes=["hash:abc123", "hash:def456"],
        )

        assert ledger.verify_evidence_hash(record.decision_id, "hash:abc123") is True
        assert ledger.verify_evidence_hash(record.decision_id, "hash:def456") is True
        assert ledger.verify_evidence_hash(record.decision_id, "hash:unknown") is False

    def test_get_statistics(self, ledger):
        """Test getting ledger statistics"""
        ledger.record_decision(
            decision_type=DecisionType.ROUTING,
            component="FlowController",
            trace_id="trace:1",
            span_id="span:1",
            input_summary="Route 1",
            output_summary="Result 1",
            outcome=DecisionOutcome.APPROVED,
        )

        ledger.record_decision(
            decision_type=DecisionType.SAFETY,
            component="SafetyGovernor",
            trace_id="trace:2",
            span_id="span:2",
            input_summary="Safety 1",
            output_summary="Result 2",
            outcome=DecisionOutcome.REJECTED,
        )

        stats = ledger.get_statistics()

        assert stats["enabled"] is True
        assert stats["total_decisions"] == 2
        assert stats["memory_records"] == 2
        assert stats["decisions_by_type"]["routing"] == 1
        assert stats["decisions_by_type"]["safety"] == 1
        assert stats["decisions_by_outcome"]["approved"] == 1
        assert stats["decisions_by_outcome"]["rejected"] == 1

    def test_disabled_ledger(self):
        """Test behavior when ledger is disabled"""
        ledger = EvidenceLedger(enabled=False)

        record = ledger.record_decision(
            decision_type=DecisionType.ROUTING,
            component="FlowController",
            trace_id="trace:abc123",
            span_id="span:def456",
            input_summary="Route task",
            output_summary="Selected agent",
            outcome=DecisionOutcome.APPROVED,
        )

        assert record.decision_id.startswith("disabled:")


class TestRetentionPolicy:
    """Tests for RetentionPolicy"""

    def test_default_retention_policy(self):
        """Test default retention policy values"""
        policy = RetentionPolicy()

        assert policy.default_ttl_days == 90
        assert policy.routing_ttl_days == 30
        assert policy.safety_ttl_days == 180
        assert policy.governance_ttl_days == 365

    def test_get_ttl_for_type(self):
        """Test getting TTL for different decision types"""
        policy = RetentionPolicy()

        routing_ttl = policy.get_ttl_for_type(DecisionType.ROUTING)
        assert routing_ttl == 30 * 86400

        safety_ttl = policy.get_ttl_for_type(DecisionType.SAFETY)
        assert safety_ttl == 180 * 86400

        governance_ttl = policy.get_ttl_for_type(DecisionType.GOVERNANCE)
        assert governance_ttl == 365 * 86400

        agent_ttl = policy.get_ttl_for_type(DecisionType.AGENT)
        assert agent_ttl == 90 * 86400  # Default


class TestGlobalSingleton:
    """Tests for global singleton pattern"""

    def test_get_evidence_ledger_singleton(self):
        """Test that get_evidence_ledger returns singleton"""
        reset_evidence_ledger()

        ledger1 = get_evidence_ledger()
        ledger2 = get_evidence_ledger()

        assert ledger1 is ledger2

    def test_reset_evidence_ledger(self):
        """Test resetting the singleton"""
        reset_evidence_ledger()

        ledger1 = get_evidence_ledger()

        reset_evidence_ledger()

        ledger2 = get_evidence_ledger()

        assert ledger1 is not ledger2
