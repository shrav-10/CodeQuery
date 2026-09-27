from app.services.embedding_service import generate_embedding
from app.services.vector_store import add_code_chunk, search_code


# -----------------------------------------
# Example code chunk
# -----------------------------------------

code = """
async def read_item(item_id: str):
    if item_id == "foo":
        return {"id": "foo"}
    return {"message": "Item not found"}
"""


# -----------------------------------------
# Generate embedding
# -----------------------------------------

embedding = generate_embedding(code)


# -----------------------------------------
# Store the chunk
# -----------------------------------------

add_code_chunk(
    chunk_id="test_read_item",
    embedding=embedding,
    code=code,
    metadata={
        "file": "tutorial001_py310.py",
        "type": "function",
        "name": "read_item",
        "start_line": 19,
        "end_line": 22
    }
)


print("Code chunk stored successfully!")


# -----------------------------------------
# Test searching
# -----------------------------------------

question = "How does read_item handle an item that is not found?"

query_embedding = generate_embedding(question)


results = search_code(
    query_embedding,
    number_of_results=1
)


print("\nSearch results:")
print(results)