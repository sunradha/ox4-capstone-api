from fastapi import HTTPException
from models.schemas import QueryRequest
from db.client import supabase
from services.graph import generate_process_graph
from services.formatter import format_data_for_openai
import pandas as pd


def fetch_data_from_supabase(table_name: str, filters: dict = None):
    query = supabase.table(table_name).select("*")

    if filters:
        for key, value in filters.items():
            if key == "skill_category":
                query = query.eq("skill_category", value)
            elif key == "outcome":
                query = query.eq("certification_earned", value.lower() == "success")
            else:
                query = query.eq(key, value)

    try:
        result = query.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase error: {str(e)}")

    if not result.data:
        raise HTTPException(status_code=404, detail="No data found")

    return result.data


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
    graph_image = generate_process_graph(data) if query_type == "process_mining" else None

    return {
        "data": formatted_data,
        "graph_image": graph_image
    }
