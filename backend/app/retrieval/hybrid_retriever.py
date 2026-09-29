"""Hybrid Retriever combining BM25 Lexical Search and Pretrained Neural Semantic Vector Search.

Applies query preprocessing, dual-channel retrieval, Reciprocal Rank Fusion,
and a confidence gate to separate valid MATCH candidates from unsupported NO_MATCH queries.
"""

from pathlib import Path
from typing import List, Optional
from backend.app.config import settings
from backend.app.retrieval.bm25_retriever import BM25Retriever
from backend.app.retrieval.documents import DocumentBuilder, RetrievalDocument
from backend.app.retrieval.preprocessing import preprocess_query
from backend.app.retrieval.scoring import ReciprocalRankFusion
from backend.app.retrieval.semantic_retriever import (
    EmbeddingProvider,
    SemanticRetriever,
)
from backend.app.retrieval.types import RetrievalResult


class HybridRetriever:
    """Unified hybrid retrieval engine for troubleshooting knowledge base."""

    def __init__(
        self,
        documents: Optional[List[RetrievalDocument]] = None,
        data_dir: Optional[Path] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_mode: Optional[str] = None,
        similarity_threshold: Optional[float] = None,
        rrf_k: int = 60,
        default_top_k: int = 5,
    ):
        if documents is None:
            builder = DocumentBuilder(data_dir=data_dir or settings.DATA_DIR)
            self.documents = builder.documents
        else:
            self.documents = documents

        self.doc_map = {doc.problem_id: doc for doc in self.documents}
        self.similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.SIMILARITY_THRESHOLD
        )
        self.rrf_k = rrf_k
        self.default_top_k = default_top_k
        self.vector_mode = vector_mode or settings.RETRIEVAL_VECTOR_MODE

        # Subsystems
        self.bm25_retriever = BM25Retriever(self.documents)
        self.semantic_retriever = SemanticRetriever(
            self.documents,
            provider=embedding_provider,
            vector_mode=self.vector_mode,
        )
        self.fusion = ReciprocalRankFusion(rrf_k=self.rrf_k)

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """Execute hybrid search on query and return fused, confidence-ranked results."""
        k = top_k or self.default_top_k
        thresh = threshold if threshold is not None else self.similarity_threshold

        cleaned_query = preprocess_query(query)
        if not cleaned_query:
            return []

        # Dual-channel retrieval
        channel_k = max(k * 2, 10)
        bm25_results = self.bm25_retriever.retrieve(cleaned_query, top_k=channel_k)
        semantic_results = self.semantic_retriever.retrieve(
            cleaned_query, top_k=channel_k
        )

        # Fuse rankings
        results = self.fusion.fuse(
            bm25_results=bm25_results,
            semantic_results=semantic_results,
            doc_map=self.doc_map,
            similarity_threshold=thresh,
            top_k=k,
        )
        return results

    def retrieve_best(
        self,
        query: str,
        threshold: Optional[float] = None,
    ) -> Optional[RetrievalResult]:
        """Retrieve top-1 candidate with confidence gate applied."""
        results = self.retrieve(query, top_k=1, threshold=threshold)
        if not results:
            return None
        return results[0]
