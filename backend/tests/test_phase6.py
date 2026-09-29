"""Phase 6 Automated Test Suite: Multi-Turn Intelligent Guided Troubleshooting.

Tests conversation state management, grounded ambiguity detection, clarification question
synthesis, diagnostic refinement via POST /troubleshoot/continue, and multi-turn timeline tracking.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.conversation import ClarificationQuestion, ConversationSession
from backend.app.models.request import ContinueTroubleshootRequest, TroubleshootRequest
from backend.app.services.clarification_service import CLARIFICATION_CATALOG, ClarificationService
from backend.app.services.troubleshooting_service import TroubleshootingService


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def tb_service():
    """TroubleshootingService fixture."""
    return TroubleshootingService()


@pytest.fixture
def clarification_service():
    """ClarificationService fixture."""
    return ClarificationService()


# =========================================================================
# 1. Clarification Catalog & Schema Integrity Tests
# =========================================================================

def test_clarification_catalog_integrity(tb_service: TroubleshootingService):
    """Verify clarification questions cover all 4 domains with grounded problem IDs."""
    domains = set()
    for q_id, q in CLARIFICATION_CATALOG.items():
        assert isinstance(q, ClarificationQuestion)
        assert q.id == q_id
        assert q.domain in {"battery", "display", "camera", "performance"}
        domains.add(q.domain)
        assert len(q.options) >= 2
        assert len(q.question) > 5

        # Verify every option has a valid grounded target_problem_id in knowledge base
        for opt in q.options:
            assert opt.id.startswith("opt_")
            assert len(opt.label) > 3
            assert len(opt.signal) > 2
            if opt.target_problem_id:
                assert (
                    opt.target_problem_id in tb_service.troubleshooting_records
                ), f"Option {opt.id} targets non-existent KB record {opt.target_problem_id}"

    assert domains == {"battery", "display", "camera", "performance"}


# =========================================================================
# 2. Ambiguity Detection & Clarification Triggers
# =========================================================================

def test_direct_diagnosis_for_specific_query(tb_service: TroubleshootingService):
    """Specific query with explicit condition bypasses clarification directly to diagnosis."""
    res = tb_service.troubleshoot("battery drains rapidly after latest software update")
    assert res.status == "diagnosis_ready"
    assert len(res.contexts) > 0
    assert res.session_id is not None
    assert res.clarification is None
    assert res.timeline is not None
    assert len(res.timeline) == 2
    assert res.timeline[0].step == "query_received"
    assert res.timeline[1].step == "diagnosis_ready"


@pytest.mark.parametrize(
    "vague_query,expected_catalog_id,expected_domain",
    [
        ("my phone gets hot", "clarify_battery_heat", "battery"),
        ("phone overheating", "clarify_battery_heat", "battery"),
        ("screen acting weird", "clarify_display_issue", "display"),
        ("camera not working", "clarify_camera_issue", "camera"),
        ("my phone is slow", "clarify_performance_issue", "performance"),
    ],
)
def test_vague_queries_trigger_clarification(
    vague_query: str,
    expected_catalog_id: str,
    expected_domain: str,
    tb_service: TroubleshootingService,
):
    """Vague queries trigger targeted domain clarification questions."""
    res = tb_service.troubleshoot(vague_query)
    assert res.status == "clarification_required"
    assert res.clarification is not None
    assert res.clarification.id == expected_catalog_id
    assert res.clarification.domain == expected_domain
    assert len(res.clarification.options) >= 2
    assert res.session_id is not None
    assert len(res.contexts) == 0
    assert res.timeline is not None
    assert len(res.timeline) == 2
    assert res.timeline[0].step == "query_received"
    assert res.timeline[1].step == "clarification_requested"


# =========================================================================
# 3. Multi-Turn Session & Diagnostic Refinement Tests
# =========================================================================

def test_multiturn_clarification_refinement_flow(tb_service: TroubleshootingService):
    """Full multi-turn flow: vague query -> clarification -> answer -> refined diagnosis."""
    # Step 1: Initial vague complaint
    init_res = tb_service.troubleshoot("my phone gets hot")
    assert init_res.status == "clarification_required"
    assert init_res.session_id is not None
    assert init_res.clarification is not None

    session_id = init_res.session_id
    selected_option_id = "opt_heat_charging"

    # Step 2: User provides clarification answer
    cont_req = ContinueTroubleshootRequest(
        session_id=session_id,
        clarification_id=init_res.clarification.id,
        answer_id=selected_option_id,
    )
    refined_res = tb_service.continue_troubleshoot(cont_req)

    assert refined_res.status == "diagnosis_ready"
    assert len(refined_res.contexts) > 0
    assert refined_res.contexts[0].goal == "Charging is slower than expected"
    assert refined_res.session_id == session_id

    # Step 3: Check complete 4-step diagnostic timeline
    assert refined_res.timeline is not None
    assert len(refined_res.timeline) == 4
    assert refined_res.timeline[0].step == "query_received"
    assert refined_res.timeline[1].step == "clarification_requested"
    assert refined_res.timeline[2].step == "clarification_answered"
    assert refined_res.timeline[3].step == "diagnosis_ready"


def test_multiturn_clarification_with_custom_text(tb_service: TroubleshootingService):
    """User provides custom text follow-up instead of option ID."""
    init_res = tb_service.troubleshoot("camera not working")
    assert init_res.status == "clarification_required"
    session_id = init_res.session_id

    cont_req = ContinueTroubleshootRequest(
        session_id=session_id,
        user_response_text="the camera app freezes when I record video",
    )
    refined_res = tb_service.continue_troubleshoot(cont_req)
    assert refined_res.status == "diagnosis_ready"
    assert len(refined_res.contexts) > 0
    assert "freeze" in refined_res.contexts[0].goal.lower()


def test_invalid_or_expired_session_handling(tb_service: TroubleshootingService):
    """Continuing with a non-existent session ID returns a clean error status."""
    cont_req = ContinueTroubleshootRequest(
        session_id="non-existent-session-uuid-12345",
        answer_id="opt_heat_charging",
    )
    res = tb_service.continue_troubleshoot(cont_req)
    assert res.status == "error"
    assert res.fallback is not None
    assert "session" in res.fallback.lower()
    assert len(res.contexts) == 0


def test_session_isolation(tb_service: TroubleshootingService):
    """Separate queries create isolated sessions with independent states."""
    res1 = tb_service.troubleshoot("phone gets hot")
    res2 = tb_service.troubleshoot("screen acting weird")

    assert res1.session_id != res2.session_id
    assert res1.clarification.domain == "battery"
    assert res2.clarification.domain == "display"

    # Refine session 1
    cont1 = tb_service.continue_troubleshoot(
        ContinueTroubleshootRequest(
            session_id=res1.session_id, answer_id="opt_heat_normal"
        )
    )
    assert cont1.contexts[0].goal == "Device gets hot during normal use"

    # Session 2 remains in clarification required state
    session2 = tb_service.clarification_service.get_session(res2.session_id)
    assert session2.status == "clarification_required"


# =========================================================================
# 4. FastAPI End-to-End Endpoint Integration Tests
# =========================================================================

def test_api_endpoint_multiturn_flow(client: TestClient):
    """POST /troubleshoot followed by POST /troubleshoot/continue via HTTP."""
    # 1. Initial request
    resp = client.post("/troubleshoot", json={"query": "my phone is slow"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "clarification_required"
    assert "session_id" in data
    assert data["clarification"]["id"] == "clarify_performance_issue"

    session_id = data["session_id"]

    # 2. Continue request
    cont_resp = client.post(
        "/troubleshoot/continue",
        json={
            "session_id": session_id,
            "clarification_id": "clarify_performance_issue",
            "answer_id": "opt_perf_multitask",
        },
    )
    assert cont_resp.status_code == 200
    cont_data = cont_resp.json()
    assert cont_data["status"] == "diagnosis_ready"
    assert len(cont_data["contexts"]) > 0
    assert len(cont_data["timeline"]) == 4
    assert cont_data["contexts"][0]["goal"] == "Device has insufficient free memory"
    assert cont_data["contexts"][0]["actions"][0]["deeplink"].startswith("prototype://")


def test_api_endpoint_out_of_scope_session(client: TestClient):
    """Out-of-scope query returns status='out_of_scope' and no clarification."""
    resp = client.post("/troubleshoot", json={"query": "Will it rain tomorrow in Paris?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "out_of_scope"
    assert len(data["contexts"]) == 0
    assert data["clarification"] is None
