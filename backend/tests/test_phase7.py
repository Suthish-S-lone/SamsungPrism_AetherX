"""
Phase 7 Multi-Turn Hardening, Safety & Diagnostic Intelligence Unit Tests.
"""

import pytest
from backend.app.config import settings
from backend.app.models.request import ContinueTroubleshootRequest, TroubleshootRequest
from backend.app.services.troubleshooting_service import TroubleshootingService
from backend.app.services.clarification_service import ClarificationService
from backend.app.evaluation.multiturn_evaluator import MultiTurnEvaluator


@pytest.fixture(scope="module")
def tb_service():
    return TroubleshootingService()


@pytest.fixture
def clarif_service():
    return ClarificationService()


def test_max_diagnostic_turns_config():
    """Verify MAX_DIAGNOSTIC_TURNS is set to 3 by default in configuration."""
    assert settings.MAX_DIAGNOSTIC_TURNS == 3


def test_explicit_diagnostic_states(tb_service):
    """Verify all explicit Phase 7 diagnostic states are properly generated."""
    # 1. diagnosis_ready on clear query
    res_ready = tb_service.troubleshoot("battery drain rapidly after latest software update")
    assert res_ready.status == "diagnosis_ready"
    assert res_ready.final_problem_id == "battery_008"
    assert res_ready.turn_count == 1
    assert len(res_ready.contexts) > 0

    # 2. clarification_required on ambiguous query
    res_clarif = tb_service.troubleshoot("phone gets hot")
    assert res_clarif.status == "clarification_required"
    assert res_clarif.clarification is not None
    assert res_clarif.session_id is not None
    assert len(res_clarif.contexts) == 0

    # 3. unsupported on out-of-scope query
    res_unsupp = tb_service.troubleshoot("Will it rain tomorrow in Paris?")
    assert res_unsupp.status in ["unsupported", "out_of_scope"]
    assert len(res_unsupp.contexts) == 0
    assert res_unsupp.fallback is not None

    # 4. error on non-existent session
    res_err = tb_service.continue_troubleshoot(
        ContinueTroubleshootRequest(session_id="non-existent-uuid-12345", answer_id="opt_heat_charging")
    )
    assert res_err.status == "error"


def test_turn_limit_exhaustion_behavior(tb_service):
    """Verify session transitions to insufficient_information after MAX_DIAGNOSTIC_TURNS."""
    # Initial ambiguous turn (Turn 1)
    res1 = tb_service.troubleshoot("phone temperature high")
    assert res1.status == "clarification_required"
    sid = res1.session_id

    # Follow-up Turn 2: still vague
    res2 = tb_service.continue_troubleshoot(
        ContinueTroubleshootRequest(
            session_id=sid,
            user_response_text="it is somewhat warm but not sure when",
        )
    )
    # Follow-up Turn 3: still vague
    res3 = tb_service.continue_troubleshoot(
        ContinueTroubleshootRequest(
            session_id=sid,
            user_response_text="still having issues throughout the day",
        )
    )
    # Follow-up Turn 4 (Exhaustion past turn limit 3)
    res4 = tb_service.continue_troubleshoot(
        ContinueTroubleshootRequest(
            session_id=sid,
            user_response_text="not sure what else to say",
        )
    )
    assert res4.status == "insufficient_information"
    assert res4.turn_count >= 3
    assert len(res4.contexts) == 0
    assert "information" in res4.fallback.lower()


def test_irrelevant_answer_handling(tb_service):
    """Verify irrelevant text responses immediately return insufficient_information fallback."""
    res1 = tb_service.troubleshoot("camera not working")
    assert res1.status == "clarification_required"
    sid = res1.session_id

    res2 = tb_service.continue_troubleshoot(
        ContinueTroubleshootRequest(
            session_id=sid,
            user_response_text="I like eating chocolate ice cream on weekends",
        )
    )
    assert res2.status == "insufficient_information"
    assert len(res2.contexts) == 0


def test_contradictory_answer_handling(tb_service):
    """Verify contradictory answers override the initial premise and re-diagnose correctly."""
    # User starts complaining about screen
    res1 = tb_service.troubleshoot("screen acting weird")
    assert res1.status == "clarification_required"
    sid = res1.session_id

    # Follow-up corrects: actually screen is fine, camera photos are blurry
    res2 = tb_service.continue_troubleshoot(
        ContinueTroubleshootRequest(
            session_id=sid,
            user_response_text="actually the screen is fine but my camera photos are blurry and out of focus",
        )
    )
    assert res2.status == "diagnosis_ready"
    assert res2.final_problem_id == "camera_019"
    assert len(res2.contexts) > 0


def test_session_isolation_and_no_contamination(tb_service):
    """Verify concurrent and sequential sessions maintain strictly isolated states."""
    # Session A: Battery
    res_a1 = tb_service.troubleshoot("phone battery dies very fast")
    sid_a = res_a1.session_id

    # Session B: Display
    res_b1 = tb_service.troubleshoot("screen brightness changes unexpectedly")
    sid_b = res_b1.session_id

    assert sid_a != sid_b

    sess_a = tb_service.clarification_service.get_session(sid_a)
    sess_b = tb_service.clarification_service.get_session(sid_b)

    assert sess_a.domain == "battery"
    assert sess_b.domain == "display"


def test_session_reset_functionality(tb_service):
    """Verify session reset returns state to initial turn and clears history."""
    res1 = tb_service.troubleshoot("phone gets hot")
    sid = res1.session_id

    # Answer one turn
    res2 = tb_service.continue_troubleshoot(
        ContinueTroubleshootRequest(
            session_id=sid,
            answer_id="opt_heat_charging",
        )
    )
    assert res2.status == "diagnosis_ready"

    # Reset session
    reset_sess = tb_service.clarification_service.reset_session(sid)
    assert reset_sess is not None
    assert reset_sess.turn_count == 1
    assert reset_sess.clarification_history == []
    assert reset_sess.selected_problem_id is None


def test_no_diagnostic_loops(tb_service):
    """Verify system does not present the same clarification question twice in a session."""
    res1 = tb_service.troubleshoot("phone gets hot")
    assert res1.status == "clarification_required"
    q1_id = res1.clarification.id
    sid = res1.session_id

    res2 = tb_service.continue_troubleshoot(
        ContinueTroubleshootRequest(
            session_id=sid,
            answer_id="opt_heat_charging",
        )
    )
    # Should resolve to diagnosis_ready, not loop back to the same heat question
    assert res2.status == "diagnosis_ready"
    assert res2.clarification is None


def test_multiturn_evaluator_execution():
    """Verify MultiTurnEvaluator executes end-to-end and returns complete report."""
    evaluator = MultiTurnEvaluator()
    report = evaluator.evaluate_all()

    assert report.total_scenarios == 72
    assert report.supported_scenarios_count == 62
    assert report.unsupported_scenarios_count == 10
    assert report.top1_accuracy_pct >= 80.0
    assert report.top3_accuracy_pct >= 90.0
    assert report.unsupported_rejection_rate_pct == 100.0
    assert report.false_positive_rate_pct == 0.0
    assert report.mean_diagnostic_turns <= 2.0
    assert report.turn_limit_enforcement_rate_pct == 100.0
    assert report.context_contamination_rate_pct == 0.0
    assert report.mean_latency_ms < 100.0
    assert report.diagnostic_loop_rate_pct == 0.0
    assert report.session_isolation_rate_pct == 100.0
