import ast
import os


def parse_python_file(file_path: str):
    # -----------------------------------------
    # Read the Python file
    # -----------------------------------------
    with open(file_path, "r", encoding="utf-8") as file:
        source_code = file.read()

    # Keep the source code as individual lines
    source_lines = source_code.splitlines()

    # Parse the source code using Python AST
    tree = ast.parse(source_code)

    # -----------------------------------------
    # Lists for extracted information
    # -----------------------------------------
    functions = []
    classes = []
    imports = []
    calls = []

    # -----------------------------------------
    # Root of our code structure tree
    # -----------------------------------------
    code_tree = {
        "type": "file",
        "name": os.path.basename(file_path),
        "children": []
    }

    # -----------------------------------------
    # Process top-level nodes
    # -----------------------------------------
    for node in tree.body:

        # =====================================
        # CLASS
        # =====================================
        if isinstance(node, ast.ClassDef):

            class_code = "\n".join(
                source_lines[node.lineno - 1:node.end_lineno]
            )

            class_node = {
                "type": "class",
                "name": node.name,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "code": class_code,
                "children": []
            }

            classes.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": node.end_lineno
            })

            # ---------------------------------
            # Find functions inside the class
            # ---------------------------------
            for child in node.body:

                if isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                ):

                    function_code = "\n".join(
                        source_lines[
                            child.lineno - 1:child.end_lineno
                        ]
                    )

                    function_node = {
                        "type": "function",
                        "name": child.name,
                        "line": child.lineno,
                        "end_line": child.end_lineno,
                        "code": function_code
                    }

                    class_node["children"].append(
                        function_node
                    )

                    functions.append({
                        "name": child.name,
                        "line": child.lineno,
                        "end_line": child.end_lineno,
                        "parent_class": node.name
                    })

            code_tree["children"].append(
                class_node
            )

        # =====================================
        # TOP-LEVEL FUNCTION
        # =====================================
        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):

            function_code = "\n".join(
                source_lines[
                    node.lineno - 1:node.end_lineno
                ]
            )

            function_node = {
                "type": "function",
                "name": node.name,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "code": function_code
            }

            code_tree["children"].append(
                function_node
            )

            functions.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "parent_class": None
            })

        # =====================================
        # IMPORTS
        # =====================================
        elif isinstance(
            node,
            (ast.Import, ast.ImportFrom)
        ):

            imports.append({
                "line": node.lineno
            })

    # -----------------------------------------
    # Find all function calls
    # -----------------------------------------
    for node in ast.walk(tree):

        if isinstance(node, ast.Call):

            # Example:
            # FastAPI()
            # JSONResponse()
            if isinstance(node.func, ast.Name):

                calls.append({
                    "name": node.func.id,
                    "line": node.lineno
                })

            # Example:
            # app.get()
            # response.json()
            elif isinstance(node.func, ast.Attribute):

                calls.append({
                    "name": node.func.attr,
                    "line": node.lineno
                })

    # -----------------------------------------
    # Return all parsed information
    # -----------------------------------------
    return {
        "file": file_path,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "calls": calls,
        "tree": code_tree
    }


def scan_repository(repository_path: str):
    parsed_files = []

    # -----------------------------------------
    # Walk through the entire repository
    # -----------------------------------------
    for root, dirs, files in os.walk(repository_path):

        # Ignore Git's internal directory
        if ".git" in root:
            continue

        for file_name in files:

            # Only process Python files
            if not file_name.endswith(".py"):
                continue

            file_path = os.path.join(
                root,
                file_name
            )

            try:

                parsed_data = parse_python_file(
                    file_path
                )

                parsed_files.append(
                    parsed_data
                )

            except Exception as e:

                print(
                    f"Error parsing {file_path}: {e}"
                )

    return parsed_files