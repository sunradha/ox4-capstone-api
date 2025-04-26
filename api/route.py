from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.analyzer import run_reasoning_pipeline
from services.reasoning import get_reasoning_category_and_intent
from db.schemas import WORKFORCE_RESKILLING_SCHEMAS

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str


@router.post("/ask-question")
def process_question(request: QuestionRequest):
    question = request.question
    schemas = WORKFORCE_RESKILLING_SCHEMAS

    try:
        # Step 1: Categorize reasoning type (no schemas needed here)
        reasoning_type = get_reasoning_category_and_intent(question)

        # Step 2: Run the full reasoning pipeline (pass reasoning type + schemas)
        reasoning_result = run_reasoning_pipeline(
            schemas=schemas,
            question=question
        )

        # Step 3: Return reasoning type and reasoning result
        return {
            "status": "success",
            "reasoning_type": reasoning_type,
            "message": "Reasoning pipeline executed successfully.",
            "details": reasoning_result  # Can include SQL, explanation, plot code if needed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
