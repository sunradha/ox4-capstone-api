from db.client import run_sql_query_postgres
from llm.openai_client import call_llm
from db.schemas import TABLE_SCHEMAS
from llm.prompts import get_kg_sql_prompt, get_kg_data_prompt, get_sql_prompt, get_reasoning_answer_prompt
from utils.utils import parsed_graph_output, parsed_kg_sql_output, clean_dataframe_columns, parsed_kg_data_output, \
    parse_final_answer_response


def process_knowledge_graph(question, reasoning_type, db_data_json):

    data_kg_prompt = get_kg_data_prompt(question, reasoning_type, db_data_json)
    data_kg_response = call_llm(data_kg_prompt)
    print("Data Response :\n", data_kg_response)
    reasoning_answer, data_nodes, data_edges = parsed_kg_data_output(data_kg_response)
    print("----------------------------------------------------")
    print(reasoning_answer)
    print(data_nodes)
    print(data_edges)
    print("----------------------------------------------------")

    graph_schema = {
        "reasoning_answer": reasoning_answer,
        "data_nodes": data_nodes,
        "data_edges": data_edges
    }
    return graph_schema


def process_causal_graph(question, reasoning_type, visualization_type):
    schema_response = call_llm(get_cg_sql_prompt(question, reasoning_type, visualization_type))
    parsed_schema = parsed_graph_output(schema_response, visualization_type)
    sql = parsed_schema.get('generated_sql')
    cause_nodes = parsed_schema['graph_schema'].get('cause_nodes')
    effect_nodes = parsed_schema['graph_schema'].get('effect_nodes')
    causal_edges = parsed_schema['graph_schema'].get('causal_edges')

    df = run_sql_query_postgres(sql)
    if df.empty:
        raise ValueError("No data returned from database.")

    db_data_json = df.to_json(orient='records')
    data_cg_response = call_llm(get_kg_data_prompt(question, db_data_json))
    parsed_data_cg = parsed_data_kg_output(data_cg_response)

    graph_schema = {
        "reasoning_answer": parsed_schema.get('reasoning_answer'),
        "schema_nodes": cause_nodes + effect_nodes,
        "schema_edges": causal_edges,
        "data_nodes": parsed_data_cg.get('nodes'),
        "data_edges": parsed_data_cg.get('edges')
    }
    return graph_schema, df


def process_process_flow(question, reasoning_type, db_data_json):
    schema_response = call_llm(get_process_flow_prompt(question, reasoning_type))
    parsed_schema = parsed_graph_output(schema_response, "Process Flow")
    sql = parsed_schema.get('generated_sql')
    process_nodes = parsed_schema['graph_schema'].get('nodes')
    process_edges = parsed_schema['graph_schema'].get('edges')

    df = run_sql_query_postgres(sql)
    if df.empty:
        raise ValueError("No data returned from database.")

    db_data_json = df.to_json(orient='records')
    data_pf_response = call_llm(get_kg_data_prompt(question, db_data_json))
    parsed_data_pf = parsed_data_kg_output(data_pf_response)

    graph_schema = {
        "reasoning_answer": parsed_schema.get('reasoning_answer'),
        "schema_nodes": process_nodes,
        "schema_edges": process_edges,
        "data_nodes": parsed_data_pf.get('nodes'),
        "data_edges": parsed_data_pf.get('edges')
    }
    return graph_schema, df


def process_charts(question, reasoning_type, visualization_type, db_data_json):
    llm_graph_prompt = get_reasoning_answer_prompt(question, reasoning_type, visualization_type, db_data_json)
    llm_response = call_llm(llm_graph_prompt)
    reasoning_answer = parse_final_answer_response(llm_response)
    graph_schema = {
        "reasoning_answer": reasoning_answer,
        "data_nodes": None,
        "data_edges": None
    }
    return graph_schema

# def generate_schema_kg_and_sql(question, reasoning_type, visualization_type):
#     kg_sql_prompt = get_kg_sql_prompt(question, reasoning_type, visualization_type)
#     return call_llm(kg_sql_prompt)
#
#
# def generate_data_kg(question, db_data):
#     kg_sql_prompt = get_kg_data_prompt(question, reasoning_type)
#     return call_llm(kg_sql_prompt)
#
#
# def knowledge_graph_pipeline(question, reasoning_type, visualization_type):
#     schema_kg_and_sql = generate_schema_kg_and_sql(question, reasoning_type, visualization_type)
#
#     data_kg = generate_data_kg(question, db_data)
#     # Step 1: Generate KG schema + SQL
#     prompt_step1 = f"""
#     You are an assistant generating SQL queries and Knowledge Graph construction logic.
#
#     Reasoning Type: {reasoning_type}
#     Visualization Type: {visualization_type}
#     Schemas:
#     {TABLE_SCHEMAS}
#
#     User Question: "{question}"
#
#     ⚡ IMPORTANT RULES:
#     - Provide both the conceptual KG schema (based on schema relationships) AND the SQL query.
#     - Alias final SQL columns as: node_id, node_label, node_type, source, target, relationship.
#     - Deduplicate nodes using DISTINCT ON, GROUP BY, or window functions.
#     - Explain all joins and relationships.
#
#     ⚠️ NOTE: You cannot access real data values. Your SQL query will be run on the database to extract real nodes and edges.
#
#     OUTPUT SECTIONS:
#     1. Reasoning Answer:
#     <Explain the graph logic and SQL approach>
#
#     2. SQL Query:
#     ```sql
#     <SQL query here>
#     ```
#
#     3. Conceptual Knowledge Graph Schema:
#     Nodes:
#     - <column>: <entity_type>
#     Edges:
#     - source: <column>, target: <column>, relationship: <relationship_label>
#     """
#
#     # → Send prompt_step1 to LLM
#     step1_response = call_llm(prompt_step1)
#
#     # === OPTIONAL: Run SQL on your backend ===
#     # db_data = run_sql_on_db(step1_response["sql_query"])
#
#     if db_data is None:
#         return step1_response
#
#     # Step 2: Build data-driven KG from real DB data
#     prompt_step2 = f"""
#     You are an assistant creating a data-driven Knowledge Graph.
#
#     Here is the real query result data:
#     {db_data}
#
#     ⚡ IMPORTANT:
#     - Extract unique nodes and edges.
#     - Identify node_id, node_label, node_type.
#     - Identify source, target, and relationship for edges.
#     - Return the KG in JSON format:
#     {{
#       "nodes": [{{ "id": "node_id", "label": "node_label", "type": "node_type" }}],
#       "edges": [{{ "source": "source_id", "target": "target_id", "relationship": "edge_label" }}]
#     }}
#
#     Provide only the final JSON, no explanation.
#     """
#
#     # → Send prompt_step2 to LLM
#     step2_response = call_llm(prompt_step2)
#
#     return {
#         "step1": step1_response,
#         "step2": step2_response
#     }
