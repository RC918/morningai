"""
DAG Builder - Phase F-2: DAG + Parallelization

EPIC F Phase F-2: Upgrade from linear dependencies to true DAG with parallel execution support.

This module provides the DAGBuilder class for constructing task DAGs from various inputs,
including linear task lists, explicit dependencies, and automatic parallelism inference.

Blueprint Reference: Section 3.1 (Planner v3 - Intelligent Planner)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .planner_types import (
    EdgeType,
    TaskEdge,
    TaskNode,
    TaskTree,
    TaskType,
)


# Task types that are safe to run in parallel
# These tasks don't have side effects that could conflict with each other
PARALLEL_SAFE_TASK_TYPES: Set[TaskType] = {
    TaskType.ANALYZE,
    TaskType.REVIEW,
    TaskType.DOCUMENT,
    TaskType.VERIFY,
}

# Task types that should never run in parallel
# These tasks have side effects or require exclusive access
PARALLEL_UNSAFE_TASK_TYPES: Set[TaskType] = {
    TaskType.SETUP,
    TaskType.CODE,
    TaskType.TEST,
    TaskType.DEPLOY,
    TaskType.CLEANUP,
}


@dataclass
class ValidationResult:
    """
    Result of DAG validation

    Attributes:
        is_valid: Whether the DAG is valid
        errors: List of validation error messages
        warnings: List of validation warning messages
    """
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message and mark as invalid"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message (doesn't affect validity)"""
        self.warnings.append(message)


class DAGBuilder:
    """
    Builds task DAG from various inputs

    Phase F-2 deliverable: Provides methods to construct TaskTree DAGs from
    linear task lists, explicit dependencies, and with automatic parallelism inference.

    Example usage:
        builder = DAGBuilder()

        # From linear list (sequential execution)
        tree = builder.from_linear(tasks)

        # From explicit dependencies
        tree = builder.from_dependencies(tasks, {"task2": ["task1"], "task3": ["task1"]})

        # Infer parallelism for safe tasks
        tree = builder.infer_parallelism(tree)

        # Validate the DAG
        result = builder.validate(tree)
    """

    def from_linear(self, tasks: List[TaskNode]) -> TaskTree:
        """
        Convert linear task list to DAG with sequential edges

        Each task depends on the previous task, creating a simple chain.

        Args:
            tasks: List of TaskNode objects in execution order

        Returns:
            TaskTree with sequential DEPENDS_ON edges
        """
        if not tasks:
            return TaskTree(nodes=[], edges=[])

        edges: List[TaskEdge] = []
        for i in range(1, len(tasks)):
            edges.append(TaskEdge(
                from_task=tasks[i - 1].task_id,
                to_task=tasks[i].task_id,
                edge_type=EdgeType.DEPENDS_ON,
            ))

        return TaskTree(nodes=list(tasks), edges=edges)

    def from_dependencies(
        self,
        tasks: List[TaskNode],
        deps: Dict[str, List[str]],
    ) -> TaskTree:
        """
        Build DAG from explicit dependencies

        Args:
            tasks: List of TaskNode objects
            deps: Dictionary mapping task_id to list of dependency task_ids
                  e.g., {"task2": ["task1"], "task3": ["task1", "task2"]}

        Returns:
            TaskTree with DEPENDS_ON edges based on the dependency map
        """
        edges: List[TaskEdge] = []

        for task_id, dep_ids in deps.items():
            for dep_id in dep_ids:
                edges.append(TaskEdge(
                    from_task=dep_id,
                    to_task=task_id,
                    edge_type=EdgeType.DEPENDS_ON,
                ))

        return TaskTree(nodes=list(tasks), edges=edges)

    def infer_parallelism(self, tree: TaskTree) -> TaskTree:
        """
        Analyze tasks and add parallel_with edges where safe

        This method identifies tasks that can run in parallel based on:
        1. Task type safety (PARALLEL_SAFE_TASK_TYPES)
        2. No dependency relationship between tasks
        3. Same dependency level (can start at the same time)

        Args:
            tree: TaskTree to analyze

        Returns:
            New TaskTree with additional PARALLEL_WITH edges
        """
        if not tree.nodes:
            return tree

        # Build dependency graph for analysis
        task_deps: Dict[str, Set[str]] = {}
        for node in tree.nodes:
            task_deps[node.task_id] = set(tree.get_dependencies(node.task_id))

        # Calculate depth (level) for each task
        depths = self._calculate_depths(tree)

        # Find tasks at the same depth that can run in parallel
        parallel_edges: List[TaskEdge] = []
        depth_groups: Dict[int, List[TaskNode]] = {}

        for node in tree.nodes:
            depth = depths.get(node.task_id, 0)
            if depth not in depth_groups:
                depth_groups[depth] = []
            depth_groups[depth].append(node)

        # For each depth level, find parallel-safe task pairs
        for depth, nodes in depth_groups.items():
            if len(nodes) < 2:
                continue

            for i, node1 in enumerate(nodes):
                for node2 in nodes[i + 1:]:
                    if self._can_run_parallel(node1, node2, tree):
                        # Add parallel edge (only one direction needed)
                        parallel_edges.append(TaskEdge(
                            from_task=node1.task_id,
                            to_task=node2.task_id,
                            edge_type=EdgeType.PARALLEL_WITH,
                        ))

        # Create new tree with additional parallel edges
        all_edges = list(tree.edges) + parallel_edges
        return TaskTree(nodes=list(tree.nodes), edges=all_edges)

    def _calculate_depths(self, tree: TaskTree) -> Dict[str, int]:
        """
        Calculate the depth (level) of each task in the DAG

        Depth is the longest path from any root node to this task.
        Tasks with no dependencies have depth 0.

        Args:
            tree: TaskTree to analyze

        Returns:
            Dictionary mapping task_id to depth
        """
        depths: Dict[str, int] = {}

        # Find root nodes (no dependencies)
        all_task_ids = {node.task_id for node in tree.nodes}
        tasks_with_deps = {
            edge.to_task for edge in tree.edges
            if edge.edge_type == EdgeType.DEPENDS_ON
        }
        root_tasks = all_task_ids - tasks_with_deps

        # Initialize root tasks with depth 0
        for task_id in root_tasks:
            depths[task_id] = 0

        # BFS to calculate depths
        queue = list(root_tasks)
        while queue:
            current = queue.pop(0)
            current_depth = depths[current]

            for dependent in tree.get_dependents(current):
                new_depth = current_depth + 1
                if dependent not in depths or depths[dependent] < new_depth:
                    depths[dependent] = new_depth
                    if dependent not in queue:
                        queue.append(dependent)

        # Handle any remaining nodes (disconnected or in cycles)
        for node in tree.nodes:
            if node.task_id not in depths:
                depths[node.task_id] = 0

        return depths

    def _can_run_parallel(
        self,
        node1: TaskNode,
        node2: TaskNode,
        tree: TaskTree,
    ) -> bool:
        """
        Determine if two tasks can run in parallel

        Args:
            node1: First task node
            node2: Second task node
            tree: TaskTree containing the tasks

        Returns:
            True if tasks can safely run in parallel
        """
        # Check if both task types are parallel-safe
        if node1.task_type not in PARALLEL_SAFE_TASK_TYPES:
            return False
        if node2.task_type not in PARALLEL_SAFE_TASK_TYPES:
            return False

        # Check there's no dependency between them
        deps1 = set(tree.get_dependencies(node1.task_id))
        deps2 = set(tree.get_dependencies(node2.task_id))

        if node1.task_id in deps2 or node2.task_id in deps1:
            return False

        # Check they don't share outputs that could conflict
        # (simplified check - could be enhanced with more sophisticated analysis)
        outputs1 = set(node1.outputs.keys()) if node1.outputs else set()
        outputs2 = set(node2.outputs.keys()) if node2.outputs else set()

        if outputs1 & outputs2:
            return False

        return True

    def validate(self, tree: TaskTree) -> ValidationResult:
        """
        Validate the DAG structure

        Checks for:
        - Cycles in the dependency graph
        - Missing nodes referenced in edges
        - Orphaned nodes (no edges)
        - Invalid edge types

        Args:
            tree: TaskTree to validate

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()

        if not tree.nodes:
            result.add_warning("Empty task tree")
            return result

        # Use TaskTree's built-in validation for basic checks
        tree_errors = tree.validate()
        for error in tree_errors:
            result.add_error(error)

        # Additional validation: check for orphaned nodes
        node_ids = {node.task_id for node in tree.nodes}
        connected_nodes: Set[str] = set()

        for edge in tree.edges:
            connected_nodes.add(edge.from_task)
            connected_nodes.add(edge.to_task)

        orphaned = node_ids - connected_nodes
        if orphaned and len(tree.nodes) > 1:
            for task_id in orphaned:
                result.add_warning(f"Orphaned task with no edges: {task_id}")

        # Check for parallel edges between dependent tasks
        for edge in tree.edges:
            if edge.edge_type == EdgeType.PARALLEL_WITH:
                # Verify no dependency exists between these tasks
                deps1 = set(tree.get_dependencies(edge.from_task))
                deps2 = set(tree.get_dependencies(edge.to_task))

                if edge.from_task in deps2 or edge.to_task in deps1:
                    result.add_error(
                        f"Invalid PARALLEL_WITH edge between dependent tasks: "
                        f"{edge.from_task} and {edge.to_task}"
                    )

        return result

    def merge_trees(
        self,
        trees: List[TaskTree],
        connection_edges: Optional[List[TaskEdge]] = None,
    ) -> TaskTree:
        """
        Merge multiple TaskTrees into a single DAG

        Useful for combining plans from different planners or
        hierarchical plan expansion.

        Args:
            trees: List of TaskTree objects to merge
            connection_edges: Optional edges connecting the trees

        Returns:
            Merged TaskTree
        """
        all_nodes: List[TaskNode] = []
        all_edges: List[TaskEdge] = []

        for tree in trees:
            all_nodes.extend(tree.nodes)
            all_edges.extend(tree.edges)

        if connection_edges:
            all_edges.extend(connection_edges)

        return TaskTree(nodes=all_nodes, edges=all_edges)

    def topological_sort(self, tree: TaskTree) -> List[TaskNode]:
        """
        Return tasks in topological order (respecting dependencies)

        Args:
            tree: TaskTree to sort

        Returns:
            List of TaskNode in execution order

        Raises:
            ValueError: If the DAG contains cycles
        """
        if not tree.nodes:
            return []

        # Validate first
        validation = self.validate(tree)
        if not validation.is_valid:
            for error in validation.errors:
                if "Cycle" in error:
                    raise ValueError("Cannot topologically sort a DAG with cycles")

        # Kahn's algorithm for topological sort
        in_degree: Dict[str, int] = {node.task_id: 0 for node in tree.nodes}

        for edge in tree.edges:
            if edge.edge_type == EdgeType.DEPENDS_ON:
                in_degree[edge.to_task] = in_degree.get(edge.to_task, 0) + 1

        # Start with nodes that have no dependencies
        queue = [
            node for node in tree.nodes
            if in_degree[node.task_id] == 0
        ]
        result: List[TaskNode] = []

        while queue:
            # Sort by priority for deterministic ordering
            queue.sort(key=lambda n: n.priority)
            node = queue.pop(0)
            result.append(node)

            for dependent_id in tree.get_dependents(node.task_id):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    dependent_node = tree.get_node(dependent_id)
                    if dependent_node:
                        queue.append(dependent_node)

        if len(result) != len(tree.nodes):
            raise ValueError("Cannot topologically sort a DAG with cycles")

        return result
