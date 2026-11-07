from __future__ import annotations

import html
import networkx as nx
import streamlit as st
import streamlit.components.v1 as components

from routing import ALGORITHMS, find_route
from topology import DEFAULT_EDGES, DEFAULT_NODES, build_graph


st.set_page_config(
    page_title="NetRoute · Traffic Sim",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;800&display=swap');
    :root { --ink:#e8edf5; --muted:#8491a5; --panel:#111a27; --line:#253246; --teal:#4ce0c1; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    .stApp { background: radial-gradient(ellipse at 68% 0%, #14253a 0%, #0b111b 48%, #090e16 100%); color:var(--ink); }
    [data-testid="stSidebar"] { background:#0d1520; border-right:1px solid #202d3e; }
    [data-testid="stSidebar"] > div { padding-top:1.2rem; }
    .block-container { max-width:1500px; padding-top:2rem; padding-bottom:2rem; }
    h1,h2,h3,p { color:var(--ink); }
    .eyebrow { color:#6f8198; font:500 11px 'DM Mono',monospace; letter-spacing:2px; text-transform:uppercase; }
    .top-title { font-size:32px; font-weight:700; letter-spacing:-1.3px; margin:4px 0 0; }
    .top-sub { color:#8794a8; font-size:14px; margin-top:5px; }
    .live-pill { display:inline-flex; gap:7px; align-items:center; border:1px solid #28584f; background:#102a29; color:#71e6cb; border-radius:20px; padding:6px 11px; font:500 11px 'DM Mono',monospace; }
    .live-dot { height:7px; width:7px; display:inline-block; border-radius:50%; background:#4ce0c1; box-shadow:0 0 12px #4ce0c1; }
    .section-label { color:#91a0b4; font:500 11px 'DM Mono',monospace; letter-spacing:1.4px; text-transform:uppercase; margin:4px 0 10px; }
    .metric-card { background:linear-gradient(145deg,#131e2c,#101824); border:1px solid #253246; border-radius:12px; padding:15px 17px; min-height:87px; }
    .metric-label { color:#8391a5; font:500 10px 'DM Mono',monospace; letter-spacing:1.3px; text-transform:uppercase; }
    .metric-value { color:#f0f4fa; font:600 24px 'DM Mono',monospace; margin-top:5px; }
    .metric-note { color:#69788d; font-size:11px; margin-top:2px; }
    .canvas-wrap { border:1px solid #243246; border-radius:14px; background:radial-gradient(ellipse at center,#111e2b 0%,#0d1520 72%); overflow:hidden; }
    .route-chip { display:inline-block; border:1px solid #27524d; color:#75e8cc; background:#102422; border-radius:6px; padding:5px 9px; font:12px 'DM Mono',monospace; margin:2px 3px 4px 0; }
    .small-note { color:#75849a; font-size:12px; }
    div.stButton > button { border-radius:8px; border:1px solid #2a394d; background:#152131; color:#e4ebf4; font-weight:600; }
    div.stButton > button[kind="primary"] { background:#43d8b8; color:#08201e; border-color:#43d8b8; }
    div.stButton > button:hover { border-color:#4ce0c1; color:#4ce0c1; }
    div.stButton > button[kind="primary"]:hover { color:#08201e; background:#6ce8ce; }
    label, .stCaption { color:#aab5c5 !important; }
    [data-baseweb="select"] > div, [data-baseweb="input"] > div { background:#111b28; border-color:#29384b; }
    hr { border-color:#253246; }
    </style>
    """,
    unsafe_allow_html=True,
)


if "nodes" not in st.session_state:
    st.session_state.nodes = DEFAULT_NODES.copy()
    st.session_state.edges = [edge.copy() for edge in DEFAULT_EDGES]
    st.session_state.running = False
    st.session_state.sent_packets = 0


def render_topology(graph: nx.Graph, route: list[str], running: bool) -> str:
    width, height = 1000, 560
    if graph.number_of_nodes() == 0:
        return '<div style="height:440px;display:grid;place-items:center;color:#8794a8;font:14px sans-serif">Add a node to begin building your network.</div>'

    raw = nx.spring_layout(graph, seed=18, iterations=80, weight=None) if graph.number_of_nodes() > 1 else {next(iter(graph.nodes)): (0, 0)}
    xs = [float(point[0]) for point in raw.values()]
    ys = [float(point[1]) for point in raw.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    def to_screen(node: str) -> tuple[float, float]:
        x, y = raw[node]
        x_span, y_span = max(max_x - min_x, 0.01), max(max_y - min_y, 0.01)
        return 80 + (float(x) - min_x) / x_span * (width - 160), 75 + (float(y) - min_y) / y_span * (height - 150)

    route_edges = {frozenset((route[i], route[i + 1])) for i in range(len(route) - 1)}
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Network topology" xmlns="http://www.w3.org/2000/svg">']
    parts.append("<defs><pattern id='grid' width='32' height='32' patternUnits='userSpaceOnUse'><path d='M 32 0 L 0 0 0 32' fill='none' stroke='#1b2938' stroke-width='0.7'/></pattern><filter id='glow'><feGaussianBlur stdDeviation='4' result='blur'/><feMerge><feMergeNode in='blur'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs>")
    parts.append(f"<rect width='{width}' height='{height}' fill='url(#grid)' opacity='.7'/>")
    route_points = [to_screen(node) for node in route]
    route_path = " ".join(("M" if i == 0 else "L") + f" {point[0]:.1f} {point[1]:.1f}" for i, point in enumerate(route_points))

    for u, v, data in graph.edges(data=True):
        x1, y1 = to_screen(u)
        x2, y2 = to_screen(v)
        active = frozenset((u, v)) in route_edges
        stroke = "#45dec0" if active else "#344255"
        stroke_width = 3.2 if active else 1.7
        congestion_color = "#fb9c63" if data["congestion"] >= 35 else "#75849a"
        parts.append(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{stroke}' stroke-width='{stroke_width}' opacity='{'.95' if active else '.72'}'/>")
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        parts.append(f"<rect x='{mid_x - 25:.1f}' y='{mid_y - 10:.1f}' width='50' height='20' rx='6' fill='#111b28' stroke='#273649'/>")
        parts.append(f"<text x='{mid_x:.1f}' y='{mid_y + 3:.1f}' text-anchor='middle' fill='{congestion_color}' font-family='DM Mono,monospace' font-size='10'>{data['latency']} ms</text>")

    if running and len(route_points) > 1:
        parts.append(f"<path d='{route_path}' fill='none' stroke='none'/>")
        for delay in ("0s", "-1.6s", "-3.2s"):
            parts.append(f"<circle r='5' fill='#8affde' filter='url(#glow)'><animateMotion dur='5s' begin='{delay}' repeatCount='indefinite' path='{route_path}'/></circle>")

    for node in graph.nodes:
        x, y = to_screen(node)
        on_route = node in route
        color = "#4ce0c1" if on_route else "#40536b"
        label = html.escape(st.session_state.nodes[node])
        node_id = html.escape(node)
        glow = "filter='url(#glow)'" if on_route else ""
        parts.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='23' fill='#142132' stroke='{color}' stroke-width='2' {glow}/>")
        parts.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='16' fill='#19283a' stroke='#34465d' stroke-width='1'/>")
        parts.append(f"<text x='{x:.1f}' y='{y + 4:.1f}' text-anchor='middle' fill='#e8edf5' font-family='DM Mono,monospace' font-size='10' font-weight='500'>{node_id}</text>")
        parts.append(f"<text x='{x:.1f}' y='{y + 42:.1f}' text-anchor='middle' fill='#9ba9bc' font-family='DM Sans,sans-serif' font-size='11'>{label}</text>")
    parts.append("</svg>")
    return "".join(parts)


# Sidebar: routing configuration and topology editor.
with st.sidebar:
    st.markdown("<div class='eyebrow'>NETROUTE / SIM</div>", unsafe_allow_html=True)
    st.markdown("## TOPOLOGY setup")
    st.caption("Configure a route, then watch packets move across the network.")
    node_ids = list(st.session_state.nodes)
    if node_ids:
        source = st.selectbox("Source node", node_ids, format_func=lambda key: f"{key} · {st.session_state.nodes[key]}", key="source_select")
        targets = [node for node in node_ids if node != source] or node_ids
        target = st.selectbox("Destination node", targets, format_func=lambda key: f"{key} · {st.session_state.nodes[key]}", key="target_select")
        algorithm = st.selectbox("Routing algorithm", ALGORITHMS)
    else:
        source = target = algorithm = None
        st.info("Create at least one node to configure a route.")

    st.markdown("---")
    st.markdown("<div class='section-label'>Build your topology</div>", unsafe_allow_html=True)
    with st.form("add_node_form", clear_on_submit=True):
        node_name = st.text_input("Node name", placeholder="e.g. Boston")
        node_id_input = st.text_input("Node ID", placeholder="e.g. BOS").strip().upper()
        if st.form_submit_button("＋  Add node", use_container_width=True):
            node_id = node_id_input or "".join(char for char in node_name.upper() if char.isalnum())[:5]
            if not node_name.strip() or not node_id:
                st.error("Enter a node name and a valid ID.")
            elif node_id in st.session_state.nodes:
                st.error("That node ID already exists.")
            else:
                st.session_state.nodes[node_id] = node_name.strip()
                st.rerun()

    if len(node_ids) >= 2:
        with st.expander("＋  Add network link"):
            with st.form("add_edge_form", clear_on_submit=True):
                left, right = st.columns(2)
                edge_source = left.selectbox("From", node_ids, key="edge_from")
                edge_target = right.selectbox("To", [node for node in node_ids if node != edge_source], key="edge_to")
                edge_latency = st.number_input("Latency (ms)", min_value=1, max_value=500, value=20)
                edge_capacity = st.number_input("Capacity (Mbps)", min_value=1, max_value=1000, value=80)
                edge_congestion = st.slider("Current congestion", 0, 100, 15, format="%d%%")
                if st.form_submit_button("Create link", use_container_width=True):
                    if any({edge["source"], edge["target"]} == {edge_source, edge_target} for edge in st.session_state.edges):
                        st.error("A link already connects those nodes.")
                    else:
                        st.session_state.edges.append({"source": edge_source, "target": edge_target, "latency": edge_latency, "capacity": edge_capacity, "congestion": edge_congestion})
                        st.rerun()

    if st.session_state.edges:
        with st.expander("✎  Edit or remove a link"):
            edge_options = list(range(len(st.session_state.edges)))
            chosen_edge_index = st.selectbox(
                "Select link",
                edge_options,
                format_func=lambda index: " — ".join(sorted((st.session_state.edges[index]["source"], st.session_state.edges[index]["target"]))),
            )
            chosen_edge = st.session_state.edges[chosen_edge_index]
            with st.form("edit_edge_form"):
                new_latency = st.number_input("Latency (ms)", 1, 500, int(chosen_edge["latency"]))
                new_capacity = st.number_input("Capacity (Mbps)", 1, 1000, int(chosen_edge["capacity"]))
                new_congestion = st.slider("Congestion", 0, 100, int(chosen_edge["congestion"]))
                edit_col, delete_col = st.columns(2)
                save_edge = edit_col.form_submit_button("Save changes", use_container_width=True)
                remove_edge = delete_col.form_submit_button("Remove link", use_container_width=True)
                if save_edge:
                    chosen_edge.update(latency=new_latency, capacity=new_capacity, congestion=new_congestion)
                    st.rerun()
                if remove_edge:
                    st.session_state.edges.pop(chosen_edge_index)
                    st.rerun()

    if st.session_state.nodes:
        with st.expander("−  Remove a node"):
            remove_node_id = st.selectbox("Node to remove", list(st.session_state.nodes), format_func=lambda key: f"{key} · {st.session_state.nodes[key]}")
            if st.button("Remove node and its links", use_container_width=True):
                del st.session_state.nodes[remove_node_id]
                st.session_state.edges = [edge for edge in st.session_state.edges if remove_node_id not in (edge["source"], edge["target"])]
                st.session_state.running = False
                st.rerun()


# Determine the selected route and its metrics.
graph = build_graph(st.session_state.nodes, st.session_state.edges)
route: list[str] = []
route_error = None
if source and target and source != target and graph.has_node(source) and graph.has_node(target):
    try:
        route = find_route(graph, source, target, algorithm)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        route_error = "No route connects these nodes. Add a link or choose a different endpoint."
elif source and source == target:
    route = [source]

path_edges = [graph[route[i]][route[i + 1]] for i in range(len(route) - 1)] if len(route) > 1 else []
total_latency = sum(edge["latency"] for edge in path_edges)
bottleneck = min((edge["capacity"] for edge in path_edges), default=0)
mean_congestion = sum(edge["congestion"] for edge in path_edges) / len(path_edges) if path_edges else 0

# Header.
head_left, head_right = st.columns([4, 1])
with head_left:
    st.markdown("<div class='eyebrow'>NETWORK INTELLIGENCE / SIMULATOR</div>", unsafe_allow_html=True)
    st.markdown("<div class='top-title'>Traffic routing lab</div>", unsafe_allow_html=True)
    st.markdown("<div class='top-sub'>Build a topology. Compare algorithms. See every route in motion.</div>", unsafe_allow_html=True)
with head_right:
    st.markdown("<div style='text-align:right;padding-top:12px'><span class='live-pill'><span class='live-dot'></span> LOCAL SIMULATION</span></div>", unsafe_allow_html=True)

st.write("")
metric_cols = st.columns(4)
metrics = [
    ("NETWORK NODES", str(graph.number_of_nodes()), "routers in topology"),
    ("ACTIVE LINKS", str(graph.number_of_edges()), "bidirectional connections"),
    ("ROUTE LATENCY", f"{total_latency} ms" if route else "—", algorithm or "select a route"),
    ("BOTTLENECK", f"{bottleneck} Mbps" if path_edges else "—", f"{mean_congestion:.0f}% avg. congestion" if path_edges else "route capacity"),
]
for column, (label, value, note) in zip(metric_cols, metrics):
    column.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>", unsafe_allow_html=True)

st.write("")
canvas_col, details_col = st.columns([2.35, 1], gap="large")
with canvas_col:
    left, right = st.columns([3, 1])
    left.markdown("<div class='section-label' style='margin-top:8px'>Live network topology</div>", unsafe_allow_html=True)
    if st.session_state.running:
        right.markdown("<div style='text-align:right;color:#66dfc4;font:11px DM Mono,monospace;padding-top:4px'>● PACKETS IN TRANSIT</div>", unsafe_allow_html=True)
    svg = render_topology(graph, route, st.session_state.running)
    components.html(f"<div style='border:1px solid #243246;border-radius:14px;overflow:hidden;background:#0d1520'>{svg}</div>", height=585, scrolling=False)
    if route_error:
        st.warning(route_error)
    elif route:
        chips = " <span style='color:#63748a'>→</span> ".join(f"<span class='route-chip'>{html.escape(node)}</span>" for node in route)
        st.markdown(f"<div style='padding-top:7px'><span class='section-label'>Selected path</span><br>{chips}</div>", unsafe_allow_html=True)
    else:
        st.info("Choose source and destination nodes to calculate a route.")

with details_col:
    st.markdown("<div class='section-label' style='margin-top:8px'>Simulation controls</div>", unsafe_allow_html=True)
    st.markdown("<div style='background:#111a27;border:1px solid #253246;border-radius:12px;padding:17px'>", unsafe_allow_html=True)
    st.markdown("**Traffic flow**")
    st.caption("Packets follow the currently selected route. Update link congestion to see routing decisions change.")
    speed = st.slider("Packet rate", min_value=1, max_value=20, value=6, help="Packets sent per simulated second")
    run_col, reset_col = st.columns(2)
    if route and len(route) > 1:
        button_label = "Ⅱ  Pause traffic" if st.session_state.running else "▶  Start traffic"
        if run_col.button(button_label, type="primary", use_container_width=True):
            st.session_state.running = not st.session_state.running
            st.rerun()
    else:
        run_col.button("▶  Start traffic", type="primary", use_container_width=True, disabled=True)
    if reset_col.button("↺  Reset", use_container_width=True):
        st.session_state.running = False
        st.session_state.sent_packets = 0
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='section-label'>Route diagnostics</div>", unsafe_allow_html=True)
    st.markdown("<div style='background:#111a27;border:1px solid #253246;border-radius:12px;padding:17px'>", unsafe_allow_html=True)
    st.markdown(f"**{algorithm or 'No algorithm selected'}**")
    if route:
        st.markdown(f"<span class='small-note'>Path length</span><span style='float:right;color:#e8edf5;font-family:DM Mono,monospace'>{len(path_edges)} hops</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='small-note'>Estimated latency</span><span style='float:right;color:#e8edf5;font-family:DM Mono,monospace'>{total_latency} ms</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='small-note'>Mean congestion</span><span style='float:right;color:#e8edf5;font-family:DM Mono,monospace'>{mean_congestion:.0f}%</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='small-note'>Packet rate</span><span style='float:right;color:#e8edf5;font-family:DM Mono,monospace'>{speed} pkt/s</span>", unsafe_allow_html=True)
    else:
        st.caption("A route's latency, hop count, and link capacity appear here.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='section-label'>Algorithm guide</div>", unsafe_allow_html=True)
    st.markdown("<div class='small-note' style='line-height:1.8'><b style='color:#dce5ef'>Breadth-First</b> finds a fewest-hop route.<br><b style='color:#dce5ef'>Depth-First</b> follows one branch deeply before backtracking.<br><b style='color:#dce5ef'>Uniform-Cost</b> finds the lowest total latency.<br><b style='color:#dce5ef'>Greedy Best-First</b> follows the estimated remaining distance.<br><b style='color:#dce5ef'>A*</b> combines route latency with an admissible distance estimate.</div>", unsafe_allow_html=True)

st.markdown("<div style='color:#56667b;font:10px DM Mono,monospace;margin-top:22px'>NETFLOW LAB 01 &nbsp;·&nbsp; SIMULATED NETWORK / NO EXTERNAL TRAFFIC</div>", unsafe_allow_html=True)
