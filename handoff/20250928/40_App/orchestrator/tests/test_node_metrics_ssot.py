"""
Tests for node_metrics decorator SSOT Telemetry v3 integration (Issue #3578)

Tests cover:
1. Feature flag control (ENABLE_SSOT_TELEMETRY)
2. Span hierarchy (parent-child relationships via current_span_id)
3. TelemetryRecordV3 emission
4. Backward compatibility (existing metrics still work)
"""

import time
from unittest.mock import MagicMock, patch


class TestNodeMetricsSSOTTelemetry:
    """Tests for node_metrics decorator SSOT telemetry integration"""

    def test_ssot_telemetry_disabled_by_default(self):
        """node_metrics should not emit SSOT spans when feature flag is disabled"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = False

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak'):
                    from langgraph_orchestrator import node_metrics

                    @node_metrics("test_node")
                    def test_func(state, success):
                        success[0] = True
                        return state

                    state = {"trace_id": "test-trace-123"}
                    result = test_func(state)

                    mock_metrics.record_node_start.assert_called_once()
                    mock_metrics.record_node_complete.assert_called_once()
                    assert "current_span_id" not in result or result.get("current_span_id") is None

    def test_ssot_telemetry_enabled_creates_span(self):
        """node_metrics should create SSOT span when feature flag is enabled"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = True

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak'):
                    from langgraph_orchestrator import node_metrics

                    @node_metrics("test_node")
                    def test_func(state, success):
                        success[0] = True
                        return state

                    state = {"trace_id": "test-trace-123"}
                    result = test_func(state)

                    assert result.get("current_span_id") is not None
                    assert len(result["current_span_id"]) == 16

    def test_ssot_telemetry_span_hierarchy(self):
        """node_metrics should establish parent-child span relationships"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = True

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak'):
                    from langgraph_orchestrator import node_metrics

                    @node_metrics("parent_node")
                    def parent_func(state, success):
                        success[0] = True
                        return state

                    @node_metrics("child_node")
                    def child_func(state, success):
                        success[0] = True
                        return state

                    state = {"trace_id": "test-trace-123"}
                    state = parent_func(state)
                    parent_span_id = state.get("current_span_id")

                    state = child_func(state)
                    child_span_id = state.get("current_span_id")

                    assert parent_span_id is not None
                    assert child_span_id is not None
                    assert parent_span_id != child_span_id

    def test_ssot_telemetry_emits_record(self):
        """node_metrics should emit TelemetryRecordV3 on completion"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = True

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak'):
                    with patch('core.telemetry.TelemetryRecordV3') as mock_record_class:
                        mock_record = MagicMock()
                        mock_record_class.create.return_value = mock_record

                        from langgraph_orchestrator import node_metrics

                        @node_metrics("test_node")
                        def test_func(state, success):
                            success[0] = True
                            return state

                        state = {"trace_id": "test-trace-123"}
                        test_func(state)

                        mock_record.emit.assert_called_once()

    def test_ssot_telemetry_records_success_status(self):
        """node_metrics should record OK status on success"""
        emitted_records = []

        def capture_emit(self):
            emitted_records.append(self)

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = True

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak'):
                    from core.telemetry import TelemetryRecordV3, StatusCode
                    original_emit = TelemetryRecordV3.emit
                    TelemetryRecordV3.emit = capture_emit

                    try:
                        from langgraph_orchestrator import node_metrics

                        @node_metrics("test_node")
                        def test_func(state, success):
                            success[0] = True
                            return state

                        state = {"trace_id": "test-trace-123"}
                        test_func(state)

                        assert len(emitted_records) == 1
                        assert emitted_records[0].status_code == StatusCode.OK
                    finally:
                        TelemetryRecordV3.emit = original_emit

    def test_ssot_telemetry_records_error_status(self):
        """node_metrics should record ERROR status on failure"""
        emitted_records = []

        def capture_emit(self):
            emitted_records.append(self)

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = True

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak'):
                    from core.telemetry import TelemetryRecordV3, StatusCode
                    original_emit = TelemetryRecordV3.emit
                    TelemetryRecordV3.emit = capture_emit

                    try:
                        from langgraph_orchestrator import node_metrics

                        @node_metrics("test_node")
                        def test_func(state, success):
                            return state

                        state = {"trace_id": "test-trace-123"}
                        test_func(state)

                        assert len(emitted_records) == 1
                        assert emitted_records[0].status_code == StatusCode.ERROR
                    finally:
                        TelemetryRecordV3.emit = original_emit

    def test_ssot_telemetry_records_latency(self):
        """node_metrics should record latency_ms in metrics"""
        emitted_records = []

        def capture_emit(self):
            emitted_records.append(self)

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = True

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak'):
                    from core.telemetry import TelemetryRecordV3
                    original_emit = TelemetryRecordV3.emit
                    TelemetryRecordV3.emit = capture_emit

                    try:
                        from langgraph_orchestrator import node_metrics

                        @node_metrics("test_node")
                        def test_func(state, success):
                            time.sleep(0.01)
                            success[0] = True
                            return state

                        state = {"trace_id": "test-trace-123"}
                        test_func(state)

                        assert len(emitted_records) == 1
                        assert "latency_ms" in emitted_records[0].metrics
                        assert emitted_records[0].metrics["latency_ms"] >= 10
                    finally:
                        TelemetryRecordV3.emit = original_emit

    def test_ssot_telemetry_preserves_trace_id(self):
        """node_metrics should preserve trace_id in span context"""
        emitted_records = []

        def capture_emit(self):
            emitted_records.append(self)

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = True

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak'):
                    from core.telemetry import TelemetryRecordV3
                    original_emit = TelemetryRecordV3.emit
                    TelemetryRecordV3.emit = capture_emit

                    try:
                        from langgraph_orchestrator import node_metrics

                        @node_metrics("test_node")
                        def test_func(state, success):
                            success[0] = True
                            return state

                        state = {"trace_id": "my-custom-trace-id"}
                        test_func(state)

                        assert len(emitted_records) == 1
                        assert emitted_records[0].span_context.trace_id == "my-custom-trace-id"
                    finally:
                        TelemetryRecordV3.emit = original_emit

    def test_ssot_telemetry_backward_compatible(self):
        """node_metrics should still work with existing metrics when SSOT is enabled"""
        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = True

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak') as mock_log_peak:
                    from langgraph_orchestrator import node_metrics

                    @node_metrics("test_node")
                    def test_func(state, success):
                        success[0] = True
                        return state

                    state = {"trace_id": "test-trace-123"}
                    test_func(state)

                    mock_metrics.record_node_start.assert_called_once_with(
                        "test_node", "test-trace-123"
                    )
                    mock_metrics.record_node_complete.assert_called_once()
                    mock_log_peak.assert_called_once()


class TestSpanTreeStructure:
    """Tests for span tree structure validation (Issue #3578 Phase 1)"""

    def test_span_tree_three_level_hierarchy(self):
        """Verify span tree structure with 3 levels of nesting"""
        span_ids = []

        def capture_span_id(state):
            span_ids.append(state.get("current_span_id"))

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = True

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak'):
                    from langgraph_orchestrator import node_metrics

                    @node_metrics("level1")
                    def level1_func(state, success):
                        capture_span_id(state)
                        success[0] = True
                        return state

                    @node_metrics("level2")
                    def level2_func(state, success):
                        capture_span_id(state)
                        success[0] = True
                        return state

                    @node_metrics("level3")
                    def level3_func(state, success):
                        capture_span_id(state)
                        success[0] = True
                        return state

                    state = {"trace_id": "test-trace-123"}
                    state = level1_func(state)
                    state = level2_func(state)
                    state = level3_func(state)

                    assert len(span_ids) == 3
                    assert all(span_id is not None for span_id in span_ids)
                    assert len(set(span_ids)) == 3

    def test_span_tree_sibling_spans(self):
        """Verify sibling spans have same parent but different span_ids"""
        emitted_records = []

        def capture_emit(self):
            emitted_records.append(self)

        with patch('langgraph_orchestrator.settings') as mock_settings:
            mock_settings.enable_ssot_telemetry = True

            with patch('langgraph_orchestrator._get_metrics') as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                with patch('langgraph_orchestrator.log_resource_peak'):
                    from core.telemetry import TelemetryRecordV3
                    original_emit = TelemetryRecordV3.emit
                    TelemetryRecordV3.emit = capture_emit

                    try:
                        from langgraph_orchestrator import node_metrics

                        @node_metrics("parent")
                        def parent_func(state, success):
                            success[0] = True
                            return state

                        @node_metrics("sibling1")
                        def sibling1_func(state, success):
                            success[0] = True
                            return state

                        @node_metrics("sibling2")
                        def sibling2_func(state, success):
                            success[0] = True
                            return state

                        state = {"trace_id": "test-trace-123"}
                        state = parent_func(state)
                        parent_span_id = state.get("current_span_id")

                        state_copy = dict(state)
                        state_copy["current_span_id"] = parent_span_id
                        sibling1_func(state_copy)

                        state_copy2 = dict(state)
                        state_copy2["current_span_id"] = parent_span_id
                        sibling2_func(state_copy2)

                        assert len(emitted_records) == 3

                        sibling1_record = emitted_records[1]
                        sibling2_record = emitted_records[2]

                        assert sibling1_record.span_context.parent_span_id == parent_span_id
                        assert sibling2_record.span_context.parent_span_id == parent_span_id
                        assert sibling1_record.span_context.span_id != sibling2_record.span_context.span_id
                    finally:
                        TelemetryRecordV3.emit = original_emit
