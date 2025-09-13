import networkx as nx
from pyvis.network import Network

# Create a NetworkX directed graph
G = nx.DiGraph()

# Add nodes with attributes
G.add_node('Clamp', title='Material: Titanium<br>Standard: AS9100', group='Component')
G.add_node('Std_AST_MIL123', title='Aerospace Fastener Standard', group='Standard')
G.add_node('Bracket', title='Material: Stainless Steel', group='Component')

# Add edges with labels
G.add_edge('Clamp', 'Std_AST_MIL123', label='complies with')
G.add_edge('Clamp', 'Bracket', label='interfaces with')

# Create a Pyvis network
net = Network(height='600px', width='100%', directed=True)
net.from_nx(G)

# Customize options (optional)
net.set_options("""
var options = {
  "nodes": {
    "font": {
      "size": 16,
      "face": "Tahoma"
    }
  },
  "edges": {
    "arrows": {
      "to": {
        "enabled": true
      }
    },
    "font": {
      "align": "top"
    }
  },
  "physics": {
    "enabled": true,
    "solver": "forceAtlas2Based"
  }
}
""")

# Save and display
net.show('clamp_relationships.html')
