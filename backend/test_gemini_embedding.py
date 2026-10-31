import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

result = client.models.embed_content(
    model="gemini-embedding-2",
    contents="def hello_world(): return 'Hello World'",
    config={
        "output_dimensionality": 768
    }
)

embedding = result.embeddings[0].values

print("===================================")
print("GEMINI EMBEDDING TEST")
print("===================================")
print(f"Embedding generated successfully")
print(f"Dimensions: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")