from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.query import QueryRequest
from app.services.repository_service import clone_repository
from app.services.code_parser import scan_repository
from app.services.rag_service import answer_code_question


router = APIRouter()


class RepositoryRequest(BaseModel):
    repository_url: str


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "CodeQuery"
    }


@router.post("/analyze-repository")
def analyze_repository(request: RepositoryRequest):
    try:
        repository_path = clone_repository(
            request.repository_url
        )

        parsed_files = scan_repository(
            repository_path
        )

        return {
            "status": "success",
            "repository_url": request.repository_url,
            "repository_path": repository_path,
            "files_analyzed": len(parsed_files),
            "message": "Repository cloned and analyzed successfully."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Could not analyze repository.",
            "error": str(e)
        }


@router.post("/query")
def query_code(request: QueryRequest):
    try:

        # -----------------------------------------
        # Send the question through the RAG pipeline
        # -----------------------------------------

        answer = answer_code_question(
            request.question
        )

        return {
            "question": request.question,
            "answer": answer
        }

    except Exception as e:

        return {
            "question": request.question,
            "answer": "Sorry, I couldn't process your question.",
            "error": str(e)
        }