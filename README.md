# Network Traffic Simulator

A local Python prototype for building a small network topology and comparing routing algorithms. Nodes and links are editable from the app; the network view animates packets along the selected route.

## Run locally

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints a local address (usually `http://localhost:8501`) when the app starts.

## Prototype features

- Add and remove network nodes and links.
- Configure link latency, capacity, and congestion.
- Compare Breadth-First Search, Depth-First Search, Uniform-Cost Search, Greedy Best-First Search, and A* Search.
- Choose source and destination, then animate simulated packets on the route.
- View route latency, bottleneck capacity, and hop count.

All topology and simulation state is stored in the current Streamlit session; it is not persisted after the app session ends.

## Code layout

- `app.py` coordinates the Streamlit interface and simulation view.
- `topology.py` contains the sample network and builds a graph from the editable node and link data.
- `routing.py` contains the available route-search algorithms.
