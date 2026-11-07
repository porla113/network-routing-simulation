"""Search algorithms used to calculate routes through the network."""

import heapq

import networkx as nx


ALGORITHMS = [
    "Breadth-First Search",
    "Depth-First Search",
    "Uniform-Cost Search",
    "Greedy Best-First Search",
    "A* Search",
]


def find_route(graph: nx.Graph, source: str, target: str, algorithm: str) -> list[str]:
    """Return a route selected by the named search algorithm."""
    if algorithm == "Breadth-First Search":
        return nx.shortest_path(graph, source, target)

    if algorithm == "Depth-First Search":
        parents: dict[str, str | None] = {source: None}
        stack = [source]
        while stack:
            node = stack.pop()
            if node == target:
                path = []
                while node is not None:
                    path.append(node)
                    node = parents[node]
                return list(reversed(path))
            for neighbor in reversed(sorted(graph.neighbors(node))):
                if neighbor not in parents:
                    parents[neighbor] = node
                    stack.append(neighbor)
        raise nx.NetworkXNoPath(f"No path between {source} and {target}")

    if algorithm == "Uniform-Cost Search":
        return nx.dijkstra_path(graph, source, target, weight="latency")

    # A hop-count lower bound multiplied by the cheapest link latency is
    # admissible for A*; it also supplies a consistent goal-directed estimate
    # for Greedy Best-First Search.
    hops_to_target = nx.single_source_shortest_path_length(graph, target)
    minimum_latency = min(
        (data["latency"] for _, _, data in graph.edges(data=True)),
        default=0,
    )

    def heuristic(node: str, _goal: str | None = None) -> float:
        return hops_to_target.get(node, 0) * minimum_latency

    if algorithm == "Greedy Best-First Search":
        parents = {source: None}
        frontier = [(heuristic(source), source)]
        while frontier:
            _, node = heapq.heappop(frontier)
            if node == target:
                path = []
                while node is not None:
                    path.append(node)
                    node = parents[node]
                return list(reversed(path))
            for neighbor in sorted(graph.neighbors(node)):
                if neighbor not in parents:
                    parents[neighbor] = node
                    heapq.heappush(frontier, (heuristic(neighbor), neighbor))
        raise nx.NetworkXNoPath(f"No path between {source} and {target}")

    if algorithm == "A* Search":
        return nx.astar_path(graph, source, target, heuristic=heuristic, weight="latency")

    raise ValueError(f"Unsupported routing algorithm: {algorithm}")
