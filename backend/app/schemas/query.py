from typing import Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    code: Optional[str] = ""
    repository: Optional[str] = None
    top_k: Optional[int] = 4
    provider: Optional[str] = None