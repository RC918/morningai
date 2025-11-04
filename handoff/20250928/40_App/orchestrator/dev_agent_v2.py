"""
Dev_Agent Phase 2: OODA Loop with Session State

Implements the OODA (Observe, Orient, Decide, Act) loop pattern for autonomous
development agents with persistent session state management.

OODA Loop Phases:
1. Observe: Gather information about current state, errors, and context
2. Orient: Analyze information and understand the situation  
3. Decide: Determine best course of action
4. Act: Execute the decided action

Session State:
- Maintains conversation history across iterations
- Tracks attempted solutions to avoid repetition
- Stores context from codebase analysis
- Persists to Redis for recovery after restarts
"""
import os
import json
import logging
from typing import Dict, List, Optional, TypedDict
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum

from redis import Redis
from openai import OpenAI

logger = logging.getLogger(__name__)

class OODAPhase(str, Enum):
    """OODA loop phases"""
    OBSERVE = "observe"
    ORIENT = "orient"
    DECIDE = "decide"
    ACT = "act"

class ActionType(str, Enum):
    """Types of actions the agent can take"""
    ANALYZE_CODE = "analyze_code"
    FIX_ERROR = "fix_error"
    RUN_TESTS = "run_tests"
    CREATE_PR = "create_pr"
    WAIT_CI = "wait_ci"
    COMPLETE = "complete"
    ESCALATE = "escalate"

@dataclass
class SessionState:
    """
    Persistent session state for Dev_Agent
    
    Attributes:
        session_id: Unique identifier for this session
        task_id: Associated task ID
        goal: Original user goal
        current_phase: Current OODA phase
        iteration: Current iteration number
        max_iterations: Maximum iterations before escalation
        observations: List of observations from each cycle
        decisions: List of decisions made
        actions: List of actions taken with results
        attempted_solutions: Set of solution approaches tried
        context: Additional context from codebase analysis
        conversation_history: LLM conversation history
        created_at: Session creation timestamp
        updated_at: Last update timestamp
        status: Session status (active, paused, completed, failed)
    """
    session_id: str
    task_id: str
    goal: str
    current_phase: OODAPhase = OODAPhase.OBSERVE
    iteration: int = 0
    max_iterations: int = 10
    observations: List[Dict] = None
    decisions: List[Dict] = None
    actions: List[Dict] = None
    attempted_solutions: List[str] = None
    context: Dict = None
    conversation_history: List[Dict] = None
    created_at: str = None
    updated_at: str = None
    status: str = "active"
    
    def __post_init__(self):
        if self.observations is None:
            self.observations = []
        if self.decisions is None:
            self.decisions = []
        if self.actions is None:
            self.actions = []
        if self.attempted_solutions is None:
            self.attempted_solutions = []
        if self.context is None:
            self.context = {}
        if self.conversation_history is None:
            self.conversation_history = []
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['current_phase'] = self.current_phase.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SessionState':
        """Create from dictionary"""
        data['current_phase'] = OODAPhase(data.get('current_phase', 'observe'))
        return cls(**data)
    
    def add_observation(self, observation: str, data: Dict = None):
        """Add observation to session"""
        self.observations.append({
            "iteration": self.iteration,
            "phase": self.current_phase.value,
            "observation": observation,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def add_decision(self, decision: str, reasoning: str, action_type: ActionType):
        """Add decision to session"""
        self.decisions.append({
            "iteration": self.iteration,
            "decision": decision,
            "reasoning": reasoning,
            "action_type": action_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def add_action(self, action_type: ActionType, result: Dict, success: bool):
        """Add action and its result to session"""
        self.actions.append({
            "iteration": self.iteration,
            "action_type": action_type.value,
            "result": result,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def mark_solution_attempted(self, solution_key: str):
        """Mark a solution approach as attempted to avoid repetition"""
        if solution_key not in self.attempted_solutions:
            self.attempted_solutions.append(solution_key)

class SessionStore:
    """Redis-backed session state storage"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 86400
    
    def save(self, state: SessionState):
        """Save session state to Redis"""
        key = f"dev_agent:session:{state.session_id}"
        data = json.dumps(state.to_dict())
        self.redis.setex(key, self.ttl, data)
        logger.info(f"Saved session state", extra={
            "operation": "session_save",
            "session_id": state.session_id,
            "iteration": state.iteration,
            "phase": state.current_phase.value
        })
    
    def load(self, session_id: str) -> Optional[SessionState]:
        """Load session state from Redis"""
        key = f"dev_agent:session:{session_id}"
        data = self.redis.get(key)
        if data:
            state_dict = json.loads(data)
            state = SessionState.from_dict(state_dict)
            logger.info(f"Loaded session state", extra={
                "operation": "session_load",
                "session_id": session_id,
                "iteration": state.iteration,
                "phase": state.current_phase.value
            })
            return state
        return None
    
    def delete(self, session_id: str):
        """Delete session state from Redis"""
        key = f"dev_agent:session:{session_id}"
        self.redis.delete(key)
        logger.info(f"Deleted session state", extra={
            "operation": "session_delete",
            "session_id": session_id
        })

class DevAgentV2:
    """
    Dev_Agent Phase 2 with OODA Loop and Session State
    """
    
    def __init__(
        self,
        openai_client: OpenAI,
        session_store: SessionStore,
        model: str = "gpt-4-turbo-preview"
    ):
        self.openai = openai_client
        self.session_store = session_store
        self.model = model
    
    def observe(self, state: SessionState) -> SessionState:
        """
        Observe phase: Gather current state information
        
        Observations include:
        - Current task status
        - Error messages if any
        - Test results
        - CI status
        - Codebase analysis
        """
        logger.info(f"OODA: Observe", extra={
            "session_id": state.session_id,
            "iteration": state.iteration
        })
        
        observation = f"Iteration {state.iteration}: Observing task '{state.goal}'"
        
        state.add_observation(
            observation=observation,
            data={
                "iteration": state.iteration,
                "previous_actions": len(state.actions),
                "attempted_solutions": len(state.attempted_solutions)
            }
        )
        
        state.current_phase = OODAPhase.ORIENT
        self.session_store.save(state)
        
        return state
    
    def orient(self, state: SessionState) -> SessionState:
        """
        Orient phase: Analyze observations and understand situation
        
        Uses GPT-4 to:
        - Analyze error patterns
        - Identify root causes
        - Consider context from previous attempts
        - Generate understanding of current state
        """
        logger.info(f"OODA: Orient", extra={
            "session_id": state.session_id,
            "iteration": state.iteration
        })
        
        recent_observations = state.observations[-3:] if state.observations else []
        recent_actions = state.actions[-3:] if state.actions else []
        
        orientation_prompt = f"""You are analyzing the current state of a development task.

Goal: {state.goal}
Iteration: {state.iteration}/{state.max_iterations}

Recent Observations:
{json.dumps(recent_observations, indent=2)}

Recent Actions:
{json.dumps(recent_actions, indent=2)}

Attempted Solutions:
{json.dumps(state.attempted_solutions, indent=2)}

Analyze the situation and provide:
1. Current understanding of the problem
2. What's working and what's not
3. Patterns or blockers identified
4. Recommendations for next steps

Keep response concise and actionable."""
        
        try:
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert development agent analyzing task progress."},
                    {"role": "user", "content": orientation_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            
            state.context["orientation_analysis"] = analysis
            state.conversation_history.append({
                "role": "assistant",
                "content": analysis,
                "phase": "orient"
            })
            
        except Exception as e:
            logger.error(f"Orient phase GPT-4 call failed: {e}", extra={
                "session_id": state.session_id
            })
            state.context["orientation_analysis"] = "Analysis failed, proceeding with basic heuristics"
        
        state.current_phase = OODAPhase.DECIDE
        self.session_store.save(state)
        
        return state
    
    def decide(self, state: SessionState) -> SessionState:
        """
        Decide phase: Determine best action based on orientation
        
        Decision factors:
        - Current iteration vs max iterations
        - Success rate of previous actions
        - Complexity of attempted solutions
        - CI/test status
        
        Possible decisions:
        - Continue with code fix
        - Run tests
        - Create PR
        - Wait for CI
        - Escalate to human
        """
        logger.info(f"OODA: Decide", extra={
            "session_id": state.session_id,
            "iteration": state.iteration
        })
        
        if state.iteration >= state.max_iterations:
            action_type = ActionType.ESCALATE
            decision = "Max iterations reached, escalating to human"
            reasoning = f"Attempted {state.iteration} iterations without success"
        elif len(state.actions) == 0:
            action_type = ActionType.ANALYZE_CODE
            decision = "Start by analyzing codebase"
            reasoning = "First iteration, need to understand codebase structure"
        else:
            last_action = state.actions[-1] if state.actions else None
            if last_action and last_action.get("success"):
                action_type = ActionType.CREATE_PR
                decision = "Previous action succeeded, create PR"
                reasoning = "Changes appear successful"
            else:
                action_type = ActionType.FIX_ERROR
                decision = "Previous action failed, try different approach"
                reasoning = "Need to address remaining issues"
        
        state.add_decision(
            decision=decision,
            reasoning=reasoning,
            action_type=action_type
        )
        
        state.current_phase = OODAPhase.ACT
        self.session_store.save(state)
        
        return state
    
    def act(self, state: SessionState) -> SessionState:
        """
        Act phase: Execute the decided action
        
        Executes action and captures result for next observation phase
        """
        logger.info(f"OODA: Act", extra={
            "session_id": state.session_id,
            "iteration": state.iteration
        })
        
        last_decision = state.decisions[-1] if state.decisions else None
        if not last_decision:
            logger.warning(f"No decision found for action phase")
            state.current_phase = OODAPhase.OBSERVE
            state.iteration += 1
            self.session_store.save(state)
            return state
        
        action_type = ActionType(last_decision["action_type"])
        
        if action_type == ActionType.ESCALATE:
            state.status = "escalated"
            state.add_action(
                action_type=action_type,
                result={"message": "Task escalated to human review"},
                success=False
            )
        elif action_type == ActionType.COMPLETE:
            state.status = "completed"
            state.add_action(
                action_type=action_type,
                result={"message": "Task completed successfully"},
                success=True
            )
        else:
            state.add_action(
                action_type=action_type,
                result={"message": f"Simulated execution of {action_type.value}"},
                success=True
            )
        
        state.current_phase = OODAPhase.OBSERVE
        state.iteration += 1
        self.session_store.save(state)
        
        return state
    
    def run_ooda_loop(
        self,
        session_id: str,
        task_id: str,
        goal: str,
        max_iterations: int = 10
    ) -> SessionState:
        """
        Run the complete OODA loop for a development task
        
        Args:
            session_id: Unique session identifier
            task_id: Associated task ID
            goal: Development goal/question
            max_iterations: Maximum OODA cycles before escalation
        
        Returns:
            Final session state
        """
        logger.info(f"Starting OODA loop", extra={
            "session_id": session_id,
            "task_id": task_id,
            "goal": goal[:50],
            "max_iterations": max_iterations
        })
        
        state = self.session_store.load(session_id)
        if not state:
            state = SessionState(
                session_id=session_id,
                task_id=task_id,
                goal=goal,
                max_iterations=max_iterations
            )
            self.session_store.save(state)
        
        while state.status == "active" and state.iteration < max_iterations:
            if state.current_phase == OODAPhase.OBSERVE:
                state = self.observe(state)
            elif state.current_phase == OODAPhase.ORIENT:
                state = self.orient(state)
            elif state.current_phase == OODAPhase.DECIDE:
                state = self.decide(state)
            elif state.current_phase == OODAPhase.ACT:
                state = self.act(state)
            
            if state.status in ["completed", "escalated", "failed"]:
                break
        
        logger.info(f"OODA loop completed", extra={
            "session_id": session_id,
            "final_status": state.status,
            "iterations": state.iteration,
            "actions_taken": len(state.actions)
        })
        
        return state

def create_dev_agent_v2(redis_client: Redis) -> DevAgentV2:
    """
    Factory function to create Dev_Agent V2 instance
    
    Args:
        redis_client: Redis client for session storage
    
    Returns:
        Configured DevAgentV2 instance
    """
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    session_store = SessionStore(redis_client)
    
    return DevAgentV2(
        openai_client=openai_client,
        session_store=session_store,
        model=os.getenv("DEV_AGENT_MODEL", "gpt-4-turbo-preview")
    )
