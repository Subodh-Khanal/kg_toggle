#!/usr/bin/env python3
"""
build_knowledge_graph.py

Single-file script you can open & run in VS Code to build a Knowledge Graph from
three CSVs and export an interactive HTML visualization (pyvis).

Usage examples:
  python build_knowledge_graph.py                                    # uses defaults or creates sample data if missing
  python build_knowledge_graph.py --nodes-doc NodeDocuments.csv \
       --nodes-draw NodesAssemblyDrawings.csv --relations Relations.csv \
       --output technical_kg_poc.html

Dependencies:
  pip install pandas networkx pyvis

This script is intentionally defensive: it will try several common column names,
create sample CSVs if the input files are missing, and give helpful error messages.

"""

import argparse
import json
import logging
import os
import sys
import webbrowser

from typing import Optional

import pandas as pd
import networkx as nx
from pyvis.network import Network


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def read_csv_if_exists(path: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        logging.debug("File not found: %s", path)
        return None
    try:
        df = pd.read_csv(path, dtype=str)
        logging.info("Loaded %s (rows=%d, cols=%d)", path, len(df), len(df.columns))
        return df
    except Exception as e:
        logging.error("Failed to read %s: %s", path, e)
        return None


def parse_properties_from_row(row: pd.Series, drop_cols: list) -> dict:
    """Return a dict of non-empty properties for a row, parsing JSON strings when appropriate."""
    props = row.drop(labels=drop_cols, errors='ignore').replace('', pd.NA).dropna().to_dict()
    for k, v in list(props.items()):
        if isinstance(v, str):
            s = v.strip()
            # try to parse JSON-ish values (dicts, lists)
            if (s.startswith('{') and s.endswith('}')) or (s.startswith('[') and s.endswith(']')):
                try:
                    props[k] = json.loads(s)
                except Exception:
                    # leave as string if JSON parsing fails
                    pass
    return props


def ensure_name(df: pd.DataFrame, candidates: list) -> str:
    """Return the first candidate column name found in df.columns, else raise."""
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of the expected columns found in dataframe: {candidates}")


def create_sample_files(out_dir: str = "sample_data") -> tuple:
    os.makedirs(out_dir, exist_ok=True)
    nodes_doc_path = os.path.join(out_dir, "NodeDocuments.csv")
    nodes_draw_path = os.path.join(out_dir, "NodesAssemblyDrawings.csv")
    relations_path = os.path.join(out_dir, "Relations.csv")

    if not os.path.exists(nodes_doc_path):
        pd.DataFrame([
            {"id": "doc1", "type": "Document", "name": "Assembly Spec", "part_number": "DOC-001", "description": "Specification for assembly"},
            {"id": "doc2", "type": "Document", "name": "Welding Spec", "part_number": "DOC-002", "description": "Welding instructions"},
        ]).to_csv(nodes_doc_path, index=False)

    if not os.path.exists(nodes_draw_path):
        pd.DataFrame([
            {"id": "draw1", "type": "Drawing", "name": "Frame Assembly", "part_number": "FR-100", "revision": "A"},
            {"id": "draw2", "type": "Drawing", "name": "Fork", "part_number": "FK-200", "revision": "B"},
        ]).to_csv(nodes_draw_path, index=False)

    if not os.path.exists(relations_path):
        pd.DataFrame([
            {"source_id": "doc1", "target_id": "draw1", "relationship_type": "documents", "note": "Primary doc for frame"},
            {"source_id": "doc2", "target_id": "draw2", "relationship_type": "references", "note": "Welding reference"},
            {"source_id": "draw1", "target_id": "draw2", "relationship_type": "contains", "note": "Frame contains fork subassembly"},
        ]).to_csv(relations_path, index=False)

    logging.info("Sample CSVs created in '%s'", out_dir)
    return nodes_doc_path, nodes_draw_path, relations_path


def build_graph(nodes_doc_df: Optional[pd.DataFrame], nodes_draw_df: Optional[pd.DataFrame], relations_df: Optional[pd.DataFrame]) -> nx.DiGraph:
    G = nx.DiGraph()

    # Helper to add/merge node rows
    def add_nodes_from_df(df: pd.DataFrame, source_label: str):
        if df is None:
            return
        # expected id col and type col might be named differently; accept common alternatives
        id_col = None
        for c in ["id", "node_id", "Id", "ID"]:
            if c in df.columns:
                id_col = c
                break
        if id_col is None:
            raise KeyError(f"No id column found in {source_label}; expected one of id/node_id/Id/ID")

        type_col = None
        for c in ["type", "node_type", "Type"]:
            if c in df.columns:
                type_col = c
                break

        for _, row in df.iterrows():
            node_id = str(row[id_col])
            node_type = row[type_col] if type_col and type_col in row.index else None
            props = parse_properties_from_row(row, drop_cols=[id_col, type_col])
            # merge if node already exists (prefer earlier values, but update with any new props)
            if node_id in G:
                # update node_type if new
                if node_type:
                    G.nodes[node_id].setdefault("node_type", node_type)
                G.nodes[node_id].update(props)
            else:
                attrs = {"node_type": node_type} if node_type else {}
                attrs.update(props)
                G.add_node(node_id, **attrs)

    add_nodes_from_df(nodes_doc_df, "nodes_doc")
    add_nodes_from_df(nodes_draw_df, "nodes_draw")

    # Edges
    if relations_df is not None:
        # find source & target column names
        s_col = None
        for c in ["source_id", "source", "from", "From"]:
            if c in relations_df.columns:
                s_col = c
                break
        t_col = None
        for c in ["target_id", "target", "to", "To"]:
            if c in relations_df.columns:
                t_col = c
                break
        if s_col is None or t_col is None:
            raise KeyError("Relations CSV must contain source and target columns (e.g. source_id, target_id)")

        # relationship type column
        rel_col = None
        for c in ["relationship_type", "rel_type", "type", "relationship"]:
            if c in relations_df.columns:
                rel_col = c
                break

        for _, row in relations_df.iterrows():
            src = str(row[s_col])
            tgt = str(row[t_col])
            rel_type = row[rel_col] if rel_col and rel_col in row.index else "RELATED_TO"
            edge_props = parse_properties_from_row(row, drop_cols=[s_col, t_col, rel_col])
            # ensure nodes exist (create placeholder if necessary)
            if src not in G:
                G.add_node(src, node_type="unknown", placeholder=True)
            if tgt not in G:
                G.add_node(tgt, node_type="unknown", placeholder=True)
            attrs = {"relationship": rel_type}
            attrs.update(edge_props)
            G.add_edge(src, tgt, **attrs)

    return G


def export_pyvis(G: nx.DiGraph, output_html: str = "technical_kg_poc.html", open_in_browser: bool = True):
    import os
    import webbrowser

    if G.number_of_nodes() == 0:
        logging.warning("Graph is empty: 0 nodes. Nothing to export.")
        return

    net = Network(
        notebook=False,
        directed=True,
        height="750px",
        width="100%",
        bgcolor="#222222",
        font_color="white"
    )

    try:
        net.repulsion(node_distance=200, spring_length=200)
    except Exception:
        pass

    # Add nodes
    for node_id, data in G.nodes(data=True):
        label = data.get("part_number") or data.get("name") or node_id
        title_lines = [f"Type: {data.get('node_type','N/A')}"]
        for k, v in data.items():
            if k == "node_type":
                continue
            if isinstance(v, (dict, list)):
                v_text = json.dumps(v)
            else:
                v_text = str(v)
            title_lines.append(f"{k.replace('_',' ').title()}: {v_text}")
        title = "<br>".join(title_lines)
        net.add_node(node_id, label=label, title=title, group=data.get('node_type', 'default'))

    # Add edges
    for u, v, edata in G.edges(data=True):
        label = edata.get('relationship', edata.get('relationship_type', ''))
        title = "; ".join(f"{k}: {v}" for k, v in edata.items())
        net.add_edge(u, v, title=title, label=label)

    # Save to HTML and open in browser
    logging.info("Writing HTML visualization to %s", output_html)
    net.write_html(output_html)  # safer than net.show() in VS Code
    if open_in_browser:
        webbrowser.open('file://' + os.path.abspath(output_html))



def main():
    parser = argparse.ArgumentParser(description="Build a knowledge graph from CSVs and export an interactive HTML (pyvis)")
    parser.add_argument("--nodes-doc", default="NodeDocuments.csv", help="CSV with document nodes (default: NodeDocuments.csv)")
    parser.add_argument("--nodes-draw", default="NodesAssemblyDrawings.csv", help="CSV with drawing nodes (default: NodesAssemblyDrawings.csv)")
    parser.add_argument("--relations", default="Relations.csv", help="CSV with relationships (default: Relations.csv)")
    parser.add_argument("--output", default="technical_kg_poc.html", help="Output HTML file")
    parser.add_argument("--no-open", action="store_true", help="Do not open the generated HTML in a browser")
    parser.add_argument("--create-sample-if-missing", action="store_true", help="Create sample CSVs if any input file is missing and use them")
    args = parser.parse_args()

    nodes_doc_df = read_csv_if_exists(args.nodes_doc)
    nodes_draw_df = read_csv_if_exists(args.nodes_draw)
    relations_df = read_csv_if_exists(args.relations)

    if args.create_sample_if_missing and (nodes_doc_df is None or nodes_draw_df is None or relations_df is None):
        s_doc, s_draw, s_rel = create_sample_files()
        nodes_doc_df = read_csv_if_exists(s_doc)
        nodes_draw_df = read_csv_if_exists(s_draw)
        relations_df = read_csv_if_exists(s_rel)
    else:
        # if any are missing, create sample automatically (friendly behaviour)
        if nodes_doc_df is None or nodes_draw_df is None or relations_df is None:
            logging.warning("One or more input CSVs not found. Creating sample CSVs in ./sample_data/ and using them.")
            s_doc, s_draw, s_rel = create_sample_files()
            nodes_doc_df = read_csv_if_exists(s_doc)
            nodes_draw_df = read_csv_if_exists(s_draw)
            relations_df = read_csv_if_exists(s_rel)

    # Build graph
    G = build_graph(nodes_doc_df, nodes_draw_df, relations_df)
    logging.info("Graph built: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())

    # Export to HTML (pyvis)
    export_pyvis(G, args.output, open_in_browser=(not args.no_open))


if __name__ == "__main__":
    main()
