import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Any

OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
EMBEDDING_MODEL = "nomic-embed-text"

# Reusable session with HTTP connection pooling for fast embedding
_session = requests.Session()
_retries = Retry(total=2, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])
_adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=_retries)
_session.mount("http://", _adapter)


def check_ollama_status() -> Dict[str, Any]:
    """Check if Ollama is reachable and the embedding model is available."""
    try:
        response = _session.get(OLLAMA_TAGS_URL, timeout=3)
        if response.status_code == 200:
            models = [m.get("name", "") for m in response.json().get("models", [])]
            has_embed_model = any(EMBEDDING_MODEL in m for m in models)
            return {
                "available": True,
                "has_embedding_model": has_embed_model,
                "models": models,
            }
        return {"available": False, "error": f"HTTP {response.status_code}"}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def generate_embedding(text: str) -> List[float]:
    """Generate a single local embedding vector with pinned model keep_alive."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    try:
        response = _session.post(
            OLLAMA_EMBED_URL,
            json={
                "model": EMBEDDING_MODEL,
                "input": text,
                "keep_alive": "2h",  # Keep model warm in RAM for fast consecutive queries
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings", [])
        if not embeddings:
            raise ValueError("Ollama returned an empty embedding array.")
        return embeddings[0]
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Failed to generate embedding from Ollama at {OLLAMA_EMBED_URL}: {exc}"
        ) from exc


def generate_batch_embeddings(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """
    Generate local embeddings for batches of texts using Ollama's batch embedding API.
    Uses keep_alive to avoid unloading the model and uses connection pooling.
    """
    if not texts:
        return []

    cleaned_texts = [t if t and t.strip() else " " for t in texts]
    all_embeddings: List[List[float]] = []

    for i in range(0, len(cleaned_texts), batch_size):
        sub_batch = cleaned_texts[i : i + batch_size]
        try:
            response = _session.post(
                OLLAMA_EMBED_URL,
                json={
                    "model": EMBEDDING_MODEL,
                    "input": sub_batch,
                    "keep_alive": "2h",  # Pin model in RAM
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            batch_vectors = data.get("embeddings", [])

            if len(batch_vectors) != len(sub_batch):
                raise ValueError(
                    f"Mismatch in returned embeddings count: got {len(batch_vectors)}, expected {len(sub_batch)}"
                )

            all_embeddings.extend(batch_vectors)

        except requests.RequestException as exc:
            # Fallback to single text if batch fails
            try:
                for single_text in sub_batch:
                    all_embeddings.append(generate_embedding(single_text))
            except Exception as inner_exc:
                raise RuntimeError(
                    f"Failed generating embeddings in sub-batch: {exc} | Fallback failed: {inner_exc}"
                ) from exc

    return all_embeddings
