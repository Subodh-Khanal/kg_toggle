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
net.from_nx(G)

# Add edge labels
for edge in net.edges:
    src, dst = edge["from"], edge["to"]
    rel = G.edges[src, dst]["relation"]
    edge["title"] = rel  # hover label
    edge["label"] = rel

# Save and display graph
net.save_graph("aircraft_graph.html")

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

st.components.v1.html(open("aircraft_graph.html", "r", encoding="utf-8").read(), height=650)
