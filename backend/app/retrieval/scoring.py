"""Score fusion algorithms and rank combination for Hybrid Retrieval.

Implements Reciprocal Rank Fusion (RRF) and confidence calibration.
"""

from typing import Dict, List, Optional, Tuple
from backend.app.retrieval.types import RetrievalCandidate, RetrievalResult
from backend.app.retrieval.documents import RetrievalDocument


class ReciprocalRankFusion:
    """Combines BM25 and Dense Semantic retrieval rankings using Reciprocal Rank Fusion."""

    def __init__(
        self,
        rrf_k: int = 60,
        bm25_weight: float = 1.0,
        semantic_weight: float = 1.0,
    ):
        self.rrf_k = rrf_k
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        # Theoretical maximum RRF score when ranked #1 in both channels
        self.max_rrf = (self.bm25_weight / (self.rrf_k + 1.0)) + (
            self.semantic_weight / (self.rrf_k + 1.0)
        )

    def fuse(
        self,
        bm25_results: List[Tuple[RetrievalCandidate, List[str]]],
        semantic_results: List[RetrievalCandidate],
        doc_map: Dict[str, RetrievalDocument],
        similarity_threshold: float = 0.55,
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """Combine BM25 and Semantic ranked lists and generate calibrated RetrievalResult list."""
        scores: Dict[str, float] = {}
        bm25_ranks: Dict[str, int] = {}
        semantic_ranks: Dict[str, int] = {}
        semantic_scores: Dict[str, float] = {}
        matched_kw_map: Dict[str, List[str]] = {}

        # 1. Process BM25 candidates
        for cand, matched_kw in bm25_results:
            p_id = cand.problem_id
            bm25_ranks[p_id] = cand.rank
            matched_kw_map[p_id] = matched_kw
            rrf_contrib = self.bm25_weight / (self.rrf_k + cand.rank)
            scores[p_id] = scores.get(p_id, 0.0) + rrf_contrib

        # 2. Process Semantic candidates
        for cand in semantic_results:
            p_id = cand.problem_id
            semantic_ranks[p_id] = cand.rank
            semantic_scores[p_id] = cand.score
            rrf_contrib = self.semantic_weight / (self.rrf_k + cand.rank)
            scores[p_id] = scores.get(p_id, 0.0) + rrf_contrib

        # Sort combined problem IDs by fused RRF score descending
        sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results: List[RetrievalResult] = []
        for p_id, raw_fused_score in sorted_candidates[:top_k]:
            doc = doc_map.get(p_id)
            if not doc:
                continue

            # Normalized RRF score in [0.0, 1.0]
            norm_rrf = min(1.0, raw_fused_score / self.max_rrf) if self.max_rrf > 0 else 0.0

            # Semantic similarity score
            sem_score = semantic_scores.get(p_id, 0.0)

            # Calibrated confidence score: balanced blend of normalized RRF and cosine similarity
            if p_id in bm25_ranks and p_id in semantic_ranks:
                # Corroborated by both channels
                confidence = (norm_rrf * 0.5) + (sem_score * 0.5)
            elif p_id in semantic_ranks:
                confidence = sem_score * 0.85
            else:
                confidence = norm_rrf * 0.70

            confidence = round(max(0.0, min(1.0, confidence)), 4)
            status = "MATCH" if confidence >= similarity_threshold else "NO_MATCH"

            # Determine retrieval method
            if p_id in bm25_ranks and p_id in semantic_ranks:
                method = "hybrid"
            elif p_id in bm25_ranks:
                method = "bm25"
            else:
                method = "semantic"

            res = RetrievalResult(
                problem_id=p_id,
                domain=doc.domain,
                problem=doc.problem,
                score=confidence,
                bm25_rank=bm25_ranks.get(p_id),
                semantic_rank=semantic_ranks.get(p_id),
                fused_score=round(raw_fused_score, 4),
                matched_keywords=matched_kw_map.get(p_id, []),
                retrieval_method=method,
                status=status,
            )
            results.append(res)

        return results
