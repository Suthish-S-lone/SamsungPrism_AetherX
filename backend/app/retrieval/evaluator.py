"""Retrieval benchmark evaluator and confidence threshold experimentation.

Evaluates hybrid retrieval accuracy against test_queries.json development benchmark,
measuring Top-1, Top-3, false positives, false negatives, and query latency.
"""

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from backend.app.config import settings
from backend.app.models.data_models import TestQueryRecord
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.retrieval.types import EvaluationMetrics, QueryEvaluationResult


class RetrievalEvaluator:
    """Benchmark evaluation harness for the SmartGuide retrieval engine."""

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        test_queries_path: Optional[Path] = None,
    ):
        self.retriever = retriever or HybridRetriever()
        self.test_queries_path = (
            test_queries_path or settings.DATA_DIR / "test_queries.json"
        )
        self.test_queries = self._load_test_queries()

    def _load_test_queries(self) -> List[TestQueryRecord]:
        """Load benchmark queries from JSON."""
        if not self.test_queries_path.exists():
            raise FileNotFoundError(f"Test queries not found: {self.test_queries_path}")
        with open(self.test_queries_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return [TestQueryRecord.model_validate(item) for item in raw_data]

    def evaluate(self, threshold: Optional[float] = None) -> EvaluationMetrics:
        """Evaluate retrieval performance across all test queries at a given threshold."""
        thresh = (
            threshold
            if threshold is not None
            else self.retriever.similarity_threshold
        )

        per_query_results: List[QueryEvaluationResult] = []
        total_latencies: List[float] = []

        top_1_correct = 0
        top_3_correct = 0
        supported_total = 0
        supported_correct = 0
        unsupported_total = 0
        unsupported_rejected = 0
        false_positives = 0
        false_negatives = 0

        for tq in self.test_queries:
            start_t = time.perf_counter()
            results = self.retriever.retrieve(tq.query, top_k=3, threshold=thresh)
            latency_ms = (time.perf_counter() - start_t) * 1000.0
            total_latencies.append(latency_ms)

            top_1 = results[0] if results else None
            top_1_pred_id = top_1.problem_id if top_1 else None
            top_1_score = top_1.score if top_1 else 0.0
            top_1_status = top_1.status if top_1 else "NO_MATCH"

            # Check target rank in top 3
            target_rank = None
            if tq.expected_problem_id:
                for idx, r in enumerate(results, start=1):
                    if r.problem_id == tq.expected_problem_id and r.status == "MATCH":
                        target_rank = idx
                        break

            is_supported = tq.expected_problem_id is not None
            query_is_correct = False

            if is_supported:
                supported_total += 1
                if top_1_status == "MATCH" and top_1_pred_id == tq.expected_problem_id:
                    query_is_correct = True
                    supported_correct += 1
                    top_1_correct += 1
                else:
                    false_negatives += 1

                if target_rank is not None and target_rank <= 3:
                    top_3_correct += 1
            else:
                unsupported_total += 1
                # For unsupported query, correct if NO_MATCH
                if top_1 is None or top_1_status == "NO_MATCH":
                    query_is_correct = True
                    unsupported_rejected += 1
                    top_1_correct += 1
                    top_3_correct += 1
                else:
                    # Falsely accepted an out-of-scope query
                    false_positives += 1

            eval_res = QueryEvaluationResult(
                query_id=tq.id,
                query=tq.query,
                expected_domain=tq.expected_domain,
                expected_problem_id=tq.expected_problem_id,
                predicted_problem_id=top_1_pred_id if top_1_status == "MATCH" else None,
                correct=query_is_correct,
                rank=target_rank if is_supported else (1 if query_is_correct else None),
                score=top_1_score,
                status=top_1_status,
                latency_ms=round(latency_ms, 3),
            )
            per_query_results.append(eval_res)

        total_q = len(self.test_queries)
        avg_lat = sum(total_latencies) / total_q if total_q > 0 else 0.0

        return EvaluationMetrics(
            total_queries=total_q,
            supported_queries=supported_total,
            unsupported_queries=unsupported_total,
            top_1_accuracy=round((top_1_correct / total_q) * 100.0, 2) if total_q else 0.0,
            top_3_accuracy=round((top_3_correct / total_q) * 100.0, 2) if total_q else 0.0,
            supported_accuracy=round((supported_correct / supported_total) * 100.0, 2)
            if supported_total
            else 0.0,
            unsupported_rejection_rate=round(
                (unsupported_rejected / unsupported_total) * 100.0, 2
            )
            if unsupported_total
            else 0.0,
            false_positives=false_positives,
            false_negatives=false_negatives,
            average_latency_ms=round(avg_lat, 2),
            threshold=thresh,
            per_query_results=per_query_results,
        )

    def run_threshold_experiment(
        self, thresholds: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """Run benchmark sweeps over a range of confidence thresholds."""
        if thresholds is None:
            thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]

        results = []
        for thresh in thresholds:
            metrics = self.evaluate(threshold=thresh)
            # Calculate F1 score for classification
            # Precision = TP / (TP + FP) where TP = supported_correct
            # Recall = TP / (TP + FN)
            tp = metrics.supported_queries - metrics.false_negatives
            fp = metrics.false_positives
            fn = metrics.false_negatives
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (
                (2 * precision * recall) / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )

            results.append(
                {
                    "threshold": thresh,
                    "top_1_accuracy": metrics.top_1_accuracy,
                    "top_3_accuracy": metrics.top_3_accuracy,
                    "supported_accuracy": metrics.supported_accuracy,
                    "unsupported_rejection_rate": metrics.unsupported_rejection_rate,
                    "false_positives": metrics.false_positives,
                    "false_negatives": metrics.false_negatives,
                    "precision": round(precision * 100.0, 2),
                    "recall": round(recall * 100.0, 2),
                    "f1_score": round(f1 * 100.0, 2),
                    "avg_latency_ms": metrics.average_latency_ms,
                }
            )
        return results
