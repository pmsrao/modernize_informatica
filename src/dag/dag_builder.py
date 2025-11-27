"""DAG Builder — Production Style
Builds workflow/session/mapping execution DAG with topological sorting and cycle detection.
"""
from typing import Dict, List, Any, Set, Optional, Tuple
from collections import defaultdict, deque
from utils.logger import get_logger
from utils.exceptions import ValidationError
from dag.dag_models import DAGNode

logger = get_logger(__name__)


class DAGBuilder:
    """Builds execution DAG from workflow, sessions, and mappings."""
    
    def build(self, workflow: Dict[str, Any], sessions: Optional[Dict[str, Any]] = None, 
              mappings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build DAG from workflow data.
        
        Args:
            workflow: Workflow data with tasks and links
            sessions: Optional session data dictionary
            mappings: Optional mapping data dictionary
            
        Returns:
            DAG structure with nodes, edges, and topological order
        """
        logger.info(f"Building DAG for workflow: {workflow.get('name', 'unknown')}")
        
        # Extract tasks and links
        tasks = workflow.get("tasks", [])
        links = workflow.get("links", [])
        
        # Build node list
        nodes = []
        node_map = {}
        
        for task in tasks:
            task_name = task.get("name", "")
            task_type = task.get("type", "")
            
            node = {
                "id": task_name,
                "name": task_name,
                "type": task_type,
                "metadata": task
            }
            nodes.append(node)
            node_map[task_name] = node
        
        # Build edge list
        edges = []
        adjacency_list = defaultdict(list)
        in_degree = defaultdict(int)
        
        for link in links:
            from_task = link.get("from")
            to_task = link.get("to")
            condition = link.get("cond") or link.get("condition")
            
            if from_task and to_task:
                edge = {
                    "id": f"{from_task}->{to_task}",
                    "from": from_task,
                    "to": to_task,
                    "condition": condition
                }
                edges.append(edge)
                adjacency_list[from_task].append(to_task)
                in_degree[to_task] += 1
                if from_task not in in_degree:
                    in_degree[from_task] = 0
        
        # Detect cycles
        has_cycle, cycle_nodes = self._detect_cycles(adjacency_list, nodes)
        if has_cycle:
            logger.warning(f"Cycle detected in workflow: {cycle_nodes}")
            raise ValidationError(f"Workflow contains cycle: {' -> '.join(cycle_nodes)}")
        
        # Topological sort
        topological_order = self._topological_sort(adjacency_list, in_degree, nodes)
        
        # Build execution levels (tasks that can run in parallel)
        execution_levels = self._build_execution_levels(topological_order, adjacency_list)
        
        # Validate dependencies
        validation_errors = self._validate_dependencies(nodes, edges, sessions, mappings)
        if validation_errors:
            logger.warning(f"Dependency validation errors: {validation_errors}")
        
        dag = {
            "workflow_name": workflow.get("name", ""),
            "nodes": nodes,
            "edges": edges,
            "topological_order": topological_order,
            "execution_levels": execution_levels,
            "has_cycle": False,
            "validation_errors": validation_errors
        }
        
        logger.info(f"DAG built: {len(nodes)} nodes, {len(edges)} edges, {len(execution_levels)} execution levels")
        
        return dag
    
    def _detect_cycles(self, adjacency_list: Dict[str, List[str]], nodes: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Detect cycles in the DAG using DFS.
        
        Args:
            adjacency_list: Adjacency list representation
            nodes: List of nodes
            
        Returns:
            Tuple of (has_cycle, cycle_nodes)
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node["id"]: WHITE for node in nodes}
        parent = {}
        cycle_nodes = []
        
        def dfs(node_id: str) -> bool:
            color[node_id] = GRAY
            for neighbor in adjacency_list.get(node_id, []):
                if color[neighbor] == GRAY:
                    # Cycle detected
                    cycle = [node_id, neighbor]
                    current = node_id
                    while current in parent and parent[current] != neighbor:
                        cycle.append(parent[current])
                        current = parent[current]
                    cycle_nodes.extend(cycle)
                    return True
                elif color[neighbor] == WHITE:
                    parent[neighbor] = node_id
                    if dfs(neighbor):
                        return True
            color[node_id] = BLACK
            return False
        
        for node in nodes:
            node_id = node["id"]
            if color[node_id] == WHITE:
                if dfs(node_id):
                    return True, cycle_nodes
        
        return False, []
    
    def _topological_sort(self, adjacency_list: Dict[str, List[str]], 
                          in_degree: Dict[str, int], nodes: List[Dict[str, Any]]) -> List[str]:
        """Perform topological sort using Kahn's algorithm.
        
        Args:
            adjacency_list: Adjacency list representation
            in_degree: In-degree count for each node
            nodes: List of nodes
            
        Returns:
            Topologically sorted list of node IDs
        """
        queue = deque()
        result = []
        
        # Initialize in-degree for all nodes
        for node in nodes:
            node_id = node["id"]
            if in_degree.get(node_id, 0) == 0:
                queue.append(node_id)
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            for neighbor in adjacency_list.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check if all nodes were processed
        if len(result) != len(nodes):
            logger.warning("Topological sort incomplete - possible cycle or disconnected nodes")
        
        return result
    
    def _build_execution_levels(self, topological_order: List[str], 
                                adjacency_list: Dict[str, List[str]]) -> List[List[str]]:
        """Build execution levels (tasks that can run in parallel).
        
        Args:
            topological_order: Topologically sorted node IDs
            adjacency_list: Adjacency list representation
            
        Returns:
            List of execution levels, each containing node IDs that can run in parallel
        """
        levels = []
        processed = set()
        remaining = set(topological_order)
        
        while remaining:
            level = []
            # Find nodes with no unprocessed dependencies
            for node_id in remaining:
                can_run = True
                # Check if all dependencies are processed
                for from_node, to_nodes in adjacency_list.items():
                    if node_id in to_nodes and from_node not in processed:
                        can_run = False
                        break
                
                if can_run:
                    level.append(node_id)
            
            if not level:
                # No nodes can run - possible issue
                logger.warning("No nodes can run at this level - possible cycle or missing dependencies")
                break
            
            levels.append(level)
            processed.update(level)
            remaining -= set(level)
        
        return levels
    
    def _validate_dependencies(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]],
                              sessions: Optional[Dict[str, Any]], 
                              mappings: Optional[Dict[str, Any]]) -> List[str]:
        """Validate dependencies between nodes.
        
        Args:
            nodes: List of nodes
            edges: List of edges
            sessions: Optional session data
            mappings: Optional mapping data
            
        Returns:
            List of validation error messages
        """
        errors = []
        node_ids = {node["id"] for node in nodes}
        
        # Validate edge references
        for edge in edges:
            from_node = edge.get("from")
            to_node = edge.get("to")
            
            if from_node and from_node not in node_ids:
                errors.append(f"Edge references unknown source node: {from_node}")
            
            if to_node and to_node not in node_ids:
                errors.append(f"Edge references unknown target node: {to_node}")
        
        # Validate session-mapping references if sessions provided
        if sessions:
            for node in nodes:
                if node.get("type") == "Session":
                    session_name = node.get("name")
                    if session_name in sessions:
                        session_data = sessions[session_name]
                        mapping_name = session_data.get("mapping")
                        if mapping_name and mappings and mapping_name not in mappings:
                            errors.append(f"Session {session_name} references unknown mapping: {mapping_name}")
        
        return errors
    
    def expand_worklets(self, workflow: Dict[str, Any], worklets: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Expand worklet references in workflow.
        
        Args:
            workflow: Workflow data
            worklets: Dictionary of worklet data keyed by worklet name
            
        Returns:
            Workflow with worklets expanded
        """
        expanded_workflow = workflow.copy()
        expanded_tasks = []
        
        for task in workflow.get("tasks", []):
            if task.get("type") == "Worklet":
                worklet_name = task.get("name")
                if worklet_name in worklets:
                    worklet = worklets[worklet_name]
                    # Add worklet tasks to workflow
                    for worklet_task in worklet.get("tasks", []):
                        expanded_tasks.append(worklet_task)
                else:
                    # Keep worklet as-is if not found
                    expanded_tasks.append(task)
            else:
                expanded_tasks.append(task)
        
        expanded_workflow["tasks"] = expanded_tasks
        return expanded_workflow
