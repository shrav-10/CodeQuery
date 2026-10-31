import time
import requests


OLLAMA_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "nomic-embed-text"


# 200 realistic-ish code snippets
texts = [
    f"""
def example_function_{i}(value):
    result = value * {i + 1}
    if result > 100:
        return result
    return result + 10
"""
    for i in range(200)
]


BATCH_SIZES = [10, 25, 50, 100, 200]


print("===================================")
print("OLLAMA BATCH SIZE BENCHMARK")
print("===================================")

results = {}


for batch_size in BATCH_SIZES:

    print("\n===================================")
    print(f"TESTING BATCH SIZE: {batch_size}")
    print("===================================")

    start_time = time.time()

    total_embeddings = 0

    for start in range(
        0,
        len(texts),
        batch_size
    ):

        batch = texts[
            start:start + batch_size
        ]

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": EMBEDDING_MODEL,
                "input": batch
            }
        )

        response.raise_for_status()

        data = response.json()

        total_embeddings += len(
            data["embeddings"]
        )

        print(
            f"Processed "
            f"{total_embeddings}/{len(texts)}"
        )

    elapsed = time.time() - start_time

    results[batch_size] = elapsed

    print(
        f"Batch size: {batch_size}"
    )

    print(
        f"Total time: {elapsed:.2f} seconds"
    )

    print(
        f"Average per embedding: "
        f"{elapsed / total_embeddings:.3f} seconds"
    )


print("\n===================================")
print("FINAL BATCH SIZE COMPARISON")
print("===================================")

for batch_size, elapsed in results.items():

    print(
        f"Batch {batch_size:>3}: "
        f"{elapsed:.2f} seconds"
    )

print("===================================")