# services/graph.py

def convert_to_knowledge_graph(data):
    """
    Converts a DataFrame into nodes and edges for Knowledge Graph visualization.

    Expected Data Columns:
        - occupation_title
        - automation_probability
        - participation_count

    Returns:
        dict: {"nodes": [...], "edges": [...]}
    """
    nodes = []
    edges = []
    added_nodes = set()

    for _, row in data.iterrows():
        occupation_id = f"Occupation: {row['occupation_title']}"
        risk_id = f"Risk: {row['automation_probability']:.2f}"
        participation_id = f"Participation: {row['participation_count']}"

        # Add nodes
        if occupation_id not in added_nodes:
            nodes.append({"id": occupation_id, "type": "Occupation", "label": row['occupation_title']})
            added_nodes.add(occupation_id)
        if risk_id not in added_nodes:
            nodes.append({"id": risk_id, "type": "Risk", "label": f"Risk: {row['automation_probability']:.2f}"})
            added_nodes.add(risk_id)
        if participation_id not in added_nodes:
            nodes.append({"id": participation_id, "type": "Participation", "label": f"Participation: {row['participation_count']}"})
            added_nodes.add(participation_id)

        # Add edges
        edges.append({"source": occupation_id, "target": risk_id, "relationship": "has automation risk"})
        edges.append({"source": occupation_id, "target": participation_id, "relationship": "has reskilling participation"})

    return {"nodes": nodes, "edges": edges}


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
        relationship_label = f"causes" + (f" (Confidence: {row['confidence']})" if 'confidence' in row and row['confidence'] is not None else "")

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
