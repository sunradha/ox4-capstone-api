from llm.openai_client import call_llm
from llm.prompts import get_kg_data_prompt, get_reasoning_answer_prompt, get_cg_data_prompt
from utils.utils import parsed_graph_output, parsed_kg_sql_output, clean_dataframe_columns, parsed_kg_data_output, \
    parse_final_answer_response


def process_knowledge_graph(question, reasoning_type, db_data_json):
    data_kg_prompt = get_kg_data_prompt(question, reasoning_type, db_data_json)
    data_kg_response = call_llm(data_kg_prompt)
    reasoning_answer, data_nodes, data_edges = parsed_kg_data_output(data_kg_response)

    graph_schema = {
        "reasoning_answer": reasoning_answer,
        "data_nodes": data_nodes,
        "data_edges": data_edges
    }
    return graph_schema


def process_causal_graph(question, reasoning_type, db_data_json):
    data_cg_prompt = get_cg_data_prompt(question, reasoning_type, db_data_json)
    data_cg_response = call_llm(data_cg_prompt)
    reasoning_answer, data_nodes, data_edges = parsed_kg_data_output(data_cg_response)

    graph_schema = {
        "reasoning_answer": reasoning_answer,
        "data_nodes": data_nodes,
        "data_edges": data_edges
    }
    return graph_schema


def process_process_flow(question, reasoning_type, db_data_json):
    data_cg_prompt = get_cg_data_prompt(question, reasoning_type, db_data_json)
    data_cg_response = call_llm(data_cg_prompt)
    reasoning_answer, data_nodes, data_edges = parsed_kg_data_output(data_cg_response)
    graph_schema = {
        "reasoning_answer": reasoning_answer,
        "data_nodes": data_nodes,
        "data_edges": data_edges
    }
    return graph_schema


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
