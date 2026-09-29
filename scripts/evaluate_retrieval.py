#!/usr/bin/env python3
"""CLI benchmark evaluation tool for SmartGuide Hybrid Retrieval.

Evaluates test_queries.json development benchmark, printing performance metrics,
sample queries, failure cases, and threshold sweep results.
"""

import sys
from pathlib import Path

# Add repository root to python path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.app.config import settings
from backend.app.retrieval.evaluator import RetrievalEvaluator
from backend.app.retrieval.hybrid_retriever import HybridRetriever


def main():
    """Run retrieval evaluation and print formatted benchmark report."""
    print("SMARTGUIDE RETRIEVAL EVALUATION")
    print("================================")
    print()
    print("Dataset:")
    print("  Development benchmark (data/development/test_queries.json)")
    print()

    retriever = HybridRetriever()
    evaluator = RetrievalEvaluator(retriever=retriever)

    # 1. Run threshold sweep to evaluate optimal calibration
    print("THRESHOLD EXPERIMENT (DEVELOPMENT DATA CALIBRATION)")
    print("--------------------------------------------------")
    print(
        f"{'Threshold':<11} | {'Top-1 Acc':<10} | {'Top-3 Acc':<10} | {'Supp Acc':<10} | "
        f"{'Unsupp Rej':<11} | {'FP':<4} | {'FN':<4} | {'F1 Score':<9} | {'Latency':<8}"
    )
    print("-" * 92)

    sweep = evaluator.run_threshold_experiment(
        [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
    )
    best_threshold = 0.55
    best_f1 = 0.0

    for res in sweep:
        print(
            f"{res['threshold']:<11.2f} | "
            f"{res['top_1_accuracy']:<9.1f}% | "
            f"{res['top_3_accuracy']:<9.1f}% | "
            f"{res['supported_accuracy']:<9.1f}% | "
            f"{res['unsupported_rejection_rate']:<10.1f}% | "
            f"{res['false_positives']:<4} | "
            f"{res['false_negatives']:<4} | "
            f"{res['f1_score']:<8.1f}% | "
            f"{res['avg_latency_ms']:<6.2f} ms"
        )
        if res["f1_score"] > best_f1:
            best_f1 = res["f1_score"]
            best_threshold = res["threshold"]

    print()
    print(f"Selected Calibrated Threshold: {best_threshold:.2f} (F1 Score: {best_f1:.1f}%)")
    print("NOTE: Calibrated exclusively on the development dataset.")
    print()

    # 2. Run detailed evaluation at selected threshold
    metrics = evaluator.evaluate(threshold=best_threshold)

    print("PRIMARY BENCHMARK METRICS")
    print("=========================")
    print(f"Queries:\n  {metrics.total_queries} ({metrics.supported_queries} supported, {metrics.unsupported_queries} unsupported)")
    print()
    print(f"Top-1 accuracy:\n  {metrics.top_1_accuracy:.1f}%")
    print()
    print(f"Top-3 accuracy:\n  {metrics.top_3_accuracy:.1f}%")
    print()
    print(f"Supported query accuracy:\n  {metrics.supported_accuracy:.1f}%")
    print()
    print(f"Unsupported query rejection:\n  {metrics.unsupported_rejection_rate:.1f}%")
    print()
    print(f"False positives:\n  {metrics.false_positives}")
    print()
    print(f"False negatives:\n  {metrics.false_negatives}")
    print()
    print(f"Average latency:\n  {metrics.average_latency_ms:.2f} ms")
    print()

    # 3. Show representative query examples
    print("SAMPLE EVALUATION QUERIES")
    print("=========================")
    correct_samples = [r for r in metrics.per_query_results if r.correct][:5]
    for sample in correct_samples:
        print(f"QUERY:\n  \"{sample.query}\"")
        print(f"EXPECTED:\n  {sample.expected_problem_id or 'NO_MATCH (unsupported)'}")
        print(f"PREDICTED:\n  {sample.predicted_problem_id or 'NO_MATCH'}")
        print(f"RANK:\n  {sample.rank or 'N/A'}")
        print(f"SCORE:\n  {sample.score:.4f}")
        print(f"STATUS:\n  {'CORRECT' if sample.correct else 'INCORRECT'}")
        print()

    # 4. Show incorrect cases (if any)
    incorrect_samples = [r for r in metrics.per_query_results if not r.correct]
    if incorrect_samples:
        print("INCORRECT / MISCLASSIFIED CASES")
        print("================================")
        for sample in incorrect_samples[:5]:
            print(f"QUERY:\n  \"{sample.query}\"")
            print(f"EXPECTED:\n  {sample.expected_problem_id or 'NO_MATCH (unsupported)'}")
            print(f"PREDICTED:\n  {sample.predicted_problem_id or 'NO_MATCH'}")
            print(f"RANK:\n  {sample.rank or 'N/A'}")
            print(f"SCORE:\n  {sample.score:.4f}")
            print(f"STATUS:\n  INCORRECT ({sample.status})")
            print()
    else:
        print("INCORRECT / MISCLASSIFIED CASES")
        print("================================")
        print("  None (0 misclassifications on development benchmark).")
        print()


if __name__ == "__main__":
    main()
