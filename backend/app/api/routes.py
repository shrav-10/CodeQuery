import os
import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.schemas.query import QueryRequest
from app.services.repository_service import clone_repository, REPOSITORIES_DIR
from app.services.code_parser import scan_repository
from app.services.indexer import index_repository
from app.services.rag_service import answer_code_question
from app.services.graph_service import (
    get_graph_visualization_data,
    get_graph_statistics,
    load_graph
)
from app.services.vector_store import get_indexed_repositories, collection

router = APIRouter()


class RepositoryRequest(BaseModel):
    repository_url: str
    include_tests: Optional[bool] = False


class EvaluationRequest(BaseModel):
    repository: str
    queries: Optional[List[str]] = None


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "CodeQuery",
        "description": "Structure-Aware RAG Assistant for Codebase Understanding",
        "features": {
            "ast_parsing": True,
            "structural_graph": True,
            "fast_embeddings": True,
            "citation_grounding": True
        }
    }


@router.get("/repositories")
def list_repositories():
    """
    List all indexed and downloaded repositories with their stats.
    """
    indexed_repos = get_indexed_repositories()
    available_repos = []

    # Check local downloaded repos directory
    if os.path.exists(REPOSITORIES_DIR):
        for name in os.listdir(REPOSITORIES_DIR):
            repo_path = os.path.join(REPOSITORIES_DIR, name)
            if os.path.isdir(repo_path) and not name.startswith("."):
                graph_stats = get_graph_statistics(name)
                available_repos.append({
                    "name": name,
                    "is_indexed": name in indexed_repos,
                    "graph_stats": graph_stats
                })

    return {
        "repositories": available_repos,
        "indexed_names": indexed_repos,
        "total_chroma_chunks": collection.count()
    }


@router.post("/analyze-repository")
def analyze_repository(request: RepositoryRequest):
    """
    Ingest, parse (parallel AST), construct structural graph (NetworkX),
    generate embeddings (FastEmbed), and store in vector database (ChromaDB).
    """
    try:
        start_time = time.time()
        url_or_path = request.repository_url.strip()

        # Handle local directory path or GitHub URL
        if os.path.isdir(url_or_path):
            repository_path = url_or_path
            repo_name = os.path.basename(os.path.normpath(repository_path))
        else:
            repository_path = clone_repository(url_or_path)
            repo_name = os.path.basename(os.path.normpath(repository_path))

        # Parallel AST Parsing
        parse_start = time.time()
        parsed_files = scan_repository(
            repository_path=repository_path,
            include_tests=request.include_tests or False
        )
        parse_time = round(time.time() - parse_start, 2)

        # Graph Building, Chunking, Embedding & Indexing
        index_result = index_repository(parsed_files, repo_name=repo_name)

        total_time = round(time.time() - start_time, 2)

        return {
            "status": "success",
            "repository_name": repo_name,
            "repository_url": request.repository_url,
            "repository_path": repository_path,
            "files_analyzed": len(parsed_files),
            "parse_time_seconds": parse_time,
            "chunks_indexed": index_result.get("chunks", 0),
            "graph_nodes": index_result.get("graph_nodes", 0),
            "graph_edges": index_result.get("graph_edges", 0),
            "graph_time_seconds": index_result.get("graph_time", 0),
            "embedding_time_seconds": index_result.get("embedding_time", 0),
            "storage_time_seconds": index_result.get("storage_time", 0),
            "total_time_seconds": total_time,
            "message": f"Successfully analyzed {len(parsed_files)} files ({index_result.get('chunks', 0)} chunks, {index_result.get('graph_nodes', 0)} graph nodes) in {total_time}s."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Could not analyze repository.",
            "error": str(e)
        }


@router.post("/query")
def query_code(request: QueryRequest):
    """
    Query repository using Structure-Aware RAG with NetworkX structural graph expansion
    and exact file:line citations.
    """
    try:
        result = answer_code_question(
            question=request.question,
            repository=request.repository,
            top_k=request.top_k or 4,
            preferred_provider=request.provider
        )
        return {
            "status": "success",
            **result
        }
    except Exception as e:
        return {
            "status": "error",
            "question": request.question,
            "answer": f"Error answering question: {str(e)}",
            "citations": [],
            "retrieved_chunks": [],
            "error": str(e)
        }


@router.get("/repository/{repo_name}/graph")
def get_repository_graph(repo_name: str, max_nodes: int = 100):
    """
    Retrieve structural graph visualization data for the given repository.
    """
    try:
        data = get_graph_visualization_data(repo_name, max_nodes=max_nodes)
        return {
            "status": "success",
            "repository": repo_name,
            **data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repository/{repo_name}/file")
def get_file_content(
    repo_name: str,
    file_path: str = Query(..., description="Relative file path"),
    start_line: Optional[int] = None,
    end_line: Optional[int] = None
):
    """
    View file content with optional line highlighting for citation inspection.
    """
    base_dir = os.path.join(REPOSITORIES_DIR, repo_name)
    clean_path = file_path.replace("\\", "/").lstrip("/")
    abs_path = os.path.normpath(os.path.join(base_dir, clean_path))

    # Security check to prevent directory traversal
    if not abs_path.startswith(os.path.normpath(base_dir)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        s_line = max(1, start_line or 1)
        e_line = min(total_lines, end_line or total_lines)

        slice_lines = lines[s_line - 1:e_line]
        return {
            "file": clean_path,
            "repository": repo_name,
            "total_lines": total_lines,
            "start_line": s_line,
            "end_line": e_line,
            "content": "".join(slice_lines),
            "full_content": "".join(lines) if total_lines <= 500 else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
def run_evaluation(request: EvaluationRequest):
    """
    Evaluate retrieval precision, citation presence, and response latency (Objective 5).
    """
    test_queries = request.queries or [
        "How is authentication or session management implemented?",
        "What are the main classes and how do they inherit from each other?",
        "Explain the request handling and retry mechanism.",
        "What exceptions and error handlers are defined?"
    ]

    results = []
    total_time = 0.0
    citations_count = 0

    for q in test_queries:
        t0 = time.time()
        res = answer_code_question(question=q, repository=request.repository, top_k=4)
        duration = time.time() - t0
        total_time += duration
        cits = res.get("citations", [])
        citations_count += len(cits)

        results.append({
            "query": q,
            "has_citations": len(cits) > 0,
            "citation_count": len(cits),
            "citations": [c["citation"] for c in cits],
            "retrieved_chunks_count": len(res.get("retrieved_chunks", [])),
            "has_graph_expansion": res.get("graph_context", {}).get("has_graph", False),
            "graph_relationships_count": len(res.get("graph_context", {}).get("relationships", [])),
            "duration_seconds": round(duration, 2),
            "answer_preview": res.get("answer", "")[:150] + "..."
        })

    avg_time = round(total_time / len(test_queries), 2) if test_queries else 0.0

    return {
        "repository": request.repository,
        "total_queries_evaluated": len(test_queries),
        "citation_coverage_rate": f"{round((sum(1 for r in results if r['has_citations']) / len(test_queries)) * 100, 1)}%",
        "average_query_latency_seconds": avg_time,
        "total_citations_generated": citations_count,
        "evaluations": results
    }