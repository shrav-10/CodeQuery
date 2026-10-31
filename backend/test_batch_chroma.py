import os
import time

from app.services.code_parser import parse_python_file
from app.services.indexer import index_repository


REPOSITORY_PATH = "data/repositories/fastapi"

# Use files that were not used in our previous tests
SKIP_FILES = 440
TEST_FILES = 200


print("===================================")
print("BATCH CHROMADB BENCHMARK")
print("===================================")


# --------------------------------------------------
# FIND PYTHON FILES
# --------------------------------------------------

python_files = []

for root, dirs, files in os.walk(REPOSITORY_PATH):

    for file in files:

        if file.endswith(".py"):

            python_files.append(
                os.path.join(root, file)
            )


python_files.sort()

selected_files = python_files[
    SKIP_FILES:SKIP_FILES + TEST_FILES
]


print(
    f"Total Python files: "
    f"{len(python_files)}"
)

print(
    f"Testing files: "
    f"{len(selected_files)}"
)


# --------------------------------------------------
# PARSE FILES
# --------------------------------------------------

parsed_files = []

parse_start = time.time()

for index, file_path in enumerate(
    selected_files,
    start=1
):

    print(
        f"Parsing {index}/{len(selected_files)}: "
        f"{file_path}"
    )

    parsed_data = parse_python_file(
        file_path
    )

    if parsed_data:

        parsed_files.append(
            parsed_data
        )


parse_time = (
    time.time() - parse_start
)


print("\n===================================")
print("PARSING COMPLETE")
print("===================================")

print(
    f"Files parsed: "
    f"{len(parsed_files)}"
)

print(
    f"Parsing time: "
    f"{parse_time:.2f} seconds"
)


# --------------------------------------------------
# INDEX REPOSITORY
# --------------------------------------------------

index_start = time.time()

result = index_repository(
    parsed_files
)

index_time = (
    time.time() - index_start
)


# --------------------------------------------------
# FINAL RESULT
# --------------------------------------------------

print("\n===================================")
print("FINAL RESULT")
print("===================================")

print(
    f"Files: "
    f"{result['files']}"
)

print(
    f"Chunks: "
    f"{result['chunks']}"
)

print(
    f"Parsing time: "
    f"{parse_time:.2f} seconds"
)

print(
    f"Indexing time: "
    f"{index_time:.2f} seconds"
)

print(
    f"Total time: "
    f"{parse_time + index_time:.2f} seconds"
)

print("===================================")