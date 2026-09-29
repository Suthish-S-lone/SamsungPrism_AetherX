"""Structured Troubleshooting Orchestration Service for SmartGuide.

Integrates Query Understanding, Pretrained Neural Hybrid Retrieval,
Prototype Deeplink Resolution, and Diagnostic Transparency.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.models.conversation import TimelineEvent
from backend.app.models.request import ContinueTroubleshootRequest
from backend.app.models.response import Action, Context, Step, TroubleshootResponse
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.retrieval.types import RetrievalResult
from backend.app.services.clarification_service import ClarificationService
from backend.app.services.query_understanding import (
    QueryUnderstandingResult,
    QueryUnderstandingService,
)


class CandidateDebugInfo(BaseModel):
    """Detailed scoring metadata for an individual retrieval candidate."""

    problem_id: str
    problem: str
    domain: str
    fused_score: float
    bm25_rank: Optional[int] = None
    semantic_rank: Optional[int] = None


class RetrievalDebugInfo(BaseModel):
    """Diagnostic transparency metadata for the retrieval phase."""

    queries_executed: List[str]
    similarity_threshold: float
    total_candidates_found: int
    top_candidates: List[CandidateDebugInfo]
    decision: str
    confidence_level: str


class LatencyBreakdown(BaseModel):
    """Execution latency breakdown across pipeline stages in milliseconds."""

    query_understanding_ms: float
    retrieval_ms: float
    response_synthesis_ms: float
    total_pipeline_ms: float


class DiagnosticDebugMetadata(BaseModel):
    """Complete diagnostic transparency payload for debugging and explainability."""

    query_understanding: QueryUnderstandingResult
    retrieval: RetrievalDebugInfo
    latency: LatencyBreakdown


class StructuredTroubleshootResponse(TroubleshootResponse):
    """Extended troubleshooting response with optional diagnostic transparency payload."""

    debug_info: Optional[DiagnosticDebugMetadata] = Field(
        default=None, description="Diagnostic debug and transparency metadata when debug=True"
    )


class TroubleshootingService:
    """Core domain orchestration service for SmartGuide troubleshooting."""

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        query_understanding: Optional[QueryUnderstandingService] = None,
        clarification_service: Optional[ClarificationService] = None,
        data_dir: Optional[Path] = None,
    ):
        self.data_dir = data_dir or settings.DATA_DIR
        self.retriever = retriever or HybridRetriever(data_dir=self.data_dir)
        self.qu_service = query_understanding or QueryUnderstandingService()
        self.clarification_service = clarification_service or ClarificationService()

        # Load knowledge base records & deeplinks
        self.troubleshooting_records: Dict[str, dict] = self._load_troubleshooting_records()
        self.deeplink_map: Dict[str, str] = self._load_deeplinks()

    def _load_troubleshooting_records(self) -> Dict[str, dict]:
        """Load raw troubleshooting JSON records indexed by problem_id."""
        tb_path = self.data_dir / "troubleshooting.json"
        if not tb_path.exists():
            return {}
        with open(tb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["id"]: item for item in data}

    def _load_deeplinks(self) -> Dict[str, str]:
        """Load prototype deeplinks indexed by target_screen."""
        dl_path = self.data_dir / "deeplinks.json"
        if not dl_path.exists():
            return {}
        with open(dl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["target_screen"]: item["uri"] for item in data}

    def _build_context_for_problem(self, problem_id: str, score: float) -> Optional[Context]:
        """Construct Context model for a matched problem_id."""
        raw_record = self.troubleshooting_records.get(problem_id)
        if not raw_record:
            return None
        actions: List[Action] = []
        for act in raw_record.get("actions", []):
            ts = act.get("target_screen", "")
            deeplink_uri = self.deeplink_map.get(ts)
            steps_objs = [Step(text=s) for s in act.get("steps", [])]
            actions.append(
                Action(
                    action_name=act.get("name", "Review settings"),
                    description=act.get("description", ""),
                    category=act.get("category", "manual"),
                    steps=steps_objs,
                    target_screen=ts,
                    deeplink=deeplink_uri,
                )
            )
        return Context(
            goal=raw_record.get("problem", ""),
            title=raw_record.get("problem", ""),
            score=round(score, 4),
            actions=actions,
        )

    def troubleshoot(
        self,
        query: str,
        threshold: Optional[float] = None,
        debug: bool = False,
        session_id: Optional[str] = None,
    ) -> StructuredTroubleshootResponse:
        """Execute the complete end-to-end troubleshooting pipeline."""
        t_start = time.perf_counter()
        sim_thresh = threshold if threshold is not None else 0.40

        # ---------------------------------------------------------
        # 1. Query Understanding & Canonicalization
        # ---------------------------------------------------------
        t_qu_start = time.perf_counter()
        qu_result = self.qu_service.analyze(query)
        t_qu_end = time.perf_counter()
        qu_latency_ms = (t_qu_end - t_qu_start) * 1000.0

        # Handle out of scope / empty queries immediately
        if qu_result.is_out_of_scope:
            t_total_ms = (time.perf_counter() - t_start) * 1000.0
            debug_meta = None
            if debug:
                debug_meta = DiagnosticDebugMetadata(
                    query_understanding=qu_result,
                    retrieval=RetrievalDebugInfo(
                        queries_executed=[],
                        similarity_threshold=sim_thresh,
                        total_candidates_found=0,
                        top_candidates=[],
                        decision="OUT_OF_SCOPE",
                        confidence_level="UNSUPPORTED",
                    ),
                    latency=LatencyBreakdown(
                        query_understanding_ms=round(qu_latency_ms, 2),
                        retrieval_ms=0.0,
                        response_synthesis_ms=0.0,
                        total_pipeline_ms=round(t_total_ms, 2),
                    ),
                )
            return StructuredTroubleshootResponse(
                status="out_of_scope",
                domain=None,
                canonical_symptom=None,
                extracted_signals=["out_of_scope_topic"],
                confidence=0.0,
                contexts=[],
                fallback=(
                    "This assistant is designed specifically for Samsung device troubleshooting "
                    "(battery, display, camera, and performance). Your query appears outside this domain."
                ),
                debug_info=debug_meta,
            )

        # ---------------------------------------------------------
        # 2. Multi-Representation Hybrid Retrieval
        # ---------------------------------------------------------
        t_ret_start = time.perf_counter()
        queries_to_run = [query]
        if qu_result.canonical_symptom and qu_result.canonical_symptom != query:
            queries_to_run.append(qu_result.canonical_symptom)

        # Execute retrieval across query representations
        candidate_map: Dict[str, RetrievalResult] = {}
        for q_text in queries_to_run:
            results = self.retriever.retrieve(q_text, top_k=5, threshold=0.0)
            for r in results:
                if r.problem_id not in candidate_map:
                    candidate_map[r.problem_id] = r
                else:
                    existing = candidate_map[r.problem_id]
                    if r.score > existing.score:
                        candidate_map[r.problem_id] = r

        # If grounded taxonomy match was identified, boost targeted candidate
        if qu_result.target_problem_id and qu_result.target_problem_id in self.retriever.doc_map:
            tid = qu_result.target_problem_id
            if tid in candidate_map:
                candidate_map[tid].score = max(candidate_map[tid].score, qu_result.confidence)
            else:
                doc = self.retriever.doc_map[tid]
                candidate_map[tid] = RetrievalResult(
                    problem_id=tid,
                    domain=doc.domain,
                    problem=doc.problem,
                    score=qu_result.confidence,
                    fused_score=qu_result.confidence,
                    bm25_rank=None,
                    semantic_rank=1,
                    status="MATCH",
                )

        sorted_candidates = sorted(
            candidate_map.values(), key=lambda x: x.score, reverse=True
        )

        t_ret_end = time.perf_counter()
        ret_latency_ms = (t_ret_end - t_ret_start) * 1000.0

        # ---------------------------------------------------------
        # 3. Decision Gating & Multi-Turn Clarification Check
        # ---------------------------------------------------------
        t_syn_start = time.perf_counter()

        top_candidate = sorted_candidates[0] if sorted_candidates else None
        is_match = top_candidate is not None and top_candidate.score >= sim_thresh

        decision = "MATCH" if is_match else "NO_MATCH"
        confidence_level = "LOW_CONFIDENCE"
        if is_match and top_candidate:
            confidence_level = "HIGH" if top_candidate.score >= 0.70 else "MEDIUM"

        # Check for ambiguity in query
        clarification_q = self.clarification_service.detect_ambiguity(
            query=query, qu_result=qu_result, top_candidates=sorted_candidates
        )

        if clarification_q:
            # Create interactive conversation session
            session = self.clarification_service.create_session(
                query=query,
                qu_result=qu_result,
                status="clarification_required",
                clarification_question=clarification_q,
                confidence=top_candidate.score if top_candidate else 0.0,
                max_turns=settings.MAX_DIAGNOSTIC_TURNS,
            )
            now_ts = time.time()
            timeline = [
                TimelineEvent(
                    step="query_received",
                    label="Complaint Received",
                    status="completed",
                    detail=f'User submitted: "{query}"',
                    timestamp=now_ts,
                ),
                TimelineEvent(
                    step="clarification_requested",
                    label="Clarification Requested",
                    status="active",
                    detail=clarification_q.question,
                    timestamp=now_ts,
                ),
            ]
            t_syn_end = time.perf_counter()
            syn_latency_ms = (t_syn_end - t_syn_start) * 1000.0
            t_total_ms = (time.perf_counter() - t_start) * 1000.0

            debug_meta = None
            if debug:
                top_debug_candidates = [
                    CandidateDebugInfo(
                        problem_id=c.problem_id,
                        problem=c.problem,
                        domain=c.domain,
                        fused_score=round(c.fused_score, 4),
                        bm25_rank=c.bm25_rank,
                        semantic_rank=c.semantic_rank,
                    )
                    for c in sorted_candidates[:5]
                ]
                debug_meta = DiagnosticDebugMetadata(
                    query_understanding=qu_result,
                    retrieval=RetrievalDebugInfo(
                        queries_executed=queries_to_run,
                        similarity_threshold=sim_thresh,
                        total_candidates_found=len(sorted_candidates),
                        top_candidates=top_debug_candidates,
                        decision="CLARIFICATION_REQUIRED",
                        confidence_level="MEDIUM",
                    ),
                    latency=LatencyBreakdown(
                        query_understanding_ms=round(qu_latency_ms, 2),
                        retrieval_ms=round(ret_latency_ms, 2),
                        response_synthesis_ms=round(syn_latency_ms, 2),
                        total_pipeline_ms=round(t_total_ms, 2),
                    ),
                )

            return StructuredTroubleshootResponse(
                status="clarification_required",
                session_id=session.session_id,
                turn_count=session.turn_count,
                max_turns=session.max_turns,
                clarification=clarification_q,
                clarification_history=session.clarification_history,
                domain=qu_result.domain,
                canonical_symptom=qu_result.canonical_symptom,
                extracted_signals=qu_result.extracted_signals,
                confidence=round(top_candidate.score, 4) if top_candidate else 0.0,
                timeline=timeline,
                contexts=[],
                fallback="Please select the option that best describes your situation to receive targeted troubleshooting steps.",
                debug_info=debug_meta,
            )

        contexts: List[Context] = []
        fallback_msg: Optional[str] = None
        status_str = "diagnosis_ready" if is_match else "out_of_scope"
        timeline: Optional[List[TimelineEvent]] = None
        session_id_out: Optional[str] = None
        final_pid: Optional[str] = None
        domain_out: Optional[str] = qu_result.domain
        conf_out: float = 0.0

        if is_match and top_candidate:
            ctx = self._build_context_for_problem(top_candidate.problem_id, top_candidate.score)
            if ctx:
                contexts.append(ctx)

            session = self.clarification_service.create_session(
                query=query,
                qu_result=qu_result,
                status="diagnosis_ready",
                selected_problem_id=top_candidate.problem_id,
                confidence=top_candidate.score,
                max_turns=settings.MAX_DIAGNOSTIC_TURNS,
            )
            session_id_out = session.session_id
            final_pid = top_candidate.problem_id
            domain_out = top_candidate.domain
            conf_out = round(top_candidate.score, 4)
            now_ts = time.time()
            timeline = [
                TimelineEvent(
                    step="query_received",
                    label="Complaint Received",
                    status="completed",
                    detail=f'User submitted: "{query}"',
                    timestamp=now_ts,
                ),
                TimelineEvent(
                    step="diagnosis_ready",
                    label="Diagnosis Ready",
                    status="completed",
                    detail=f"Identified matching issue: {top_candidate.problem} ({top_candidate.problem_id}) with {top_candidate.score*100:.0f}% confidence",
                    timestamp=now_ts,
                ),
            ]
        else:
            fallback_msg = (
                "No matching troubleshooting steps found for your query. "
                "Please check the description or try describing the symptoms differently."
            )

        t_syn_end = time.perf_counter()
        syn_latency_ms = (t_syn_end - t_syn_start) * 1000.0
        t_total_ms = (time.perf_counter() - t_start) * 1000.0

        # ---------------------------------------------------------
        # 4. Diagnostic Transparency Metadata Assembly
        # ---------------------------------------------------------
        debug_meta = None
        if debug:
            top_debug_candidates = [
                CandidateDebugInfo(
                    problem_id=c.problem_id,
                    problem=c.problem,
                    domain=c.domain,
                    fused_score=round(c.fused_score, 4),
                    bm25_rank=c.bm25_rank,
                    semantic_rank=c.semantic_rank,
                )
                for c in sorted_candidates[:5]
            ]
            debug_meta = DiagnosticDebugMetadata(
                query_understanding=qu_result,
                retrieval=RetrievalDebugInfo(
                    queries_executed=queries_to_run,
                    similarity_threshold=sim_thresh,
                    total_candidates_found=len(sorted_candidates),
                    top_candidates=top_debug_candidates,
                    decision=decision,
                    confidence_level=confidence_level,
                ),
                latency=LatencyBreakdown(
                    query_understanding_ms=round(qu_latency_ms, 2),
                    retrieval_ms=round(ret_latency_ms, 2),
                    response_synthesis_ms=round(syn_latency_ms, 2),
                    total_pipeline_ms=round(t_total_ms, 2),
                ),
            )

        return StructuredTroubleshootResponse(
            status=status_str,
            session_id=session_id_out,
            turn_count=1,
            max_turns=settings.MAX_DIAGNOSTIC_TURNS,
            final_problem_id=final_pid,
            domain=domain_out,
            canonical_symptom=qu_result.canonical_symptom,
            extracted_signals=qu_result.extracted_signals,
            confidence=conf_out,
            timeline=timeline,
            contexts=contexts,
            fallback=fallback_msg,
            debug_info=debug_meta,
        )

    def continue_troubleshoot(
        self,
        request: ContinueTroubleshootRequest,
        threshold: Optional[float] = None,
        debug: bool = False,
    ) -> StructuredTroubleshootResponse:
        """Continue a multi-turn troubleshooting session with user's clarification answer."""
        t_start = time.perf_counter()
        session = self.clarification_service.get_session(request.session_id)
        if not session:
            return StructuredTroubleshootResponse(
                status="error",
                fallback="Troubleshooting session expired or not found. Please submit a new query.",
                contexts=[],
            )

        # Refine query and signals using selected clarification option
        refined_query, new_signals, target_problem_id, is_irrelevant = self.clarification_service.refine_with_answer(
            session=session,
            answer_id=request.answer_id,
            user_response_text=request.user_response_text,
        )

        # Turn limit & Irrelevant response handling (Phase 7.3)
        if is_irrelevant or session.turn_count > session.max_turns:
            session.status = "insufficient_information"
            now_ts = time.time()
            timeline = [
                TimelineEvent(
                    step="query_received",
                    label="Complaint Received",
                    status="completed",
                    detail=f'User submitted: "{session.original_query}"',
                    timestamp=session.created_at,
                ),
                TimelineEvent(
                    step="clarification_requested",
                    label="Clarification Requested",
                    status="completed",
                    detail=session.clarification_question.question if session.clarification_question else "Clarification",
                    timestamp=session.created_at,
                ),
                TimelineEvent(
                    step="insufficient_information",
                    label="Insufficient Information",
                    status="completed",
                    detail="Diagnosis halted after turn limit or irrelevant response.",
                    timestamp=now_ts,
                ),
            ]
            return StructuredTroubleshootResponse(
                status="insufficient_information",
                session_id=session.session_id,
                turn_count=session.turn_count,
                max_turns=session.max_turns,
                clarification_history=session.clarification_history,
                domain=session.domain,
                canonical_symptom=session.canonical_symptom,
                extracted_signals=session.extracted_signals,
                confidence=0.0,
                timeline=timeline,
                contexts=[],
                fallback="I don't have enough information to confidently identify the issue. Please describe what you see, when the problem occurs, and what you were doing immediately before it happened.",
            )

        t_qu_start = time.perf_counter()
        qu_result = self.qu_service.analyze(refined_query)
        t_qu_end = time.perf_counter()
        qu_latency_ms = (t_qu_end - t_qu_start) * 1000.0

        t_ret_start = time.perf_counter()
        candidate_map: Dict[str, RetrievalResult] = {}
        for q_text in [refined_query, session.original_query]:
            results = self.retriever.retrieve(q_text, top_k=5, threshold=0.0)
            for r in results:
                if r.problem_id not in candidate_map or r.score > candidate_map[r.problem_id].score:
                    candidate_map[r.problem_id] = r

        # Grounded target problem boost
        chosen_pid = target_problem_id or qu_result.target_problem_id
        if chosen_pid and chosen_pid in self.retriever.doc_map:
            doc = self.retriever.doc_map[chosen_pid]
            candidate_map[chosen_pid] = RetrievalResult(
                problem_id=chosen_pid,
                domain=doc.domain,
                problem=doc.problem,
                score=0.96,
                fused_score=0.96,
                bm25_rank=1,
                semantic_rank=1,
                status="MATCH",
            )

        sorted_candidates = sorted(
            candidate_map.values(), key=lambda x: x.score, reverse=True
        )
        t_ret_end = time.perf_counter()
        ret_latency_ms = (t_ret_end - t_ret_start) * 1000.0

        top_candidate = sorted_candidates[0] if sorted_candidates else None
        contexts: List[Context] = []
        fallback_msg: Optional[str] = None
        status_str = "diagnosis_ready"
        final_pid = None
        domain_out = qu_result.domain or session.domain
        conf_out = 0.0

        if top_candidate and top_candidate.score >= (threshold or 0.40):
            ctx = self._build_context_for_problem(top_candidate.problem_id, top_candidate.score)
            if ctx:
                contexts.append(ctx)
            session.status = "diagnosis_ready"
            session.selected_problem_id = top_candidate.problem_id
            session.confidence = top_candidate.score
            final_pid = top_candidate.problem_id
            domain_out = top_candidate.domain
            conf_out = round(top_candidate.score, 4)
        else:
            status_str = "insufficient_information"
            fallback_msg = "I don't have enough information to confidently identify the issue. Please describe what you see, when the problem occurs, and what you were doing immediately before it happened."

        now_ts = time.time()
        timeline = [
            TimelineEvent(
                step="query_received",
                label="Complaint Received",
                status="completed",
                detail=f'User submitted: "{session.original_query}"',
                timestamp=session.created_at,
            ),
            TimelineEvent(
                step="clarification_requested",
                label="Clarification Requested",
                status="completed",
                detail=session.clarification_question.question if session.clarification_question else "Clarification",
                timestamp=session.created_at,
            ),
            TimelineEvent(
                step="clarification_answered",
                label="Clarification Answered",
                status="completed",
                detail=f"Selected: {session.clarification_answer_label or request.answer_id or 'Custom Response'}",
                timestamp=now_ts,
            ),
            TimelineEvent(
                step="diagnosis_ready" if contexts else "insufficient_information",
                label="Refined Diagnosis Ready" if contexts else "Insufficient Information",
                status="completed",
                detail=f"Grounded resolution identified: {top_candidate.problem if top_candidate else 'General Steps'} ({top_candidate.problem_id if top_candidate else 'N/A'}) with {top_candidate.score*100 if top_candidate else 0:.0f}% confidence" if contexts else fallback_msg,
                timestamp=now_ts,
            ),
        ]

        t_total_ms = (time.perf_counter() - t_start) * 1000.0
        debug_meta = None
        if debug:
            top_debug_candidates = [
                CandidateDebugInfo(
                    problem_id=c.problem_id,
                    problem=c.problem,
                    domain=c.domain,
                    fused_score=round(c.fused_score, 4),
                    bm25_rank=c.bm25_rank,
                    semantic_rank=c.semantic_rank,
                )
                for c in sorted_candidates[:5]
            ]
            debug_meta = DiagnosticDebugMetadata(
                query_understanding=qu_result,
                retrieval=RetrievalDebugInfo(
                    queries_executed=[refined_query, session.original_query],
                    similarity_threshold=threshold or 0.40,
                    total_candidates_found=len(sorted_candidates),
                    top_candidates=top_debug_candidates,
                    decision="MATCH" if contexts else "NO_MATCH",
                    confidence_level="HIGH" if contexts else "LOW",
                ),
                latency=LatencyBreakdown(
                    query_understanding_ms=round(qu_latency_ms, 2),
                    retrieval_ms=round(ret_latency_ms, 2),
                    response_synthesis_ms=0.5,
                    total_pipeline_ms=round(t_total_ms, 2),
                ),
            )

        return StructuredTroubleshootResponse(
            status=status_str,
            session_id=session.session_id,
            turn_count=session.turn_count,
            max_turns=session.max_turns,
            clarification_history=session.clarification_history,
            final_problem_id=final_pid,
            domain=domain_out,
            canonical_symptom=qu_result.canonical_symptom,
            extracted_signals=new_signals if new_signals else session.extracted_signals,
            confidence=conf_out,
            timeline=timeline,
            contexts=contexts,
            fallback=fallback_msg,
            debug_info=debug_meta,
        )
