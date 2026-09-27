import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:1.5b"

def ask_local_model(code: str, question: str) -> str:
    prompt = f"""
You are CodeQuery, an AI assistant that helps users understand code.

Here is the code:

{code}

User's question:
{question}

Explain the answer clearly and accurately.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
    "model": MODEL_NAME,
    "prompt": prompt,
    "stream": False,
    "options": {
        "num_predict": 300,
        "temperature": 0.2
    }
},
        timeout=120
    )

    response.raise_for_status()

    return response.json()["response"]