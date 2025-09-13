import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import math

# ---------------------------
# Define Knowledge Graph Data
# ---------------------------
G = nx.DiGraph()

# Categories
systems = ["Hydraulic System", "Electrical System", "Fuel System"]
components = ["Actuator", "Hydraulic Pump", "Reservoir", "Battery", "Generator", "Wiring"]
locations = ["Landing Gear Bay", "Wing", "Fuselage", "Engine Bay"]
standards = ["SAE-AS7949", "MIL-PRF-5606", "MIL-PRF-81757", "FAA Part 25"]
suppliers = ["Safran", "Parker Aerospace", "Honeywell"]

all_nodes = ["Aircraft"] + systems + components + locations + standards + suppliers
G.add_nodes_from(all_nodes)

relationships = [
    ("Aircraft", "Hydraulic System", "includes"),
    ("Aircraft", "Electrical System", "includes"),
    ("Aircraft", "Fuel System", "includes"),

    ("Hydraulic System", "Actuator", "includes"),
    ("Hydraulic System", "Hydraulic Pump", "includes"),
    ("Hydraulic System", "Reservoir", "includes"),

    ("Electrical System", "Battery", "includes"),
    ("Electrical System", "Generator", "includes"),
    ("Electrical System", "Wiring", "includes"),

    ("Actuator", "Landing Gear Bay", "located in"),
    ("Hydraulic Pump", "Engine Bay", "located in"),
    ("Battery", "Fuselage", "located in"),
    ("Generator", "Engine Bay", "located in"),
    ("Wiring", "Wing", "routed through"),

    ("Actuator", "SAE-AS7949", "conforms to"),
    ("Hydraulic Pump", "MIL-PRF-5606", "uses fluid spec"),
    ("Battery", "MIL-PRF-81757", "conforms to"),
    ("Wiring", "FAA Part 25", "regulated under"),

    ("Actuator", "Safran", "supplied by"),
    ("Hydraulic Pump", "Parker Aerospace", "supplied by"),
    ("Battery", "Honeywell", "supplied by"),
    ("Generator", "Honeywell", "supplied by")
]
for src, dst, rel in relationships:
    G.add_edge(src, dst, relation=rel)

# ---------------------------
# Layout: concentric layers
# ---------------------------
layers = {
    "Aircraft": 0,
    "Systems": 1,
    "Components": 2,
    "Suppliers": 3,
    "Standards": 3,
    "Locations": 3,
}
colors = {
    "Aircraft": "black",
    "Systems": "blue",
    "Components": "green",
    "Suppliers": "orange",
    "Standards": "purple",
    "Locations": "brown",
}
radii = {0: 0, 1: 200, 2: 400, 3: 600}

positions = {}
for category, nodeset in [
    ("Aircraft", ["Aircraft"]),
    ("Systems", systems),
    ("Components", components),
    ("Suppliers", suppliers),
    ("Standards", standards),
    ("Locations", locations),
]:
    r = radii[layers[category]]
    n = len(nodeset)
    for i, node in enumerate(nodeset):
        angle = 2 * math.pi * i / n if n > 0 else 0
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        positions[node] = (x, y)

# ---------------------------
# Build Plotly visualization
# ---------------------------
edge_x, edge_y = [], []
for src, dst, rel in relationships:
    x0, y0 = positions[src]
    x1, y1 = positions[dst]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=1, color="gray"),
    hoverinfo="none",
    mode="lines"
)

node_traces = []
for cat, nodeset in [
    ("Aircraft", ["Aircraft"]),
    ("Systems", systems),
    ("Components", components),
    ("Suppliers", suppliers),
    ("Standards", standards),
    ("Locations", locations),
]:
    node_traces.append(
        go.Scatter(
            x=[positions[n][0] for n in nodeset],
            y=[positions[n][1] for n in nodeset],
            mode="markers+text",
            text=nodeset,
            textposition="top center",
            marker=dict(size=20, color=colors[cat]),
            name=cat
        )
    )

# Background concentric circles
circle_shapes = []
for r in [200, 400, 600]:
    circle_shapes.append(
        dict(
            type="circle",
            xref="x", yref="y",
            x0=-r, y0=-r, x1=r, y1=r,
            line=dict(color="lightgray", width=1, dash="dot"),
        )
    )

fig = go.Figure(data=[edge_trace] + node_traces)
fig.update_layout(
    showlegend=True,
    height=700,
    shapes=circle_shapes,
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
)

# ---------------------------
# Streamlit App
# ---------------------------
st.title("Aircraft System Knowledge Graph (Concentric View)")
st.plotly_chart(fig, use_container_width=True)

# Search functionality
search_part = st.text_input("Search for a part, location, standard, or supplier:")
if search_part and search_part in G.nodes:
    neighbors = list(G.neighbors(search_part))
    relations = [G.edges[search_part, n]["relation"] for n in neighbors]
    explanation = [f"{search_part} → {rel} → {n}" for rel, n in zip(relations, neighbors)]
    st.subheader(f"Connections for {search_part}:")
    for line in explanation:
        st.write("- " + line)
