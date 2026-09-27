from app.services.code_parser import scan_repository
from app.services.code_chunker import create_code_chunks
from app.services.embedding_service import generate_embedding
from app.services.vector_store import add_code_chunk


def index_repository(repository_path: str):
    """
    Parse a repository, create code chunks,
    generate embeddings, and store them in ChromaDB.
    """

    # -----------------------------------------
    # 1. Parse repository
    # -----------------------------------------

    parsed_files = scan_repository(repository_path)

    total_files = len(parsed_files)
    total_chunks = 0

    print(f"Python files found: {total_files}")

    # -----------------------------------------
    # 2. Process every parsed file
    # -----------------------------------------

    for file_index, parsed_file in enumerate(
        parsed_files,
        start=1
    ):

        print(
            f"Processing file "
            f"{file_index}/{total_files}: "
            f"{parsed_file['file']}"
        )

        # Create chunks from the parsed file
        chunks = create_code_chunks(
            parsed_file
        )

        # -------------------------------------
        # 3. Process every chunk
        # -------------------------------------

        for chunk_index, chunk in enumerate(
            chunks
        ):

            # Generate embedding
            embedding = generate_embedding(
                chunk["code"]
            )

            # Create a unique ID
            chunk_id = (
                f"{parsed_file['file']}"
                f"::{chunk['type']}"
                f"::{chunk['name']}"
                f"::{chunk['start_line']}"
            )

            # Store in ChromaDB
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

            total_chunks += 1

    # -----------------------------------------
    # 4. Return indexing information
    # -----------------------------------------

    return {
        "files": total_files,
        "chunks": total_chunks
    }