"""BM25 Lexical Retriever for SmartGuide.

Indexes field-weighted troubleshooting documents using BM25Okapi.
"""

from typing import List, Optional, Tuple
from rank_bm25 import BM25Okapi

from backend.app.retrieval.documents import RetrievalDocument
from backend.app.retrieval.preprocessing import preprocess_query, tokenize
from backend.app.retrieval.types import RetrievalCandidate


class BM25Retriever:
    """BM25 lexical search retriever."""

    def __init__(self, documents: List[RetrievalDocument]):
        if not documents:
            raise ValueError("Cannot initialize BM25Retriever with empty document list.")
        self.documents = documents
        self.doc_map = {doc.problem_id: doc for doc in documents}
        self.corpus = [doc.tokens for doc in documents]
        self.bm25 = BM25Okapi(self.corpus)

    def retrieve(
        self, query: str, top_k: int = 5
    ) -> List[Tuple[RetrievalCandidate, List[str]]]:
        """Retrieve top-k problem candidates for a given user query.

        Returns a list of tuples: (RetrievalCandidate, matched_keywords).
        """
        query_tokens = tokenize(query, remove_stopwords=True)
        if not query_tokens:
            # Fallback without stopword removal if all tokens were filtered
            query_tokens = tokenize(query, remove_stopwords=False)

        if not query_tokens:
            return []

        raw_scores = self.bm25.get_scores(query_tokens)

        # Pair scores with documents
        scored_docs = []
        for idx, score in enumerate(raw_scores):
            if score > 0.0:
                doc = self.documents[idx]
                scored_docs.append((doc, float(score)))

        # Sort descending by BM25 score
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for rank, (doc, score) in enumerate(scored_docs[:top_k], start=1):
            # Identify matched keywords
            query_set = set(query_tokens)
            matched_kw = [
                kw for kw in doc.keywords
                if any(q in kw.lower() for q in query_set)
            ]

            candidate = RetrievalCandidate(
                problem_id=doc.problem_id,
                domain=doc.domain,
                score=score,
                rank=rank,
            )
            results.append((candidate, matched_kw))

        return results
