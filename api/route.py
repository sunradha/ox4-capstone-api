import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.analyzer import run_reasoning_pipeline

router = APIRouter()

logger = logging.getLogger(__name__)


class QuestionRequest(BaseModel):
    question: str


@router.post("/ask-question")
def process_question(request: QuestionRequest):
    question = request.question

    try:
        reasoning_result = run_reasoning_pipeline(question)
        is_success = reasoning_result.get("error") is None

        return {
            "status": "success" if is_success else "failure",
            "result": reasoning_result
        }
    except Exception as e:
        logger.error(f"Pipeline execution error: {e}")
        return {
            "status": "failure",
            "result": {
                "reasoning_type": None,
                "reasoning_justification": None,
                "intent": None,
                "intent_justification": None,
                "reasoning_answer": None,
                "graph": None,
                "error": str(e)
            }
        }
