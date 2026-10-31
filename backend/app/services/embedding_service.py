import hashlib
from typing import List
from fastembed import TextEmbedding

# Model name: BAAI/bge-small-en-v1.5 (fastest, high accuracy, 384 dimensions)
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSIONS = 384

# Initialize FastEmbed once in memory
_embedding_model: TextEmbedding | None = None


def get_model() -> TextEmbedding:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
    return _embedding_model


# In-memory cache for previously generated embeddings
_EMBEDDING_CACHE: dict[str, List[float]] = {}
MAX_CACHE_SIZE = 50000


def _hash_text(text: str) -> str:
    """Generate a stable hash for input text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding for a single text using FastEmbed.
    Reuses cache when available.
    """
    text_hash = _hash_text(text)
    if text_hash in _EMBEDDING_CACHE:
        return _EMBEDDING_CACHE[text_hash]

    model = get_model()
    embeddings_gen = model.embed([text])
    embedding = list(embeddings_gen)[0].tolist()

    if len(_EMBEDDING_CACHE) < MAX_CACHE_SIZE:
        _EMBEDDING_CACHE[text_hash] = embedding

    return embedding


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts using FastEmbed in-process ONNX runtime.
    Vectorized and runs at hundreds of chunks per second on CPU.
    """
    if not texts:
        return []

    results: List[List[float] | None] = [None] * len(texts)
    missing_indices = []
    missing_texts = []

    for index, text in enumerate(texts):
        text_hash = _hash_text(text)
        if text_hash in _EMBEDDING_CACHE:
            results[index] = _EMBEDDING_CACHE[text_hash]
        else:
            missing_indices.append(index)
            missing_texts.append(text)

    if missing_texts:
        model = get_model()
        embeddings_gen = model.embed(missing_texts, batch_size=128)

        for index, text, emb in zip(missing_indices, missing_texts, embeddings_gen):
            emb_list = emb.tolist()
            results[index] = emb_list
            if len(_EMBEDDING_CACHE) < MAX_CACHE_SIZE:
                _EMBEDDING_CACHE[_hash_text(text)] = emb_list

    return [emb for emb in results if emb is not None]


def generate_embeddings_parallel(
    texts: List[str],
    batch_size: int = 128,
    max_workers: int = 1,
) -> List[List[float]]:
    """
    Generate embeddings using FastEmbed.
    FastEmbed natively parallelizes across CPU cores via ONNX Runtime threadpool.
    """
    return generate_embeddings(texts)