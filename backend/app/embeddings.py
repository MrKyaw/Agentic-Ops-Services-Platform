"""Local embedding model (all-MiniLM-L6-v2, 384-dim): real dense vectors, offline, free.

This is a small general-purpose model — appropriate for dev/eval and for proving the
dense path end to end (pgvector HNSW, hybrid fusion, re-embedding). Production quality
thresholds still require evaluated embedding-model selection (RG-6, O1); the model id
and version are recorded on every embedding batch for that comparison.
"""

from functools import lru_cache

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
DIM = 384


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_ID)


@lru_cache(maxsize=2048)
def _cached_encode(texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
    vectors = _model().encode(list(texts), normalize_embeddings=True)
    return tuple(tuple(map(float, row)) for row in vectors)


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return [list(row) for row in _cached_encode(tuple(texts))]


def model_card() -> dict:
    return {"model": MODEL_ID, "dim": DIM}
