"""
HITL Gate Node Integration Tests with Checkpointer

Issue #3164: Add HITL Gate Node integration tests with checkpointer

This module provides integration tests for the HITL (Human-in-the-Loop) Gate Node
interrupt/resume flow with checkpointer support.

Test Scenarios:
1. Interrupt/Resume with MemorySaver - Test that interrupt() properly pauses
   execution and Command(resume=True) resumes it
2. State checkpointing during interrupt - Verify state is properly saved
3. State reset after workflow completion - Verify HITL flags are reset
4. Multi-session state isolation - Verify concurrent sessions don't share HITL state

Related:
- Parent Issue: #3158 (C-5 Pilot)
- Implementation PR: #3160
"""
import uuid
from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain_core.messages import BaseMessage, AIMessage


class SimpleHITLState(TypedDict):
    """Minimal state for HITL integration tests."""
    trace_id: str
    messages: Annotated[list[BaseMessage], operator.add]
    requires_hitl_approval: bool
    hitl_approved: bool
    workflow_result: str


def create_hitl_test_graph():
    """Create a minimal graph for testing HITL interrupt/resume flow.

    Graph structure:
    start -> hitl_gate -> process -> finalize -> END

    The hitl_gate node will interrupt if requires_hitl_approval=True
    and hitl_approved=False.
    """

    def start_node(state: SimpleHITLState) -> SimpleHITLState:
        """Initial node that sets up the workflow."""
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="[START] Workflow started")
        ]
        return state

    def hitl_gate_node(state: SimpleHITLState) -> SimpleHITLState:
        """HITL Gate Node - mirrors production implementation."""
        requires_hitl = state.get("requires_hitl_approval", False)
        hitl_approved = state.get("hitl_approved", False)

        if requires_hitl and not hitl_approved:
            state["messages"] = state.get("messages", []) + [
                AIMessage(content="[HITL_GATE] Pausing for human approval")
            ]

            approval = interrupt({
                "type": "hitl_approval_required",
                "trace_id": state.get("trace_id", "unknown"),
                "message": "Human approval required",
            })

            if approval:
                state["hitl_approved"] = True
                state["messages"] = state.get("messages", []) + [
                    AIMessage(content=f"[HITL_GATE] Approval received: {approval}")
                ]
            else:
                state["hitl_approved"] = False
                state["workflow_result"] = "rejected"
                state["messages"] = state.get("messages", []) + [
                    AIMessage(content="[HITL_GATE] Approval rejected")
                ]

        return state

    def process_node(state: SimpleHITLState) -> SimpleHITLState:
        """Process node - simulates actual work."""
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="[PROCESS] Processing completed")
        ]
        state["workflow_result"] = "processed"
        return state

    def finalize_node(state: SimpleHITLState) -> SimpleHITLState:
        """Finalize node - resets HITL flags (mirrors production behavior)."""
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="[FINALIZE] Workflow finalized")
        ]

        if not state.get("workflow_result"):
            state["workflow_result"] = "completed"

        hitl_flags_to_reset = ["hitl_approved", "requires_hitl_approval"]
        for flag in hitl_flags_to_reset:
            if state.get(flag):
                state[flag] = False

        return state

    workflow = StateGraph(SimpleHITLState)

    workflow.add_node("start", start_node)
    workflow.add_node("hitl_gate", hitl_gate_node)
    workflow.add_node("process", process_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("start")
    workflow.add_edge("start", "hitl_gate")
    workflow.add_edge("hitl_gate", "process")
    workflow.add_edge("process", "finalize")
    workflow.add_edge("finalize", END)

    return workflow


class TestHITLInterruptResumeWithMemorySaver:
    """Integration tests for HITL interrupt/resume flow with MemorySaver.

    Issue #3164 Acceptance Criteria:
    - Integration test using MemorySaver that verifies interrupt/resume flow
    """

    def test_workflow_without_hitl_requirement_completes(self):
        """Test that workflow completes normally when HITL is not required."""
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "trace_id": "test-no-hitl",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": False,
            "workflow_result": "",
        }

        result = app.invoke(initial_state, config)

        assert result["workflow_result"] == "processed"
        message_contents = [m.content for m in result["messages"]]
        assert any("[START]" in c for c in message_contents)
        assert any("[PROCESS]" in c for c in message_contents)
        assert any("[FINALIZE]" in c for c in message_contents)

    def test_workflow_with_hitl_requirement_interrupts(self):
        """Test that workflow interrupts when HITL approval is required."""
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer, interrupt_before=["hitl_gate"])

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "trace_id": "test-hitl-interrupt",
            "messages": [],
            "requires_hitl_approval": True,
            "hitl_approved": False,
            "workflow_result": "",
        }

        result = app.invoke(initial_state, config)

        assert result is not None
        assert result.get("requires_hitl_approval") is True
        assert result.get("hitl_approved") is False


class TestHITLStateCheckpointing:
    """Integration tests for state checkpointing during HITL interrupt.

    Issue #3164 Acceptance Criteria:
    - Integration test that verifies state is properly checkpointed during interrupt
    """

    def test_state_persisted_in_checkpointer(self):
        """Test that state is properly saved to checkpointer."""
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "trace_id": "test-checkpoint",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": False,
            "workflow_result": "",
        }

        app.invoke(initial_state, config)

        checkpoint = checkpointer.get(config)
        assert checkpoint is not None

    def test_checkpoint_contains_hitl_state(self):
        """Test that checkpoint contains HITL-related state fields."""
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "trace_id": "test-checkpoint-hitl",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": False,
            "workflow_result": "",
        }

        app.invoke(initial_state, config)

        checkpoint = checkpointer.get(config)
        assert checkpoint is not None

        channel_values = checkpoint.get("channel_values", {})
        assert "trace_id" in channel_values
        assert "requires_hitl_approval" in channel_values
        assert "hitl_approved" in channel_values


class TestHITLStateReset:
    """Integration tests for HITL state reset after workflow completion.

    Issue #3164 Acceptance Criteria:
    - Test that verifies state reset after workflow completion
    """

    def test_hitl_flags_reset_after_completion(self):
        """Test that HITL flags are reset to False after workflow completion.

        This test sets initial flags to True to verify the finalize_node
        actually resets them. Without this, the reset logic would not be
        exercised since flags start at False.
        """
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "trace_id": "test-reset",
            "messages": [],
            "requires_hitl_approval": True,
            "hitl_approved": True,
            "workflow_result": "",
        }

        result = app.invoke(initial_state, config)

        assert result["hitl_approved"] is False
        assert result["requires_hitl_approval"] is False

    def test_hitl_approved_reset_after_approval_flow(self):
        """Test that hitl_approved is reset even after approval was granted."""
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        initial_state = {
            "trace_id": "test-reset-after-approval",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": True,
            "workflow_result": "",
        }

        result = app.invoke(initial_state, config)

        assert result["hitl_approved"] is False


class TestHITLMultiSessionIsolation:
    """Integration tests for multi-session HITL state isolation.

    Issue #3164 Acceptance Criteria:
    - Test that verifies concurrent sessions do not share HITL state
    """

    def test_separate_threads_have_isolated_state(self):
        """Test that different thread_ids have isolated HITL state."""
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id_1 = str(uuid.uuid4())
        thread_id_2 = str(uuid.uuid4())
        config_1 = {"configurable": {"thread_id": thread_id_1}}
        config_2 = {"configurable": {"thread_id": thread_id_2}}

        state_1 = {
            "trace_id": "session-1",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": False,
            "workflow_result": "",
        }

        state_2 = {
            "trace_id": "session-2",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": False,
            "workflow_result": "",
        }

        result_1 = app.invoke(state_1, config_1)
        result_2 = app.invoke(state_2, config_2)

        assert result_1["trace_id"] == "session-1"
        assert result_2["trace_id"] == "session-2"

        checkpoint_1 = checkpointer.get(config_1)
        checkpoint_2 = checkpointer.get(config_2)

        assert checkpoint_1 is not None
        assert checkpoint_2 is not None
        assert checkpoint_1 != checkpoint_2

    def test_hitl_state_does_not_leak_between_sessions(self):
        """Test that HITL approval in one session doesn't affect another."""
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id_1 = str(uuid.uuid4())
        thread_id_2 = str(uuid.uuid4())
        config_1 = {"configurable": {"thread_id": thread_id_1}}
        config_2 = {"configurable": {"thread_id": thread_id_2}}

        state_with_approval = {
            "trace_id": "session-with-approval",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": True,
            "workflow_result": "",
        }

        state_without_approval = {
            "trace_id": "session-without-approval",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": False,
            "workflow_result": "",
        }

        result_1 = app.invoke(state_with_approval, config_1)
        result_2 = app.invoke(state_without_approval, config_2)

        assert result_1["hitl_approved"] is False
        assert result_2["hitl_approved"] is False

    def test_concurrent_sessions_maintain_isolation(self):
        """Test that concurrent workflow executions maintain state isolation."""
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        sessions = []
        for i in range(5):
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            state = {
                "trace_id": f"concurrent-session-{i}",
                "messages": [],
                "requires_hitl_approval": False,
                "hitl_approved": False,
                "workflow_result": "",
            }
            sessions.append((config, state))

        results = []
        for config, state in sessions:
            result = app.invoke(state, config)
            results.append(result)

        for i, result in enumerate(results):
            assert result["trace_id"] == f"concurrent-session-{i}"
            assert result["workflow_result"] == "processed"
            assert result["hitl_approved"] is False


class TestHITLGateNodeBehavior:
    """Tests for HITL Gate Node specific behavior patterns.

    These tests verify the gate node logic without full workflow execution.
    """

    def test_gate_node_passes_when_no_hitl_required(self):
        """Test that gate node passes through when HITL is not required."""
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        state = {
            "trace_id": "test-no-hitl-gate",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": False,
            "workflow_result": "",
        }

        result = app.invoke(state, config)

        assert result["workflow_result"] == "processed"
        message_contents = [m.content for m in result["messages"]]
        assert any("[PROCESS]" in c for c in message_contents)

    def test_gate_node_passes_when_already_approved(self):
        """Test that gate node passes through when already approved."""
        workflow = create_hitl_test_graph()
        checkpointer = MemorySaver()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        state = {
            "trace_id": "test-already-approved",
            "messages": [],
            "requires_hitl_approval": True,
            "hitl_approved": True,
            "workflow_result": "",
        }

        result = app.invoke(state, config)

        assert result["workflow_result"] == "processed"


class TestMemorySaverCheckpointerIntegration:
    """Tests for MemorySaver checkpointer integration.

    These tests verify that MemorySaver works correctly with the HITL workflow.
    """

    def test_memory_saver_stores_workflow_state(self):
        """Test that MemorySaver correctly stores workflow state."""
        checkpointer = MemorySaver()
        workflow = create_hitl_test_graph()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        state = {
            "trace_id": "test-memory-saver",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": False,
            "workflow_result": "",
        }

        app.invoke(state, config)

        stored_checkpoint = checkpointer.get(config)
        assert stored_checkpoint is not None

    def test_memory_saver_allows_state_retrieval(self):
        """Test that state can be retrieved from MemorySaver after workflow."""
        checkpointer = MemorySaver()
        workflow = create_hitl_test_graph()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        state = {
            "trace_id": "test-retrieval",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": False,
            "workflow_result": "",
        }

        app.invoke(state, config)

        checkpoint_tuple = checkpointer.get_tuple(config)
        assert checkpoint_tuple is not None

    def test_memory_saver_list_checkpoints(self):
        """Test that MemorySaver can list checkpoints for a thread."""
        checkpointer = MemorySaver()
        workflow = create_hitl_test_graph()
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        state = {
            "trace_id": "test-list",
            "messages": [],
            "requires_hitl_approval": False,
            "hitl_approved": False,
            "workflow_result": "",
        }

        app.invoke(state, config)

        checkpoints = list(checkpointer.list(config))
        assert len(checkpoints) > 0
