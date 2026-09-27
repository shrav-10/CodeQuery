import chromadb


# -----------------------------------------
# Create a persistent ChromaDB client
# -----------------------------------------

CHROMA_PATH = "data/chroma"

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


# -----------------------------------------
# Create / get our code collection
# -----------------------------------------

collection = client.get_or_create_collection(
    name="code_chunks"
)


def add_code_chunk(
    chunk_id: str,
    embedding: list,
    code: str,
    metadata: dict
):
    """
    Store one code chunk in ChromaDB.
    """

    collection.add(
        ids=[chunk_id],
        embeddings=[embedding],
        documents=[code],
        metadatas=[metadata]
    )


def search_code(
    query_embedding: list,
    number_of_results: int = 5
):
    """
    Search ChromaDB for code chunks
    similar to the query embedding.
    """

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=number_of_results
    )

    return results