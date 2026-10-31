import os
import time

from app.services.code_parser import parse_python_file
from app.services.indexer import index_repository


REPOSITORY_PATH = "data/repositories/fastapi"


# -----------------------------------------
# Find 20 Python files
# -----------------------------------------

python_files = []

for root, dirs, files in os.walk(REPOSITORY_PATH):

    # Skip directories that don't contain useful source code
    dirs[:] = [
        d for d in dirs
        if d not in {
            ".git",
            "__pycache__",
            "venv",
            ".venv",
            "node_modules"
        }
    ]

    for file in files:

        if file.endswith(".py"):

            python_files.append(
                os.path.join(root, file)
            )

        if len(python_files) >= 20:
            break

    if len(python_files) >= 20:
        break


print("===================================")
print("PARALLEL INDEXER BENCHMARK")
print("===================================")

print(f"Python files selected: {len(python_files)}")


# -----------------------------------------
# Parse files
# -----------------------------------------

parsed_files = []

print("\nParsing files...")

parse_start = time.time()

for file_path in python_files:

    parsed_file = parse_python_file(file_path)

    parsed_files.append(parsed_file)

parse_time = time.time() - parse_start


print(f"Parsing time: {parse_time:.2f} seconds")


# -----------------------------------------
# Index files
# -----------------------------------------

print("\nStarting parallel indexing...")

index_start = time.time()

result = index_repository(parsed_files)

index_time = time.time() - index_start


# -----------------------------------------
# Results
# -----------------------------------------

print("\n===================================")
print("BENCHMARK COMPLETE")
print("===================================")

print(f"Files processed:  {result['files']}")
print(f"Chunks processed: {result['chunks']}")
print(f"Parsing time:     {parse_time:.2f} seconds")
print(f"Indexing time:    {index_time:.2f} seconds")
print(
    f"Total time:       "
    f"{parse_time + index_time:.2f} seconds"
)

print("===================================")