import os
import io
import re
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import base64
from pyvis.network import Network


def render_knowledge_graph_interactive(df, nodes_info, edges_info, output_html_path=None):
    """
    Renders an interactive Knowledge Graph using PyVis (Vis.js-based).
    Args:
        df (pd.DataFrame): SQL query result as DataFrame.
        nodes_info (str): Node definitions from LLM output.
        edges_info (str): Edge definitions from LLM output.
        output_html_path (str): Path to save the interactive HTML file.
    Returns:
        str: Path to the generated HTML file.
    """
    net = Network(height="800px", width="100%", directed=False)
    net.barnes_hut()  # Physics-based layout (similar to spring layout)

    # Parse nodes
    nodes = []
    for line in nodes_info.strip().split('\n'):
        if ':' in line:
            clean_line = re.sub(r'^[-*]\s+', '', line)
            col_name = clean_line.split(':')[0].strip()
            nodes.append(col_name)

    # Add nodes
    for node_col in nodes:
        for val in df[node_col].dropna().unique():
            net.add_node(str(val), label=str(val))

    # Parse edges
    edge_lines = edges_info.strip().split('\n')
    for line in edge_lines:
        source_match = re.search(r'source: (.*?),', line)
        target_match = re.search(r'target: (.*?),', line)
        relationship_match = re.search(r'relationship: (.*)', line)
        if source_match and target_match and relationship_match:
            src_col = source_match.group(1).strip()
            tgt_col = target_match.group(1).strip()
            relationship = relationship_match.group(1).strip()

            for _, row in df.iterrows():
                if pd.notnull(row[src_col]) and pd.notnull(row[tgt_col]):
                    net.add_edge(str(row[src_col]), str(row[tgt_col]), label=relationship)

    # If no output path was provided, create the output directory and set the default file name
    if not output_html_path:
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)
        output_html_path = os.path.join(output_dir, "knowledge_graph_interactive.html")

    # ✅ Now generate the interactive HTML using PyVis
    net.show(output_html_path)
    print(f"✅ Interactive Knowledge Graph saved at: {output_html_path}")

    return output_html_path  # Always return the final saved file path


def render_knowledge_graph(df, nodes_info, edges_info):
    G = nx.Graph()

    # Parse nodes
    nodes = []
    for line in nodes_info.strip().split('\n'):
        if ':' in line:
            # Remove "- " or "* " at the start
            clean_line = re.sub(r'^[-*]\s+', '', line)
            col_name = clean_line.split(':')[0].strip()
            nodes.append(col_name)

    # Validate node columns exist in the DataFrame
    missing_node_cols = [col for col in nodes if col not in df.columns]
    if missing_node_cols:
        raise ValueError(f"Missing node columns in data: {missing_node_cols}")

    # Add nodes to graph
    for node_col in nodes:
        unique_nodes = df[node_col].dropna().unique()
        G.add_nodes_from(unique_nodes)

    # Parse edges
    edge_lines = edges_info.strip().split('\n')
    for line in edge_lines:
        source_match = re.search(r'source: (.*?),', line)
        target_match = re.search(r'target: (.*?),', line)
        relationship_match = re.search(r'relationship: (.*)', line)

        if source_match and target_match and relationship_match:
            src_col = source_match.group(1).strip()
            tgt_col = target_match.group(1).strip()
            relationship = relationship_match.group(1).strip()

            # Validate edge columns exist
            if src_col not in df.columns or tgt_col not in df.columns:
                raise ValueError(f"Missing edge columns in data: {src_col}, {tgt_col}")

            # Add edges to the graph
            for _, row in df.iterrows():
                if pd.notnull(row[src_col]) and pd.notnull(row[tgt_col]):
                    G.add_edge(row[src_col], row[tgt_col], label=relationship)

    # Plot the graph
    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(G, k=0.5)
    nx.draw(G, pos, with_labels=True, node_size=300, node_color='skyblue', font_size=8)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)
    plt.tight_layout()

    # Save plot to Base64 image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')  # Save BEFORE closing or showing
    buf.seek(0)

    plt.close()  # Now safe to close

    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    output_file_path = os.path.join(output_dir, "knowledge_graph_output.png")

    with open(output_file_path, "wb") as f:
        f.write(buf.getvalue())

    # Return Base64 for API use
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return image_base64


def convert_to_causal_graph(data):
    """
    Converts a DataFrame into nodes and edges for Causal Graph visualization.

    Expected Data Columns:
        - cause
        - effect
        - confidence (optional)

    Returns:
        dict: {"nodes": [...], "edges": [...]}
    """
    nodes = []
    edges = []
    added_nodes = set()

    for _, row in data.iterrows():
        cause_id = f"Cause: {row['cause']}"
        effect_id = f"Effect: {row['effect']}"
        relationship_label = f"causes" + (
            f" (Confidence: {row['confidence']})" if 'confidence' in row and row['confidence'] is not None else "")

        # Add nodes
        if cause_id not in added_nodes:
            nodes.append({"id": cause_id, "type": "Cause", "label": row['cause']})
            added_nodes.add(cause_id)
        if effect_id not in added_nodes:
            nodes.append({"id": effect_id, "type": "Effect", "label": row['effect']})
            added_nodes.add(effect_id)

        # Add edge
        edges.append({
            "source": cause_id,
            "target": effect_id,
            "relationship": relationship_label
        })

    return {"nodes": nodes, "edges": edges}
