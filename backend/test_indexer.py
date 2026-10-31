import time

from app.services.code_parser import parse_python_file
from app.services.indexer import index_repository


file_path = (
    "data/repositories/fastapi/"
    "docs_src/additional_responses/"
    "tutorial001_py310.py"
)


print("===================================")
print("CODEQUERY INDEXER TEST")
print("===================================")

# -----------------------------------------
# Parse the file
# -----------------------------------------

print("\nParsing file...")

start_time = time.time()

parsed_file = parse_python_file(file_path)

parse_time = time.time() - start_time

print(f"File parsed in {parse_time:.2f} seconds")


# -----------------------------------------
# Index using the NEW parallel indexer
# -----------------------------------------

print("\nStarting indexer...")

start_time = time.time()

result = index_repository(
    [parsed_file]
)

index_time = time.time() - start_time


# -----------------------------------------
# Results
# -----------------------------------------

print("\n===================================")
print("INDEXING COMPLETE")
print("===================================")

print(f"Files indexed:  {result['files']}")
print(f"Chunks indexed: {result['chunks']}")
print(f"Indexing time:  {index_time:.2f} seconds")
print(f"Total time:     {parse_time + index_time:.2f} seconds")

print("===================================")