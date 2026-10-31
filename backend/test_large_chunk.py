from app.services.code_parser import parse_python_file
from app.services.code_chunker import create_code_chunks


file_path = (
    "data/repositories/requests/"
    "src/requests/adapters.py"
)


parsed_data = parse_python_file(file_path)

chunks = create_code_chunks(parsed_data)


print("===================================")
print("LARGE FILE CHUNK TEST")
print("===================================")

print(f"\nTotal chunks: {len(chunks)}")


for i, chunk in enumerate(chunks, start=1):

    print(
        f"Chunk {i}: "
        f"{chunk['type']} - "
        f"{chunk['name']} - "
        f"{len(chunk['code'])} characters"
    )