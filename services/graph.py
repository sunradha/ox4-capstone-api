from typing import List, Dict
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pandas as pd


def generate_process_graph(data: List[Dict[str, any]]) -> str:
    G = nx.DiGraph()
    df = pd.DataFrame(data)

    for case_id, group in df.groupby('case_id'):
        group = group.sort_values('timestamp')
        activities = group['activity'].tolist()

        for i in range(len(activities) - 1):
            src, tgt = activities[i], activities[i + 1]
            if G.has_edge(src, tgt):
                G[src][tgt]['weight'] += 1
            else:
                G.add_edge(src, tgt, weight=1)

    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='gray')
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()
