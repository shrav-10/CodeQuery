import os
import time
from typing import List, Dict, Any, Optional

from app.services.code_chunker import create_code_chunks
from app.services.embedding_service import generate_embeddings_parallel
from app.services.vector_store import add_code_chunks
from app.services.graph_service import build_repository_graph


BATCH_SIZE = 64
MAX_EMBEDDING_WORKERS = 4


def _extract_repo_and_rel_path(file_path: str, default_repo: str = "default") -> tuple[str, str]:
    norm_path = file_path.replace("\\", "/")
    if "/repositories/" in norm_path:
        after_repos = norm_path.split("/repositories/")[-1]
        parts = after_repos.split("/", 1)
        repo_name = parts[0]
        rel_path = parts[1] if len(parts) > 1 else os.path.basename(norm_path)
        return repo_name, rel_path
    repo_name = default_repo or os.path.basename(os.path.dirname(file_path)) or "default"
    rel_path = os.path.basename(file_path)
    return repo_name, rel_path


def index_repository(parsed_files: List[Dict[str, Any]], repo_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete structure-aware indexing pipeline:
    1. Infer repo name
    2. Construct structural relationship graph (NetworkX)
    3. Generate code chunks with docstrings & metadata
    4. Batch generate vector embeddings (FastEmbed)
    5. Batch upsert into ChromaDB with repository partitioning
    """
    total_files = len(parsed_files)
    if not parsed_files:
        return {
            "files": 0,
            "chunks": 0,
            "graph_nodes": 0,
            "graph_edges": 0,
            "total_time": 0.0
        }

    # Infer repository name if not provided
    if not repo_name:
        first_file = parsed_files[0].get("file", "")
        repo_name, _ = _extract_repo_and_rel_path(first_file)

    overall_start = time.time()

    # --------------------------------------------------
    # STEP 1: CONSTRUCT STRUCTURAL RELATIONSHIP GRAPH
    # --------------------------------------------------
    print("===================================")
    print(f"BUILDING STRUCTURAL GRAPH ({repo_name})")
    print("===================================")
    graph_start = time.time()
    G = build_repository_graph(parsed_files, repo_name)
    graph_time = time.time() - graph_start
    print(f"Graph built in {graph_time:.2f}s: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # --------------------------------------------------
    # STEP 2: CREATE CODE CHUNKS
    # --------------------------------------------------
    print("\n===================================")
    print("CREATING CODE CHUNKS")
    print("===================================")
    chunking_start = time.time()
    all_chunks = []

    for parsed_file in parsed_files:
        chunks = create_code_chunks(parsed_file)
        for chunk in chunks:
            code = chunk["code"].strip()
            # Skip extremely small chunks with no information
            if len(code) < 60:
                continue

            all_chunks.append({
                "file": parsed_file["file"],
                "chunk": chunk
            })

    total_chunks = len(all_chunks)
    chunking_time = time.time() - chunking_start
    print(f"Files scanned: {total_files}")
    print(f"Chunks produced: {total_chunks} in {chunking_time:.2f}s")

    if not all_chunks:
        return {
            "repository": repo_name,
            "files": total_files,
            "chunks": 0,
            "graph_nodes": G.number_of_nodes(),
            "graph_edges": G.number_of_edges(),
            "total_time": round(time.time() - overall_start, 2)
        }

    # --------------------------------------------------
    # STEP 3: GENERATE EMBEDDINGS (PARALLEL)
    # --------------------------------------------------
    print("\n===================================")
    print("GENERATING EMBEDDINGS (FASTEMBED)")
    print("===================================")
    texts = [item["chunk"]["code"] for item in all_chunks]

    embedding_start = time.time()
    embeddings = generate_embeddings_parallel(
        texts=texts,
        batch_size=BATCH_SIZE,
        max_workers=MAX_EMBEDDING_WORKERS
    )
    embedding_time = time.time() - embedding_start
    print(f"Embeddings generated: {len(embeddings)} in {embedding_time:.2f}s")

    # --------------------------------------------------
    # STEP 4: PREPARE DATA FOR CHROMADB
    # --------------------------------------------------
    print("\n===================================")
    print("PREPARING CHROMADB DATA")
    print("===================================")
    chunk_ids = []
    codes = []
    metadatas = []
    seen_ids = set()

    for item in all_chunks:
        chunk = item["chunk"]
        raw_file = item["file"].replace("\\", "/")
        r_name, rel_path = _extract_repo_and_rel_path(raw_file, repo_name)

        base_id = (
            f"{r_name}::{rel_path}"
            f"::{chunk['type']}"
            f"::{chunk['name']}"
            f"::{chunk['start_line']}"
        )
        chunk_id = base_id
        counter = 1
        while chunk_id in seen_ids:
            chunk_id = f"{base_id}_{counter}"
            counter += 1

        seen_ids.add(chunk_id)
        chunk_ids.append(chunk_id)
        codes.append(chunk["code"])
        metadatas.append({
            "file": raw_file,
            "rel_path": rel_path,
            "repository": r_name,
            "type": chunk["type"],
            "name": chunk["name"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "docstring": (chunk.get("docstring") or "")[:500]
        })

    # --------------------------------------------------
    # STEP 5: BATCH WRITE TO CHROMADB
    # --------------------------------------------------
    print("\n===================================")
    print("STORING IN CHROMADB")
    print("===================================")
    storage_start = time.time()
    add_code_chunks(
        chunk_ids=chunk_ids,
        embeddings=embeddings,
        codes=codes,
        metadatas=metadatas,
        batch_size=500
    )
    storage_time = time.time() - storage_start
    print(f"Stored {len(chunk_ids)} chunks in ChromaDB in {storage_time:.2f}s")

    total_indexing_time = time.time() - overall_start

    print("\n===================================")
    print("INDEXING COMPLETE")
    print("===================================")
    print(f"Graph time:     {graph_time:.2f}s")
    print(f"Embedding time: {embedding_time:.2f}s")
    print(f"Storage time:   {storage_time:.2f}s")
    print(f"Total time:     {total_indexing_time:.2f}s")

    return {
        "repository": repo_name,
        "files": total_files,
        "chunks": total_chunks,
        "graph_nodes": G.number_of_nodes(),
        "graph_edges": G.number_of_edges(),
        "graph_time": round(graph_time, 2),
        "embedding_time": round(embedding_time, 2),
        "storage_time": round(storage_time, 2),
        "total_time": round(total_indexing_time, 2)
    }