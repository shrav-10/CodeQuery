import requests


OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBEDDING_MODEL = "nomic-embed-text"


def generate_embedding(text: str):
    """
    Generate an embedding for the given text
    using the local Ollama embedding model.
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": EMBEDDING_MODEL,
            "prompt": text
        }
    )

    response.raise_for_status()

    data = response.json()

    return data["embedding"]