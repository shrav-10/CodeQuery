from app.services.code_parser import parse_python_file
from app.services.code_chunker import create_code_chunks


file_path = (
    "data/repositories/fastapi/"
    "docs_src/additional_responses/"
    "tutorial001_py310.py"
)


parsed_data = parse_python_file(file_path)

chunks = create_code_chunks(parsed_data)


print("===================================")
print("CODE CHUNKS")
print("===================================")

print(f"\nTotal chunks: {len(chunks)}")


for i, chunk in enumerate(chunks, start=1):

    print("\n-----------------------------------")
    print(f"Chunk {i}")
    print("-----------------------------------")

    print("Type:", chunk["type"])
    print("Name:", chunk["name"])
    print("File:", chunk["file"])

    print(
        "Lines:",
        chunk["start_line"],
        "-",
        chunk["end_line"]
    )

    print("\nCode:")
    print(chunk["code"])