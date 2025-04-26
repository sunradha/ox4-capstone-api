from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.analyzer import run_reasoning_pipeline

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str


@router.post("/ask-question")
def process_question(request: QuestionRequest):
    question = request.question

    try:
        reasoning_result = run_reasoning_pipeline(question)

        return {
            "status": "success",
            "reasoning_result": reasoning_result,
            "message": "Reasoning pipeline executed successfully.",
            "details": reasoning_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
