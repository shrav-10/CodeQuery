import os
import time
import json
import hashlib
from typing import Optional, Dict, Tuple, Any
import requests

from dotenv import load_dotenv

load_dotenv()

# Optional cloud SDKs
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")

# In-memory query response cache: prompt_hash -> (answer, provider)
_RESPONSE_CACHE: Dict[str, Tuple[str, str]] = {}
MAX_RESPONSE_CACHE = 1000


def _get_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ask_anthropic(prompt: str, model: str = "claude-3-5-sonnet-latest") -> Optional[str]:
    """Call Anthropic Claude API if key is present."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not HAS_ANTHROPIC:
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        if response.content and len(response.content) > 0:
            return response.content[0].text
    except Exception as e:
        print(f"Anthropic API error: {e}")
    return None


def ask_local_ollama(prompt: str, model: str = DEFAULT_OLLAMA_MODEL, max_tokens: int = 250) -> str:
    """Call local Ollama server (e.g. qwen2.5-coder:1.5b). Fast and 100% offline."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.2,
            "top_p": 0.9,
            "num_ctx": 2048,
            "num_thread": max(1, os.cpu_count() or 4)
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=90
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Ollama server connection error at {OLLAMA_URL}. Ensure Ollama is running (`ollama serve`). Details: {e}"
        )


def generate_llm_response(prompt: str, preferred_provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate response with provider selection, automatic fallback, and LRU cache.
    Providers: 'claude', 'ollama', or 'auto'.
    """
    prompt_hash = _get_hash(prompt)
    if prompt_hash in _RESPONSE_CACHE:
        cached_answer, cached_provider = _RESPONSE_CACHE[prompt_hash]
        return {
            "answer": cached_answer,
            "provider": f"{cached_provider} (cached)",
            "duration": 0.001
        }

    start_time = time.time()
    answer = None
    provider_used = "ollama"

    # 1. Check if user preferred Anthropic or Auto with ANTHROPIC_API_KEY set
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if (preferred_provider == "claude" or (preferred_provider in (None, "auto") and anthropic_key)) and anthropic_key:
        answer = ask_anthropic(prompt)
        if answer:
            provider_used = "anthropic-claude"

    # 2. Fallback or direct use of local Ollama
    if not answer:
        answer = ask_local_ollama(prompt)
        provider_used = f"ollama-{DEFAULT_OLLAMA_MODEL}"

    duration = round(time.time() - start_time, 2)

    # Cache response
    if len(_RESPONSE_CACHE) < MAX_RESPONSE_CACHE:
        _RESPONSE_CACHE[prompt_hash] = (answer, provider_used)

    return {
        "answer": answer,
        "provider": provider_used,
        "duration": duration
    }


def ask_local_model(code: str, question: str) -> str:
    """Backward compatibility function."""
    prompt = f"Code:\n{code}\n\nQuestion:\n{question}\n\nExplain clearly:"
    res = generate_llm_response(prompt)
    return res["answer"]