import time
import requests

OLLAMA_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "nomic-embed-text"

texts = [
    f"""
def example_function_{i}(value):
    result = value * {i + 1}
    return result
"""
    for i in range(10)
]

print("===================================")
print("OLLAMA BATCH EMBEDDING TEST")
print("===================================")

start = time.time()

response = requests.post(
    OLLAMA_URL,
    json={
        "model": EMBEDDING_MODEL,
        "input": texts
    }
)

response.raise_for_status()

data = response.json()

elapsed = time.time() - start

print(f"Status: {response.status_code}")
print(f"Time: {elapsed:.2f} seconds")

print(f"Number of embeddings: {len(data['embeddings'])}")
print(f"Embedding size: {len(data['embeddings'][0])}")

print("===================================")