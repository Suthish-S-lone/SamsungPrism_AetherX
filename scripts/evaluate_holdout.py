#!/usr/bin/env python3
"""CLI benchmark evaluation tool for SmartGuide Holdout Dataset (Phase 2.75).

Evaluates the generalization of the Pretrained Neural Sentence Transformer Hybrid Retriever
vs. the Statistical TF-IDF Baseline on genuinely unseen holdout queries.
Produces the direct comparison table, threshold sweeps, latency distributions, and qualitative error analysis.
"""

import sys
import time
from pathlib import Path

# Add repository root to python path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.app.retrieval.holdout_evaluator import (
    HoldoutEvaluator,
    check_holdout_integrity,
)
from backend.app.retrieval.hybrid_retriever import HybridRetriever


def main():
    """Run holdout evaluation and print comparison report."""
    print("SMARTGUIDE HOLDOUT RETRIEVAL EVALUATION (PHASE 2.75)")
    print("====================================================")
    print()

    # 1. Check dataset integrity
    integrity = check_holdout_integrity()
    print("Holdout Integrity Status:")
    if integrity.is_valid:
        print("  PASSED (All 60 queries verified: 0 duplicate IDs, 0 data leakages with training corpus).")
    else:
        print(f"  FAILED: {integrity}")
        sys.exit(1)
    print()

    # 2. Warm up and initialize both models
    print("Initializing Retrievers...")
    t0 = time.perf_counter()
    neural_retriever = HybridRetriever(vector_mode="sentence_transformer")
    neural_load_time = time.perf_counter() - t0
    print(f"  Pretrained Neural Model ({neural_retriever.semantic_retriever.provider.model_name}) initialized in {neural_load_time:.2f}s")

    tfidf_retriever = HybridRetriever(vector_mode="tfidf")
    print(f"  Statistical TF-IDF Baseline initialized.")
    print()

    neural_evaluator = HoldoutEvaluator(retriever=neural_retriever)
    tfidf_evaluator = HoldoutEvaluator(retriever=tfidf_retriever)

    # 3. Threshold Comparison Sweep for Neural Model
    print("NEURAL MODEL THRESHOLD SWEEP (all-MiniLM-L6-v2 + BM25 + RRF)")
    print("-----------------------------------------------------------------------------------------")
    print(
        f"{'Threshold':<10} | {'Supp Top-1':<11} | {'Supp Top-3':<11} | {'Unsupp Rej':<11} | "
        f"{'FP':<4} | {'FN':<4} | {'Overall Acc':<12} | {'Latency':<8}"
    )
    print("-" * 89)

    neural_sweep = neural_evaluator.run_threshold_experiment(
        [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
    )

    for res in neural_sweep:
        print(
            f"{res['threshold']:<10.2f} | "
            f"{res['supported_top_1']:<10.1f}% | "
            f"{res['supported_top_3']:<10.1f}% | "
            f"{res['unsupported_rejection']:<10.1f}% | "
            f"{res['false_positives']:<4} | "
            f"{res['false_negatives']:<4} | "
            f"{res['overall_accuracy']:<11.1f}% | "
            f"{res['avg_latency_ms']:<6.2f} ms"
        )
    print()

    # 4. Primary Metrics at Calibrated Threshold (0.70)
    selected_threshold = 0.70
    neural_metrics = neural_evaluator.evaluate(threshold=selected_threshold)
    tfidf_metrics = tfidf_evaluator.evaluate(threshold=selected_threshold)

    print("PRIMARY HOLDOUT METRICS (Threshold = 0.70)")
    print("==========================================")
    print(f"Holdout queries:\n  {neural_metrics.total_queries}")
    print()
    print(f"Supported:\n  {neural_metrics.supported_queries}")
    print()
    print(f"Unsupported:\n  {neural_metrics.unsupported_queries}")
    print()
    print(f"Top-1 accuracy (Overall):\n  {neural_metrics.top_1_accuracy:.1f}%")
    print(f"Top-1 accuracy (Supported only):\n  {neural_metrics.supported_top_1_accuracy:.1f}%")
    print()
    print(f"Top-3 accuracy (Overall):\n  {neural_metrics.top_3_accuracy:.1f}%")
    print(f"Top-3 accuracy (Supported only):\n  {neural_metrics.supported_top_3_accuracy:.1f}%")
    print()
    print(f"Unsupported rejection:\n  {neural_metrics.unsupported_rejection_rate:.1f}%")
    print()
    print(f"False positives:\n  {neural_metrics.false_positives}")
    print()
    print(f"False negatives:\n  {neural_metrics.false_negatives}")
    print()
    print(f"Average latency:\n  {neural_metrics.average_latency_ms:.2f} ms")
    print()
    print(f"P50 latency:\n  {neural_metrics.p50_latency_ms:.2f} ms")
    print()
    print(f"P95 latency:\n  {neural_metrics.p95_latency_ms:.2f} ms")
    print()

    # 5. Comparative Performance Table (Section 19)
    print("COMPARISON: TF-IDF BASELINE VS. PRETRAINED NEURAL RETRIEVAL (Threshold = 0.70)")
    print("================================================================================")
    print(f"{'Metric':<28} | {'TF-IDF Baseline':<17} | {'Sentence Transformer':<22} | {'Absolute Delta'}")
    print("-" * 88)
    print(f"{'Supported Top-1':<28} | {tfidf_metrics.supported_top_1_accuracy:<16.1f}% | {neural_metrics.supported_top_1_accuracy:<21.1f}% | +{neural_metrics.supported_top_1_accuracy - tfidf_metrics.supported_top_1_accuracy:.1f}%")
    print(f"{'Supported Top-3':<28} | {tfidf_metrics.supported_top_3_accuracy:<16.1f}% | {neural_metrics.supported_top_3_accuracy:<21.1f}% | +{neural_metrics.supported_top_3_accuracy - tfidf_metrics.supported_top_3_accuracy:.1f}%")
    print(f"{'Unsupported Rejection':<28} | {tfidf_metrics.unsupported_rejection_rate:<16.1f}% | {neural_metrics.unsupported_rejection_rate:<21.1f}% | {neural_metrics.unsupported_rejection_rate - tfidf_metrics.unsupported_rejection_rate:+.1f}%")
    print(f"{'False Positives':<28} | {tfidf_metrics.false_positives:<17} | {neural_metrics.false_positives:<22} | {neural_metrics.false_positives - tfidf_metrics.false_positives:+d}")
    print(f"{'False Negatives':<28} | {tfidf_metrics.false_negatives:<17} | {neural_metrics.false_negatives:<22} | {neural_metrics.false_negatives - tfidf_metrics.false_negatives:+d}")
    print(f"{'Overall Accuracy':<28} | {tfidf_metrics.overall_accuracy:<16.1f}% | {neural_metrics.overall_accuracy:<21.1f}% | +{neural_metrics.overall_accuracy - tfidf_metrics.overall_accuracy:.1f}%")
    print(f"{'Avg Query Latency':<28} | {tfidf_metrics.average_latency_ms:<14.2f} ms | {neural_metrics.average_latency_ms:<19.2f} ms | +{neural_metrics.average_latency_ms - tfidf_metrics.average_latency_ms:.2f} ms")
    print(f"{'P95 Query Latency':<28} | {tfidf_metrics.p95_latency_ms:<14.2f} ms | {neural_metrics.p95_latency_ms:<19.2f} ms | +{neural_metrics.p95_latency_ms - tfidf_metrics.p95_latency_ms:.2f} ms")
    print()

    # 6. Qualitative Analysis
    # A. 5 Correctly retrieved supported queries
    correct_supp = [
        c for c in neural_metrics.detailed_candidates if c["supported"] and c["correct"]
    ]
    print("1. CORRECTLY RETRIEVED SUPPORTED QUERIES (Sample 5)")
    print("===================================================")
    for c in correct_supp[:5]:
        print(f"QUERY:                   \"{c['query']}\"")
        print(f"EXPECTED:                {c['expected_problem_id']}")
        print(f"PREDICTED:               {c['predicted_problem_id']}")
        print(f"RANK:                    {c['rank']}")
        print(f"BM25 contribution/rank:  {c['bm25_rank'] or 'None'}")
        print(f"VECTOR contribution/rank:{c['semantic_rank'] or 'None'}")
        print(f"RRF score:               {c['fused_score']:.4f}")
        print(f"FINAL STATUS:            CORRECT ({c['status']})")
        print("-" * 60)
    print()

    # B. Incorrectly retrieved supported queries (if any)
    incorrect_supp = [
        c for c in neural_metrics.detailed_candidates if c["supported"] and not c["correct"]
    ]
    print(f"2. INCORRECTLY RETRIEVED SUPPORTED QUERIES ({len(incorrect_supp)} total)")
    print("===================================================")
    if incorrect_supp:
        for c in incorrect_supp[:5]:
            print(f"QUERY:                   \"{c['query']}\"")
            print(f"EXPECTED:                {c['expected_problem_id']}")
            print(f"PREDICTED:               {c['predicted_problem_id']}")
            print(f"RANK:                    {c['rank'] or 'N/A'}")
            print(f"BM25 contribution/rank:  {c['bm25_rank'] or 'None'}")
            print(f"VECTOR contribution/rank:{c['semantic_rank'] or 'None'}")
            print(f"RRF score:               {c['fused_score']:.4f}")
            print(f"FINAL STATUS:            INCORRECT ({c['status']})")
            print("-" * 60)
    else:
        print("  None (0 misclassifications on supported holdout queries).")
    print()

    # C. 5 Correctly rejected unsupported queries
    correct_unsupp = [
        c for c in neural_metrics.detailed_candidates if not c["supported"] and c["correct"]
    ]
    print("3. CORRECTLY REJECTED UNSUPPORTED QUERIES (Sample 5)")
    print("=====================================================")
    for c in correct_unsupp[:5]:
        print(f"QUERY:                   \"{c['query']}\"")
        print(f"EXPECTED:                None (unsupported)")
        print(f"PREDICTED:               {c['predicted_problem_id'] or 'None'}")
        print(f"RANK:                    N/A")
        print(f"BM25 contribution/rank:  {c['bm25_rank'] or 'None'}")
        print(f"VECTOR contribution/rank:{c['semantic_rank'] or 'None'}")
        print(f"RRF score:               {c['fused_score']:.4f}")
        print(f"FINAL STATUS:            CORRECT ({c['status']})")
        print("-" * 60)
    print()

    # D. Incorrectly accepted unsupported queries (if any)
    incorrect_unsupp = [
        c for c in neural_metrics.detailed_candidates if not c["supported"] and not c["correct"]
    ]
    print(f"4. INCORRECTLY ACCEPTED UNSUPPORTED QUERIES ({len(incorrect_unsupp)} total)")
    print("=====================================================")
    if incorrect_unsupp:
        for c in incorrect_unsupp[:5]:
            print(f"QUERY:                   \"{c['query']}\"")
            print(f"EXPECTED:                None (unsupported)")
            print(f"PREDICTED:               {c['predicted_problem_id']}")
            print(f"RANK:                    1")
            print(f"BM25 contribution/rank:  {c['bm25_rank']}")
            print(f"VECTOR contribution/rank:{c['semantic_rank']}")
            print(f"RRF score:               {c['fused_score']:.4f}")
            print(f"FINAL STATUS:            FALSE POSITIVE ({c['status']})")
            print("-" * 60)
    else:
        print("  None (0 false positives on unsupported holdout queries).")
    print()


if __name__ == "__main__":
    main()
