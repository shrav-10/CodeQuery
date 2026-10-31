MAX_CHUNK_SIZE = 1500


def split_large_chunk(chunk):
    """
    Split a large code chunk into smaller pieces along line boundaries,
    preserving docstring and metadata.
    """
    code = chunk["code"]

    if len(code) <= MAX_CHUNK_SIZE:
        return [chunk]

    lines = code.splitlines(keepends=True)
    chunks = []
    current_lines = []
    current_len = 0
    current_start_line = chunk["start_line"]
    part_number = 1

    for line in lines:
        if current_len + len(line) > MAX_CHUNK_SIZE and current_lines:
            part_code = "".join(current_lines).strip()
            if part_code:
                part_end_line = current_start_line + len(current_lines) - 1
                chunks.append({
                    "file": chunk["file"],
                    "type": chunk["type"],
                    "name": f"{chunk['name']}_part_{part_number}",
                    "start_line": current_start_line,
                    "end_line": part_end_line,
                    "code": part_code,
                    "docstring": chunk.get("docstring", ""),
                    "parent_class": chunk.get("parent_class"),
                    "bases": chunk.get("bases", [])
                })
                part_number += 1
            current_start_line += len(current_lines)
            current_lines = []
            current_len = 0

        current_lines.append(line)
        current_len += len(line)

    if current_lines:
        part_code = "".join(current_lines).strip()
        if part_code:
            part_end_line = current_start_line + len(current_lines) - 1
            chunks.append({
                "file": chunk["file"],
                "type": chunk["type"],
                "name": f"{chunk['name']}_part_{part_number}" if part_number > 1 else chunk["name"],
                "start_line": current_start_line,
                "end_line": part_end_line,
                "code": part_code,
                "docstring": chunk.get("docstring", ""),
                "parent_class": chunk.get("parent_class"),
                "bases": chunk.get("bases", [])
            })

    return chunks if chunks else [chunk]


def create_code_chunks(parsed_file):
    """
    Convert parser output into independent code chunks.
    Preserves file path, line numbers, docstring metadata, and structural attributes.
    Avoids duplicating method code inside parent class chunks.
    """
    chunks = []

    file_path = parsed_file["file"]
    tree = parsed_file.get("tree", {})

    for node in tree.get("children", []):

        if node["type"] == "class":
            methods = [
                child for child in node.get("children", [])
                if child["type"] == "function"
            ]

            class_doc = node.get("docstring", "")
            class_bases = node.get("bases", [])

            if not methods:
                # Class with no methods (data model, constants, dataclass, enum)
                class_chunk = {
                    "file": file_path,
                    "type": "class",
                    "name": node["name"],
                    "start_line": node["line"],
                    "end_line": node["end_line"],
                    "code": node["code"],
                    "docstring": class_doc,
                    "parent_class": None,
                    "bases": class_bases
                }
                chunks.extend(split_large_chunk(class_chunk))
            else:
                # Extract class header/docstring if present before the first method
                first_method_line = min(m["line"] for m in methods)
                if first_method_line > node["line"]:
                    class_lines = node["code"].splitlines()
                    header_line_count = first_method_line - node["line"]
                    header_code = "\n".join(class_lines[:header_line_count]).strip()
                    if len(header_code) >= 40:
                        header_chunk = {
                            "file": file_path,
                            "type": "class",
                            "name": node["name"],
                            "start_line": node["line"],
                            "end_line": first_method_line - 1,
                            "code": header_code,
                            "docstring": class_doc,
                            "parent_class": None,
                            "bases": class_bases
                        }
                        chunks.extend(split_large_chunk(header_chunk))

                # Extract each method independently with class context
                for child in methods:
                    method_chunk = {
                        "file": file_path,
                        "type": "method",
                        "name": f"{node['name']}.{child['name']}",
                        "start_line": child["line"],
                        "end_line": child["end_line"],
                        "code": child["code"],
                        "docstring": child.get("docstring", ""),
                        "parent_class": node["name"],
                        "bases": class_bases
                    }
                    chunks.extend(split_large_chunk(method_chunk))

        elif node["type"] == "function":
            function_chunk = {
                "file": file_path,
                "type": "function",
                "name": node["name"],
                "start_line": node["line"],
                "end_line": node["end_line"],
                "code": node["code"],
                "docstring": node.get("docstring", ""),
                "parent_class": None,
                "bases": []
            }
            chunks.extend(split_large_chunk(function_chunk))

    return chunks
