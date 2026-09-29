"""SmartGuide Retrieval Package (Phase 2, 2.5 & 2.75: Neural Hybrid Retrieval).

Exposes BM25 lexical search, pretrained sentence transformer embeddings,
scoring algorithms, benchmark evaluators, and holdout validation tooling.
"""

from backend.app.retrieval.bm25_retriever import BM25Retriever
from backend.app.retrieval.documents import DocumentBuilder, RetrievalDocument
from backend.app.retrieval.evaluator import RetrievalEvaluator
from backend.app.retrieval.holdout_evaluator import (
    HoldoutEvaluator,
    HoldoutIntegrityReport,
    HoldoutMetrics,
    check_holdout_integrity,
)
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.retrieval.preprocessing import (
    preprocess_query,
    strip_conversational_wrappers,
    tokenize,
)
from backend.app.retrieval.scoring import ReciprocalRankFusion
from backend.app.retrieval.semantic_retriever import (
    EmbeddingProvider,
    LocalDenseEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    SemanticRetriever,
    VectorIndex,
    get_embedding_provider,
)
from backend.app.retrieval.types import (
    EvaluationMetrics,
    QueryEvaluationResult,
    RetrievalCandidate,
    RetrievalResult,
)

__all__ = [
    "BM25Retriever",
    "DocumentBuilder",
    "RetrievalDocument",
    "RetrievalEvaluator",
    "HoldoutEvaluator",
    "HoldoutIntegrityReport",
    "HoldoutMetrics",
    "check_holdout_integrity",
    "HybridRetriever",
    "preprocess_query",
    "strip_conversational_wrappers",
    "tokenize",
    "ReciprocalRankFusion",
    "EmbeddingProvider",
    "LocalDenseEmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "SemanticRetriever",
    "VectorIndex",
    "get_embedding_provider",
    "EvaluationMetrics",
    "QueryEvaluationResult",
    "RetrievalCandidate",
    "RetrievalResult",
]
