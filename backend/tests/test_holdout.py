"""Unit tests for Phase 2.5: Holdout Benchmark and Generalization Hardening.

Verifies:
- Holdout dataset loads and validates against HoldoutQueryRecord schema
- Referential integrity with troubleshooting problem IDs
- No data leakage / exact overlap with development benchmark
- HoldoutEvaluator metrics calculation and threshold sweep
"""

import json
from pathlib import Path
import pytest

from backend.app.config import settings
from backend.app.models.data_models import HoldoutQueryRecord
from backend.app.retrieval.holdout_evaluator import (
    HoldoutEvaluator,
    check_holdout_integrity,
)
from backend.app.retrieval.hybrid_retriever import HybridRetriever


@pytest.fixture(scope="module")
def holdout_path() -> Path:
    """Fixture returning path to holdout_queries.json."""
    return settings.DATA_DIR / "holdout_queries.json"


@pytest.fixture(scope="module")
def holdout_evaluator():
    """Fixture returning an initialized HoldoutEvaluator instance."""
    retriever = HybridRetriever()
    return HoldoutEvaluator(retriever=retriever)


def test_holdout_dataset_loads_and_validates(holdout_path: Path):
    """Test 1: Holdout dataset loads all 60 records and conforms to schema."""
    assert holdout_path.exists(), f"holdout_queries.json missing at {holdout_path}"

    with open(holdout_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    assert len(raw_data) == 60
    records = [HoldoutQueryRecord.model_validate(r) for r in raw_data]
    assert len(records) == 60

    supported = [r for r in records if r.supported]
    unsupported = [r for r in records if not r.supported]
    assert len(supported) == 40
    assert len(unsupported) == 20


def test_holdout_expected_problem_ids_exist(holdout_path: Path):
    """Test 2: All supported holdout queries reference valid troubleshooting problem IDs."""
    with open(settings.DATA_DIR / "troubleshooting.json", "r", encoding="utf-8") as f:
        tb_data = json.load(f)
    valid_ids = {r["id"] for r in tb_data}

    with open(holdout_path, "r", encoding="utf-8") as f:
        holdout_data = json.load(f)

    for r in holdout_data:
        if r["supported"]:
            assert (
                r["expected_problem_id"] in valid_ids
            ), f"Invalid expected_problem_id: {r['expected_problem_id']} in query {r['id']}"
            assert r["expected_domain"] in [
                "battery",
                "display",
                "camera",
                "performance",
            ]


def test_holdout_unsupported_queries_have_null_targets(holdout_path: Path):
    """Test 3: Unsupported holdout queries have null expected_problem_id and expected_domain."""
    with open(holdout_path, "r", encoding="utf-8") as f:
        holdout_data = json.load(f)

    for r in holdout_data:
        if not r["supported"]:
            assert r["expected_problem_id"] is None
            assert r["expected_domain"] is None


def test_holdout_integrity_and_no_duplicate_benchmark_queries():
    """Test 4: Integrity check verifies 0 leakage and 0 duplicate IDs."""
    integrity = check_holdout_integrity()
    assert integrity.is_valid is True
    assert integrity.total_queries == 60
    assert integrity.supported_queries == 40
    assert integrity.unsupported_queries == 20
    assert len(integrity.duplicate_ids) == 0
    assert len(integrity.exact_matches_with_canonical) == 0
    assert len(integrity.exact_matches_with_test_queries) == 0
    assert len(integrity.exact_matches_with_variations) == 0


def test_holdout_evaluator_runs_and_calculates_metrics(holdout_evaluator: HoldoutEvaluator):
    """Test 5: HoldoutEvaluator produces complete metrics including P50/P95 latencies."""
    metrics = holdout_evaluator.evaluate(threshold=0.70)
    assert metrics.total_queries == 60
    assert metrics.supported_queries == 40
    assert metrics.unsupported_queries == 20
    assert metrics.average_latency_ms > 0
    assert metrics.p50_latency_ms > 0
    assert metrics.p95_latency_ms >= metrics.p50_latency_ms
    assert 0 <= metrics.unsupported_rejection_rate <= 100.0


def test_holdout_threshold_sweep_runs(holdout_evaluator: HoldoutEvaluator):
    """Test 6: HoldoutEvaluator threshold sweep produces comparison metrics."""
    sweep = holdout_evaluator.run_threshold_experiment([0.50, 0.70, 0.90])
    assert len(sweep) == 3
    # Check that unsupported rejection rate increases or stays high with stricter threshold
    assert sweep[2]["unsupported_rejection"] >= sweep[0]["unsupported_rejection"]
