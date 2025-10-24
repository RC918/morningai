# Agent MVP Implementation Plan: Week 1-6

**Goal:** Transform MorningAI from template-based to truly autonomous AI agents  
**Timeline:** 6 weeks  
**Success Criteria:** 85%+ automation rate, LLM-powered decision making, multi-agent orchestration

---

## 🎯 Week 1-2: Core AI Integration

### Objective
Replace hard-coded logic with GPT-4 powered intelligence across all agent operations.

---

### Task 1.1: LLM-Powered Planning (Days 1-3)

**Current State:**
```python
# graph.py - Hard-coded planning
def planner(goal:str):
    steps = ["analyze", "patch", "open PR", "check CI"]
    save_text("goal", goal)
    return steps
```

**Target State:**
```python
# llm/planner.py - GPT-4 powered planning
class LLMPlanner:
    def __init__(self, openai_client: OpenAI):
        self.llm = openai_client
        self.model = "gpt-4-turbo-preview"
    
    def plan(self, goal: str, context: dict) -> List[Step]:
        """
        Generate dynamic execution plan using GPT-4
        
        Args:
            goal: User's goal/question
            context: Additional context (repo, previous attempts, etc.)
        
        Returns:
            List of structured steps with tools and validation
        """
        prompt = self._build_planning_prompt(goal, context)
        
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000
        )
        
        plan_data = json.loads(response.choices[0].message.content)
        return self._parse_plan(plan_data)
    
    def _build_planning_prompt(self, goal: str, context: dict) -> str:
        """Build structured prompt for planning"""
        return f"""
        Analyze this development goal and create a detailed execution plan.
        
        **Goal:** {goal}
        
        **Context:**
        - Repository: {context.get('repo', 'unknown')}
        - Previous attempts: {len(context.get('previous_attempts', []))}
        - Available tools: {', '.join(context.get('available_tools', []))}
        - Constraints: {context.get('constraints', 'none')}
        
        **Requirements:**
        1. Break down the goal into concrete, actionable steps
        2. For each step, specify:
           - Action description
           - Required tools (Git, LSP, Shell, Browser, etc.)
           - Success criteria
           - Estimated complexity (low/medium/high)
           - Dependencies on previous steps
        3. Consider edge cases and error handling
        4. Include validation and testing steps
        
        **Output Format (JSON):**
        {{
          "analysis": "Brief analysis of the goal",
          "approach": "High-level approach",
          "steps": [
            {{
              "id": 1,
              "action": "Analyze codebase structure",
              "tools": ["LSP", "FileSystem"],
              "success_criteria": "Identified relevant files and functions",
              "complexity": "low",
              "dependencies": []
            }},
            ...
          ],
          "risks": ["Potential risk 1", "Potential risk 2"],
          "estimated_time": "30 minutes"
        }}
        """
```

**Implementation Steps:**
1. Create `handoff/20250928/40_App/orchestrator/llm/planner.py`
2. Define `PLANNER_SYSTEM_PROMPT` with agent capabilities
3. Implement `_parse_plan()` to convert JSON to Step objects
4. Add validation for plan structure
5. Create unit tests with mock OpenAI responses
6. Integration test with real GPT-4 API

**Success Criteria:**
- [ ] Plans generated dynamically based on goal
- [ ] 90%+ plan quality vs human baseline (manual review)
- [ ] Average planning time <10 seconds
- [ ] Test coverage >80%

**Files to Create:**
- `orchestrator/llm/__init__.py`
- `orchestrator/llm/planner.py`
- `orchestrator/llm/prompts.py`
- `orchestrator/tests/test_llm_planner.py`

---

### Task 1.2: True Code Generation (Days 4-6)

**Current State:**
```python
# llm/faq_generator.py - Template-based with fallback
def generate_faq_content(goal, trace_id, repo_full):
    try:
        # GPT-4 call (but often fails to fallback)
        response = openai.chat.completions.create(...)
        return response.choices[0].message.content
    except:
        # Fallback to template
        return f"# FAQ\n\n## {goal}\n\n..."
```

**Target State:**
```python
# llm/code_generator.py - Robust code generation
class CodeGenerator:
    def __init__(self, openai_client: OpenAI, lsp_client: LSPClient):
        self.llm = openai_client
        self.lsp = lsp_client
        self.model = "gpt-4-turbo-preview"
    
    def generate_fix(
        self,
        error: ErrorContext,
        codebase_context: CodebaseContext
    ) -> CodeFix:
        """
        Generate code fix using GPT-4 with LSP guidance
        
        Args:
            error: Error information (message, stack trace, file, line)
            codebase_context: Relevant code context from LSP
        
        Returns:
            CodeFix with changes, explanation, and tests
        """
        # Step 1: Analyze error with LSP
        relevant_symbols = self.lsp.find_related_symbols(
            error.file,
            error.line
        )
        
        # Step 2: Build context-rich prompt
        prompt = self._build_fix_prompt(error, codebase_context, relevant_symbols)
        
        # Step 3: Generate fix with GPT-4
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": CODE_GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,  # Lower temp for code generation
            max_tokens=3000
        )
        
        fix_data = json.loads(response.choices[0].message.content)
        
        # Step 4: Validate syntax
        if not self._validate_syntax(fix_data['code'], error.language):
            raise CodeGenerationError("Generated code has syntax errors")
        
        # Step 5: Generate tests
        tests = self._generate_tests(fix_data['code'], error)
        
        return CodeFix(
            file=error.file,
            changes=fix_data['changes'],
            explanation=fix_data['explanation'],
            tests=tests,
            confidence=fix_data.get('confidence', 0.8)
        )
    
    def _build_fix_prompt(
        self,
        error: ErrorContext,
        codebase: CodebaseContext,
        symbols: List[Symbol]
    ) -> str:
        """Build comprehensive prompt for code generation"""
        return f"""
        Fix this error in the codebase.
        
        **Error:**
        ```
        {error.message}
        
        File: {error.file}:{error.line}
        Stack trace:
        {error.stack_trace}
        ```
        
        **Current Code:**
        ```{error.language}
        {error.code_snippet}
        ```
        
        **Related Symbols:**
        {self._format_symbols(symbols)}
        
        **Codebase Context:**
        - Language: {codebase.language}
        - Framework: {codebase.framework}
        - Style guide: {codebase.style_guide}
        - Dependencies: {', '.join(codebase.dependencies)}
        
        **Requirements:**
        1. Analyze the error and identify root cause
        2. Generate a fix that:
           - Resolves the error
           - Follows codebase conventions
           - Maintains backward compatibility
           - Includes proper error handling
        3. Provide clear explanation of the fix
        4. Suggest test cases to validate the fix
        
        **Output Format (JSON):**
        {{
          "analysis": "Root cause analysis",
          "changes": [
            {{
              "file": "path/to/file.py",
              "line_start": 42,
              "line_end": 45,
              "old_code": "...",
              "new_code": "...",
              "reason": "Why this change is needed"
            }}
          ],
          "explanation": "Clear explanation of the fix",
          "test_cases": [
            {{
              "description": "Test case 1",
              "code": "def test_...",
              "expected": "Expected behavior"
            }}
          ],
          "confidence": 0.85,
          "risks": ["Potential risk 1"]
        }}
        """
    
    def _validate_syntax(self, code: str, language: str) -> bool:
        """Validate generated code syntax"""
        if language == "python":
            try:
                ast.parse(code)
                return True
            except SyntaxError:
                return False
        elif language == "typescript":
            # Use TypeScript compiler API
            return self._validate_typescript(code)
        return True  # Default to true for unknown languages
    
    def _generate_tests(self, code: str, error: ErrorContext) -> List[TestCase]:
        """Generate test cases for the fix"""
        prompt = f"""
        Generate test cases for this code fix.
        
        **Fixed Code:**
        ```{error.language}
        {code}
        ```
        
        **Original Error:**
        {error.message}
        
        Generate 3-5 test cases that:
        1. Verify the fix resolves the original error
        2. Test edge cases
        3. Ensure no regressions
        
        Return as JSON array of test cases.
        """
        
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)['tests']
```

**Implementation Steps:**
1. Create `orchestrator/llm/code_generator.py`
2. Integrate with LSP client for symbol analysis
3. Implement syntax validation for Python/TypeScript
4. Add test generation capability
5. Create confidence scoring system
6. Add retry logic with exponential backoff
7. Implement caching for similar errors

**Success Criteria:**
- [ ] 85%+ fix success rate (fixes pass CI)
- [ ] Generated code follows style guide
- [ ] Syntax validation catches 100% of invalid code
- [ ] Test generation covers 80%+ of cases
- [ ] Average generation time <30 seconds

**Files to Create:**
- `orchestrator/llm/code_generator.py`
- `orchestrator/llm/syntax_validator.py`
- `orchestrator/llm/test_generator.py`
- `orchestrator/tests/test_code_generator.py`

---

### Task 1.3: Multi-Agent Orchestration (Days 7-10)

**Current State:**
- Single agent (FAQ generator) works in isolation
- No agent selection logic
- No parallel execution
- No agent communication

**Target State:**
```python
# meta_agent_decision_hub.py - Enhanced orchestration
class MetaAgentV2:
    """
    Meta-Agent orchestrates multiple specialized agents
    using OODA loop pattern and LLM-powered decision making
    """
    
    def __init__(
        self,
        openai_client: OpenAI,
        session_store: SessionStore
    ):
        self.llm = openai_client
        self.session_store = session_store
        self.model = "gpt-4-turbo-preview"
        
        # Register specialized agents
        self.agents = {
            "dev": DevAgent(openai_client, session_store),
            "ops": OpsAgent(openai_client, session_store),
            "pm": PMAgent(openai_client, session_store),
            "growth": GrowthStrategist(openai_client, session_store),
            "faq": FAQAgent(openai_client, session_store)
        }
        
        # Agent capabilities registry
        self.capabilities = {
            "dev": ["bug_fix", "code_review", "refactor", "test_generation"],
            "ops": ["incident_response", "monitoring", "scaling", "deployment"],
            "pm": ["task_planning", "prioritization", "estimation"],
            "growth": ["strategy", "analytics", "optimization"],
            "faq": ["documentation", "knowledge_base"]
        }
    
    def execute_ooda_loop(
        self,
        goal: str,
        context: dict,
        session_id: str
    ) -> ExecutionResult:
        """
        Execute OODA loop with multi-agent coordination
        
        OODA Phases:
        1. Observe: Gather information from all agents
        2. Orient: Analyze with GPT-4
        3. Decide: Select agent(s) and action(s)
        4. Act: Execute with coordination
        """
        # Load or create session
        session = self.session_store.load(session_id)
        if not session:
            session = self._create_session(session_id, goal, context)
        
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations and session.status == "active":
            # OBSERVE: Gather current state
            observations = self._observe(session, context)
            
            # ORIENT: Analyze with GPT-4
            analysis = self._orient(observations, session)
            
            # DECIDE: Select agent and action
            decision = self._decide(analysis, session)
            
            # ACT: Execute decision
            result = self._act(decision, session)
            
            # Update session
            session.add_observation(observations)
            session.add_decision(decision)
            session.add_action(result)
            self.session_store.save(session)
            
            # Check if goal achieved
            if result.status == "completed":
                session.status = "completed"
                break
            elif result.status == "escalate":
                session.status = "escalated"
                break
            
            iteration += 1
        
        return ExecutionResult(
            session_id=session_id,
            status=session.status,
            iterations=iteration,
            final_result=result
        )
    
    def _observe(self, session: Session, context: dict) -> Observations:
        """
        Observe phase: Gather information from all relevant agents
        """
        observations = Observations()
        
        # Query each agent for their current state
        for agent_type, agent in self.agents.items():
            if self._is_agent_relevant(agent_type, session.goal):
                agent_obs = agent.observe(context)
                observations.add(agent_type, agent_obs)
        
        # Add system observations
        observations.add("system", {
            "iteration": session.iteration,
            "previous_actions": len(session.actions),
            "attempted_solutions": len(session.attempted_solutions),
            "time_elapsed": self._calculate_elapsed_time(session)
        })
        
        return observations
    
    def _orient(self, observations: Observations, session: Session) -> Analysis:
        """
        Orient phase: Analyze observations with GPT-4
        """
        prompt = f"""
        Analyze the current state of this development task.
        
        **Goal:** {session.goal}
        **Iteration:** {session.iteration}/{session.max_iterations}
        
        **Observations:**
        {observations.to_json()}
        
        **Previous Decisions:**
        {json.dumps(session.decisions[-3:], indent=2)}
        
        **Previous Actions:**
        {json.dumps(session.actions[-3:], indent=2)}
        
        **Attempted Solutions:**
        {json.dumps(session.attempted_solutions, indent=2)}
        
        Provide:
        1. Current understanding of the situation
        2. Progress assessment (0-100%)
        3. Blockers or challenges identified
        4. Recommended next steps
        5. Which agent(s) should handle next action
        
        Output as JSON.
        """
        
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": META_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1500
        )
        
        analysis_data = json.loads(response.choices[0].message.content)
        return Analysis.from_dict(analysis_data)
    
    def _decide(self, analysis: Analysis, session: Session) -> Decision:
        """
        Decide phase: Select agent and action based on analysis
        """
        # Check for escalation conditions
        if session.iteration >= session.max_iterations:
            return Decision(
                agent="human",
                action="escalate",
                reasoning="Max iterations reached",
                confidence=1.0
            )
        
        # Use GPT-4 for decision making
        prompt = f"""
        Based on this analysis, decide the next action.
        
        **Analysis:**
        {analysis.to_json()}
        
        **Available Agents:**
        {json.dumps(self.capabilities, indent=2)}
        
        **Session State:**
        - Iteration: {session.iteration}
        - Previous agent: {session.actions[-1].agent if session.actions else 'none'}
        - Success rate: {self._calculate_success_rate(session)}
        
        Decide:
        1. Which agent should handle this?
        2. What specific action should they take?
        3. Should multiple agents work in parallel?
        4. What are the success criteria?
        
        Output as JSON.
        """
        
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a meta-agent coordinator."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=1000
        )
        
        decision_data = json.loads(response.choices[0].message.content)
        return Decision.from_dict(decision_data)
    
    def _act(self, decision: Decision, session: Session) -> ActionResult:
        """
        Act phase: Execute decision with selected agent(s)
        """
        if decision.agent == "human":
            return self._escalate_to_human(decision, session)
        
        # Get selected agent
        agent = self.agents.get(decision.agent)
        if not agent:
            raise ValueError(f"Unknown agent: {decision.agent}")
        
        # Execute action
        try:
            result = agent.execute(
                action=decision.action,
                context=decision.context,
                session=session
            )
            
            return ActionResult(
                agent=decision.agent,
                action=decision.action,
                status="success" if result.success else "failure",
                result=result.data,
                error=result.error
            )
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", extra={
                "agent": decision.agent,
                "action": decision.action,
                "session_id": session.session_id
            })
            
            return ActionResult(
                agent=decision.agent,
                action=decision.action,
                status="error",
                result=None,
                error=str(e)
            )
    
    def _escalate_to_human(
        self,
        decision: Decision,
        session: Session
    ) -> ActionResult:
        """
        Escalate to human via HITL (Telegram)
        """
        hitl_client = HITLClient(os.getenv("TELEGRAM_BOT_TOKEN"))
        
        message = f"""
        🚨 **Agent Escalation Required**
        
        **Task:** {session.goal}
        **Session:** {session.session_id}
        **Iterations:** {session.iteration}
        
        **Reason:** {decision.reasoning}
        
        **Context:**
        {self._format_session_summary(session)}
        
        **Options:**
        1. Provide guidance
        2. Take over manually
        3. Abort task
        
        Reply with your decision.
        """
        
        approval = hitl_client.request_approval(
            message=message,
            timeout=3600  # 1 hour
        )
        
        return ActionResult(
            agent="human",
            action="escalate",
            status="escalated",
            result={"approval": approval},
            error=None
        )
```

**Implementation Steps:**
1. Enhance `meta_agent_decision_hub.py` with OODA loop
2. Create agent registry and capabilities system
3. Implement agent selection logic with GPT-4
4. Add parallel execution support (asyncio)
5. Create agent communication protocol
6. Implement HITL escalation via Telegram
7. Add comprehensive logging and tracing

**Success Criteria:**
- [ ] 3+ agents orchestrated successfully
- [ ] Agent selection accuracy >90%
- [ ] Parallel execution reduces time by 40%
- [ ] HITL escalation works end-to-end
- [ ] Test coverage >80%

**Files to Create/Modify:**
- `meta_agent_decision_hub.py` (enhance existing)
- `orchestrator/coordination/agent_registry.py`
- `orchestrator/coordination/parallel_executor.py`
- `orchestrator/hitl/telegram_client.py`
- `orchestrator/tests/test_meta_agent_v2.py`

---

## 📊 Week 1-2 Success Metrics

### Quantitative Metrics
- [ ] LLM planning accuracy: 90%+
- [ ] Code generation success rate: 85%+
- [ ] Multi-agent coordination: 3+ agents
- [ ] Test coverage: 80%+
- [ ] Average task completion time: <5 minutes

### Qualitative Metrics
- [ ] Plans are dynamic and context-aware
- [ ] Generated code follows style guide
- [ ] Agents collaborate effectively
- [ ] HITL escalation is smooth
- [ ] System is observable and debuggable

---

## 🔄 Week 3-4: Session State & Memory

### Objective
Implement persistent session management and learning loop for continuous improvement.

---

### Task 2.1: Persistent Session Management (Days 11-13)

**Implementation:**
1. Enhance existing `dev_agent_v2.py` session state
2. Add PostgreSQL long-term memory
3. Create session recovery mechanism
4. Implement session analytics

**Files:**
- `orchestrator/persistence/session_manager.py`
- `orchestrator/persistence/postgres_store.py`
- `orchestrator/tests/test_session_persistence.py`

---

### Task 2.2: Knowledge Graph Indexing (Days 14-16)

**Implementation:**
1. Create knowledge graph schema in PostgreSQL
2. Implement semantic indexing with pgvector
3. Add pattern storage and retrieval
4. Create similarity search

**Files:**
- `orchestrator/memory/knowledge_graph.py`
- `orchestrator/memory/semantic_index.py`
- `orchestrator/tests/test_knowledge_graph.py`

---

### Task 2.3: Learning Loop (Days 17-20)

**Implementation:**
1. Collect feedback from CI results
2. Store successful patterns
3. Implement pattern matching
4. Enable continuous improvement

**Files:**
- `orchestrator/learning/feedback_collector.py`
- `orchestrator/learning/pattern_matcher.py`
- `orchestrator/tests/test_learning_loop.py`

---

## 🔄 Week 5-6: Closed-Loop Validation

### Objective
Complete end-to-end automation chains with quality gates and HITL integration.

---

### Task 3.1: Complete Automation Chains (Days 21-25)

**Chains to Implement:**
1. **Bug Fix Chain:** Detection → Analysis → Fix → Test → PR → Merge
2. **Incident Chain:** Alert → Diagnose → Fix → Deploy → Postmortem
3. **Feature Chain:** Request → Plan → Implement → Test → Deploy

---

### Task 3.2: Quality Gates (Days 26-28)

**Implementation:**
1. Automated code review with GPT-4
2. Test generation and execution
3. Security scanning integration
4. Performance validation

---

### Task 3.3: HITL Integration (Days 29-30)

**Implementation:**
1. Telegram bot for approvals
2. Confidence scoring system
3. Escalation thresholds
4. Manual override capability

---

## 📈 Overall Success Criteria (Week 6)

### Agent Performance
- [ ] 85%+ automation rate
- [ ] 85%+ fix success rate
- [ ] <5 minute average task time
- [ ] 3+ task types automated

### Code Quality
- [ ] 80%+ test coverage
- [ ] 95%+ CI success rate
- [ ] A rating on code quality
- [ ] Zero security vulnerabilities

### System Reliability
- [ ] 99.9% uptime
- [ ] <1 second API response time
- [ ] Zero data loss
- [ ] Complete audit trail

---

## 🚀 Next Steps After Week 6

1. **Week 7-10:** Ops Agent Enhancement
2. **Week 11-14:** Security & Governance
3. **Week 15-20:** Commercialization (Phase 9)

---

*Document Version: 1.0*  
*Last Updated: 2025-10-24*  
*Owner: CTO*
