from app.services.code_parser import parse_python_file
from app.services.code_chunker import create_code_chunks
from app.services.embedding_service import generate_embedding
from app.services.vector_store import add_code_chunk


file_path = (
    "data/repositories/fastapi/"
    "docs_src/additional_responses/"
    "tutorial001_py310.py"
)


# -----------------------------------------
# Parse the file
# -----------------------------------------

parsed_file = parse_python_file(
    file_path
)


# -----------------------------------------
# Create chunks
# -----------------------------------------

chunks = create_code_chunks(
    parsed_file
)


print("Total chunks:", len(chunks))


# -----------------------------------------
# Store each chunk
# -----------------------------------------

for index, chunk in enumerate(
    chunks,
    start=1
):

    print(
        f"\nProcessing chunk "
        f"{index}/{len(chunks)}: "
        f"{chunk['name']}"
    )

    embedding = generate_embedding(
        chunk["code"]
    )

    chunk_id = (
        f"{file_path}"
        f"::{chunk['type']}"
        f"::{chunk['name']}"
        f"::{chunk['start_line']}"
    )

    add_code_chunk(
        chunk_id=chunk_id,
        embedding=embedding,
        code=chunk["code"],
        metadata={
            "file": chunk["file"],
            "type": chunk["type"],
            "name": chunk["name"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"]
        }
    )

    print("Stored successfully!")


print("\n===================================")
print("INDEXING COMPLETE")
print("===================================")