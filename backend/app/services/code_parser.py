import ast
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional


def _extract_base_name(base_node: ast.AST) -> Optional[str]:
    """Helper to extract class inheritance base name from AST node."""
    if isinstance(base_node, ast.Name):
        return base_node.id
    elif isinstance(base_node, ast.Attribute):
        value_name = _extract_base_name(base_node.value)
        return f"{value_name}.{base_node.attr}" if value_name else base_node.attr
    return None


def _extract_function_calls(node: ast.AST) -> List[Dict[str, Any]]:
    """Helper to extract function calls within a specific AST subtree."""
    calls = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            if isinstance(sub.func, ast.Name):
                calls.append({
                    "name": sub.func.id,
                    "line": getattr(sub, "lineno", 0)
                })
            elif isinstance(sub.func, ast.Attribute):
                calls.append({
                    "name": sub.func.attr,
                    "line": getattr(sub, "lineno", 0)
                })
    return calls


def parse_python_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a Python file using the AST module.
    Extracts functions, methods, classes, docstrings, inheritance, imports,
    and scoped function calls for structural graph building and chunking.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as file:
        source_code = file.read()

    source_lines = source_code.splitlines()

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {
            "file": file_path,
            "functions": [],
            "classes": [],
            "imports": [],
            "calls": [],
            "tree": {"type": "file", "name": os.path.basename(file_path), "children": []},
            "error": str(e)
        }

    functions = []
    classes = []
    imports = []
    file_calls = []

    code_tree = {
        "type": "file",
        "name": os.path.basename(file_path),
        "children": []
    }

    file_docstring = ast.get_docstring(tree) or ""

    for node in tree.body:
        # =====================================
        # CLASS DEFINITION
        # =====================================
        if isinstance(node, ast.ClassDef):
            class_code = "\n".join(
                source_lines[node.lineno - 1:node.end_lineno]
            )
            class_docstring = ast.get_docstring(node) or ""

            # Extract base classes for inheritance graph
            bases = []
            for b in node.bases:
                base_name = _extract_base_name(b)
                if base_name:
                    bases.append(base_name)

            class_node = {
                "type": "class",
                "name": node.name,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "code": class_code,
                "docstring": class_docstring,
                "bases": bases,
                "children": []
            }

            classes.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "docstring": class_docstring,
                "bases": bases
            })

            # Find functions/methods inside the class
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_code = "\n".join(
                        source_lines[child.lineno - 1:child.end_lineno]
                    )
                    method_docstring = ast.get_docstring(child) or ""
                    method_args = [a.arg for a in child.args.args if a.arg != "self" and a.arg != "cls"]
                    method_calls = _extract_function_calls(child)

                    method_node = {
                        "type": "function",
                        "name": child.name,
                        "line": child.lineno,
                        "end_line": child.end_lineno,
                        "code": method_code,
                        "docstring": method_docstring,
                        "args": method_args,
                        "parent_class": node.name,
                        "calls": method_calls
                    }

                    class_node["children"].append(method_node)
                    functions.append({
                        "name": child.name,
                        "line": child.lineno,
                        "end_line": child.end_lineno,
                        "docstring": method_docstring,
                        "args": method_args,
                        "parent_class": node.name,
                        "calls": method_calls
                    })

            code_tree["children"].append(class_node)

        # =====================================
        # TOP-LEVEL FUNCTION
        # =====================================
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_code = "\n".join(
                source_lines[node.lineno - 1:node.end_lineno]
            )
            fn_docstring = ast.get_docstring(node) or ""
            fn_args = [a.arg for a in node.args.args]
            fn_calls = _extract_function_calls(node)

            function_node = {
                "type": "function",
                "name": node.name,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "code": function_code,
                "docstring": fn_docstring,
                "args": fn_args,
                "parent_class": None,
                "calls": fn_calls
            }

            code_tree["children"].append(function_node)
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "docstring": fn_docstring,
                "args": fn_args,
                "parent_class": None,
                "calls": fn_calls
            })

        # =====================================
        # IMPORTS
        # =====================================
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "module": alias.name,
                    "names": [alias.asname or alias.name],
                    "line": node.lineno
                })
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            imported_names = [alias.name for alias in node.names]
            imports.append({
                "module": module_name,
                "names": imported_names,
                "line": node.lineno
            })

    # Global/file-level function calls
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                file_calls.append({"name": node.func.id, "line": node.lineno})
            elif isinstance(node.func, ast.Attribute):
                file_calls.append({"name": node.func.attr, "line": node.lineno})

    return {
        "file": file_path,
        "docstring": file_docstring,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "calls": file_calls,
        "tree": code_tree
    }


DEFAULT_EXCLUDED_DIRS = {
    ".git", "__pycache__", "venv", ".venv", "env", ".env",
    "node_modules", "build", "dist", ".pytest_cache", ".mypy_cache",
    ".tox", "site-packages", "tests", "test", "testing", "docs", "docs_src",
    "scripts"
}


def scan_repository(repository_path: str, include_tests: bool = False, max_workers: int = 8) -> List[Dict[str, Any]]:
    """
    Scan and parse an entire repository using high-speed parallel AST parsing.
    Filters out dependencies, virtualenvs, and test directories to ensure fast indexing.
    """
    excluded = set(DEFAULT_EXCLUDED_DIRS)
    if include_tests:
        excluded -= {"tests", "test", "testing"}

    py_files = []

    for root, dirs, files in os.walk(repository_path):
        dirs[:] = [
            d for d in dirs
            if d.lower() not in excluded and not d.startswith(".")
        ]

        for file_name in files:
            if file_name.endswith(".py"):
                py_files.append(os.path.join(root, file_name))

    parsed_files = []

    # Parallel parsing with ThreadPoolExecutor for speed
    if len(py_files) <= 4:
        for fpath in py_files:
            try:
                parsed_files.append(parse_python_file(fpath))
            except Exception as e:
                print(f"Error parsing {fpath}: {e}")
    else:
        workers = min(max_workers, len(py_files))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_file = {executor.submit(parse_python_file, fpath): fpath for fpath in py_files}
            for future in as_completed(future_to_file):
                fpath = future_to_file[future]
                try:
                    res = future.result()
                    parsed_files.append(res)
                except Exception as e:
                    print(f"Error parsing {fpath}: {e}")

    # Maintain deterministic sorting by file path
    parsed_files.sort(key=lambda x: x.get("file", ""))
    return parsed_files