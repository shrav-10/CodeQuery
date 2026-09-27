from pydantic import BaseModel


class QueryRequest(BaseModel):
    code: str
    question: str