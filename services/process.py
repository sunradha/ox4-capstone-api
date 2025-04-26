from fastapi import HTTPException
import pandas as pd  # For handling HTTP exceptions
from services.datafetcher import fetch_data_from_supabase, \
    fetch_data_from_supabase_psycopg2  # For fetching data from Supabase
from services.formatter import format_data_for_openai
from services.graph import generate_process_graph
from utils.sql_queries import sql_queries, reasoning_queries  # For SQL and reasoning queries
from utils.visualizer import (
    visualize_process_mining,
    visualize_knowledge_graph,
    visualize_causal_graph
)  # For visualizations
from utils.openai_client import query_openai_o3  # For querying OpenAI
from models.schemas import QueryRequest  # For handling request models


def run_analysis(analysis_type):
    """
    Runs the complete workflow for the specified analysis type.

    Args:
        analysis_type: 'process_mining', 'knowledge_graph', or 'causal_graph'
    """
    if analysis_type not in ['process_mining', 'knowledge_graph', 'causal_graph']:
        raise ValueError("Invalid analysis type. Choose from: process_mining, knowledge_graph, causal_graph")

    # Fetch data using the appropriate SQL query
    query_key = f"{analysis_type}_events" if analysis_type == "process_mining" else f"{analysis_type}_relationships"
    data = fetch_data_from_supabase_psycopg2(sql_queries[query_key])

    # Query OpenAI with the appropriate reasoning query
    insights = query_openai_o3(data.to_json(), reasoning_queries[analysis_type])

    # Visualize results using the appropriate function
    if analysis_type == "process_mining":
        visualize_process_mining(data)
    elif analysis_type == "knowledge_graph":
        visualize_knowledge_graph(data)
    elif analysis_type == "causal_graph":
        visualize_causal_graph(data)

    return {"insights": insights}  # You might need to adjust response data as needed


async def handle_process_request(request: QueryRequest):
    query_type = request.query_type
    filters = request.filters or {}

    if query_type == "process_mining":
        data = fetch_data_from_supabase("workforce_reskilling_events", filters)
    elif query_type == "knowledge_graph":
        employees = fetch_data_from_supabase("employee_profile")
        jobs = fetch_data_from_supabase("job_risk")
        cases = fetch_data_from_supabase("workforce_reskilling_cases", filters)

        df = pd.DataFrame(employees).merge(pd.DataFrame(jobs), on="soc_code", how="left")
        df = df.merge(pd.DataFrame(cases), on="employee_id", how="left")
        data = df.to_dict(orient="records")

    elif query_type == "causal_graph":
        employees = fetch_data_from_supabase("employee_profile")
        jobs = fetch_data_from_supabase("job_risk")
        cases = fetch_data_from_supabase("workforce_reskilling_cases", filters)
        events = fetch_data_from_supabase("workforce_reskilling_events")

        df = pd.DataFrame(employees).merge(pd.DataFrame(jobs), on="soc_code", how="left")
        df = df.merge(pd.DataFrame(cases), on="employee_id", how="left")
        df = df.merge(pd.DataFrame(events), on="case_id", how="left")
        data = df.to_dict(orient="records")

    else:
        raise HTTPException(status_code=400, detail="Invalid query_type")

    formatted_data = format_data_for_openai(data, query_type)
    print("=================================")
    print(formatted_data)
    print("=================================")
    graph_image = generate_process_graph(data) if query_type == "process_mining" else None

    return {
        "data": formatted_data,
        "graph_image": graph_image
    }
