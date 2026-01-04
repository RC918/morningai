"""
Tests for SSOT Telemetry Schema v3

Tests cover:
1. SpanContext creation and hierarchy
2. TelemetryRecordV3 creation and serialization
3. Redaction functionality
4. Version tracking
5. Evidence chain
6. Backward compatibility adapters
"""

import json
from datetime import datetime

from core.telemetry.schema import (
    TelemetryRecordV3,
    SpanContext,
    SpanKind,
    StatusCode,
    RedactionStrategy,
    RedactionInfo,
    VersionInfo,
    EvidenceRef,
    EvidenceKind,
    create_span_context,
    generate_span_id,
    generate_trace_id,
    _compute_hash,
)


class TestSpanContext:
    """Tests for SpanContext"""

    def test_create_span_context_generates_ids(self):
        """create_span_context should generate trace_id and span_id"""
        ctx = create_span_context()

        assert ctx.trace_id is not None
        assert len(ctx.trace_id) == 32
        assert ctx.span_id is not None
        assert len(ctx.span_id) == 16
        assert ctx.parent_span_id is None

    def test_create_span_context_with_trace_id(self):
        """create_span_context should use provided trace_id"""
        ctx = create_span_context(trace_id="abc123")

        assert ctx.trace_id == "abc123"
        assert ctx.span_id is not None

    def test_create_span_context_with_parent(self):
        """create_span_context should set parent_span_id"""
        ctx = create_span_context(trace_id="abc123", parent_span_id="parent123")

        assert ctx.trace_id == "abc123"
        assert ctx.parent_span_id == "parent123"

    def test_span_context_create_child(self):
        """SpanContext.create_child should create child with same trace_id"""
        parent = create_span_context(trace_id="abc123")
        child = parent.create_child()

        assert child.trace_id == parent.trace_id
        assert child.parent_span_id == parent.span_id
        assert child.span_id != parent.span_id

    def test_span_context_to_dict(self):
        """SpanContext.to_dict should serialize correctly"""
        ctx = SpanContext(
            trace_id="trace123",
            span_id="span456",
            parent_span_id="parent789",
        )

        result = ctx.to_dict()

        assert result["trace_id"] == "trace123"
        assert result["span_id"] == "span456"
        assert result["parent_span_id"] == "parent789"

    def test_span_context_to_dict_omits_none_parent(self):
        """SpanContext.to_dict should omit None parent_span_id"""
        ctx = SpanContext(trace_id="trace123", span_id="span456")

        result = ctx.to_dict()

        assert "parent_span_id" not in result


class TestGenerateIds:
    """Tests for ID generation functions"""

    def test_generate_span_id_length(self):
        """generate_span_id should return 16-char hex string"""
        span_id = generate_span_id()

        assert len(span_id) == 16
        assert all(c in "0123456789abcdef" for c in span_id)

    def test_generate_trace_id_length(self):
        """generate_trace_id should return 32-char hex string"""
        trace_id = generate_trace_id()

        assert len(trace_id) == 32
        assert all(c in "0123456789abcdef" for c in trace_id)

    def test_generate_span_id_unique(self):
        """generate_span_id should generate unique IDs"""
        ids = [generate_span_id() for _ in range(100)]

        assert len(set(ids)) == 100


class TestVersionInfo:
    """Tests for VersionInfo"""

    def test_version_info_defaults(self):
        """VersionInfo should have default schema version"""
        info = VersionInfo()

        assert info.schema == "3.0"

    def test_version_info_to_dict(self):
        """VersionInfo.to_dict should serialize correctly"""
        info = VersionInfo(
            schema="3.0",
            code_sha="abc123",
            prompt_template={"id": "review_v1", "version": "1.0"},
            model_config={"provider": "alicloud", "model": "qwen-max"},
        )

        result = info.to_dict()

        assert result["schema"] == "3.0"
        assert result["code_sha"] == "abc123"
        assert result["prompt_template"]["id"] == "review_v1"
        assert result["model_config"]["provider"] == "alicloud"

    def test_version_info_to_dict_omits_none(self):
        """VersionInfo.to_dict should omit None values"""
        info = VersionInfo()

        result = info.to_dict()

        assert "code_sha" not in result
        assert "prompt_template" not in result


class TestRedactionInfo:
    """Tests for RedactionInfo"""

    def test_redaction_info_defaults(self):
        """RedactionInfo should default to HASH strategy"""
        info = RedactionInfo()

        assert info.strategy == RedactionStrategy.HASH

    def test_redaction_info_to_dict(self):
        """RedactionInfo.to_dict should serialize correctly"""
        info = RedactionInfo(
            strategy=RedactionStrategy.HASH,
            fields_hashed=["input", "output"],
            input_hash="abc123",
            output_hash="def456",
        )

        result = info.to_dict()

        assert result["strategy"] == "hash"
        assert result["fields_hashed"] == ["input", "output"]
        assert result["input_hash"] == "abc123"

    def test_redaction_info_to_dict_omits_empty(self):
        """RedactionInfo.to_dict should omit empty lists"""
        info = RedactionInfo()

        result = info.to_dict()

        assert "fields_dropped" not in result
        assert "fields_hashed" not in result


class TestEvidenceRef:
    """Tests for EvidenceRef"""

    def test_evidence_ref_to_dict(self):
        """EvidenceRef.to_dict should serialize correctly"""
        ref = EvidenceRef(
            kind=EvidenceKind.RETRIEVAL_DOC,
            ref="doc-123",
            hash="abc123",
            metadata={"rank": 1, "score": 0.95},
        )

        result = ref.to_dict()

        assert result["kind"] == "retrieval_doc"
        assert result["ref"] == "doc-123"
        assert result["hash"] == "abc123"
        assert result["metadata"]["rank"] == 1

    def test_evidence_ref_to_dict_omits_none(self):
        """EvidenceRef.to_dict should omit None hash"""
        ref = EvidenceRef(kind=EvidenceKind.CI_LOG, ref="log-456")

        result = ref.to_dict()

        assert "hash" not in result
        assert "metadata" not in result


class TestComputeHash:
    """Tests for _compute_hash function"""

    def test_compute_hash_string(self):
        """_compute_hash should hash strings with 128-bit (32 hex chars) output"""
        hash1 = _compute_hash("hello world")
        hash2 = _compute_hash("hello world")

        assert hash1 == hash2
        assert len(hash1) == 32  # 128-bit hash for reduced collision probability

    def test_compute_hash_dict(self):
        """_compute_hash should hash dicts"""
        hash1 = _compute_hash({"key": "value"})
        hash2 = _compute_hash({"key": "value"})

        assert hash1 == hash2

    def test_compute_hash_different_values(self):
        """_compute_hash should produce different hashes for different values"""
        hash1 = _compute_hash("hello")
        hash2 = _compute_hash("world")

        assert hash1 != hash2

    def test_compute_hash_none(self):
        """_compute_hash should return empty string for None"""
        result = _compute_hash(None)

        assert result == ""


class TestTelemetryRecordV3:
    """Tests for TelemetryRecordV3"""

    def test_create_minimal_record(self):
        """TelemetryRecordV3.create should create minimal record"""
        ctx = create_span_context(trace_id="trace123")
        record = TelemetryRecordV3.create(
            name="test.event",
            span_context=ctx,
            component="TestComponent",
        )

        assert record.name == "test.event"
        assert record.component == "TestComponent"
        assert record.span_context.trace_id == "trace123"
        assert record.timestamp is not None
        assert record.timestamp_ms > 0

    def test_create_with_status(self):
        """TelemetryRecordV3.create should set status correctly"""
        ctx = create_span_context()
        record = TelemetryRecordV3.create(
            name="test.event",
            span_context=ctx,
            component="TestComponent",
            status_code=StatusCode.ERROR,
            status_message="Something went wrong",
        )

        assert record.status_code == StatusCode.ERROR
        assert record.status_message == "Something went wrong"

    def test_create_with_metrics(self):
        """TelemetryRecordV3.create should set metrics correctly"""
        ctx = create_span_context()
        record = TelemetryRecordV3.create(
            name="llm.call",
            span_context=ctx,
            component="BaseAgent",
            metrics={"latency_ms": 1500.5, "tokens_in": 500, "tokens_out": 200},
        )

        assert record.metrics["latency_ms"] == 1500.5
        assert record.metrics["tokens_in"] == 500

    def test_create_with_redaction(self):
        """TelemetryRecordV3.create should auto-generate redaction info"""
        ctx = create_span_context()
        record = TelemetryRecordV3.create(
            name="llm.call",
            span_context=ctx,
            component="BaseAgent",
            input_data={"prompt": "secret prompt"},
            output_data={"response": "secret response"},
        )

        assert record.redaction is not None
        assert record.redaction.strategy == RedactionStrategy.HASH
        assert "input" in record.redaction.fields_hashed
        assert "output" in record.redaction.fields_hashed
        assert record.redaction.input_hash is not None
        assert record.redaction.output_hash is not None

    def test_create_without_redaction(self):
        """TelemetryRecordV3.create should skip redaction when disabled"""
        ctx = create_span_context()
        record = TelemetryRecordV3.create(
            name="llm.call",
            span_context=ctx,
            component="BaseAgent",
            input_data={"prompt": "test"},
            redact_inputs=False,
            redact_outputs=False,
        )

        assert record.redaction is None or record.redaction.input_hash is None

    def test_create_with_evidence_refs(self):
        """TelemetryRecordV3.create should set evidence refs"""
        ctx = create_span_context()
        evidence = [
            EvidenceRef(kind=EvidenceKind.DIFF, ref="pr-123"),
            EvidenceRef(kind=EvidenceKind.CI_LOG, ref="log-456"),
        ]
        record = TelemetryRecordV3.create(
            name="agent.decision",
            span_context=ctx,
            component="FlowController",
            evidence_refs=evidence,
        )

        assert len(record.evidence_refs) == 2
        assert record.evidence_refs[0].kind == EvidenceKind.DIFF

    def test_to_dict_schema_version(self):
        """TelemetryRecordV3.to_dict should include schema_version"""
        ctx = create_span_context()
        record = TelemetryRecordV3.create(
            name="test.event",
            span_context=ctx,
            component="TestComponent",
        )

        result = record.to_dict()

        assert result["schema_version"] == "3.0"

    def test_to_dict_span_structure(self):
        """TelemetryRecordV3.to_dict should include span structure"""
        ctx = SpanContext(
            trace_id="trace123",
            span_id="span456",
            parent_span_id="parent789",
        )
        record = TelemetryRecordV3.create(
            name="test.event",
            span_context=ctx,
            component="TestComponent",
        )

        result = record.to_dict()

        assert result["span"]["trace_id"] == "trace123"
        assert result["span"]["span_id"] == "span456"
        assert result["span"]["parent_span_id"] == "parent789"

    def test_to_dict_status_structure(self):
        """TelemetryRecordV3.to_dict should include status structure"""
        ctx = create_span_context()
        record = TelemetryRecordV3.create(
            name="test.event",
            span_context=ctx,
            component="TestComponent",
            status_code=StatusCode.ERROR,
            status_message="Error occurred",
        )

        result = record.to_dict()

        assert result["status"]["code"] == "ERROR"
        assert result["status"]["message"] == "Error occurred"

    def test_to_dict_omits_empty_values(self):
        """TelemetryRecordV3.to_dict should omit empty values"""
        ctx = create_span_context()
        record = TelemetryRecordV3.create(
            name="test.event",
            span_context=ctx,
            component="TestComponent",
        )

        result = record.to_dict()

        assert "agent_id" not in result
        assert "node_name" not in result
        assert "evidence_refs" not in result
        assert "decision_context" not in result

    def test_to_json(self):
        """TelemetryRecordV3.to_json should produce valid JSON"""
        ctx = create_span_context()
        record = TelemetryRecordV3.create(
            name="test.event",
            span_context=ctx,
            component="TestComponent",
            metrics={"latency_ms": 100},
        )

        json_str = record.to_json()
        parsed = json.loads(json_str)

        assert parsed["name"] == "test.event"
        assert parsed["metrics"]["latency_ms"] == 100

    def test_timestamp_is_iso_format(self):
        """TelemetryRecordV3 timestamp should be ISO 8601 format"""
        ctx = create_span_context()
        record = TelemetryRecordV3.create(
            name="test.event",
            span_context=ctx,
            component="TestComponent",
        )

        normalized = record.timestamp.replace('Z', '+00:00')
        parsed = datetime.fromisoformat(normalized)

        assert parsed.tzinfo is not None


class TestTelemetryRecordV3Integration:
    """Integration tests for TelemetryRecordV3"""

    def test_full_record_with_all_fields(self):
        """TelemetryRecordV3 should handle all fields correctly"""
        ctx = create_span_context(trace_id="trace123")
        child_ctx = ctx.create_child()

        record = TelemetryRecordV3.create(
            name="llm.call",
            span_context=child_ctx,
            component="ReviewerAgent",
            kind=SpanKind.CLIENT,
            status_code=StatusCode.OK,
            agent_id="reviewer_agent",
            node_name="reviewer_node",
            epic_tag="EPIC-B",
            versions=VersionInfo(
                code_sha="abc123",
                model_config={"provider": "alicloud", "model": "qwen-max"},
            ),
            evidence_refs=[
                EvidenceRef(kind=EvidenceKind.DIFF, ref="pr-123", hash="diff_hash"),
            ],
            decision_context={"decision_mode": "auto"},
            metrics={"latency_ms": 1500, "tokens_in": 500, "tokens_out": 200},
            attributes={"task_type": "review", "risk_level": "medium"},
            input_data={"prompt": "Review this code"},
            output_data={"review": "LGTM"},
        )

        result = record.to_dict()

        assert result["schema_version"] == "3.0"
        assert result["name"] == "llm.call"
        assert result["span"]["trace_id"] == "trace123"
        assert result["span"]["parent_span_id"] == ctx.span_id
        assert result["component"] == "ReviewerAgent"
        assert result["kind"] == "client"
        assert result["status"]["code"] == "OK"
        assert result["agent_id"] == "reviewer_agent"
        assert result["node_name"] == "reviewer_node"
        assert result["epic_tag"] == "EPIC-B"
        assert result["versions"]["code_sha"] == "abc123"
        assert result["redaction"]["strategy"] == "hash"
        assert len(result["evidence_refs"]) == 1
        assert result["decision_context"]["decision_mode"] == "auto"
        assert result["metrics"]["latency_ms"] == 1500
        assert result["attributes"]["task_type"] == "review"
