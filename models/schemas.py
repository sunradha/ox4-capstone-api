from typing import Optional, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query_type: str
    filters: Optional[Dict[str, Any]] = None


class ReasoningRequest(BaseModel):
    data: Dict[str, Any]
    question: str
