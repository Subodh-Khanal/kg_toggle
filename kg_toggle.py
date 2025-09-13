import streamlit as st
import networkx as nx
from pyvis.network import Network
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
# Streamlit UI
# ---------------------------
st.title("Aircraft System Parts Knowledge Graph")
mode = st.radio("Choose Graph Layout:", ["PyVis (Hierarchical)", "Plotly (Concentric Circles)"])

# ---------------------------
# PyVis Hierarchical Layout
# ---------------------------
if mode == "PyVis (Hierarchical)":
    # Levels for layering
    levels = {
        "Aircraft": 0,
        **{s: 1 for s in systems},
        **{c: 2 for c in components},
        **{l: 3 for l in locations},
        **{st: 3 for st in standards},
        **{sup: 4 for sup in suppliers}
    }

    # Color map
    color_map = {}
    color_map.update({s: "#1f77b4" for s in systems})
    color_map.update({c: "#2ca02c" for c in components})
    color_map.update({l: "#ff7f0e" for l in locations})
    color_map.update({st: "#9467bd" for st in standards})
    color_map.update({sup: "#d62728" for sup in suppliers})
    color_map["Aircraft"] = "#000000"

    net = Network(height="600px", width="100%", directed=True)
    net.from_nx(G)

    for node in net.nodes:
        node["level"] = levels[node["id"]]
        node["color"] = color_map.get(node["id"], "#cccccc")
        node["size"] = 25 if node["id"] == "Aircraft" else 15

    for edge in net.edges:
        src, dst = edge["from"], edge["to"]
        rel = G.edges[src, dst]["relation"]
        edge["title"] = rel
        edge["label"] = rel

    net.set_options("""
    {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "levelSeparation": 180,
          "nodeSpacing": 200
        }
      },
      "nodes": {
        "borderWidth": 1,
        "shadow": true
      },
      "edges": {
        "smooth": true,
        "arrows": {"to": {"enabled": true}}
      },
      "physics": {
        "hierarchicalRepulsion": {
          "nodeDistance": 180
        },
        "stabilization": {
          "enabled": true,
          "iterations": 200
        }
      }
    }
    """)

    html_file = "aircraft_graph.html"
    net.save_graph(html_file)
    with open(html_file, "r", encoding="utf-8") as f:
        st.components.v1.html(f.read(), height=650)

# ---------------------------
# Plotly Concentric Layout
# ---------------------------
else:
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

    # Edges
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

    # Filled concentric layers
    fill_traces = []
    fill_colors = ["rgba(173,216,230,0.2)", "rgba(144,238,144,0.2)", "rgba(255,182,193,0.2)"]  # light blue, light green, light pink
    for i, r in enumerate([200, 400, 600]):
        theta = [j * 2 * math.pi / 100 for j in range(101)]
        x = [r * math.cos(t) for t in theta]
        y = [r * math.sin(t) for t in theta]
        fill_traces.append(
            go.Scatter(
                x=x, y=y,
                fill="toself",
                fillcolor=fill_colors[i % len(fill_colors)],
                line=dict(color="rgba(0,0,0,0)"),
                hoverinfo="none",
                mode="lines",
                showlegend=False
            )
        )

    fig = go.Figure(data=fill_traces + [edge_trace] + node_traces)
    fig.update_layout(
        showlegend=True,
        height=700,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Search Functionality
# ---------------------------
search_part = st.text_input("Search for a part, location, standard, or supplier:")
if search_part and search_part in G.nodes:
    neighbors = list(G.neighbors(search_part))
    relations = [G.edges[search_part, n]['relation'] for n in neighbors]
    explanation = [f"{search_part} → {rel} → {n}" for rel, n in zip(relations, neighbors)]
    st.subheader(f"Connections for {search_part}:")
    for line in explanation:
        st.write("- " + line)
