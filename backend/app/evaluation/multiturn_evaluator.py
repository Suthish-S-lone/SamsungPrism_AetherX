"""
Multi-turn Evaluation Framework for SmartGuide (Phase 7).

Evaluates the complete multi-turn conversational troubleshooting pipeline across
all 14 evaluation metrics against data/development/multiturn_test_queries.json.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from backend.app.config import settings
from backend.app.models.request import ContinueTroubleshootRequest
from backend.app.services.troubleshooting_service import TroubleshootingService


@dataclass
class ScenarioResult:
    scenario_id: str
    category: str
    category_name: str
    initial_query: str
    initial_status: str
    final_status: str
    expected_final_status: str
    final_problem_id: Optional[str]
    expected_final_problem_id: Optional[str]
    is_top1_match: bool
    is_top3_match: bool
    is_unsupported_rejected: bool
    is_false_positive: bool
    turn_count: int
    clarification_triggered: bool
    clarification_ids_asked: List[str]
    has_loop: bool
    latencies_ms: List[float] = field(default_factory=list)
    notes: str = ""


@dataclass
class MultiTurnEvaluationReport:
    total_scenarios: int
    supported_scenarios_count: int
    unsupported_scenarios_count: int
    top1_accuracy_pct: float
    top3_accuracy_pct: float
    unsupported_rejection_rate_pct: float
    false_positive_rate_pct: float
    mean_diagnostic_turns: float
    clarification_trigger_precision_pct: float
    clarification_trigger_recall_pct: float
    turn_limit_enforcement_rate_pct: float
    contradictory_resolution_rate_pct: float
    irrelevant_handling_rate_pct: float
    context_contamination_rate_pct: float
    mean_latency_ms: float
    max_latency_ms: float
    diagnostic_loop_rate_pct: float
    session_isolation_rate_pct: float
    category_breakdown: Dict[str, Dict[str, Any]]
    results: List[ScenarioResult]


class MultiTurnEvaluator:
    """Evaluates multi-turn conversational troubleshooting scenarios."""

    def __init__(self, service: Optional[TroubleshootingService] = None, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.service = service or TroubleshootingService(data_dir=self.data_dir)

    def load_scenarios(self, test_file: Optional[Path] = None) -> List[Dict[str, Any]]:
        target = test_file or (self.data_dir / "multiturn_test_queries.json")
        if not target.exists():
            raise FileNotFoundError(f"Multi-turn test file not found: {target}")
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate_scenario(self, scenario: Dict[str, Any]) -> ScenarioResult:
        sid = scenario["id"]
        cat = scenario.get("category", "")
        cat_name = scenario.get("category_name", "")
        init_q = scenario["initial_query"]
        exp_init_status = scenario.get("expected_initial_status")
        exp_final_status = scenario.get("expected_final_status")
        exp_final_pid = scenario.get("expected_final_problem_id")
        sim_ans_id = scenario.get("simulated_answer_id")
        sim_user_text = scenario.get("simulated_user_text")

        latencies: List[float] = []
        clarification_ids: List[str] = []

        # Turn 1: Initial query
        t0 = time.perf_counter()
        resp1 = self.service.troubleshoot(query=init_q, debug=True)
        t_turn1 = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_turn1)

        init_status = resp1.status
        turn_count = 1
        current_resp = resp1

        if resp1.clarification:
            clarification_ids.append(resp1.clarification.id)

        # Multi-turn continuation if clarification required and answer/text is provided
        if resp1.status == "clarification_required" and resp1.session_id and (sim_ans_id or sim_user_text):
            t_ans0 = time.perf_counter()
            req = ContinueTroubleshootRequest(
                session_id=resp1.session_id,
                clarification_id=resp1.clarification.id if resp1.clarification else None,
                answer_id=sim_ans_id,
                user_response_text=sim_user_text,
            )
            current_resp = self.service.continue_troubleshoot(request=req, debug=True)
            t_ans = (time.perf_counter() - t_ans0) * 1000.0
            latencies.append(t_ans)
            turn_count += 1
            if current_resp.clarification:
                clarification_ids.append(current_resp.clarification.id)

        final_status = current_resp.status
        final_pid = current_resp.final_problem_id
        if not final_pid and current_resp.contexts:
            final_pid = getattr(current_resp.contexts[0], "id", None) or getattr(current_resp.contexts[0], "problem_id", None)

        # Check candidate top-3
        top3_pids: List[str] = []
        if current_resp.debug_info and current_resp.debug_info.retrieval:
            top3_pids = [c.problem_id for c in current_resp.debug_info.retrieval.top_candidates[:3]]
        if final_pid and final_pid not in top3_pids:
            top3_pids.insert(0, final_pid)

        # Metrics evaluation
        is_supported = exp_final_status == "diagnosis_ready"
        is_top1 = False
        is_top3 = False
        is_unsupported_rejected = False
        is_false_pos = False

        if is_supported:
            if exp_final_pid:
                is_top1 = (final_pid == exp_final_pid)
                is_top3 = is_top1 or (exp_final_pid in top3_pids)
            else:
                is_top1 = (final_status == "diagnosis_ready")
                is_top3 = is_top1
        else:
            # Expected unsupported or insufficient_information
            if final_status in ["unsupported", "out_of_scope", "insufficient_information"]:
                is_unsupported_rejected = True
                is_false_pos = False
            else:
                is_unsupported_rejected = False
                is_false_pos = True

        # Diagnostic loop detection: duplicate identical clarification question ID
        has_loop = len(clarification_ids) != len(set(clarification_ids))

        return ScenarioResult(
            scenario_id=sid,
            category=cat,
            category_name=cat_name,
            initial_query=init_q,
            initial_status=init_status,
            final_status=final_status,
            expected_final_status=exp_final_status or "",
            final_problem_id=final_pid,
            expected_final_problem_id=exp_final_pid,
            is_top1_match=is_top1,
            is_top3_match=is_top3,
            is_unsupported_rejected=is_unsupported_rejected,
            is_false_positive=is_false_pos,
            turn_count=turn_count,
            clarification_triggered=len(clarification_ids) > 0,
            clarification_ids_asked=clarification_ids,
            has_loop=has_loop,
            latencies_ms=latencies,
        )

    def evaluate_all(self, test_file: Optional[Path] = None) -> MultiTurnEvaluationReport:
        scenarios = self.load_scenarios(test_file)
        results: List[ScenarioResult] = []

        all_latencies: List[float] = []
        supported_results: List[ScenarioResult] = []
        unsupported_results: List[ScenarioResult] = []

        # Track ambiguity classification for precision / recall
        ambiguous_scenarios_count = 0
        clarification_correctly_triggered = 0
        unambiguous_scenarios_count = 0
        clarification_false_triggers = 0

        # Turn limit enforcement
        exhaustion_scenarios: List[ScenarioResult] = []
        contradictory_scenarios: List[ScenarioResult] = []
        irrelevant_scenarios: List[ScenarioResult] = []

        for s in scenarios:
            res = self.evaluate_scenario(s)
            results.append(res)
            all_latencies.extend(res.latencies_ms)

            cat = res.category
            is_ambiguous = cat in ["B", "C", "D", "E", "F", "G", "H", "I"] or s.get("expected_initial_status") == "clarification_required"
            
            if is_ambiguous:
                ambiguous_scenarios_count += 1
                if res.clarification_triggered:
                    clarification_correctly_triggered += 1
            else:
                unambiguous_scenarios_count += 1
                if res.clarification_triggered:
                    clarification_false_triggers += 1

            if cat == "M":
                contradictory_scenarios.append(res)
            elif cat == "N":
                irrelevant_scenarios.append(res)

            if s.get("expected_final_status") == "diagnosis_ready":
                supported_results.append(res)
            elif s.get("expected_final_status") in ["unsupported", "out_of_scope", "insufficient_information"]:
                unsupported_results.append(res)

        # Context contamination & session isolation test
        # Run interleaved concurrent sessions and test for data leakage
        isolation_success = self._verify_session_isolation()

        # Aggregate calculations
        n_supp = len(supported_results)
        n_unsupp = len(unsupported_results)
        n_total = len(results)

        top1_acc = (sum(1 for r in supported_results if r.is_top1_match) / n_supp * 100.0) if n_supp > 0 else 0.0
        top3_acc = (sum(1 for r in supported_results if r.is_top3_match) / n_supp * 100.0) if n_supp > 0 else 0.0
        unsupp_rej = (sum(1 for r in unsupported_results if r.is_unsupported_rejected) / n_unsupp * 100.0) if n_unsupp > 0 else 0.0
        false_pos = (sum(1 for r in unsupported_results if r.is_false_positive) / n_unsupp * 100.0) if n_unsupp > 0 else 0.0

        mean_turns = (sum(r.turn_count for r in supported_results) / n_supp) if n_supp > 0 else 0.0

        total_clarification_triggers = clarification_correctly_triggered + clarification_false_triggers
        clarif_prec = (clarification_correctly_triggered / total_clarification_triggers * 100.0) if total_clarification_triggers > 0 else 100.0
        clarif_rec = (clarification_correctly_triggered / ambiguous_scenarios_count * 100.0) if ambiguous_scenarios_count > 0 else 100.0

        turn_limit_enforced = 100.0 if self._verify_turn_limit_exhaustion() else 0.0

        contra_rate = (sum(1 for r in contradictory_scenarios if r.final_status == "diagnosis_ready" and r.is_top1_match) / len(contradictory_scenarios) * 100.0) if contradictory_scenarios else 100.0
        irrel_rate = (sum(1 for r in irrelevant_scenarios if r.final_status in ["insufficient_information", "unsupported"]) / len(irrelevant_scenarios) * 100.0) if irrelevant_scenarios else 100.0

        loop_count = sum(1 for r in results if r.has_loop)
        loop_rate = (loop_count / n_total * 100.0) if n_total > 0 else 0.0

        mean_lat = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0
        max_lat = max(all_latencies) if all_latencies else 0.0

        # Category breakdown
        cat_breakdown: Dict[str, Dict[str, Any]] = {}
        for r in results:
            if r.category not in cat_breakdown:
                cat_breakdown[r.category] = {
                    "name": r.category_name,
                    "total": 0,
                    "top1_matches": 0,
                    "top3_matches": 0,
                    "unsupported_rejected": 0,
                    "turns": [],
                    "latencies": [],
                }
            cb = cat_breakdown[r.category]
            cb["total"] += 1
            if r.is_top1_match:
                cb["top1_matches"] += 1
            if r.is_top3_match:
                cb["top3_matches"] += 1
            if r.is_unsupported_rejected:
                cb["unsupported_rejected"] += 1
            cb["turns"].append(r.turn_count)
            cb["latencies"].extend(r.latencies_ms)

        for cat_k, cb in cat_breakdown.items():
            tot = cb["total"]
            cb["mean_turns"] = round(sum(cb["turns"]) / len(cb["turns"]), 2) if cb["turns"] else 0.0
            cb["mean_latency_ms"] = round(sum(cb["latencies"]) / len(cb["latencies"]), 2) if cb["latencies"] else 0.0
            cb["success_rate_pct"] = round((cb["top1_matches"] + cb["unsupported_rejected"]) / tot * 100.0, 1) if tot > 0 else 0.0

        return MultiTurnEvaluationReport(
            total_scenarios=n_total,
            supported_scenarios_count=n_supp,
            unsupported_scenarios_count=n_unsupp,
            top1_accuracy_pct=round(top1_acc, 2),
            top3_accuracy_pct=round(top3_acc, 2),
            unsupported_rejection_rate_pct=round(unsupp_rej, 2),
            false_positive_rate_pct=round(false_pos, 2),
            mean_diagnostic_turns=round(mean_turns, 2),
            clarification_trigger_precision_pct=round(clarif_prec, 2),
            clarification_trigger_recall_pct=round(clarif_rec, 2),
            turn_limit_enforcement_rate_pct=round(turn_limit_enforced, 2),
            contradictory_resolution_rate_pct=round(contra_rate, 2),
            irrelevant_handling_rate_pct=round(irrel_rate, 2),
            context_contamination_rate_pct=0.0 if isolation_success else 100.0,
            mean_latency_ms=round(mean_lat, 2),
            max_latency_ms=round(max_lat, 2),
            diagnostic_loop_rate_pct=round(loop_rate, 2),
            session_isolation_rate_pct=100.0 if isolation_success else 0.0,
            category_breakdown=cat_breakdown,
            results=results,
        )

    def _verify_session_isolation(self) -> bool:
        """Verify that multiple simultaneous or interleaved sessions do not contaminate each other."""
        try:
            # Start session A (battery)
            res_a1 = self.service.troubleshoot(query="phone battery dies very fast", debug=False)
            session_a = res_a1.session_id

            # Start session B (camera)
            res_b1 = self.service.troubleshoot(query="camera app takes blurry photos", debug=False)
            session_b = res_b1.session_id

            # Validate that sessions are distinct
            if session_a and session_b and session_a == session_b:
                return False

            # Inspect session retrieval states
            if session_a:
                sess_obj_a = self.service.clarification_service.get_session(session_a)
                if sess_obj_a and sess_obj_a.domain != "battery":
                    return False

            if session_b:
                sess_obj_b = self.service.clarification_service.get_session(session_b)
                if sess_obj_b and sess_obj_b.domain != "camera":
                    return False

            return True
        except Exception:
            return False

    def _verify_turn_limit_exhaustion(self) -> bool:
        """Verify that a session that continues without resolving terminates at MAX_DIAGNOSTIC_TURNS with insufficient_information."""
        try:
            # Turn 1: initial ambiguous query
            resp = self.service.troubleshoot(query="phone problem", debug=False)
            if resp.status != "clarification_required" or not resp.session_id:
                # Try another ambiguous trigger
                resp = self.service.troubleshoot(query="phone gets hot", debug=False)
                if resp.status != "clarification_required" or not resp.session_id:
                    return False

            # Submit 3 vague turns
            curr = resp
            for _ in range(4):
                if curr.status in ["insufficient_information", "unsupported", "error"]:
                    break
                req = ContinueTroubleshootRequest(
                    session_id=curr.session_id,
                    user_response_text="still having vague problem without details",
                )
                curr = self.service.continue_troubleshoot(request=req, debug=False)

            return curr.status == "insufficient_information" and curr.turn_count <= (settings.MAX_DIAGNOSTIC_TURNS + 1)
        except Exception:
            return False
