import os


def create_code_chunks(parsed_file):
    """
    Convert parser output into independent code chunks.
    """

    chunks = []

    file_path = parsed_file["file"]
    tree = parsed_file["tree"]

    # -----------------------------------------
    # Process classes and their methods
    # -----------------------------------------
    for node in tree["children"]:

        if node["type"] == "class":

            # Add the class itself as a chunk
            chunks.append({
                "file": file_path,
                "type": "class",
                "name": node["name"],
                "start_line": node["line"],
                "end_line": node["end_line"],
                "code": node["code"]
            })

            # Add methods inside the class
            for child in node.get("children", []):

                if child["type"] == "function":

                    chunks.append({
                        "file": file_path,
                        "type": "method",
                        "name": child["name"],
                        "start_line": child["line"],
                        "end_line": child["end_line"],
                        "code": child["code"]
                    })

        # -------------------------------------
        # Process top-level functions
        # -------------------------------------
        elif node["type"] == "function":

            chunks.append({
                "file": file_path,
                "type": "function",
                "name": node["name"],
                "start_line": node["line"],
                "end_line": node["end_line"],
                "code": node["code"]
            })

    return chunks