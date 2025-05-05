import re
import json
from typing import Optional, Dict


def parsed_reasoning_output(llm_output):
    result = {
        "reasoning_type": None,
        "reasoning_justification": None,
        "reasoning_path": None,
        "visualization_type": None
    }

    # Extract Reasoning Type
    type_match = re.search(r"Reasoning Type:\s*(.+)", llm_output)
    if type_match:
        result["reasoning_type"] = type_match.group(1).strip()

    # Extract Reasoning Justification
    justification_match = re.search(r"Reasoning Justification:\s*(.+)", llm_output)
    if justification_match:
        result["reasoning_justification"] = justification_match.group(1).strip()

    # Extract Reasoning Path
    path_match = re.search(r"Reasoning Path:\s*(\[[^\]]*\])", llm_output)
    if path_match:
        raw_path = path_match.group(1).strip()
        cleaned_path = re.sub(r'^"\[|\]"$', '[', raw_path).replace('\\"', '"')
        cleaned_path = cleaned_path.replace('"', '')
        result["reasoning_path"] = cleaned_path

    # Extract Visualization Type (only main type, ignore parentheses)
    visualization_match = re.search(r"Visualization Type:\s*(.+)", llm_output)
    if visualization_match:
        visualization_raw = visualization_match.group(1).strip()
        visualization_clean = re.sub(r'\s*\(.*\)', '', visualization_raw).strip()
        result["visualization_type"] = visualization_clean

    return result


def parsed_kg_sql_output(llm_output):
    """
    Parses LLM output for Knowledge Graph
    Returns a structured dictionary.
    """
    result = {
        'reasoning_answer': '',
        'generated_sql': '',
        'graph_schema': {
            'nodes': [],
            'edges': []
        }
    }

    if not llm_output or not isinstance(llm_output, str):
        raise ValueError("LLM output is empty or invalid.")

    # Extract reasoning answer
    reasoning_match = re.search(r'1\.\s*Reasoning Answer:\s*(.*?)(?=2\.\s*SQL Query:)', llm_output, re.DOTALL)
    if reasoning_match:
        result['reasoning_answer'] = reasoning_match.group(1).strip()

    # Extract SQL query
    sql_match = re.search(r'2\.\s*SQL Query:\s*```sql(.*?)```', llm_output, re.DOTALL)
    if sql_match:
        result['generated_sql'] = sql_match.group(1).strip()

    # Extract conceptual schema (nodes + edges)
    schema_match = re.search(
        r'3\.\s*(Conceptual Knowledge Graph Schema|Causal Graph Schema|Process Flow Schema):\s*(.*)', llm_output,
        re.DOTALL)
    if schema_match:
        schema_text = schema_match.group(2).strip()

        # Extract nodes section
        nodes_match = re.search(r'Nodes:\s*- (.*?)(?=(Edges:|Cause Nodes:|Effect Nodes:|Causal Edges:|$))', schema_text,
                                re.DOTALL)
        if nodes_match:
            nodes_raw = nodes_match.group(1).strip().split('\n- ')
            result['graph_schema']['nodes'] = [line.strip() for line in nodes_raw if line.strip()]

        # Extract edges section
        edges_match = re.search(r'Edges:\s*- (.*)', schema_text, re.DOTALL)
        if edges_match:
            edges_raw = edges_match.group(1).strip().split('\n- ')
            result['graph_schema']['edges'] = [line.strip() for line in edges_raw if line.strip()]

    return result


def parsed_kg_data_output(llm_output_str):
    # Extract the Reasoning Answer section
    reasoning_match = re.search(r"1\. Reasoning Answer:\s*(.*?)(?:2\. Nodes & Edges JSON:|$)", llm_output_str,
                                re.DOTALL | re.IGNORECASE)
    reasoning_answer = reasoning_match.group(1).strip() if reasoning_match else ""

    # First try: with markdown fences
    json_match = re.search(r"2\. Nodes & Edges JSON:\s*```json\s*(\{.*?\})\s*```", llm_output_str,
                           re.DOTALL | re.IGNORECASE)

    # Fallback: without markdown fences
    if not json_match:
        json_match = re.search(r"2\. Nodes & Edges JSON:\s*(\{.*\})", llm_output_str, re.DOTALL | re.IGNORECASE)

    json_str = json_match.group(1).strip() if json_match else ""

    # Clean out any accidental ``` fences if present
    json_str = re.sub(r"```json|```", "", json_str, flags=re.IGNORECASE).strip()

    # Parse JSON safely
    try:
        kg_data = json.loads(json_str)
        data_nodes = kg_data.get('nodes', [])
        data_edges = kg_data.get('edges', [])
    except json.JSONDecodeError:
        data_nodes = []
        data_edges = []

    return reasoning_answer, data_nodes, data_edges


def parsed_2sqls(text: str) -> Dict[str, Optional[str]]:
    pattern_nodes = r"1\. Nodes SQL:\s*```sql\s*(.*?)\s*```"
    pattern_edges = r"2\. Edges SQL:\s*```sql\s*(.*?)\s*```"

    nodes_match = re.search(pattern_nodes, text, re.DOTALL | re.IGNORECASE)
    edges_match = re.search(pattern_edges, text, re.DOTALL | re.IGNORECASE)

    result: Dict[str, Optional[str]] = {}

    if nodes_match:
        result['nodes_sql'] = nodes_match.group(1).strip()
    else:
        result['nodes_sql'] = None

    if edges_match:
        result['edges_sql'] = edges_match.group(1).strip()
    else:
        result['edges_sql'] = None

    return result


def parsed_sql(text):
    pattern = r"```sql\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
        return sql
    else:
        return None


def parse_final_answer_response(text):
    pattern = r"Final Answer:\s*(.*)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        final_answer = match.group(1).strip()
        return final_answer
    else:
        return None


def parsed_graph_output(response_text, visualization_type):
    reasoning = re.search(r"1\.\s*Reasoning.*?:\s*(.*?)(?:\n\s*2\.)", response_text, re.DOTALL)
    sql = re.search(r"2\.\s*SQL.*?```sql\n(.*?)```", response_text, re.DOTALL)
    reasoning_answer = reasoning.group(1).strip() if reasoning else ""
    sql_query = sql.group(1).strip() if sql else None

    nodes, edges = None, None
    if visualization_type == "Knowledge Graph":
        nodes = re.search(r"Nodes:\s*(.*?)(?:\nEdges:|\Z)", response_text, re.DOTALL)
        edges = re.search(r"Edges:\s*(.*?)(?:\n|$)", response_text, re.DOTALL)
    elif visualization_type == "Causal Graph":
        nodes = re.search(r"Cause Nodes:\s*(.*?)(?:\nEffect Nodes:|\Z)", response_text, re.DOTALL)
        edges = re.search(r"Causal Edges:\s*(.*?)(?:\n|$)", response_text, re.DOTALL)
    elif visualization_type == "Process Flow":
        nodes = re.search(r"Nodes:\s*(.*?)(?:\nEdges:|\Z)", response_text, re.DOTALL)
        edges = re.search(r"Edges:\s*(.*?)(?:\n|$)", response_text, re.DOTALL)

    return {
        "reasoning_answer": reasoning_answer,
        "generated_sql": sql_query,
        "graph_schema": {
            "nodes": nodes.group(1).strip() if nodes else None,
            "edges": edges.group(1).strip() if edges else None
        }
    }


def clean_dataframe_columns(df):
    # Remove surrounding single or double quotes from all column names
    cleaned_columns = [re.sub(r"^['\"]|['\"]$", '', col) for col in df.columns]
    df.columns = cleaned_columns
    return df
