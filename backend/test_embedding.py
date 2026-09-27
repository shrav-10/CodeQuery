from app.services.embedding_service import generate_embedding


text = """
def read_item(item_id: str):
    return {"id": item_id}
"""


embedding = generate_embedding(text)


print("Embedding generated successfully!")
print("Embedding length:", len(embedding))
print("First 10 values:")
print(embedding[:10])