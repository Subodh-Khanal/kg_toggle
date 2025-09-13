import streamlit as st
import networkx as nx
from pyvis.network import Network

# ---------------------------
# Define Knowledge Graph Data
# ---------------------------
G = nx.DiGraph()

# Add nodes (systems, components, locations, standards, suppliers)
systems = ["Hydraulic System", "Electrical System", "Fuel System"]
components = ["Actuator", "Hydraulic Pump", "Reservoir", "Battery", "Generator", "Wiring"]
locations = ["Landing Gear Bay", "Wing", "Fuselage", "Engine Bay"]
standards = ["SAE-AS7949", "MIL-PRF-5606", "MIL-PRF-81757", "FAA Part 25"]
suppliers = ["Safran", "Parker Aerospace", "Honeywell"]

all_nodes = systems + components + locations + standards + suppliers + ["Aircraft"]
G.add_nodes_from(all_nodes)

# Add relationships (edges)
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
# Generate Interactive Graph
# ---------------------------
net = Network(height="600px", width="100%", directed=True)

# Map layers (Aircraft in center, then Systems, then Components, then others)
layer_map = {
    "Aircraft": 0,
    **{s: 1 for s in systems},
    **{c: 2 for c in components},
    **{l: 3 for l in locations},
    **{st: 3 for st in standards},
    **{sup: 4 for sup in suppliers}
}

# Node colors by type
color_map = {}
color_map.update({s: "#1f77b4" for s in systems})      # blue for systems
color_map.update({c: "#2ca02c" for c in components})   # green for components
color_map.update({l: "#ff7f0e" for l in locations})    # orange for locations
color_map.update({st: "#9467bd" for st in standards})  # purple for standards
color_map.update({sup: "#d62728" for sup in suppliers})# red for suppliers
color_map["Aircraft"] = "#000000"                      # black for core

net.from_nx(G)

# Style nodes
for node in net.nodes:
    node["level"] = layer_map[node["id"]]
    node["color"] = color_map.get(node["id"], "#cccccc")
    node["size"] = 25 if node["id"] == "Aircraft" else 15

# Add edge labels
for edge in net.edges:
    src, dst = edge["from"], edge["to"]
    rel = G.edges[src, dst]["relation"]
    edge["title"] = rel
    edge["label"] = rel

# Apply layered circular layout (fixed JSON)
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

# Save and display graph in the same folder
html_file = "aircraft_graph.html"
net.save_graph(html_file)

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("Aircraft System Parts Knowledge Graph")

# Search functionality
search_part = st.text_input("Search for a part, location, standard, or supplier:")
if search_part and search_part in G.nodes:
    neighbors = list(G.neighbors(search_part))
    relations = [G.edges[search_part, n]['relation'] for n in neighbors]
    explanation = [f"{search_part} → {rel} → {n}" for rel, n in zip(relations, neighbors)]
    st.subheader(f"Connections for {search_part}:")
    for line in explanation:
        st.write("- " + line)

with open(html_file, "r", encoding="utf-8") as f:
    st.components.v1.html(f.read(), height=650)
