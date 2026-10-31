import os
import time

from app.services.code_parser import parse_python_file
from app.services.indexer import index_repository


REPOSITORY_PATH = "data/repositories/fastapi"

# We already indexed the first 20 files.
# Skip them and test the next 20 files.
SKIP_FILES = 20
TEST_FILES = 20


# ==================================================
# FIND PYTHON FILES
# ==================================================

all_python_files = []

for root, dirs, files in os.walk(REPOSITORY_PATH):

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

            full_path = os.path.join(root, file)

            all_python_files.append(full_path)


# Sort so the selection is consistent
all_python_files.sort()


# Select files that we have NOT tested before
python_files = all_python_files[
    SKIP_FILES:SKIP_FILES + TEST_FILES
]


# ==================================================
# START BENCHMARK
# ==================================================

print("===================================")
print("BATCH INDEXER BENCHMARK")
print("===================================")

print(
    f"Total Python files found: "
    f"{len(all_python_files)}"
)

print(
    f"Files skipped: "
    f"{SKIP_FILES}"
)

print(
    f"Files selected for test: "
    f"{len(python_files)}"
)


# ==================================================
# PARSE FILES
# ==================================================

print("\n===================================")
print("PARSING FILES")
print("===================================")

parse_start = time.time()

parsed_files = []

for file_path in python_files:

    parsed_file = parse_python_file(file_path)

    parsed_files.append(parsed_file)

parse_time = time.time() - parse_start

print(
    f"\nParsing time: "
    f"{parse_time:.2f} seconds"
)


# ==================================================
# INDEX REPOSITORY
# ==================================================

print("\n===================================")
print("STARTING BATCH INDEXING")
print("===================================")

index_start = time.time()

result = index_repository(
    parsed_files
)

index_time = time.time() - index_start


# ==================================================
# FINAL RESULTS
# ==================================================

print("\n===================================")
print("BATCH BENCHMARK COMPLETE")
print("===================================")

print(
    f"Files processed:  "
    f"{result['files']}"
)

print(
    f"Chunks processed: "
    f"{result['chunks']}"
)

print(
    f"Parsing time:     "
    f"{parse_time:.2f} seconds"
)

print(
    f"Indexing time:    "
    f"{index_time:.2f} seconds"
)

print(
    f"Total time:       "
    f"{parse_time + index_time:.2f} seconds"
)

print("===================================")