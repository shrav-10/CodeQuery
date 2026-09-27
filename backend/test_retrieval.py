from app.services.embedding_service import generate_embedding
from app.services.vector_store import search_code


question = """
How does the read_item function handle an item that is not found?
"""


# Generate an embedding for the question
query_embedding = generate_embedding(question)


# Search ChromaDB
results = search_code(
    query_embedding,
    number_of_results=3
)


print("===================================")
print("CODE RETRIEVAL RESULTS")
print("===================================")


for i in range(len(results["ids"][0])):

    print("\n-----------------------------------")
    print(f"Result {i + 1}")
    print("-----------------------------------")

    print("ID:", results["ids"][0][i])

    print(
        "Distance:",
        results["distances"][0][i]
    )

    print(
        "Metadata:",
        results["metadatas"][0][i]
    )

    print("\nCode:")
    print(
        results["documents"][0][i]
    )