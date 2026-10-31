import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.embedding_service import generate_embedding


print("===================================")
print("PARALLEL EMBEDDING SPEED TEST")
print("===================================")

texts = [
    f"""
def example_function_{i}(value):
    result = value * {i + 1}
    return result
"""
    for i in range(10)
]


def embed_text(text):
    return generate_embedding(text)


def run_test(workers):
    print(f"\n===================================")
    print(f"TEST: {workers} CONCURRENT REQUESTS")
    print("===================================")

    start_time = time.time()

    embeddings = []

    with ThreadPoolExecutor(max_workers=workers) as executor:

        futures = [
            executor.submit(embed_text, text)
            for text in texts
        ]

        for i, future in enumerate(as_completed(futures), start=1):
            embedding = future.result()
            embeddings.append(embedding)

            print(
                f"Completed {i}/10 | "
                f"Embedding length: {len(embedding)}"
            )

    total_time = time.time() - start_time

    print("-----------------------------------")
    print(f"Workers: {workers}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average per embedding: {total_time / len(texts):.2f} seconds")
    print("-----------------------------------")

    return total_time


# -----------------------------------
# Run benchmarks
# -----------------------------------

results = {}

for workers in [1, 2, 4]:
    results[workers] = run_test(workers)


# -----------------------------------
# Final comparison
# -----------------------------------

print("\n===================================")
print("FINAL COMPARISON")
print("===================================")

for workers, total_time in results.items():
    print(
        f"{workers} worker(s): "
        f"{total_time:.2f} seconds"
    )

baseline = results[1]

print("\n===================================")
print("SPEEDUP")
print("===================================")

for workers, total_time in results.items():
    speedup = baseline / total_time

    print(
        f"{workers} worker(s): "
        f"{speedup:.2f}x"
    )

print("===================================")