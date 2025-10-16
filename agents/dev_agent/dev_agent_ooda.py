#!/usr/bin/env python3
"""
Dev_Agent OODA Loop Implementation
Phase 1 Week 3: Basic OODA cycle for development tasks
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DevAgentState(TypedDict):
    """State schema for Dev_Agent OODA loop"""
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
    """Dev_Agent OODA Loop Implementation"""

    def __init__(self, sandbox_endpoint: str, github_token: Optional[str] = None):
        self.sandbox_endpoint = sandbox_endpoint
        self.git_tool = GitTool(sandbox_endpoint, github_token)
        self.ide_tool = IDETool(sandbox_endpoint)
        self.fs_tool = FileSystemTool(sandbox_endpoint)
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create LangGraph workflow for OODA cycle"""
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

        return workflow.compile()

    async def _observe_node(self, state: DevAgentState) -> DevAgentState:
        """
        Observe phase: Explore codebase and identify relevant context
        """
        logger.info(f"[Observe] Starting observation for task: {state['task']}")

        observations = []

        try:
            tree_result = await self.ide_tool.get_file_tree('.')
            if tree_result.get('success'):
                observations.append(f"Codebase structure: {tree_result.get('stdout', '')[:500]}")

            keywords = self._extract_keywords(state['task'])
            for keyword in keywords:
                search_result = await self.ide_tool.search_code(keyword)
                if search_result.get('success'):
                    observations.append(f"Found '{keyword}' in: {search_result.get('stdout', '')[:200]}")

            git_status = await self.git_tool.status()
            if git_status.get('success'):
                observations.append(f"Git status: {git_status.get('stdout', '')[:200]}")

            state['observations'] = observations
            state['context']['last_observe_time'] = datetime.now().isoformat()

            logger.info(f"[Observe] Collected {len(observations)} observations")

        except Exception as e:
            logger.error(f"[Observe] Error: {e}")
            state['error'] = str(e)

        return state

    async def _orient_node(self, state: DevAgentState) -> DevAgentState:
        """
        Orient phase: Analyze observations and formulate strategies
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

            logger.info(f"[Orient] Generated {len(strategies)} potential strategies")

        except Exception as e:
            logger.error(f"[Orient] Error: {e}")
            state['error'] = str(e)

        return state

    async def _decide_node(self, state: DevAgentState) -> DevAgentState:
        """
        Decide phase: Select best strategy and create action plan
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

            logger.info(f"[Decide] Selected strategy: {best_strategy['name']}")
            logger.info(f"[Decide] Action plan has {len(action_plan)} steps")

        except Exception as e:
            logger.error(f"[Decide] Error: {e}")
            state['error'] = str(e)

        return state

    async def _act_node(self, state: DevAgentState) -> DevAgentState:
        """
        Act phase: Execute action plan and collect results
        """
        logger.info("[Act] Executing action plan")

        action_results = []

        try:
            actions = state.get('actions', [])

            for idx, action in enumerate(actions):
                logger.info(f"[Act] Executing action {idx + 1}/{len(actions)}: {action['type']}")

                result = await self._execute_action(action)
                action_results.append(result)

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

            logger.info(f"[Act] Completed iteration {state['iteration']}")

        except Exception as e:
            logger.error(f"[Act] Error: {e}")
            state['error'] = str(e)
            state['result'] = {'success': False, 'error': str(e)}

        return state

    def _should_continue(self, state: DevAgentState) -> str:
        """Determine whether to continue OODA loop or end"""
        if state.get('result', {}).get('success'):
            return "end"
        if state.get('error'):
            return "end"
        if state['iteration'] >= state['max_iterations']:
            return "end"

        return "continue"

    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action using appropriate tool"""
        action_type = action['type']

        try:
            if action_type == 'git_clone':
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
            elif action_type == 'read_file':
                return await self.fs_tool.read_file(action['file_path'])
            elif action_type == 'write_file':
                return await self.fs_tool.write_file(action['file_path'], action['content'])
            elif action_type == 'format_code':
                return await self.ide_tool.format_code(action['file_path'], action.get('language', 'python'))
            elif action_type == 'run_linter':
                return await self.ide_tool.run_linter(action['file_path'], action.get('language', 'python'))
            else:
                return {'success': False, 'error': f'Unknown action type: {action_type}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

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
        """Create detailed action plan from strategy"""
        actions = []

        if 'git' in strategy.get('tools', []):
            actions.append({
                'type': 'git_status',
                'description': 'Check current git status',
                'critical': False
            })

        task_type = self._classify_task(task)
        if task_type == 'feature_addition':
            actions.append({
                'type': 'write_file',
                'file_path': 'new_feature.py',
                'content': '# New feature placeholder (important-comment)\n',
                'description': 'Create new feature file',
                'critical': True
            })

        return actions

    async def execute_task(self, task: str, priority: str = "medium", max_iterations: int = 3) -> Dict[str, Any]:
        """
        Execute a development task using OODA loop

        Args:
            task: Task description
            priority: Task priority (critical/high/medium/low)
            max_iterations: Maximum OODA iterations

        Returns:
            Dict with task execution results
        """
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
            max_iterations=max_iterations
        )

        logger.info(f"[DevAgentOODA] Starting task execution: {task}")

        try:
            final_state = await self.graph.ainvoke(initial_state)
            return final_state
        except Exception as e:
            logger.error(f"[DevAgentOODA] Task execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'task': task
            }


def create_dev_agent_ooda(sandbox_endpoint: str, github_token: Optional[str] = None) -> DevAgentOODA:
    """Factory function to create Dev_Agent OODA instance"""
    return DevAgentOODA(sandbox_endpoint, github_token)
