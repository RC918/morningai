#!/usr/bin/env python3
"""
FAQ Agent OODA Loop Implementation
Adaptive FAQ management with observe-orient-decide-act cycle
"""
import logging
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from langgraph.graph import StateGraph, END

try:
    from agents.faq_agent.tools import FAQSearchTool, FAQManagementTool, EmbeddingTool
    FAQ_TOOLS_AVAILABLE = True
except ImportError:
    FAQ_TOOLS_AVAILABLE = False
    logging.warning("FAQ Agent tools not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FAQTaskType(Enum):
    """FAQ task types"""
    SEARCH = "search"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    OPTIMIZE = "optimize"
    ANALYZE = "analyze"


class FAQAgentState(TypedDict):
    """State schema for FAQ Agent OODA loop"""
    task: str
    task_type: str
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
    decision_trace: List[Dict[str, Any]]


@dataclass
class FAQObservationResult:
    """Result from Observe phase"""
    timestamp: datetime
    current_faq_count: int
    search_quality_metrics: Dict[str, float]
    category_distribution: Dict[str, int]
    issues_identified: List[str]


@dataclass
class FAQOrientationResult:
    """Result from Orient phase"""
    timestamp: datetime
    task_analysis: str
    required_actions: List[str]
    potential_strategies: List[Dict[str, Any]]
    risk_factors: List[str]


@dataclass
class FAQDecisionResult:
    """Result from Decide phase"""
    timestamp: datetime
    selected_strategy: str
    action_plan: List[Dict[str, Any]]
    expected_outcome: str
    confidence: float


class FAQAgentOODA:
    """FAQ Agent OODA Loop Implementation"""

    MAX_ITERATIONS = 10
    MAX_STEPS = 50

    def __init__(self):
        if not FAQ_TOOLS_AVAILABLE:
            raise ImportError("FAQ Agent tools are not available")
        
        self.search_tool = FAQSearchTool()
        self.mgmt_tool = FAQManagementTool()
        self.embedding_tool = EmbeddingTool()
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create LangGraph workflow for FAQ OODA cycle"""
        workflow = StateGraph(FAQAgentState)

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

    async def _observe_node(self, state: FAQAgentState) -> FAQAgentState:
        """Observe phase: Collect current FAQ system state and metrics"""
        logger.info(f"[Observe] Starting observation for task: {state['task']}")

        observations = []
        context_data = {}

        try:
            stats_result = await self.mgmt_tool.get_stats()
            if stats_result.get('success'):
                stats = stats_result.get('stats', {})
                observations.append(f"Total FAQs: {stats.get('total_faqs', 0)}")
                observations.append(f"Categories: {stats.get('category_count', 0)}")
                context_data['stats'] = stats
            else:
                logger.warning(f"[Observe] Failed to get stats: {stats_result.get('error')}")

            categories_result = await self.mgmt_tool.get_categories()
            if categories_result.get('success'):
                categories = categories_result.get('categories', [])
                observations.append(f"Category distribution: {len(categories)} categories")
                context_data['categories'] = categories
            else:
                logger.warning(f"[Observe] Failed to get categories: {categories_result.get('error')}")

            if state['task_type'] == FAQTaskType.SEARCH.value:
                test_queries = self._extract_search_queries(state['task'])
                search_results = {}
                for query in test_queries[:3]:
                    result = await self.search_tool.search(query, limit=5)
                    if result.get('success'):
                        count = result.get('count', 0)
                        observations.append(f"Search '{query}': {count} results")
                        search_results[query] = count
                context_data['search_results'] = search_results

            state['observations'] = observations
            state['context']['last_observe_time'] = datetime.now(timezone.utc).isoformat()
            state['context']['observation_data'] = context_data

            decision_entry = {
                'phase': 'observe',
                'observations_count': len(observations),
                'context_data_keys': list(context_data.keys()),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            state['decision_trace'].append(decision_entry)

            logger.info(f"[Observe] Collected {len(observations)} observations")

        except Exception as e:
            logger.error(f"[Observe] Error: {e}")
            state['error'] = f"Observe phase failed: {str(e)}"

        return state

    async def _orient_node(self, state: FAQAgentState) -> FAQAgentState:
        """Orient phase: Analyze observations and formulate strategies"""
        logger.info("[Orient] Analyzing observations and formulating strategies")

        try:
            observations = state.get('observations', [])
            task = state['task']
            task_type = state['task_type']

            complexity = self._assess_complexity(task, observations)
            required_actions = self._identify_required_actions(task_type)
            strategies = self._generate_strategies(task, task_type, observations)

            orientation = {
                'task_analysis': f"Task type: {task_type}, Complexity: {complexity}",
                'complexity': complexity,
                'required_actions': required_actions,
                'strategies': strategies,
                'risk_factors': self._identify_risks(task_type, complexity)
            }

            state['orientation'] = orientation
            state['context']['last_orient_time'] = datetime.now(timezone.utc).isoformat()

            decision_entry = {
                'phase': 'orient',
                'complexity': complexity,
                'required_actions': required_actions,
                'strategies_count': len(strategies),
                'risk_factors': orientation['risk_factors'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            state['decision_trace'].append(decision_entry)

            logger.info(f"[Orient] Generated {len(strategies)} potential strategies")

        except Exception as e:
            logger.error(f"[Orient] Error: {e}")
            state['error'] = f"Orient phase failed: {str(e)}"

        return state

    async def _decide_node(self, state: FAQAgentState) -> FAQAgentState:
        """Decide phase: Select best strategy and create action plan"""
        logger.info("[Decide] Selecting strategy and creating action plan")

        try:
            orientation = state.get('orientation', {})
            strategies = orientation.get('strategies', [])

            best_strategy = self._select_best_strategy(strategies)
            action_plan = self._create_action_plan(best_strategy, state['task'], state['task_type'])

            state['strategy'] = best_strategy['name']
            state['actions'] = action_plan
            state['context']['last_decide_time'] = datetime.now(timezone.utc).isoformat()

            decision_entry = {
                'phase': 'decide',
                'selected_strategy': best_strategy['name'],
                'strategy_confidence': best_strategy.get('confidence', 0),
                'action_count': len(action_plan),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            state['decision_trace'].append(decision_entry)

            logger.info(f"[Decide] Selected strategy: {best_strategy['name']}")
            logger.info(f"[Decide] Action plan has {len(action_plan)} steps")

        except Exception as e:
            logger.error(f"[Decide] Error: {e}")
            state['error'] = f"Decide phase failed: {str(e)}"

        return state

    async def _act_node(self, state: FAQAgentState) -> FAQAgentState:
        """Act phase: Execute action plan and collect results"""
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
            state['context']['last_act_time'] = datetime.now(timezone.utc).isoformat()

            all_success = all(r.get('success', False) for r in action_results)
            if all_success:
                state['result'] = {
                    'success': True,
                    'message': 'All actions completed successfully',
                    'actions_executed': len(action_results),
                    'results': action_results
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
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            state['decision_trace'].append(decision_entry)

            logger.info(f"[Act] Completed iteration {state['iteration']}")

        except Exception as e:
            logger.error(f"[Act] Error: {e}")
            state['error'] = f"Act phase failed: {str(e)}"
            state['result'] = {'success': False, 'error': state['error']}

        return state

    def _should_continue(self, state: FAQAgentState) -> str:
        """Determine whether to continue OODA loop or end"""
        if state.get('result', {}).get('success'):
            return "end"
        if state.get('error'):
            return "end"
        if state['iteration'] >= state['max_iterations']:
            logger.warning(f"[OODA] Max iterations ({state['max_iterations']}) reached")
            state['error'] = f"Maximum iterations ({state['max_iterations']}) exceeded"
            return "end"

        total_steps = state['iteration'] * 4
        if total_steps >= self.MAX_STEPS:
            logger.error(f"[OODA] Max steps ({self.MAX_STEPS}) exceeded")
            state['error'] = f"Maximum workflow steps ({self.MAX_STEPS}) exceeded"
            return "end"

        return "continue"

    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action using appropriate tool"""
        action_type = action['type']

        try:
            if action_type == 'search_faq':
                return await self.search_tool.search(
                    action['query'],
                    limit=action.get('limit', 10),
                    category=action.get('category')
                )
            elif action_type == 'create_faq':
                return await self.mgmt_tool.create_faq(
                    question=action['question'],
                    answer=action['answer'],
                    category=action.get('category'),
                    tags=action.get('tags', [])
                )
            elif action_type == 'update_faq':
                return await self.mgmt_tool.update_faq(
                    faq_id=action['faq_id'],
                    question=action.get('question'),
                    answer=action.get('answer'),
                    category=action.get('category'),
                    tags=action.get('tags')
                )
            elif action_type == 'delete_faq':
                return await self.mgmt_tool.delete_faq(action['faq_id'])
            elif action_type == 'get_faq':
                return await self.mgmt_tool.get_faq(action['faq_id'])
            elif action_type == 'get_stats':
                return await self.mgmt_tool.get_stats()
            elif action_type == 'get_categories':
                return await self.mgmt_tool.get_categories()
            elif action_type == 'generate_embedding':
                return await self.embedding_tool.generate_embedding(action['text'])
            else:
                return {
                    'success': False,
                    'error': f"Unknown action type: {action_type}"
                }

        except Exception as e:
            logger.error(f"[Execute] Error executing {action_type}: {e}")
            return {
                'success': False,
                'error': str(e),
                'action_type': action_type
            }

    def _extract_search_queries(self, task: str) -> List[str]:
        """Extract potential search queries from task"""
        words = task.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in ['what', 'how', 'when', 'where', 'which', 'search', 'find']]
        return keywords[:5]

    def _assess_complexity(self, task: str, observations: List[str]) -> str:
        """Assess task complexity based on task description and observations"""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ['batch', 'bulk', 'multiple', 'all', 'migrate']):
            return 'high'
        elif any(word in task_lower for word in ['update', 'modify', 'refactor', 'optimize']):
            return 'medium'
        else:
            return 'low'

    def _identify_required_actions(self, task_type: str) -> List[str]:
        """Identify required actions based on task type"""
        action_map = {
            FAQTaskType.SEARCH.value: ['search_faq', 'get_stats'],
            FAQTaskType.CREATE.value: ['create_faq', 'generate_embedding'],
            FAQTaskType.UPDATE.value: ['get_faq', 'update_faq', 'generate_embedding'],
            FAQTaskType.DELETE.value: ['get_faq', 'delete_faq'],
            FAQTaskType.OPTIMIZE.value: ['get_stats', 'search_faq', 'update_faq'],
            FAQTaskType.ANALYZE.value: ['get_stats', 'get_categories', 'search_faq']
        }
        return action_map.get(task_type, ['search_faq'])

    def _generate_strategies(self, task: str, task_type: str, observations: List[str]) -> List[Dict[str, Any]]:
        """Generate potential strategies based on task and observations"""
        strategies = []

        if task_type == FAQTaskType.SEARCH.value:
            strategies.append({
                'name': 'semantic_search',
                'description': 'Use semantic search with embeddings',
                'confidence': 0.9,
                'priority': 1
            })
            strategies.append({
                'name': 'keyword_search',
                'description': 'Use keyword-based search',
                'confidence': 0.7,
                'priority': 2
            })
        elif task_type == FAQTaskType.CREATE.value:
            strategies.append({
                'name': 'direct_create',
                'description': 'Create FAQ with embedding generation',
                'confidence': 0.95,
                'priority': 1
            })
        elif task_type == FAQTaskType.UPDATE.value:
            strategies.append({
                'name': 'fetch_and_update',
                'description': 'Fetch existing FAQ and update with new data',
                'confidence': 0.9,
                'priority': 1
            })
        elif task_type == FAQTaskType.OPTIMIZE.value:
            strategies.append({
                'name': 'analyze_and_improve',
                'description': 'Analyze FAQ quality and improve low-performing entries',
                'confidence': 0.8,
                'priority': 1
            })
        else:
            strategies.append({
                'name': 'adaptive',
                'description': 'Adapt based on observations',
                'confidence': 0.6,
                'priority': 1
            })

        return strategies

    def _identify_risks(self, task_type: str, complexity: str) -> List[str]:
        """Identify potential risk factors"""
        risks = []

        if complexity == 'high':
            risks.append("High complexity task may require multiple iterations")
        
        if task_type == FAQTaskType.DELETE.value:
            risks.append("Deletion is irreversible - verify before proceeding")
        
        if task_type == FAQTaskType.UPDATE.value:
            risks.append("Update may affect search ranking and embeddings")

        return risks

    def _select_best_strategy(self, strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select best strategy based on confidence and priority"""
        if not strategies:
            return {
                'name': 'default',
                'description': 'Default fallback strategy',
                'confidence': 0.5,
                'priority': 999
            }
        
        return max(strategies, key=lambda s: (s.get('confidence', 0), -s.get('priority', 999)))

    def _create_action_plan(self, strategy: Dict[str, Any], task: str, task_type: str) -> List[Dict[str, Any]]:
        """Create action plan based on selected strategy"""
        actions = []

        if task_type == FAQTaskType.SEARCH.value:
            queries = self._extract_search_queries(task)
            for query in queries:
                actions.append({
                    'type': 'search_faq',
                    'query': query,
                    'limit': 10,
                    'critical': False
                })
        elif task_type == FAQTaskType.CREATE.value:
            actions.append({
                'type': 'create_faq',
                'question': task,
                'answer': 'Generated answer placeholder',
                'critical': True
            })
        elif task_type == FAQTaskType.ANALYZE.value:
            actions.append({'type': 'get_stats', 'critical': False})
            actions.append({'type': 'get_categories', 'critical': False})

        return actions

    async def execute_task(self, task: str, task_type: str = None, max_iterations: int = None) -> Dict[str, Any]:
        """Execute FAQ task using OODA loop
        
        Args:
            task: Task description
            task_type: Type of task (search, create, update, delete, optimize, analyze)
            max_iterations: Maximum OODA iterations
        
        Returns:
            Task execution result with decision trace
        """
        if task_type is None:
            task_type = self._infer_task_type(task)

        logger.info(f"[OODA] Starting task: {task} (type: {task_type})")

        initial_state: FAQAgentState = {
            'task': task,
            'task_type': task_type,
            'context': {},
            'observations': [],
            'orientation': {},
            'strategy': None,
            'actions': [],
            'action_results': [],
            'result': None,
            'error': None,
            'iteration': 0,
            'max_iterations': max_iterations or self.MAX_ITERATIONS,
            'decision_trace': []
        }

        try:
            final_state = await self.graph.ainvoke(initial_state)

            result = {
                'success': final_state.get('result', {}).get('success', False),
                'task': task,
                'task_type': task_type,
                'strategy': final_state.get('strategy'),
                'iterations': final_state['iteration'],
                'result': final_state.get('result'),
                'error': final_state.get('error'),
                'decision_trace': final_state.get('decision_trace', []),
                'context': final_state.get('context', {})
            }

            logger.info(f"[OODA] Task completed: success={result['success']}, iterations={result['iterations']}")
            return result

        except Exception as e:
            logger.error(f"[OODA] Task execution failed: {e}")
            return {
                'success': False,
                'task': task,
                'task_type': task_type,
                'error': str(e),
                'decision_trace': []
            }

    def _infer_task_type(self, task: str) -> str:
        """Infer task type from task description"""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ['search', 'find', 'look', 'query']):
            return FAQTaskType.SEARCH.value
        elif any(word in task_lower for word in ['create', 'add', 'new']):
            return FAQTaskType.CREATE.value
        elif any(word in task_lower for word in ['update', 'modify', 'edit', 'change']):
            return FAQTaskType.UPDATE.value
        elif any(word in task_lower for word in ['delete', 'remove']):
            return FAQTaskType.DELETE.value
        elif any(word in task_lower for word in ['optimize', 'improve', 'enhance']):
            return FAQTaskType.OPTIMIZE.value
        elif any(word in task_lower for word in ['analyze', 'report', 'stats']):
            return FAQTaskType.ANALYZE.value
        else:
            return FAQTaskType.SEARCH.value


def create_faq_agent_ooda() -> FAQAgentOODA:
    """Factory function to create FAQ Agent OODA instance"""
    return FAQAgentOODA()
