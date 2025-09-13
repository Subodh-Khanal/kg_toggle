{
    "cells":[
        {
            "cell_type":"code",
            "execution_count":1,
            "id": "XXXX",
            "metadata": {},
            "outputs":[],
            "source": [
                "import sqlite3\n"
                "import networkx as nx\n"
                "import pandas as pd\n"
                "import json"
                      ]
        },
{
  cell_type":"code",
            "execution_count":2,
            "id": "XXXXX",
            "metadata": {},
            "outputs":[
                {
                    "name:"stdout",
                    "output_type":"stream",
                    "text":[
                        "Graph built with 14 nodes and 14 edges.\n"
                    ]
                }
            ],  

"source":[
"\n",
"# ---1.Load Data(from your manual CSVs) ---\n",
"nodes_doc= pd.read_csv('NodeDocuments.csv')\n",
"nodes_draw=pd.read_csv(\"NodesAssemblyDrawings.csv\")\n",
"relationships_df=pd.read_csv('Relations.csv')\n",
"\n",
"# ---2.Build NetworkX Graph ---\n",
"G=nx.DiGraph()\n",
"\n",
"for index,row in nodes_doc.iterrows():\n",
    "node_id=row['id']\n",
    "node_type=row['type']\n",
    "properties=row.drop(['id','type']).dropna.to_dict()", #Get all other columns as properties\n",
    "G.add_node(node_id,type=node_type, **properties)\n",
    "\n",
"for index,row in nodes_draw.iterrows():\n",
    "node_id=row['id']\n",
    "node_type=row['type']\n",
    "properties=row.drop(['id','type']).dropna.to_dict()", #Get all other columns as properties\n",
    "G.add_node(node_id,type=node_type, **properties)\n",
    "\n",
"for index,row in relationships_df.iterrows():\n",
    "source=row['source_id']\n",
    "target=row['target_id']\n",
    "rel_type=row['relationship_type']\n",
    "G.add_edge('source,target,type=rel_type')\n",
"\n",
"print(f\"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.\")\n",
"\n",
"\n"
]
},
{
   cell_type":"code",
            "execution_count":4,
            "id": "XXXXXXX",
            "metadata": {},
            "outputs":[
                {
                    "name:"stdout",
                    "output_type":"stream",
                    "text":[
                    "Warning: When cdn_resources is 'local' jupyter notebook has issues displaying graphics on chrome/safari. Use cdn_resources='inline' or cdn_resources='remote' if you have issues viewing graphics in a notebook.\n",
                    "technical_kg_poc.html\n",
                    "Graph visualization saved to technical_kg_poc.html\n"
                    ]
                }
            ],
"source":[
    "from pyvis.network import Network\n",
    "#import json# Needed if properties are JSON strings\n",
    "\n",
    "# Assuming G is your networkx graph from above\n",
    "net=Network(notebook=True, directed=True,height=\"750px\",width=\"100%\", bgcolor=\"#222222\",font_color=\"white\")\n",
    "net.repulsion(node_distance=100,spring_length=200) # Adjust for better layout\n",
    "\n",
    "for node_id, data in G.nodes(data=True):\n",
    "title_parts=[f\"Type:{data.get('type','N/A')}\"]\n",
    "for prop,value in data.items():\n",
    ""if prop!='type': #Already handled type\n",
    "title_parts.append(f\"prop.replace('_','').title()}:{value}\")\n",
    "title_str=\"\\n\".join(title_parts)\n",
    "net.add_node(node_id,label=data.get('part_number') or data.get('name') or node_id, title=title_str, group=data.get('type'))\n",
    "\n",
    "for u,v,data in G.edges(data=True):\n",
    "net.add_edge(u,v,title=data.get('type', 'RELATED_TO'),label=data.get('type',''))\n",
    "\n",
    "net.show(\"technical_kg_poc.html\")\n",
    "print(\"Graph visualization saved to technical_kg_poc.html\")"
]
},
{
 "cell_type":"code",
            "execution_count":null,
            "id": "XXXXXX",
            "metadata": {},
            "outputs":[],
            "source": []   
}
    ],
    "metadata":{
        "kernelspec":{
            "display_name":"Python 3 (ipykernel)",
            "language":"python",
            "name":"python3"
        },
"language_info":{
    "codemirror_mode":{
        "name":"ipython",
        "version":3
    },
    "file_extension":".py",
    "mimetype":"text/x-python",
    "name":"python",
    "nbconvert_exporter":"python",
    "pygments_lexer":"ipython3",
    "version":"3.13.5"
}
    },
    "nbformat":4,
    "nbformat_minor":5
}        





