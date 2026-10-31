import chromadb
from app.services.vector_store import collection

print("Collection:", collection.name)
print("Stored records:", collection.count())

sample = collection.get(
    limit=1,
    include=["documents", "metadatas", "embeddings"]
)

if sample["ids"]:
    print("Chunk ID:", sample["ids"][0])
    print("Code chunk:", sample["documents"][0])
    print("Metadata:", sample["metadatas"][0])
    print("Embedding dimensions:", len(sample["embeddings"][0]))