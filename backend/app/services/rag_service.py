import re
import os
import time
from typing import List, Dict, Any, Optional

from app.services.embedding_service import generate_embedding
from app.services.vector_store import search_code
from app.services.graph_service import expand_structural_context
from app.services.llm_service import generate_llm_response


CITATION_PATTERN = re.compile(r"\[([a-zA-Z0-9_\-\./\\]+\.py):(\d+)(?:-(\d+))?\]")


def _extract_citations(answer: str, retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse [file.py:line-line] citations from generated answer and associate with retrieved snippets.
    """
    citations = []
    seen = set()

    for match in CITATION_PATTERN.finditer(answer):
        file_path, start_line, end_line = match.groups()
        start = int(start_line)
        end = int(end_line) if end_line else start
        cit_key = f"{file_path}:{start}-{end}"
        if cit_key in seen:
            continue
        seen.add(cit_key)

        # Find matching chunk for code snippet preview
        snippet = ""
        chunk_name = ""
        for chunk in retrieved_chunks:
            chunk_file = chunk.get("rel_path", "") or chunk.get("file", "")
            if file_path in chunk_file or os.path.basename(chunk_file) == os.path.basename(file_path):
                snippet = chunk.get("code", "")[:350]
                chunk_name = chunk.get("name", "")
                break

        citations.append({
            "file": file_path,
            "start_line": start,
            "end_line": end,
            "citation": f"[{file_path}:{start}-{end}]",
            "name": chunk_name,
            "snippet": snippet
        })

    # If LLM didn't format exact brackets, populate from top retrieved chunks as verified sources
    if not citations and retrieved_chunks:
        for chunk in retrieved_chunks[:3]:
            rel_path = chunk.get("rel_path") or os.path.basename(chunk.get("file", ""))
            s_line = chunk.get("start_line", 1)
            e_line = chunk.get("end_line", s_line)
            citations.append({
                "file": rel_path,
                "start_line": s_line,
                "end_line": e_line,
                "citation": f"[{rel_path}:{s_line}-{e_line}]",
                "name": chunk.get("name", ""),
                "snippet": chunk.get("code", "")[:350]
            })

    return citations


def answer_code_question(
    question: str,
    repository: Optional[str] = None,
    top_k: int = 4,
    preferred_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Structure-Aware Retrieval-Augmented Generation (RAG) Pipeline:
    1. Embed user query using FastEmbed
    2. Retrieve top semantically similar code chunks from ChromaDB
    3. Perform structural graph expansion via NetworkX (call graph, inheritance, imports)
    4. Construct grounded prompt with exact file/line metadata
    5. Query LLM (Claude API / local Ollama)
    6. Extract exact file-and-line citations and return structured payload
    """
    overall_start = time.time()
    timings = {}

    # 1. Embed query
    t0 = time.time()
    query_embedding = generate_embedding(question)
    timings["embedding"] = round(time.time() - t0, 3)

    # 2. Vector search in ChromaDB
    t0 = time.time()
    results = search_code(
        query_embedding=query_embedding,
        number_of_results=top_k,
        repository=repository
    )
    timings["vector_search"] = round(time.time() - t0, 3)

    # 3. Format retrieved chunks
    retrieved_chunks: List[Dict[str, Any]] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if "distances" in results else []

    for idx, doc in enumerate(documents):
        meta = metadatas[idx] if idx < len(metadatas) else {}
        dist = distances[idx] if idx < len(distances) else None
        retrieved_chunks.append({
            "code": doc,
            "file": meta.get("file", "unknown"),
            "rel_path": meta.get("rel_path", meta.get("file", "unknown")),
            "repository": meta.get("repository", repository or "default"),
            "type": meta.get("type", "code"),
            "name": meta.get("name", "unknown"),
            "start_line": meta.get("start_line", 1),
            "end_line": meta.get("end_line", 1),
            "docstring": meta.get("docstring", ""),
            "distance": round(dist, 4) if dist is not None else None
        })

    if not retrieved_chunks:
        return {
            "question": question,
            "answer": "No relevant code found in the indexed repository. Please ensure the repository is analyzed.",
            "citations": [],
            "retrieved_chunks": [],
            "graph_context": {"has_graph": False, "relationships": []},
            "timings": timings,
            "provider": "none"
        }

    # Inferred repo name for graph expansion
    target_repo = repository or retrieved_chunks[0].get("repository") or "default"

    # 4. Structural Graph Expansion (NetworkX)
    t0 = time.time()
    graph_context = expand_structural_context(target_repo, retrieved_chunks, max_hops=1)
    timings["graph_expansion"] = round(time.time() - t0, 3)

    # 5. Build Grounded Prompt with Citations instructions
    context_blocks = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        block = (
            f"--- CHUNK {i}: [{chunk['rel_path']}:{chunk['start_line']}-{chunk['end_line']}] "
            f"({chunk['type'].upper()}: {chunk['name']}) ---\n"
            f"{chunk['code']}\n"
        )
        context_blocks.append(block)

    code_context_str = "\n".join(context_blocks)
    graph_rel_str = graph_context.get("graph_summary", "")

    prompt = f"""You are CodeQuery, a structure-aware AI assistant for codebase understanding.
Your task is to answer the developer's question using ONLY the retrieved source code chunks and structural graph relationships provided below.

RULES:
1. Ground every claim strictly in the provided code. Do NOT invent functions, files, or behaviors.
2. For EVERY claim, function, or implementation explanation, cite the exact source location in the format: [rel_path:start_line-end_line] (e.g. [{retrieved_chunks[0]['rel_path']}:{retrieved_chunks[0]['start_line']}-{retrieved_chunks[0]['end_line']}]).
3. Utilize the call relationships, inheritance, and containment from the Codebase Structural Graph to explain how components interact.
4. If the code context does not provide sufficient detail to answer completely, acknowledge what is known and specify what is missing.

{graph_rel_str}

SOURCE CODE CONTEXT:
{code_context_str}

DEVELOPER QUESTION:
{question}

Provide an accurate, well-structured explanation with exact file:line citations:"""

    # 6. LLM Generation
    t0 = time.time()
    llm_res = generate_llm_response(prompt, preferred_provider=preferred_provider)
    timings["llm_generation"] = round(time.time() - t0, 3)
    timings["total"] = round(time.time() - overall_start, 3)

    answer_text = llm_res.get("answer", "")
    citations = _extract_citations(answer_text, retrieved_chunks)

    return {
        "question": question,
        "answer": answer_text,
        "citations": citations,
        "retrieved_chunks": retrieved_chunks,
        "graph_context": graph_context,
        "provider": llm_res.get("provider", "unknown"),
        "timings": timings
    }