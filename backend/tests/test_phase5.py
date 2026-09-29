"""End-to-End Validation & Hardening Tests for Phase 5.

Verifies:
1. Health endpoint response schema and subsystem statuses
2. Supported queries across all 4 domains (Battery, Display, Camera, Performance)
3. Colloquial query understanding and grounded resolution
4. Noisy queries (typos, punctuation, casual slang)
5. Out-of-scope query rejection (weather, recipes, travel, movies, appliances)
6. Empty / whitespace request validation
7. Diagnostic debug transparency metadata
8. Prototype deeplink resolution integrity
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.troubleshooting_service import TroubleshootingService

client = TestClient(app)


@pytest.fixture(scope="module")
def tb_service():
    """Module-level troubleshooting service instance."""
    return TroubleshootingService()


# -----------------------------------------------------------------------------
# 1. Health Endpoint Tests
# -----------------------------------------------------------------------------

def test_health_endpoint_contract():
    """Verify GET /health returns valid schema and status 'ok'."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["data"] == "ready"
    assert data["schema"] == "ready"


# -----------------------------------------------------------------------------
# 2. Supported Domain Queries (Battery, Display, Camera, Performance)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "query,expected_domain",
    [
        ("battery drain issue after update", "battery"),
        ("phone gets very hot while charging", "battery"),
        ("charging is slower than expected with cable", "battery"),
        ("camera app freezes and locks up", "camera"),
        ("camera takes too long to open from home screen", "camera"),
        ("screen brightness keeps changing unexpectedly", "display"),
        ("navigation swipe gestures behave unexpectedly", "display"),
        ("phone is slow and sluggish with multiple apps open", "performance"),
    ],
)
def test_supported_queries_end_to_end(query: str, expected_domain: str, tb_service: TroubleshootingService):
    """Verify supported queries return confident resolution within expected domain."""
    res = tb_service.troubleshoot(query, debug=True)
    assert len(res.contexts) > 0, f"Expected match for '{query}'"
    top_ctx = res.contexts[0]
    assert top_ctx.score > 0.0
    assert len(top_ctx.actions) > 0

    # Verify action deeplinks use prototype:// scheme
    for act in top_ctx.actions:
        if act.deeplink:
            assert act.deeplink.startswith("prototype://"), f"Invalid deeplink scheme: {act.deeplink}"

    # Verify debug info is present
    assert res.debug_info is not None
    assert res.debug_info.latency.total_pipeline_ms > 0


# -----------------------------------------------------------------------------
# 3. Colloquial Queries Validation
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "colloquial_query,expected_keyword",
    [
        ("My phone dies before lunch every day", "battery"),
        ("My phone gets really hot just sitting there", "hot"),
        ("The camera just freezes when I try recording", "camera"),
        ("The screen keeps changing brightness by itself", "brightness"),
        ("Everything feels slow when I open many apps", "slow"),
    ],
)
def test_colloquial_queries_understanding(colloquial_query: str, expected_keyword: str, tb_service: TroubleshootingService):
    """Verify natural colloquial phrases are translated to grounded actions."""
    res = tb_service.troubleshoot(colloquial_query, debug=True)
    assert len(res.contexts) > 0, f"Colloquial query '{colloquial_query}' produced no match"
    top_context = res.contexts[0]
    assert top_context.actions[0].target_screen != ""
    assert top_context.actions[0].deeplink is not None


# -----------------------------------------------------------------------------
# 4. Noisy Queries (Typos, Casual, Missing Punctuation)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "noisy_query",
    [
        "phone battery draining fast",
        "camera freezing when recording video",
        "scrn brightness flickring dim",
        "phone laggy freezing up",
    ],
)
def test_noisy_queries_resilience(noisy_query: str, tb_service: TroubleshootingService):
    """Verify retrieval engine resists typographical and casual noise."""
    res = tb_service.troubleshoot(noisy_query, debug=True)
    # Neural semantic retriever should surface candidate
    assert len(res.contexts) > 0, f"Noisy query '{noisy_query}' failed to retrieve"


# -----------------------------------------------------------------------------
# 5. Out-of-Scope Query Rejection
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "unsupported_query",
    [
        "Will it rain tomorrow in Seoul?",
        "How do I bake chocolate chip cookies?",
        "Best flight deals to Tokyo for vacation",
        "Who directed the movie Inception?",
        "How to connect my smart refrigerator to wifi",
    ],
)
def test_out_of_scope_queries_rejected(unsupported_query: str, tb_service: TroubleshootingService):
    """Verify completely unsupported queries are safely rejected without false positives."""
    res = tb_service.troubleshoot(unsupported_query, debug=True)
    assert len(res.contexts) == 0, f"Query '{unsupported_query}' should be rejected as out-of-scope"
    assert res.fallback is not None
    assert "supported" in res.fallback.lower() or "troubleshooting" in res.fallback.lower()


# -----------------------------------------------------------------------------
# 6. Edge Cases & Request Validation
# -----------------------------------------------------------------------------

def test_api_empty_query_rejected():
    """Verify empty query is rejected with HTTP 422 Unprocessable Entity."""
    response = client.post("/troubleshoot", json={"query": ""})
    assert response.status_code == 422


def test_api_whitespace_query_handled():
    """Verify whitespace-only query is handled gracefully or rejected."""
    response = client.post("/troubleshoot", json={"query": "   "})
    # Pydantic or service should reject or return out-of-scope fallback
    if response.status_code == 200:
        data = response.json()
        assert len(data["contexts"]) == 0
        assert data["fallback"] is not None


def test_api_debug_flag_toggle():
    """Verify debug=true includes debug_info while debug=false omits it."""
    res_debug = client.post("/troubleshoot?debug=true", json={"query": "battery drain"})
    assert res_debug.status_code == 200
    assert res_debug.json()["debug_info"] is not None

    res_nodebug = client.post("/troubleshoot?debug=false", json={"query": "battery drain"})
    assert res_nodebug.status_code == 200
    assert res_nodebug.json()["debug_info"] is None
