"""Dense Semantic Retriever and Vector Index for SmartGuide.

Supports both:
1. Pretrained Neural Sentence Transformer embeddings (e.g. all-MiniLM-L6-v2) - Phase 2.75
2. Local Statistical TF-IDF/n-gram baseline vectorizer - Phase 2 Baseline
"""

from abc import ABC, abstractmethod
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

from backend.app.config import settings
from backend.app.retrieval.documents import RetrievalDocument
from backend.app.retrieval.preprocessing import preprocess_query, tokenize
from backend.app.retrieval.types import RetrievalCandidate


# ==============================================================================
# Embedding Provider Abstraction
# ==============================================================================

class EmbeddingProvider(ABC):
    """Abstract base class for text embedding models."""

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """Generate a dense 1D L2-normalized embedding vector for a single text string."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Generate a 2D dense embedding matrix (N, D) for a list of texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding vector dimension."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return identifier / model name."""
        pass


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Pretrained Neural Sentence Transformer embedding provider (Phase 2.75).

    Utilizes sentence-transformers (default: all-MiniLM-L6-v2) to produce
    384-dimensional dense semantic embeddings.
    Embeddings are L2-normalized for exact cosine similarity dot products.
    """

    _cached_model = None
    _cached_model_name = None

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._device = device

        # Lazy load and cache model instance at class level for instant reuse
        if (
            SentenceTransformerEmbeddingProvider._cached_model is None
            or SentenceTransformerEmbeddingProvider._cached_model_name != self._model_name
        ):
            from sentence_transformers import SentenceTransformer

            SentenceTransformerEmbeddingProvider._cached_model = SentenceTransformer(
                self._model_name, device=self._device
            )
            SentenceTransformerEmbeddingProvider._cached_model_name = self._model_name

        self._model = SentenceTransformerEmbeddingProvider._cached_model
        if hasattr(self._model, "get_embedding_dimension"):
            self._dim = self._model.get_embedding_dimension()
        else:
            self._dim = self._model.get_sentence_embedding_dimension()

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_text(self, text: str) -> np.ndarray:
        """Generate a normalized 1D dense embedding vector."""
        cleaned = preprocess_query(text)
        if not cleaned:
            return np.zeros(self._dim, dtype=np.float32)

        # encode with normalize_embeddings=True for cosine similarity via dot product
        emb = self._model.encode(
            cleaned,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(emb, dtype=np.float32)

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Generate a 2D normalized dense embedding matrix (N, D)."""
        cleaned_texts = [preprocess_query(t) or t for t in texts]
        embs = self._model.encode(
            cleaned_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,
        )
        return np.asarray(embs, dtype=np.float32)


class LocalDenseEmbeddingProvider(EmbeddingProvider):
    """Deterministic local statistical TF-IDF and n-gram vectorizer (Phase 2 Baseline).

    Computes normalized sub-word and token n-gram vectors.
    """

    def __init__(self, corpus: Optional[List[str]] = None):
        self._vocab: Dict[str, int] = {}
        self._idf: np.ndarray = np.array([])
        self._dim = 0
        if corpus:
            self.fit(corpus)

    @property
    def model_name(self) -> str:
        return "local_tfidf_ngram_statistical"

    def _extract_features(self, text: str) -> List[str]:
        """Extract word unigrams, bigrams, and character tri/4-grams."""
        cleaned = preprocess_query(text)
        words = tokenize(cleaned, remove_stopwords=False)
        features = list(words)

        # Word bigrams
        for i in range(len(words) - 1):
            features.append(f"{words[i]}_{words[i+1]}")

        # Character n-grams for typo resilience
        text_no_space = "".join(words)
        for n in (3, 4):
            for i in range(len(text_no_space) - n + 1):
                features.append(f"#{text_no_space[i:i+n]}")

        return features

    def fit(self, corpus: List[str]) -> "LocalDenseEmbeddingProvider":
        """Build vocabulary and compute IDF statistics over the document corpus."""
        doc_count = len(corpus)
        df_counts: Dict[str, int] = {}

        for text in corpus:
            features = set(self._extract_features(text))
            for feat in features:
                df_counts[feat] = df_counts.get(feat, 0) + 1

        # Build vocabulary
        self._vocab = {feat: idx for idx, feat in enumerate(sorted(df_counts.keys()))}
        self._dim = len(self._vocab)

        # Compute Smooth IDF: log((N + 1) / (df + 1)) + 1
        idf_values = np.zeros(self._dim, dtype=np.float32)
        for feat, idx in self._vocab.items():
            df = df_counts[feat]
            idf_values[idx] = math.log((doc_count + 1.0) / (df + 1.0)) + 1.0
        self._idf = idf_values
        return self

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single query or text string into a normalized 1D vector."""
        if self._dim == 0:
            raise RuntimeError("LocalDenseEmbeddingProvider has not been fitted.")

        vec = np.zeros(self._dim, dtype=np.float32)
        features = self._extract_features(text)
        if not features:
            return vec

        for feat in features:
            if feat in self._vocab:
                vec[self._vocab[feat]] += 1.0

        # Sublinear TF scaling: 1 + log(tf) if tf > 0
        mask = vec > 0
        vec[mask] = (1.0 + np.log(vec[mask])) * self._idf[mask]

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embed a collection of documents into a 2D matrix (N, D)."""
        matrix = np.zeros((len(texts), self._dim), dtype=np.float32)
        for idx, text in enumerate(texts):
            matrix[idx] = self.embed_text(text)
        return matrix


def get_embedding_provider(
    mode: Optional[str] = None,
    corpus: Optional[List[str]] = None,
) -> EmbeddingProvider:
    """Factory helper to obtain the configured EmbeddingProvider."""
    vector_mode = mode or settings.RETRIEVAL_VECTOR_MODE

    if vector_mode == "tfidf":
        return LocalDenseEmbeddingProvider(corpus=corpus)
    elif vector_mode in ("sentence_transformer", "neural"):
        try:
            return SentenceTransformerEmbeddingProvider(
                model_name=settings.EMBEDDING_MODEL
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize SentenceTransformerEmbeddingProvider: {e}. "
                "Ensure sentence-transformers is installed and model files are cached."
            )
    else:
        raise ValueError(f"Unknown vector retrieval mode: '{vector_mode}'")


# ==============================================================================
# Vector Index
# ==============================================================================

class VectorIndex:
    """Lightweight in-memory vector index with cosine similarity search and persistence."""

    def __init__(self, provider: EmbeddingProvider):
        self.provider = provider
        self.problem_ids: List[str] = []
        self.doc_map: Dict[str, RetrievalDocument] = {}
        self.vectors: Optional[np.ndarray] = None

    def build(self, documents: List[RetrievalDocument]) -> "VectorIndex":
        """Build vector embeddings index for given documents."""
        self.problem_ids = [doc.problem_id for doc in documents]
        self.doc_map = {doc.problem_id: doc for doc in documents}
        texts = [doc.searchable_text for doc in documents]

        if hasattr(self.provider, "fit") and getattr(self.provider, "_dim", 0) == 0:
            self.provider.fit(texts)

        self.vectors = self.provider.embed_documents(texts)
        return self

    def save(self, cache_dir: Path) -> None:
        """Persist vector index to disk cache."""
        cache_dir.mkdir(parents=True, exist_ok=True)
        if self.vectors is not None:
            np.save(str(cache_dir / f"embeddings_{self.provider.model_name.replace('/', '_')}.npy"), self.vectors)
        meta = {
            "problem_ids": self.problem_ids,
            "dimension": self.provider.dimension,
            "model_name": self.provider.model_name,
        }
        with open(cache_dir / "index_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def load(self, cache_dir: Path, documents: List[RetrievalDocument]) -> bool:
        """Load vector index from disk cache if available."""
        npy_path = cache_dir / f"embeddings_{self.provider.model_name.replace('/', '_')}.npy"
        meta_path = cache_dir / "index_meta.json"
        if not npy_path.exists() or not meta_path.exists():
            return False

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        if meta.get("model_name") != self.provider.model_name:
            return False

        self.problem_ids = meta["problem_ids"]
        self.doc_map = {doc.problem_id: doc for doc in documents}
        self.vectors = np.load(str(npy_path))
        return True

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """Calculate cosine similarity against indexed vectors and return top-k matches."""
        if self.vectors is None or len(self.problem_ids) == 0:
            raise RuntimeError("Vector index has not been built.")

        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return []

        # Cosine similarity (vectors are already L2-normalized)
        similarities = np.dot(self.vectors, query_embedding)

        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            p_id = self.problem_ids[idx]
            results.append((p_id, max(0.0, min(1.0, score))))

        return results


# ==============================================================================
# Dense Semantic Retriever
# ==============================================================================

class SemanticRetriever:
    """Semantic retriever executing dense vector search."""

    def __init__(
        self,
        documents: List[RetrievalDocument],
        provider: Optional[EmbeddingProvider] = None,
        vector_mode: Optional[str] = None,
    ):
        self.documents = documents
        self.doc_map = {doc.problem_id: doc for doc in documents}
        texts = [doc.searchable_text for doc in documents]

        if provider is None:
            self.provider = get_embedding_provider(mode=vector_mode, corpus=texts)
        else:
            self.provider = provider

        self.index = VectorIndex(provider=self.provider)
        self.index.build(documents)

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalCandidate]:
        """Retrieve top-k candidates for a query using dense vector cosine similarity."""
        query_embedding = self.provider.embed_text(query)
        matches = self.index.search(query_embedding, top_k=top_k)

        candidates = []
        for rank, (problem_id, score) in enumerate(matches, start=1):
            doc = self.doc_map[problem_id]
            candidates.append(
                RetrievalCandidate(
                    problem_id=problem_id,
                    domain=doc.domain,
                    score=round(score, 4),
                    rank=rank,
                )
            )
        return candidates
