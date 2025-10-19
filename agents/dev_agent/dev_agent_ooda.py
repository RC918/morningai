#!/usr/bin/env python3
"""
Dev_Agent OODA Loop Implementation
Phase 1 Week 3-4: OODA cycle with session persistence
Week 3: Basic OODA cycle
Week 4: Session state, decision trace, error handling, path whitelist
"""
import logging
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from langgraph.graph import StateGraph, END
from agents.dev_agent.tools.git_tool import GitTool
from agents.dev_agent.tools.ide_tool import IDETool
from agents.dev_agent.tools.filesystem_tool import FileSystemTool
from agents.dev_agent.error_handler import ErrorCode, create_error
from agents.dev_agent.persistence.session_state import SessionStateManager
from agents.dev_agent.refactoring.refactoring_engine import RefactoringEngine
from agents.dev_agent.testing.test_generator import TestGenerator
from agents.dev_agent.error_diagnosis.error_diagnoser import ErrorDiagnoser
from agents.dev_agent.performance.performance_analyzer import PerformanceAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DevAgentState(TypedDict):
    """State schema for Dev_Agent OODA loop (Week 4 enhanced)"""
    task: str
    task_priority: str
    context: Dict[str, Any]
    observations: List[str]
    orientation: Dict[str, Any]
    strategy: Optional[str]
    actions: List[Dict[str, Any]]
    action_results: List[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    iteration: int
    max_iterations: int
    session_id: Optional[str]
    decision_trace: List[Dict[str, Any]]


@dataclass
class ObservationResult:
    """Result from Observe phase"""
    timestamp: datetime
    codebase_structure: Dict[str, Any]
    relevant_files: List[str]
    issues_identified: List[str]
    context_summary: str


@dataclass
class OrientationResult:
    """Result from Orient phase"""
    timestamp: datetime
    task_analysis: str
    complexity_assessment: str
    required_tools: List[str]
    potential_strategies: List[Dict[str, Any]]
    risk_factors: List[str]


@dataclass
class DecisionResult:
    """Result from Decide phase"""
    timestamp: datetime
    selected_strategy: str
    action_plan: List[Dict[str, Any]]
    expected_outcome: str
    confidence: float


class DevAgentOODA:
    """Dev_Agent OODA Loop Implementation (Week 4 enhanced)"""

    MAX_STEPS = 100

    def __init__(
        self,
        sandbox_endpoint: str,
        github_token: Optional[str] = None,
        enable_persistence: bool = True,
        session_manager: Optional[SessionStateManager] = None
    ):
        self.sandbox_endpoint = sandbox_endpoint
        self.git_tool = GitTool(sandbox_endpoint, github_token)
        self.ide_tool = IDETool(sandbox_endpoint)
        self.fs_tool = FileSystemTool(sandbox_endpoint)
        self.enable_persistence = enable_persistence
        self.session_manager = session_manager if enable_persistence else None
        self.refactoring_engine = RefactoringEngine()
        self.test_generator = TestGenerator()
        self.error_diagnoser = ErrorDiagnoser()
        self.performance_analyzer = PerformanceAnalyzer()
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create LangGraph workflow for OODA cycle (Week 4: added max_steps)"""
        workflow = StateGraph(DevAgentState)

        workflow.add_node("observe", self._observe_node)
        workflow.add_node("orient", self._orient_node)
        workflow.add_node("decide", self._decide_node)
        workflow.add_node("act", self._act_node)

        workflow.set_entry_point("observe")
        workflow.add_edge("observe", "orient")
        workflow.add_edge("orient", "decide")
        workflow.add_edge("decide", "act")

        workflow.add_conditional_edges(
            "act",
            self._should_continue,
            {
                "continue": "observe",
                "end": END
            }
        )

        return workflow.compile(
            debug=False,
            checkpointer=None,
            interrupt_before=None,
            interrupt_after=None
        )

    async def _observe_node(self, state: DevAgentState) -> DevAgentState:
        """
        Observe phase: Explore codebase and identify relevant context (Week 4: improved data collection)
        """
        logger.info(f"[Observe] Starting observation for task: {state['task']}")

        observations = []
        context_data = {}

        try:
            tree_result = await self.ide_tool.get_file_tree('.')
            if tree_result.get('success'):
                tree_output = tree_result.get('stdout', '')
                observations.append(f"Codebase structure: {tree_output[:500]}")
                context_data['file_tree'] = tree_output[:1000]
            else:
                logger.warning(f"[Observe] Failed to get file tree: {tree_result.get('error')}")

            list_result = await self.fs_tool.list_files('.', pattern='*.py')
            if list_result.get('success'):
                files_output = list_result.get('stdout', '')
                observations.append(f"Python files found: {files_output[:300]}")
                context_data['python_files'] = files_output[:500]
            else:
                logger.warning(f"[Observe] Failed to list files: {list_result.get('error')}")

            keywords = self._extract_keywords(state['task'])
            search_results = {}
            for keyword in keywords[:3]:
                search_result = await self.ide_tool.search_code(keyword, file_pattern='*.py')
                if search_result.get('success'):
                    search_output = search_result.get('stdout', '')
                    if search_output and search_output.strip():
                        observations.append(f"Found '{keyword}' in: {search_output[:200]}")
                        search_results[keyword] = search_output[:300]
            context_data['search_results'] = search_results

            git_status = await self.git_tool.status()
            if git_status.get('success'):
                status_output = git_status.get('stdout', '')
                observations.append(f"Git status: {status_output[:200]}")
                context_data['git_status'] = status_output[:500]
            else:
                logger.warning(f"[Observe] Failed to get git status: {git_status.get('error')}")

            state['observations'] = observations
            state['context']['last_observe_time'] = datetime.now().isoformat()
            state['context']['observation_data'] = context_data

            decision_entry = {
                'phase': 'observe',
                'observations_count': len(observations),
                'keywords_searched': keywords,
                'context_data_keys': list(context_data.keys()),
                'timestamp': datetime.now().isoformat()
            }
            state['decision_trace'].append(decision_entry)

            if self.session_manager and state.get('session_id'):
                self.session_manager.add_decision_trace(
                    state['session_id'],
                    'observe',
                    decision_entry
                )

            logger.info(f"[Observe] Collected {len(observations)} observations")

        except Exception as e:
            logger.error(f"[Observe] Error: {e}")
            error = create_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"Observe phase failed: {str(e)}",
                hint="Check tool availability and network connectivity"
            )
            state['error'] = error['error']

        return state

    async def _orient_node(self, state: DevAgentState) -> DevAgentState:
        """
        Orient phase: Analyze observations and formulate strategies (Week 4: added decision trace)
        """
        logger.info("[Orient] Analyzing observations and formulating strategies")

        try:
            observations = state.get('observations', [])
            task = state['task']

            complexity = self._assess_complexity(task, observations)

            required_tools = self._identify_required_tools(task)

            strategies = self._generate_strategies(task, observations, required_tools)

            orientation = {
                'task_analysis': f"Task type: {self._classify_task(task)}",
                'complexity': complexity,
                'required_tools': required_tools,
                'strategies': strategies,
                'risk_factors': self._identify_risks(task, complexity)
            }

            state['orientation'] = orientation
            state['context']['last_orient_time'] = datetime.now().isoformat()

            decision_entry = {
                'phase': 'orient',
                'complexity': complexity,
                'required_tools': required_tools,
                'strategies_count': len(strategies),
                'risk_factors': orientation['risk_factors'],
                'timestamp': datetime.now().isoformat()
            }
            state['decision_trace'].append(decision_entry)

            if self.session_manager and state.get('session_id'):
                self.session_manager.add_decision_trace(
                    state['session_id'],
                    'orient',
                    decision_entry
                )

            logger.info(f"[Orient] Generated {len(strategies)} potential strategies")

        except Exception as e:
            logger.error(f"[Orient] Error: {e}")
            error = create_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"Orient phase failed: {str(e)}"
            )
            state['error'] = error['error']

        return state

    async def _decide_node(self, state: DevAgentState) -> DevAgentState:
        """
        Decide phase: Select best strategy and create action plan (Week 4: added decision trace)
        """
        logger.info("[Decide] Selecting strategy and creating action plan")

        try:
            orientation = state.get('orientation', {})
            strategies = orientation.get('strategies', [])

            best_strategy = self._select_best_strategy(strategies, state['task_priority'])

            action_plan = self._create_action_plan(best_strategy, state['task'])

            state['strategy'] = best_strategy['name']
            state['actions'] = action_plan
            state['context']['last_decide_time'] = datetime.now().isoformat()

            decision_entry = {
                'phase': 'decide',
                'selected_strategy': best_strategy['name'],
                'strategy_confidence': best_strategy.get('confidence', 0),
                'action_count': len(action_plan),
                'timestamp': datetime.now().isoformat()
            }
            state['decision_trace'].append(decision_entry)

            if self.session_manager and state.get('session_id'):
                self.session_manager.add_decision_trace(
                    state['session_id'],
                    'decide',
                    decision_entry
                )

            logger.info(f"[Decide] Selected strategy: {best_strategy['name']}")
            logger.info(f"[Decide] Action plan has {len(action_plan)} steps")

        except Exception as e:
            logger.error(f"[Decide] Error: {e}")
            error = create_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"Decide phase failed: {str(e)}"
            )
            state['error'] = error['error']

        return state

    async def _act_node(self, state: DevAgentState) -> DevAgentState:
        """
        Act phase: Execute action plan and collect results (Week 4: added decision trace)
        """
        logger.info("[Act] Executing action plan")

        action_results = []

        try:
            actions = state.get('actions', [])

            for idx, action in enumerate(actions):
                logger.info(f"[Act] Executing action {idx + 1}/{len(actions)}: {action['type']}")

                result = await self._execute_action(action)
                action_results.append(result)

                if self.session_manager and state.get('session_id'):
                    self.session_manager.add_to_context_window(
                        state['session_id'],
                        {
                            'action_type': action['type'],
                            'action_index': idx,
                            'success': result.get('success', False),
                            'result': result
                        }
                    )

                if not result.get('success') and action.get('critical', False):
                    logger.error(f"[Act] Critical action failed: {action['type']}")
                    break

            state['action_results'] = action_results
            state['iteration'] += 1
            state['context']['last_act_time'] = datetime.now().isoformat()

            all_success = all(r.get('success', False) for r in action_results)
            if all_success:
                state['result'] = {
                    'success': True,
                    'message': 'All actions completed successfully',
                    'actions_executed': len(action_results)
                }
            else:
                failed_actions = [r for r in action_results if not r.get('success')]
                state['result'] = {
                    'success': False,
                    'message': f'{len(failed_actions)} actions failed',
                    'failures': failed_actions
                }

            decision_entry = {
                'phase': 'act',
                'actions_executed': len(action_results),
                'success_count': sum(1 for r in action_results if r.get('success')),
                'iteration': state['iteration'],
                'timestamp': datetime.now().isoformat()
            }
            state['decision_trace'].append(decision_entry)

            if self.session_manager and state.get('session_id'):
                self.session_manager.add_decision_trace(
                    state['session_id'],
                    'act',
                    decision_entry
                )

            logger.info(f"[Act] Completed iteration {state['iteration']}")

        except Exception as e:
            logger.error(f"[Act] Error: {e}")
            error = create_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"Act phase failed: {str(e)}"
            )
            state['error'] = error['error']
            state['result'] = {'success': False, 'error': error['error']}

        return state

    def _should_continue(self, state: DevAgentState) -> str:
        """Determine whether to continue OODA loop or end (Week 4: added max_steps check)"""
        if state.get('result', {}).get('success'):
            return "end"
        if state.get('error'):
            return "end"
        if state['iteration'] >= state['max_iterations']:
            logger.warning(f"[OODA] Max iterations ({state['max_iterations']}) reached")
            error = create_error(
                ErrorCode.MAX_ITERATIONS_EXCEEDED,
                f"Maximum iterations ({state['max_iterations']}) exceeded",
                hint="Consider breaking down the task into smaller subtasks"
            )
            state['error'] = error['error']
            return "end"

        total_steps = state['iteration'] * 4
        if total_steps >= self.MAX_STEPS:
            logger.error(f"[OODA] Max steps ({self.MAX_STEPS}) exceeded")
            error = create_error(
                ErrorCode.MAX_ITERATIONS_EXCEEDED,
                f"Maximum workflow steps ({self.MAX_STEPS}) exceeded",
                hint="Workflow may be stuck in a loop"
            )
            state['error'] = error['error']
            return "end"

        return "continue"

    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action using appropriate tool (Week 4: added missing actions)"""
        action_type = action['type']

        try:
            if action_type == 'git_status':
                return await self.git_tool.status()
            elif action_type == 'git_clone':
                return await self.git_tool.clone(action['repo_url'], action.get('destination'))
            elif action_type == 'git_commit':
                return await self.git_tool.commit(action['message'], action.get('files'))
            elif action_type == 'git_push':
                return await self.git_tool.push(action.get('remote', 'origin'), action.get('branch'))
            elif action_type == 'git_create_pr':
                return await self.git_tool.create_pr(
                    action['repo'], action['title'], action['body'],
                    action['head'], action.get('base', 'main')
                )
            elif action_type == 'git_diff':
                return await self.git_tool.diff(action.get('file_path'))
            elif action_type == 'git_create_branch':
                return await self.git_tool.create_branch(action['branch_name'], action.get('base'))
            elif action_type == 'read_file':
                return await self.fs_tool.read_file(action['file_path'])
            elif action_type == 'write_file':
                return await self.fs_tool.write_file(action['file_path'], action['content'])
            elif action_type == 'list_files':
                return await self.fs_tool.list_files(action.get('directory', '.'), action.get('pattern'))
            elif action_type == 'search_files':
                return await self.fs_tool.search_files(action['query'], action.get('directory', '.'))
            elif action_type == 'search_code':
                return await self.ide_tool.search_code(action['query'], action.get('file_pattern'))
            elif action_type == 'get_file_tree':
                return await self.ide_tool.get_file_tree(action.get('path', '.'))
            elif action_type == 'format_code':
                return await self.ide_tool.format_code(action['file_path'], action.get('language', 'python'))
            elif action_type == 'run_linter':
                return await self.ide_tool.run_linter(action['file_path'], action.get('language', 'python'))
            elif action_type == 'open_file':
                return await self.ide_tool.open_file(action['file_path'])
            elif action_type == 'analyze_code_quality':
                return self.refactoring_engine.analyze_code(action['code'])
            elif action_type == 'apply_refactoring':
                from agents.dev_agent.refactoring.refactoring_engine import RefactoringSuggestion, RefactoringType
                
                suggestion = action['suggestion']
                if isinstance(suggestion, dict):
                    line = suggestion.get('line', 1)
                    location = suggestion.get('location', {
                        'start_line': line,
                        'end_line': line,
                        'column': 0
                    })
                    if 'start_line' not in location and 'line' in suggestion:
                        location['start_line'] = suggestion['line']
                        location['end_line'] = suggestion['line']
                    
                    suggestion = RefactoringSuggestion(
                        type=RefactoringType(suggestion.get('type', 'rename')),
                        severity=suggestion.get('severity', 'medium'),
                        description=suggestion.get('description', ''),
                        location=location,
                        code_snippet=suggestion.get('original_code', ''),
                        suggested_code=suggestion.get('suggested_code'),
                        confidence=suggestion.get('confidence', 0.8),
                        impact=suggestion.get('impact', 'medium')
                    )
                
                return self.refactoring_engine.apply_refactoring(
                    action['code'],
                    suggestion
                )
            elif action_type == 'verify_refactoring':
                return self.refactoring_engine.verify_refactoring(
                    action['original_code'],
                    action['refactored_code']
                )
            elif action_type == 'generate_tests':
                return self.test_generator.generate_tests(
                    action['code'],
                    action.get('file_path', 'unknown')
                )
            elif action_type == 'diagnose_error':
                return self.error_diagnoser.diagnose_error(
                    action['error_message'],
                    action.get('code_context')
                )
            elif action_type == 'analyze_performance':
                return self.performance_analyzer.analyze_code(action['code'])
            else:
                return create_error(
                    ErrorCode.INVALID_ACTION,
                    f'Unknown action type: {action_type}',
                    hint="Check action type spelling and available actions"
                )
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return create_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"Failed to execute {action_type}: {str(e)}",
                hint="Check action parameters and tool availability"
            )

    def _extract_keywords(self, task: str) -> List[str]:
        """Extract relevant keywords from task description"""
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = task.lower().split()
        return [w for w in words if len(w) > 3 and w not in common_words][:5]

    def _assess_complexity(self, task: str, observations: List[str]) -> str:
        """Assess task complexity based on task and observations"""
        task_lower = task.lower()
        if any(word in task_lower for word in ['refactor', 'redesign', 'migrate']):
            return 'high'
        elif any(word in task_lower for word in ['fix', 'update', 'modify']):
            return 'medium'
        else:
            return 'low'

    def _identify_required_tools(self, task: str) -> List[str]:
        """Identify which tools are needed for the task"""
        task_lower = task.lower()
        tools = []

        if any(word in task_lower for word in ['git', 'commit', 'pr', 'branch']):
            tools.append('git')
        if any(word in task_lower for word in ['file', 'read', 'write', 'create']):
            tools.append('filesystem')
        if any(word in task_lower for word in ['format', 'lint', 'code', 'search']):
            tools.append('ide')

        return tools if tools else ['git', 'filesystem', 'ide']

    def _classify_task(self, task: str) -> str:
        """Classify task type"""
        task_lower = task.lower()
        if 'bug' in task_lower or 'fix' in task_lower:
            return 'bug_fix'
        elif 'feature' in task_lower or 'add' in task_lower:
            return 'feature_addition'
        elif 'refactor' in task_lower:
            return 'refactoring'
        elif 'test' in task_lower:
            return 'testing'
        else:
            return 'general_development'

    def _generate_strategies(self, task: str, observations: List[str], required_tools: List[str]) -> List[Dict[str, Any]]:
        """Generate potential strategies for completing the task"""
        strategies = []

        strategies.append({
            'name': 'direct_implementation',
            'description': 'Directly implement the required changes',
            'tools': required_tools,
            'risk': 'low',
            'confidence': 0.8
        })

        if self._assess_complexity(task, observations) in ['medium', 'high']:
            strategies.append({
                'name': 'exploratory_then_implement',
                'description': 'First explore codebase, then implement',
                'tools': ['ide'] + required_tools,
                'risk': 'medium',
                'confidence': 0.6
            })

        return strategies

    def _identify_risks(self, task: str, complexity: str) -> List[str]:
        """Identify potential risks"""
        risks = []

        if complexity == 'high':
            risks.append('High complexity may require multiple iterations')

        task_lower = task.lower()
        if 'migration' in task_lower or 'refactor' in task_lower:
            risks.append('May affect multiple parts of codebase')
        if 'database' in task_lower or 'schema' in task_lower:
            risks.append('Database changes require careful review')

        return risks

    def _select_best_strategy(self, strategies: List[Dict[str, Any]], priority: str) -> Dict[str, Any]:
        """Select best strategy based on confidence and priority"""
        if not strategies:
            return {
                'name': 'default_strategy',
                'description': 'Default fallback strategy',
                'tools': ['git', 'filesystem', 'ide']
            }

        return max(strategies, key=lambda s: s.get('confidence', 0))

    def _create_action_plan(self, strategy: Dict[str, Any], task: str) -> List[Dict[str, Any]]:
        """Create detailed action plan from strategy (Week 4: improved logic)"""
        actions = []
        task_type = self._classify_task(task)
        task_lower = task.lower()

        if 'git' in strategy.get('tools', []):
            actions.append({
                'type': 'git_status',
                'description': 'Check current git status',
                'critical': False
            })

        if task_type == 'bug_fix':
            if any(word in task_lower for word in ['file', 'module', 'class']):
                actions.append({
                    'type': 'search_code',
                    'query': self._extract_keywords(task)[0] if self._extract_keywords(task) else 'error',
                    'description': 'Search for bug location in code',
                    'critical': True
                })
            actions.append({
                'type': 'list_files',
                'directory': '.',
                'pattern': '*.py',
                'description': 'List relevant files',
                'critical': False
            })

        elif task_type == 'feature_addition':
            actions.append({
                'type': 'get_file_tree',
                'path': '.',
                'description': 'Get codebase structure',
                'critical': False
            })
            actions.append({
                'type': 'list_files',
                'directory': '.',
                'pattern': '*.py',
                'description': 'List existing Python files',
                'critical': False
            })

        elif task_type == 'refactoring':
            keywords = self._extract_keywords(task)
            if keywords:
                actions.append({
                    'type': 'search_code',
                    'query': keywords[0],
                    'description': f"Search for '{keywords[0]}' in codebase",
                    'critical': True
                })

        elif task_type == 'testing':
            actions.append({
                'type': 'list_files',
                'directory': '.',
                'pattern': 'test_*.py',
                'description': 'List test files',
                'critical': False
            })

        if not actions:
            actions.append({
                'type': 'get_file_tree',
                'path': '.',
                'description': 'Explore codebase structure',
                'critical': False
            })

        return actions

    async def execute_task(
        self,
        task: str,
        priority: str = "medium",
        max_iterations: int = 3,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a development task using OODA loop (Week 4: added session persistence)

        Args:
            task: Task description
            priority: Task priority (critical/high/medium/low)
            max_iterations: Maximum OODA iterations
            session_id: Optional session ID for persistence

        Returns:
            Dict with task execution results
        """
        if self.session_manager and not session_id:
            session_result = self.session_manager.create_session(task, priority)
            if session_result['success']:
                session_id = session_result['session_id']
                logger.info(f"[DevAgentOODA] Created session {session_id}")
            else:
                logger.warning("[DevAgentOODA] Failed to create session, continuing without persistence")

        initial_state = DevAgentState(
            task=task,
            task_priority=priority,
            context={
                'start_time': datetime.now().isoformat(),
                'sandbox_endpoint': self.sandbox_endpoint
            },
            observations=[],
            orientation={},
            strategy=None,
            actions=[],
            action_results=[],
            result=None,
            error=None,
            iteration=0,
            max_iterations=max_iterations,
            session_id=session_id,
            decision_trace=[]
        )

        logger.info(f"[DevAgentOODA] Starting task execution: {task}")

        try:
            final_state = await self.graph.ainvoke(initial_state)

            if self.session_manager and session_id:
                self.session_manager.update_session(
                    session_id,
                    {
                        'result': final_state.get('result'),
                        'decision_trace': final_state.get('decision_trace', []),
                        'completed_at': datetime.now().isoformat()
                    }
                )

            return final_state
        except Exception as e:
            logger.error(f"[DevAgentOODA] Task execution failed: {e}")
            error = create_error(
                ErrorCode.UNKNOWN_ERROR,
                f"Task execution failed: {str(e)}",
                hint="Check logs for more details",
                task=task
            )
            return {
                'success': False,
                'error': error['error'],
                'task': task,
                'session_id': session_id
            }


def create_dev_agent_ooda(
    sandbox_endpoint: str,
    github_token: Optional[str] = None,
    enable_persistence: bool = False
) -> DevAgentOODA:
    """
    Factory function to create Dev_Agent OODA instance (Week 4: added persistence support)

    Args:
        sandbox_endpoint: Sandbox API endpoint
        github_token: Optional GitHub token for PR operations
        enable_persistence: Enable Redis session persistence
    """
    session_manager = None
    if enable_persistence:
        try:
            from agents.dev_agent.persistence import get_session_manager
            session_manager = get_session_manager()
            logger.info("Session persistence enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize session manager: {e}")
            logger.warning("Continuing without persistence")

    return DevAgentOODA(
        sandbox_endpoint,
        github_token,
        enable_persistence=enable_persistence,
        session_manager=session_manager
    )
