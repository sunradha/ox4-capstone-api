from fastapi import APIRouter, HTTPException
from models.schemas import QueryRequest, ReasoningRequest
from services.process import handle_process_request
from services.reasoning import query_openai_reasoning
from db.client import supabase
import pandas as pd

router = APIRouter()


@router.post("/process-mining")
async def process_mining(request: QueryRequest):
    return await handle_process_request(request)


@router.post("/reasoning")
async def reasoning_query(request: ReasoningRequest):
    return await query_openai_reasoning(request.data, request.question)


@router.get("/training-performance")
def training_performance():
    result = supabase.table("training_program_performance").select("*").execute()
    return result.data


@router.get("/high-risk-roles")
def get_high_risk_roles():
    result = supabase.table("job_risk").select("job_title, automation_probability").gt("automation_probability",
                                                                                       0.7).execute()
    return result.data


@router.get("/training-effectiveness")
def get_training_effectiveness():
    result = supabase.table("workforce_reskilling_cases").select("*").execute()
    if not result.data:
        return {"message": "No data found"}

    df = pd.DataFrame(result.data)
    effectiveness = df.groupby("training_program")["certification_earned"].mean().reset_index()
    effectiveness['certification_earned'] = effectiveness['certification_earned'].apply(
        lambda x: "Success" if x >= 0.5 else "Failure")

    return effectiveness.to_dict(orient="records")
