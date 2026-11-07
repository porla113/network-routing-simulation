"""Default topology data and conversion helpers for the simulator."""

import networkx as nx


DEFAULT_NODES = {
    "SEA": "Seattle",
    "SFO": "San Francisco",
    "LAX": "Los Angeles",
    "DEN": "Denver",
    "DFW": "Dallas",
    "ORD": "Chicago",
    "NYC": "New York",
}

DEFAULT_EDGES = [
    {"source": "SEA", "target": "SFO", "latency": 18, "capacity": 80, "congestion": 22},
    {"source": "SEA", "target": "DEN", "latency": 24, "capacity": 70, "congestion": 12},
    {"source": "SFO", "target": "LAX", "latency": 12, "capacity": 90, "congestion": 35},
    {"source": "SFO", "target": "DEN", "latency": 31, "capacity": 65, "congestion": 8},
    {"source": "LAX", "target": "DEN", "latency": 36, "capacity": 55, "congestion": 18},
    {"source": "LAX", "target": "DFW", "latency": 29, "capacity": 75, "congestion": 42},
    {"source": "DEN", "target": "DFW", "latency": 20, "capacity": 85, "congestion": 15},
    {"source": "DEN", "target": "ORD", "latency": 27, "capacity": 90, "congestion": 10},
    {"source": "DFW", "target": "ORD", "latency": 22, "capacity": 70, "congestion": 28},
    {"source": "DFW", "target": "NYC", "latency": 34, "capacity": 60, "congestion": 20},
    {"source": "ORD", "target": "NYC", "latency": 19, "capacity": 95, "congestion": 16},
]


def build_graph(nodes: dict[str, str], edges: list[dict]) -> nx.Graph:
    """Build an undirected NetworkX graph from the editable topology data."""
    graph = nx.Graph()
    for node_id, label in nodes.items():
        graph.add_node(node_id, label=label)
    for edge in edges:
        graph.add_edge(
            edge["source"],
            edge["target"],
            latency=edge["latency"],
            capacity=edge["capacity"],
            congestion=edge["congestion"],
        )
    return graph
