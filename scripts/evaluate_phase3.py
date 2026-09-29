#!/usr/bin/env python3
"""CLI benchmark evaluation tool for SmartGuide Phase 3.

Evaluates the complete end-to-end Query Understanding + Pretrained Neural Hybrid Retrieval
pipeline across both the Development benchmark (72 queries) and the Unseen Holdout benchmark (60 queries).
Computes ablation comparisons, latency distributions, and comparative progress tables.
"""

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add repository root to python path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.app.config import settings
from backend.app.retrieval.documents import DocumentBuilder
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.services.canonicalizer import QueryCanonicalizer
from backend.app.services.query_understanding import QueryUnderstandingService
from backend.app.services.troubleshooting_service import TroubleshootingService


def evaluate_dataset(
    service: TroubleshootingService,
    dataset_path: Path,
    threshold: float = 0.70,
) -> dict:
    """Run full Phase 3 evaluation on a JSON benchmark dataset."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_queries = len(data)
    supported_queries = 0
    unsupported_queries = 0

    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0

    supp_top_1_correct = 0
    supp_top_3_correct = 0
    unsupp_correct_rejections = 0

    latencies_qu = []
    latencies_ret = []
    latencies_syn = []
    latencies_total = []

    per_query_results = []

    # Map problem title to problem_id
    title_to_id = {doc.problem: doc.problem_id for doc in service.retriever.documents}

    for item in data:
        q_text = item["query"]
        expected_id = item.get("expected_problem_id")
        is_supported = item.get("supported", expected_id is not None)

        if is_supported:
            supported_queries += 1
        else:
            unsupported_queries += 1

        t0 = time.perf_counter()
        resp = service.troubleshoot(q_text, threshold=threshold, debug=True)
        total_time_ms = (time.perf_counter() - t0) * 1000.0

        if resp.debug_info:
            latencies_qu.append(resp.debug_info.latency.query_understanding_ms)
            latencies_ret.append(resp.debug_info.latency.retrieval_ms)
            latencies_syn.append(resp.debug_info.latency.response_synthesis_ms)
            latencies_total.append(resp.debug_info.latency.total_pipeline_ms)
        else:
            latencies_total.append(total_time_ms)

        predicted_id = None
        predicted_score = 0.0
        if resp.contexts:
            ctx = resp.contexts[0]
            predicted_id = title_to_id.get(ctx.goal)
            predicted_score = ctx.score

        # Candidate check for Top-3
        top_candidates = []
        if resp.debug_info and resp.debug_info.retrieval:
            top_candidates = [c.problem_id for c in resp.debug_info.retrieval.top_candidates[:3]]

        is_top_1 = (predicted_id == expected_id) if is_supported else (predicted_id is None)
        is_top_3 = (expected_id in top_candidates) if is_supported else (predicted_id is None)

        status = "UNKNOWN"
        if is_supported:
            if is_top_1:
                true_positives += 1
                supp_top_1_correct += 1
                supp_top_3_correct += 1
                status = "CORRECT_TOP_1"
            elif is_top_3:
                true_positives += 1
                supp_top_3_correct += 1
                status = "CORRECT_TOP_3"
            else:
                false_negatives += 1
                status = "MISCLASSIFIED" if predicted_id else "REJECTED_FALSE_NEGATIVE"
        else:
            if predicted_id is None:
                true_negatives += 1
                unsupp_correct_rejections += 1
                status = "CORRECT_REJECTION"
            else:
                false_positives += 1
                status = "FALSE_POSITIVE"

        per_query_results.append({
            "id": item.get("id"),
            "query": q_text,
            "expected_problem_id": expected_id,
            "predicted_problem_id": predicted_id,
            "predicted_score": predicted_score,
            "is_supported": is_supported,
            "status": status,
            "debug": resp.debug_info,
        })

    supp_top_1 = (supp_top_1_correct / supported_queries * 100.0) if supported_queries else 0.0
    supp_top_3 = (supp_top_3_correct / supported_queries * 100.0) if supported_queries else 0.0
    unsupp_rej = (unsupp_correct_rejections / unsupported_queries * 100.0) if unsupported_queries else 100.0
    overall_acc = ((supp_top_1_correct + unsupp_correct_rejections) / total_queries * 100.0) if total_queries else 0.0

    precision = (true_positives / (true_positives + false_positives)) if (true_positives + false_positives) else 0.0
    recall = (true_positives / (true_positives + false_negatives)) if (true_positives + false_negatives) else 0.0
    f1 = (2 * precision * recall / (precision + recall) * 100.0) if (precision + recall) else 0.0

    latencies_sorted = sorted(latencies_total)
    p50_lat = latencies_sorted[int(len(latencies_sorted) * 0.50)] if latencies_sorted else 0.0
    p95_lat = latencies_sorted[int(len(latencies_sorted) * 0.95)] if latencies_sorted else 0.0
    avg_lat = statistics.mean(latencies_total) if latencies_total else 0.0

    return {
        "total_queries": total_queries,
        "supported_queries": supported_queries,
        "unsupported_queries": unsupported_queries,
        "supported_top_1": supp_top_1,
        "supported_top_3": supp_top_3,
        "unsupported_rejection": unsupp_rej,
        "overall_accuracy": overall_acc,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "f1_score": f1,
        "avg_latency_ms": avg_lat,
        "p50_latency_ms": p50_lat,
        "p95_latency_ms": p95_lat,
        "avg_qu_ms": statistics.mean(latencies_qu) if latencies_qu else 0.0,
        "avg_ret_ms": statistics.mean(latencies_ret) if latencies_ret else 0.0,
        "avg_syn_ms": statistics.mean(latencies_syn) if latencies_syn else 0.0,
        "per_query_results": per_query_results,
    }


def main():
    """Run full Phase 3 benchmark evaluation."""
    print("================================================================================")
    print("           SMARTGUIDE PHASE 3 COMPREHENSIVE BENCHMARK EVALUATION                ")
    print("   Query Understanding + Pretrained Neural Hybrid Retrieval + Deeplink Engine   ")
    print("================================================================================")
    print()

    # Initialize Troubleshooting Service
    print("Initializing Phase 3 Services...")
    t_init = time.perf_counter()
    service = TroubleshootingService()
    print(f"Phase 3 Pipeline initialized in {time.perf_counter() - t_init:.2f}s\n")

    # 1. Development Dataset Evaluation
    dev_path = settings.DATA_DIR / "test_queries.json"
    print("1. EVALUATION ON DEVELOPMENT BENCHMARK (72 Queries)")
    print("--------------------------------------------------------------------------------")
    dev_metrics = evaluate_dataset(service, dev_path, threshold=0.70)
    print(f"Total Queries:            {dev_metrics['total_queries']} ({dev_metrics['supported_queries']} supported, {dev_metrics['unsupported_queries']} unsupported)")
    print(f"Supported Top-1 Accuracy: {dev_metrics['supported_top_1']:.1f}%")
    print(f"Supported Top-3 Accuracy: {dev_metrics['supported_top_3']:.1f}%")
    print(f"Unsupported Rejection:    {dev_metrics['unsupported_rejection']:.1f}%")
    print(f"False Positives:          {dev_metrics['false_positives']}")
    print(f"False Negatives:          {dev_metrics['false_negatives']}")
    print(f"Overall Accuracy:         {dev_metrics['overall_accuracy']:.1f}%")
    print(f"F1 Score:                 {dev_metrics['f1_score']:.1f}%")
    print(f"Average Pipeline Latency: {dev_metrics['avg_latency_ms']:.2f} ms")
    print()

    # 2. Holdout Dataset Evaluation
    holdout_path = settings.DATA_DIR / "holdout_queries.json"
    print("2. EVALUATION ON UNSEEN HOLDOUT BENCHMARK (60 Queries)")
    print("--------------------------------------------------------------------------------")
    holdout_metrics = evaluate_dataset(service, holdout_path, threshold=0.70)
    print(f"Total Queries:            {holdout_metrics['total_queries']} ({holdout_metrics['supported_queries']} supported, {holdout_metrics['unsupported_queries']} unsupported)")
    print(f"Supported Top-1 Accuracy: {holdout_metrics['supported_top_1']:.1f}%")
    print(f"Supported Top-3 Accuracy: {holdout_metrics['supported_top_3']:.1f}%")
    print(f"Unsupported Rejection:    {holdout_metrics['unsupported_rejection']:.1f}%")
    print(f"False Positives:          {holdout_metrics['false_positives']}")
    print(f"False Negatives:          {holdout_metrics['false_negatives']}")
    print(f"Overall Accuracy:         {holdout_metrics['overall_accuracy']:.1f}%")
    print(f"F1 Score:                 {holdout_metrics['f1_score']:.1f}%")
    print()
    print("Latency Profile (Holdout):")
    print(f"  - Query Understanding (ms):   {holdout_metrics['avg_qu_ms']:.2f} ms")
    print(f"  - Hybrid Retrieval (ms):       {holdout_metrics['avg_ret_ms']:.2f} ms")
    print(f"  - Response Synthesis (ms):     {holdout_metrics['avg_syn_ms']:.2f} ms")
    print(f"  - Total Average Latency (ms):  {holdout_metrics['avg_latency_ms']:.2f} ms")
    print(f"  - P50 Latency (ms):            {holdout_metrics['p50_latency_ms']:.2f} ms")
    print(f"  - P95 Latency (ms):            {holdout_metrics['p95_latency_ms']:.2f} ms")
    print()

    # 3. 3-Way Comparative Benchmark Table across all Phases on Holdout
    p3_top1_str = f"{holdout_metrics['supported_top_1']:.1f}%"
    p3_top3_str = f"{holdout_metrics['supported_top_3']:.1f}%"
    p3_rej_str = f"{holdout_metrics['unsupported_rejection']:.1f}%"
    p3_fp_str = str(holdout_metrics['false_positives'])
    p3_fn_str = str(holdout_metrics['false_negatives'])
    p3_acc_str = f"{holdout_metrics['overall_accuracy']:.1f}%"
    p3_f1_str = f"{holdout_metrics['f1_score']:.1f}%"
    p3_lat_str = f"{holdout_metrics['avg_latency_ms']:.2f} ms"
    p3_p95_str = f"{holdout_metrics['p95_latency_ms']:.2f} ms"

    print("3. HOLDOUT GENERALIZATION COMPARISON ACROSS ALL DEVELOPMENT PHASES")
    print("================================================================================")
    print(f"{'Metric':<26} | {'Phase 2.5 (TF-IDF)':<18} | {'Phase 2.75 (Neural)':<20} | {'Phase 3 (Full Pipeline)':<22}")
    print("-" * 94)
    print(f"{'Supported Top-1 Acc':<26} | {'2.5%':<18} | {'25.0%':<20} | {p3_top1_str:<22}")
    print(f"{'Supported Top-3 Acc':<26} | {'2.5%':<18} | {'25.0%':<20} | {p3_top3_str:<22}")
    print(f"{'Unsupported Rejection':<26} | {'100.0%':<18} | {'100.0%':<20} | {p3_rej_str:<22}")
    print(f"{'False Positives':<26} | {'0':<18} | {'0':<20} | {p3_fp_str:<22}")
    print(f"{'False Negatives':<26} | {'39':<18} | {'30':<20} | {p3_fn_str:<22}")
    print(f"{'Overall Accuracy':<26} | {'35.0%':<18} | {'50.0%':<20} | {p3_acc_str:<22}")
    print(f"{'F1 Score':<26} | {'4.9%':<18} | {'40.0%':<20} | {p3_f1_str:<22}")
    print(f"{'Average Latency':<26} | {'0.25 ms':<18} | {'7.85 ms':<20} | {p3_lat_str:<22}")
    print(f"{'P95 Latency':<26} | {'0.50 ms':<18} | {'12.30 ms':<20} | {p3_p95_str:<22}")
    print()

    # 4. Sample End-to-End Query Verification
    print("4. SAMPLE END-TO-END PREDICTIONS FROM HOLDOUT BENCHMARK")
    print("================================================================================")
    sample_queries = [
        "I have to plug my phone into the wall multiple times throughout the day.",
        "The back panel becomes uncomfortably warm even when I am just reading emails.",
        "Swiping up from the bottom of the glass to go home is completely unresponsive or triggers the wrong window.",
        "Tapping the photography icon shows a black window before crashing back to the home screen.",
        "Too many background syncing processes are hogging system resources.",
        "Will it rain tomorrow in Seattle?",
        "How do I order pizza using a delivery app?",
    ]

    for sq in sample_queries:
        r = service.troubleshoot(sq, debug=True)
        print(f"QUERY:     \"{sq}\"")
        if r.contexts:
            ctx = r.contexts[0]
            print(f"GOAL:      {ctx.goal}")
            print(f"SCORE:     {ctx.score}")
            print(f"ACTION:    {ctx.actions[0].action_name} -> {ctx.actions[0].target_screen}")
            print(f"DEEPLINK:  {ctx.actions[0].deeplink}")
        else:
            print(f"FALLBACK:  {r.fallback}")
        if r.debug_info:
            print(f"DECISION:  {r.debug_info.retrieval.decision} ({r.debug_info.retrieval.confidence_level})")
            print(f"LATENCY:   {r.debug_info.latency.total_pipeline_ms:.2f} ms")
        print("-" * 80)


if __name__ == "__main__":
    main()
