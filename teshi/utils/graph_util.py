from collections import deque

def topological_sort(graph):
    """
    Performs topological sort on a DAG.
    graph: dict {node_id: [child_id, ...]}
    Returns: list of node_ids in topological order.
    """
    in_degree = {u: 0 for u in graph}
    for u in graph:
        for v in graph[u]:
             # Ensure v is in in_degree map even if it has no children (and thus might not be a key in graph if graph strictly only has keys for nodes with children, though usually list of all nodes is better). 
             # Assuming 'graph' keys affect all nodes, or we need to scan values.
             # Based on automate_engine logic, 'graph' contains all nodes as keys.
            if v not in in_degree:
                 in_degree[v] = 0
            in_degree[v] += 1
    
    queue = deque([u for u in in_degree if in_degree[u] == 0])
    result = []
    
    while queue:
        u = queue.popleft()
        result.append(u)
        
        if u in graph:
            for v in graph[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
                    
    # Check for cycles if result length != len(in_degree)
    # But for now assuming DAG.
    return result

def topological_sort_node_parent(graph, target_node):
    """
    Returns topological sort of the subgraph containing ONLY the ancestors of target_node (and target_node itself).
    Used for 'Run Single Node and Parent'.
    """
    # 1. Find all ancestors of target_node by reversing the graph or BFS/DFS search leading to target
    # Since we have Parent -> Children, we need to find who points to whom.
    
    # Build reverse graph: Child -> Parents
    rev_graph = {}
    nodes = set(graph.keys())
    for u in graph:
        nodes.add(u)
        for v in graph[u]:
            nodes.add(v)
            if v not in rev_graph:
                rev_graph[v] = []
            rev_graph[v].append(u)

    # BFS/DFS backwards from target_node to find all ancestors
    ancestors = set()
    queue = deque([target_node])
    while queue:
        curr = queue.popleft()
        if curr in ancestors:
            continue
        ancestors.add(curr)
        
        if curr in rev_graph:
            for parent in rev_graph[curr]:
                if parent not in ancestors:
                    queue.append(parent)
    
    # 2. Extract subgraph for these ancestors
    subgraph = {u: [] for u in ancestors}
    for u in ancestors:
        if u in graph:
            for v in graph[u]:
                if v in ancestors:
                    subgraph[u].append(v)
    
    # 3. Topological sort this subgraph
    return topological_sort(subgraph)
