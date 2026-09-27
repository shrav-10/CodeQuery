from app.services.rag_service import answer_code_question


question = """
How does the read_item function handle an item that is not found?
"""


answer = answer_code_question(question)


print("===================================")
print("CODEQUERY RAG ANSWER")
print("===================================")

print("\nQuestion:")
print(question)

print("\nAnswer:")
print(answer)