"""
Tests for DAGBuilder - Phase F-2: DAG + Parallelization

EPIC F Phase F-2: Tests for DAG construction and validation.
"""

import pytest

from core.planner.dag_builder import (
    DAGBuilder,
    PARALLEL_SAFE_TASK_TYPES,
    PARALLEL_UNSAFE_TASK_TYPES,
)
from core.planner.planner_types import (
    EdgeType,
    TaskEdge,
    TaskNode,
    TaskTree,
    TaskType,
)


class TestDAGBuilderFromLinear:
    """Tests for DAGBuilder.from_linear()"""

    def test_empty_list_returns_empty_tree(self):
        """Empty task list should return empty tree"""
        builder = DAGBuilder()
        tree = builder.from_linear([])

        assert len(tree.nodes) == 0
        assert len(tree.edges) == 0

    def test_single_task_returns_tree_with_no_edges(self):
        """Single task should have no edges"""
        builder = DAGBuilder()
        task = TaskNode(task_id="task1", task_type=TaskType.CODE, description="Test")
        tree = builder.from_linear([task])

        assert len(tree.nodes) == 1
        assert len(tree.edges) == 0
        assert tree.nodes[0].task_id == "task1"

    def test_multiple_tasks_creates_sequential_edges(self):
        """Multiple tasks should create sequential DEPENDS_ON edges"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Code"),
            TaskNode(task_id="task3", task_type=TaskType.TEST, description="Test"),
        ]
        tree = builder.from_linear(tasks)

        assert len(tree.nodes) == 3
        assert len(tree.edges) == 2

        # Check edges are sequential
        assert tree.edges[0].from_task == "task1"
        assert tree.edges[0].to_task == "task2"
        assert tree.edges[0].edge_type == EdgeType.DEPENDS_ON

        assert tree.edges[1].from_task == "task2"
        assert tree.edges[1].to_task == "task3"
        assert tree.edges[1].edge_type == EdgeType.DEPENDS_ON


class TestDAGBuilderFromDependencies:
    """Tests for DAGBuilder.from_dependencies()"""

    def test_empty_dependencies_returns_tree_with_no_edges(self):
        """Empty dependencies should return tree with no edges"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.CODE, description="Task 1"),
        ]
        tree = builder.from_dependencies(tasks, {})

        assert len(tree.nodes) == 1
        assert len(tree.edges) == 0

    def test_single_dependency_creates_edge(self):
        """Single dependency should create one edge"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Code"),
        ]
        deps = {"task2": ["task1"]}
        tree = builder.from_dependencies(tasks, deps)

        assert len(tree.edges) == 1
        assert tree.edges[0].from_task == "task1"
        assert tree.edges[0].to_task == "task2"

    def test_multiple_dependencies_creates_multiple_edges(self):
        """Multiple dependencies should create multiple edges"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="task2", task_type=TaskType.ANALYZE, description="Analyze"),
            TaskNode(task_id="task3", task_type=TaskType.CODE, description="Code"),
        ]
        deps = {"task3": ["task1", "task2"]}
        tree = builder.from_dependencies(tasks, deps)

        assert len(tree.edges) == 2
        edge_pairs = [(e.from_task, e.to_task) for e in tree.edges]
        assert ("task1", "task3") in edge_pairs
        assert ("task2", "task3") in edge_pairs

    def test_diamond_dependency_pattern(self):
        """Diamond pattern: A -> B, A -> C, B -> D, C -> D"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="A", task_type=TaskType.SETUP, description="A"),
            TaskNode(task_id="B", task_type=TaskType.ANALYZE, description="B"),
            TaskNode(task_id="C", task_type=TaskType.ANALYZE, description="C"),
            TaskNode(task_id="D", task_type=TaskType.CODE, description="D"),
        ]
        deps = {
            "B": ["A"],
            "C": ["A"],
            "D": ["B", "C"],
        }
        tree = builder.from_dependencies(tasks, deps)

        assert len(tree.edges) == 4


class TestDAGBuilderInferParallelism:
    """Tests for DAGBuilder.infer_parallelism()"""

    def test_empty_tree_returns_empty(self):
        """Empty tree should return empty tree"""
        builder = DAGBuilder()
        tree = TaskTree(nodes=[], edges=[])
        result = builder.infer_parallelism(tree)

        assert len(result.nodes) == 0
        assert len(result.edges) == 0

    def test_parallel_safe_tasks_at_same_level_get_parallel_edges(self):
        """Parallel-safe tasks at same depth should get PARALLEL_WITH edges"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="setup", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="analyze1", task_type=TaskType.ANALYZE, description="Analyze 1"),
            TaskNode(task_id="analyze2", task_type=TaskType.ANALYZE, description="Analyze 2"),
        ]
        deps = {
            "analyze1": ["setup"],
            "analyze2": ["setup"],
        }
        tree = builder.from_dependencies(tasks, deps)
        result = builder.infer_parallelism(tree)

        # Should have original 2 DEPENDS_ON edges plus 1 PARALLEL_WITH edge
        parallel_edges = [e for e in result.edges if e.edge_type == EdgeType.PARALLEL_WITH]
        assert len(parallel_edges) == 1

    def test_parallel_unsafe_tasks_do_not_get_parallel_edges(self):
        """Parallel-unsafe tasks should not get PARALLEL_WITH edges"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="setup", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="code1", task_type=TaskType.CODE, description="Code 1"),
            TaskNode(task_id="code2", task_type=TaskType.CODE, description="Code 2"),
        ]
        deps = {
            "code1": ["setup"],
            "code2": ["setup"],
        }
        tree = builder.from_dependencies(tasks, deps)
        result = builder.infer_parallelism(tree)

        # CODE is not parallel-safe, so no PARALLEL_WITH edges
        parallel_edges = [e for e in result.edges if e.edge_type == EdgeType.PARALLEL_WITH]
        assert len(parallel_edges) == 0

    def test_dependent_tasks_do_not_get_parallel_edges(self):
        """Tasks with dependencies between them should not get PARALLEL_WITH edges"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="analyze1", task_type=TaskType.ANALYZE, description="Analyze 1"),
            TaskNode(task_id="analyze2", task_type=TaskType.ANALYZE, description="Analyze 2"),
        ]
        deps = {"analyze2": ["analyze1"]}
        tree = builder.from_dependencies(tasks, deps)
        result = builder.infer_parallelism(tree)

        # analyze2 depends on analyze1, so no parallel edge
        parallel_edges = [e for e in result.edges if e.edge_type == EdgeType.PARALLEL_WITH]
        assert len(parallel_edges) == 0


class TestDAGBuilderValidate:
    """Tests for DAGBuilder.validate()"""

    def test_empty_tree_returns_warning(self):
        """Empty tree should return warning"""
        builder = DAGBuilder()
        tree = TaskTree(nodes=[], edges=[])
        result = builder.validate(tree)

        assert result.is_valid
        assert len(result.warnings) == 1
        assert "Empty" in result.warnings[0]

    def test_valid_tree_returns_valid_result(self):
        """Valid tree should return valid result"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Code"),
        ]
        tree = builder.from_linear(tasks)
        result = builder.validate(tree)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_missing_node_in_edge_returns_error(self):
        """Edge referencing missing node should return error"""
        builder = DAGBuilder()
        tree = TaskTree(
            nodes=[TaskNode(task_id="task1", task_type=TaskType.CODE, description="Task")],
            edges=[TaskEdge(from_task="task1", to_task="missing", edge_type=EdgeType.DEPENDS_ON)],
        )
        result = builder.validate(tree)

        assert not result.is_valid
        assert any("unknown" in e.lower() for e in result.errors)

    def test_cycle_detection(self):
        """Cycle in DAG should return error"""
        builder = DAGBuilder()
        tree = TaskTree(
            nodes=[
                TaskNode(task_id="A", task_type=TaskType.CODE, description="A"),
                TaskNode(task_id="B", task_type=TaskType.CODE, description="B"),
                TaskNode(task_id="C", task_type=TaskType.CODE, description="C"),
            ],
            edges=[
                TaskEdge(from_task="A", to_task="B", edge_type=EdgeType.DEPENDS_ON),
                TaskEdge(from_task="B", to_task="C", edge_type=EdgeType.DEPENDS_ON),
                TaskEdge(from_task="C", to_task="A", edge_type=EdgeType.DEPENDS_ON),
            ],
        )
        result = builder.validate(tree)

        assert not result.is_valid
        assert any("cycle" in e.lower() for e in result.errors)


class TestDAGBuilderTopologicalSort:
    """Tests for DAGBuilder.topological_sort()"""

    def test_empty_tree_returns_empty_list(self):
        """Empty tree should return empty list"""
        builder = DAGBuilder()
        tree = TaskTree(nodes=[], edges=[])
        result = builder.topological_sort(tree)

        assert result == []

    def test_linear_tree_returns_correct_order(self):
        """Linear tree should return tasks in order"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="task1", task_type=TaskType.SETUP, description="Setup"),
            TaskNode(task_id="task2", task_type=TaskType.CODE, description="Code"),
            TaskNode(task_id="task3", task_type=TaskType.TEST, description="Test"),
        ]
        tree = builder.from_linear(tasks)
        result = builder.topological_sort(tree)

        assert len(result) == 3
        assert result[0].task_id == "task1"
        assert result[1].task_id == "task2"
        assert result[2].task_id == "task3"

    def test_diamond_pattern_respects_dependencies(self):
        """Diamond pattern should respect all dependencies"""
        builder = DAGBuilder()
        tasks = [
            TaskNode(task_id="A", task_type=TaskType.SETUP, description="A"),
            TaskNode(task_id="B", task_type=TaskType.ANALYZE, description="B"),
            TaskNode(task_id="C", task_type=TaskType.ANALYZE, description="C"),
            TaskNode(task_id="D", task_type=TaskType.CODE, description="D"),
        ]
        deps = {
            "B": ["A"],
            "C": ["A"],
            "D": ["B", "C"],
        }
        tree = builder.from_dependencies(tasks, deps)
        result = builder.topological_sort(tree)

        # A must come first, D must come last
        task_ids = [t.task_id for t in result]
        assert task_ids[0] == "A"
        assert task_ids[-1] == "D"
        # B and C must come before D
        assert task_ids.index("B") < task_ids.index("D")
        assert task_ids.index("C") < task_ids.index("D")

    def test_cycle_raises_error(self):
        """Cycle in DAG should raise ValueError"""
        builder = DAGBuilder()
        tree = TaskTree(
            nodes=[
                TaskNode(task_id="A", task_type=TaskType.CODE, description="A"),
                TaskNode(task_id="B", task_type=TaskType.CODE, description="B"),
            ],
            edges=[
                TaskEdge(from_task="A", to_task="B", edge_type=EdgeType.DEPENDS_ON),
                TaskEdge(from_task="B", to_task="A", edge_type=EdgeType.DEPENDS_ON),
            ],
        )

        with pytest.raises(ValueError, match="cycle"):
            builder.topological_sort(tree)


class TestDAGBuilderMergeTrees:
    """Tests for DAGBuilder.merge_trees()"""

    def test_merge_empty_trees(self):
        """Merging empty trees should return empty tree"""
        builder = DAGBuilder()
        result = builder.merge_trees([])

        assert len(result.nodes) == 0
        assert len(result.edges) == 0

    def test_merge_single_tree(self):
        """Merging single tree should return same tree"""
        builder = DAGBuilder()
        tasks = [TaskNode(task_id="task1", task_type=TaskType.CODE, description="Task")]
        tree = TaskTree(nodes=tasks, edges=[])
        result = builder.merge_trees([tree])

        assert len(result.nodes) == 1
        assert result.nodes[0].task_id == "task1"

    def test_merge_multiple_trees(self):
        """Merging multiple trees should combine all nodes and edges"""
        builder = DAGBuilder()
        tree1 = TaskTree(
            nodes=[TaskNode(task_id="A", task_type=TaskType.CODE, description="A")],
            edges=[],
        )
        tree2 = TaskTree(
            nodes=[TaskNode(task_id="B", task_type=TaskType.CODE, description="B")],
            edges=[],
        )
        result = builder.merge_trees([tree1, tree2])

        assert len(result.nodes) == 2

    def test_merge_with_connection_edges(self):
        """Merging with connection edges should include them"""
        builder = DAGBuilder()
        tree1 = TaskTree(
            nodes=[TaskNode(task_id="A", task_type=TaskType.CODE, description="A")],
            edges=[],
        )
        tree2 = TaskTree(
            nodes=[TaskNode(task_id="B", task_type=TaskType.CODE, description="B")],
            edges=[],
        )
        connection = [TaskEdge(from_task="A", to_task="B", edge_type=EdgeType.DEPENDS_ON)]
        result = builder.merge_trees([tree1, tree2], connection_edges=connection)

        assert len(result.edges) == 1
        assert result.edges[0].from_task == "A"
        assert result.edges[0].to_task == "B"


class TestParallelSafeTaskTypes:
    """Tests for PARALLEL_SAFE_TASK_TYPES and PARALLEL_UNSAFE_TASK_TYPES"""

    def test_parallel_safe_types_are_defined(self):
        """PARALLEL_SAFE_TASK_TYPES should be defined"""
        assert len(PARALLEL_SAFE_TASK_TYPES) > 0

    def test_parallel_unsafe_types_are_defined(self):
        """PARALLEL_UNSAFE_TASK_TYPES should be defined"""
        assert len(PARALLEL_UNSAFE_TASK_TYPES) > 0

    def test_no_overlap_between_safe_and_unsafe(self):
        """Safe and unsafe sets should not overlap"""
        overlap = PARALLEL_SAFE_TASK_TYPES & PARALLEL_UNSAFE_TASK_TYPES
        assert len(overlap) == 0

    def test_analyze_is_parallel_safe(self):
        """ANALYZE should be parallel-safe"""
        assert TaskType.ANALYZE in PARALLEL_SAFE_TASK_TYPES

    def test_code_is_parallel_unsafe(self):
        """CODE should be parallel-unsafe"""
        assert TaskType.CODE in PARALLEL_UNSAFE_TASK_TYPES
