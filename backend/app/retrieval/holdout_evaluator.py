"""Holdout Evaluation Harness and Integrity Verification.

Validates the holdout dataset integrity, checks for exact/near duplicates against
the training/development benchmark, and computes holdout generalization metrics
(Top-1, Top-3, Unsupported Rejection, P50/P95 Latency, Threshold Sweep).
"""

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.models.data_models import HoldoutQueryRecord, TroubleshootingRecord
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.retrieval.preprocessing import normalize_whitespace, preprocess_query
from backend.app.retrieval.types import QueryEvaluationResult


class HoldoutIntegrityReport(BaseModel):
    """Integrity check results for the holdout benchmark dataset."""

    total_queries: int
    supported_queries: int
    unsupported_queries: int
    duplicate_ids: List[str] = Field(default_factory=list)
    invalid_problem_ids: List[str] = Field(default_factory=list)
    invalid_unsupported_entries: List[str] = Field(default_factory=list)
    exact_matches_with_canonical: List[str] = Field(default_factory=list)
    exact_matches_with_test_queries: List[str] = Field(default_factory=list)
    exact_matches_with_variations: List[str] = Field(default_factory=list)
    high_similarity_matches: List[Dict[str, str]] = Field(default_factory=list)
    is_valid: bool = True


class HoldoutMetrics(BaseModel):
    """Aggregate metrics for holdout evaluation."""

    total_queries: int
    supported_queries: int
    unsupported_queries: int
    top_1_accuracy: float
    top_3_accuracy: float
    supported_top_1_accuracy: float
    supported_top_3_accuracy: float
    unsupported_rejection_rate: float
    false_positives: int
    false_negatives: int
    overall_accuracy: float
    average_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    threshold: float
    per_query_results: List[QueryEvaluationResult] = Field(default_factory=list)
    detailed_candidates: List[Dict[str, Any]] = Field(default_factory=list)


def check_holdout_integrity(
    holdout_path: Optional[Path] = None,
    data_dir: Optional[Path] = None,
) -> HoldoutIntegrityReport:
    """Validate holdout dataset schema, ID uniqueness, and lack of duplication."""
    data_directory = data_dir or settings.DATA_DIR
    h_path = holdout_path or (data_directory / "holdout_queries.json")
    tb_path = data_directory / "troubleshooting.json"
    tq_path = data_directory / "test_queries.json"
    qv_path = data_directory / "query_variations.json"

    if not h_path.exists():
        raise FileNotFoundError(f"Holdout dataset not found at: {h_path}")

    with open(h_path, "r", encoding="utf-8") as f:
        raw_holdout = json.load(f)
    with open(tb_path, "r", encoding="utf-8") as f:
        raw_tb = json.load(f)
    with open(tq_path, "r", encoding="utf-8") as f:
        raw_tq = json.load(f)
    with open(qv_path, "r", encoding="utf-8") as f:
        raw_qv = json.load(f)

    holdout_records = [HoldoutQueryRecord.model_validate(r) for r in raw_holdout]
    valid_problem_ids: Set[str] = {r["id"] for r in raw_tb}
    canonical_problems: Set[str] = {preprocess_query(r["problem"]) for r in raw_tb}
    existing_test_queries: Set[str] = {preprocess_query(r["query"]) for r in raw_tq}
    existing_variations: Set[str] = {
        preprocess_query(v) for item in raw_qv for v in item.get("query_variations", [])
    }

    seen_ids: Set[str] = set()
    duplicate_ids: List[str] = []
    invalid_p_ids: List[str] = []
    invalid_unsupported: List[str] = []
    exact_canonical: List[str] = []
    exact_test: List[str] = []
    exact_var: List[str] = []
    high_sim: List[Dict[str, str]] = []

    supported_count = 0
    unsupported_count = 0

    for r in holdout_records:
        if r.id in seen_ids:
            duplicate_ids.append(r.id)
        seen_ids.add(r.id)

        cleaned_q = preprocess_query(r.query)

        if r.supported:
            supported_count += 1
            if not r.expected_problem_id or r.expected_problem_id not in valid_problem_ids:
                invalid_p_ids.append(f"{r.id}: {r.expected_problem_id}")
        else:
            unsupported_count += 1
            if r.expected_problem_id is not None or r.expected_domain is not None:
                invalid_unsupported.append(r.id)

        # Check exact overlap
        if cleaned_q in canonical_problems:
            exact_canonical.append(f"{r.id}: '{r.query}'")
        if cleaned_q in existing_test_queries:
            exact_test.append(f"{r.id}: '{r.query}'")
        if cleaned_q in existing_variations:
            exact_var.append(f"{r.id}: '{r.query}'")

    is_valid = (
        len(duplicate_ids) == 0
        and len(invalid_p_ids) == 0
        and len(invalid_unsupported) == 0
        and len(exact_canonical) == 0
        and len(exact_test) == 0
        and len(exact_var) == 0
    )

    return HoldoutIntegrityReport(
        total_queries=len(holdout_records),
        supported_queries=supported_count,
        unsupported_queries=unsupported_count,
        duplicate_ids=duplicate_ids,
        invalid_problem_ids=invalid_p_ids,
        invalid_unsupported_entries=invalid_unsupported,
        exact_matches_with_canonical=exact_canonical,
        exact_matches_with_test_queries=exact_test,
        exact_matches_with_variations=exact_var,
        high_similarity_matches=high_sim,
        is_valid=is_valid,
    )


class HoldoutEvaluator:
    """Evaluates the hybrid retriever against the unseen holdout benchmark."""

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        holdout_path: Optional[Path] = None,
    ):
        self.retriever = retriever or HybridRetriever()
        self.holdout_path = holdout_path or (settings.DATA_DIR / "holdout_queries.json")
        self.holdout_records = self._load_holdout_data()

    def _load_holdout_data(self) -> List[HoldoutQueryRecord]:
        """Load holdout queries from JSON."""
        if not self.holdout_path.exists():
            raise FileNotFoundError(f"Holdout file not found: {self.holdout_path}")
        with open(self.holdout_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [HoldoutQueryRecord.model_validate(r) for r in raw]

    def evaluate(self, threshold: Optional[float] = None) -> HoldoutMetrics:
        """Run evaluation over holdout queries at specified confidence threshold."""
        thresh = (
            threshold
            if threshold is not None
            else self.retriever.similarity_threshold
        )

        per_query_results: List[QueryEvaluationResult] = []
        detailed_candidates: List[Dict[str, Any]] = []
        latencies: List[float] = []

        top_1_correct = 0
        top_3_correct = 0
        supported_total = 0
        supported_top_1 = 0
        supported_top_3 = 0
        unsupported_total = 0
        unsupported_rejected = 0
        false_positives = 0
        false_negatives = 0

        for r in self.holdout_records:
            start_t = time.perf_counter()
            results = self.retriever.retrieve(r.query, top_k=3, threshold=thresh)
            lat_ms = (time.perf_counter() - start_t) * 1000.0
            latencies.append(lat_ms)

            top_1 = results[0] if results else None
            top_1_pred_id = top_1.problem_id if top_1 else None
            top_1_score = top_1.score if top_1 else 0.0
            top_1_status = top_1.status if top_1 else "NO_MATCH"

            # Check target rank in top 3
            target_rank = None
            if r.expected_problem_id:
                for idx, res in enumerate(results, start=1):
                    if res.problem_id == r.expected_problem_id and res.status == "MATCH":
                        target_rank = idx
                        break

            is_supported = r.supported
            query_is_correct = False

            if is_supported:
                supported_total += 1
                if top_1_status == "MATCH" and top_1_pred_id == r.expected_problem_id:
                    query_is_correct = True
                    supported_top_1 += 1
                    top_1_correct += 1
                else:
                    false_negatives += 1

                if target_rank is not None and target_rank <= 3:
                    supported_top_3 += 1
                    top_3_correct += 1
            else:
                unsupported_total += 1
                if top_1 is None or top_1_status == "NO_MATCH":
                    query_is_correct = True
                    unsupported_rejected += 1
                    top_1_correct += 1
                    top_3_correct += 1
                else:
                    false_positives += 1

            eval_res = QueryEvaluationResult(
                query_id=r.id,
                query=r.query,
                expected_domain=r.expected_domain,
                expected_problem_id=r.expected_problem_id,
                predicted_problem_id=top_1_pred_id if top_1_status == "MATCH" else None,
                correct=query_is_correct,
                rank=target_rank if is_supported else (1 if query_is_correct else None),
                score=top_1_score,
                status=top_1_status,
                latency_ms=round(lat_ms, 3),
            )
            per_query_results.append(eval_res)

            # Store detailed candidate breakdown for qualitative analysis
            detailed_candidates.append(
                {
                    "query_id": r.id,
                    "query": r.query,
                    "supported": r.supported,
                    "expected_problem_id": r.expected_problem_id,
                    "expected_domain": r.expected_domain,
                    "predicted_problem_id": top_1_pred_id if top_1 else None,
                    "predicted_domain": top_1.domain if top_1 else None,
                    "score": top_1_score,
                    "bm25_rank": top_1.bm25_rank if top_1 else None,
                    "semantic_rank": top_1.semantic_rank if top_1 else None,
                    "fused_score": top_1.fused_score if top_1 else 0.0,
                    "retrieval_method": top_1.retrieval_method if top_1 else "none",
                    "status": top_1_status,
                    "correct": query_is_correct,
                    "rank": target_rank,
                }
            )

        total_q = len(self.holdout_records)
        avg_lat = float(np.mean(latencies)) if latencies else 0.0
        p50_lat = float(np.percentile(latencies, 50)) if latencies else 0.0
        p95_lat = float(np.percentile(latencies, 95)) if latencies else 0.0

        overall_acc = (top_1_correct / total_q) * 100.0 if total_q else 0.0
        supp_top1_acc = (
            (supported_top_1 / supported_total) * 100.0 if supported_total else 0.0
        )
        supp_top3_acc = (
            (supported_top_3 / supported_total) * 100.0 if supported_total else 0.0
        )
        unsupp_rej_rate = (
            (unsupported_rejected / unsupported_total) * 100.0
            if unsupported_total
            else 0.0
        )

        return HoldoutMetrics(
            total_queries=total_q,
            supported_queries=supported_total,
            unsupported_queries=unsupported_total,
            top_1_accuracy=round(overall_acc, 2),
            top_3_accuracy=round(
                ((supported_top_3 + unsupported_rejected) / total_q) * 100.0, 2
            ),
            supported_top_1_accuracy=round(supp_top1_acc, 2),
            supported_top_3_accuracy=round(supp_top3_acc, 2),
            unsupported_rejection_rate=round(unsupp_rej_rate, 2),
            false_positives=false_positives,
            false_negatives=false_negatives,
            overall_accuracy=round(overall_acc, 2),
            average_latency_ms=round(avg_lat, 2),
            p50_latency_ms=round(p50_lat, 2),
            p95_latency_ms=round(p95_lat, 2),
            threshold=thresh,
            per_query_results=per_query_results,
            detailed_candidates=detailed_candidates,
        )

    def run_threshold_experiment(
        self, thresholds: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Run threshold evaluation across range of thresholds."""
        if thresholds is None:
            thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]

        results = []
        for thresh in thresholds:
            m = self.evaluate(threshold=thresh)
            results.append(
                {
                    "threshold": thresh,
                    "supported_top_1": m.supported_top_1_accuracy,
                    "supported_top_3": m.supported_top_3_accuracy,
                    "unsupported_rejection": m.unsupported_rejection_rate,
                    "false_positives": m.false_positives,
                    "false_negatives": m.false_negatives,
                    "overall_accuracy": m.overall_accuracy,
                    "avg_latency_ms": m.average_latency_ms,
                }
            )
        return results
