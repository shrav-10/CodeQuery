from app.services.embedding_service import generate_embedding
from app.services.vector_store import search_code
from app.services.llm_service import ask_local_model


def answer_code_question(question: str):
    """
    Retrieve relevant code and use the local Qwen model
    to generate an answer.
    """

    # -----------------------------------------
    # 1. Convert the question into an embedding
    # -----------------------------------------

    query_embedding = generate_embedding(question)

    # -----------------------------------------
    # 2. Retrieve relevant code from ChromaDB
    # -----------------------------------------

    results = search_code(
        query_embedding,
        number_of_results=3
    )

    # -----------------------------------------
    # 3. Extract retrieved code
    # -----------------------------------------

    retrieved_chunks = results["documents"][0]

    if not retrieved_chunks:
        return "I could not find relevant code in the repository."

    # -----------------------------------------
    # 4. Combine retrieved code
    # -----------------------------------------

    context = "\n\n".join(
        retrieved_chunks
    )

    # -----------------------------------------
    # 5. Ask Qwen using the retrieved code
    # -----------------------------------------

    prompt = f"""
You are CodeQuery, an AI assistant for understanding codebases.

Answer the user's question using the provided code context.

If the answer cannot be determined from the provided
code context, clearly say that the available code
does not provide enough information.

CODE CONTEXT:
{context}

USER QUESTION:
{question}

Provide a clear and concise explanation.
"""

    answer = ask_local_model(
        code=context,
        question=prompt
    )

    return answer