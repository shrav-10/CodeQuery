import os
from typing import Optional, List, Dict, Any
import chromadb


CHROMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "chroma"
)

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_or_create_collection(
    name="code_chunks_fast"
)


def add_code_chunk(
    chunk_id: str,
    embedding: list,
    code: str,
    metadata: dict
):
    """Add or update a single code chunk in ChromaDB."""
    collection.upsert(
        ids=[chunk_id],
        embeddings=[embedding],
        documents=[code],
        metadatas=[metadata]
    )


def add_code_chunks(
    chunk_ids: list,
    embeddings: list,
    codes: list,
    metadatas: list,
    batch_size: int = 500
):
    """
    Add or update multiple code chunks in ChromaDB in manageable batches.
    """
    if not chunk_ids:
        return

    total = len(chunk_ids)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        collection.upsert(
            ids=chunk_ids[start:end],
            embeddings=embeddings[start:end],
            documents=codes[start:end],
            metadatas=metadatas[start:end]
        )


def search_code(
    query_embedding: list,
    number_of_results: int = 5,
    repository: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for similar code chunks with optional repository filter.
    Safely adjusts n_results to collection count.
    """
    total_count = collection.count()
    if total_count == 0:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

    n_results = min(number_of_results, total_count)
    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": n_results
    }
    if repository:
        query_args["where"] = {"repository": repository}

    try:
        results = collection.query(**query_args)
    except Exception as e:
        # If filtering returned fewer or query failed, retry without where or return empty
        print(f"Chroma query warning: {e}")
        query_args.pop("where", None)
        try:
            results = collection.query(**query_args)
        except Exception:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    return results


def get_indexed_repositories() -> List[str]:
    """Get list of distinct repository names stored in ChromaDB."""
    try:
        data = collection.get(include=["metadatas"])
        repos = set()
        for meta in data.get("metadatas", []):
            if meta and "repository" in meta:
                repos.add(meta["repository"])
        return sorted(list(repos))
    except Exception:
        return []