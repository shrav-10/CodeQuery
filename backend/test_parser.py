from app.services.code_parser import scan_repository


repository_path = "data/repositories/fastapi"

results = scan_repository(repository_path)

print(f"Python files found: {len(results)}")

for result in results[:5]:

    print("\nFile:", result["file"])

    print("Functions:")
    for function in result["functions"][:5]:
        print(
            f"  {function['name']} "
            f"(lines {function['line']}-{function['end_line']})"
        )

    print("Classes:")
    for class_info in result["classes"][:5]:
        print(
            f"  {class_info['name']} "
            f"(lines {class_info['line']}-{class_info['end_line']})"
        )

    print("Calls:")
    for call in result["calls"][:5]:
        print(
            f"  {call['name']} "
            f"(line {call['line']})"
        )
    print("Tree:")
    print(result["tree"])