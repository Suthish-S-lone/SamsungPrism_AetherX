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
from backend.app.models.response import Action, Context, Step, TroubleshootResponse
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.retrieval.types import RetrievalResult
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
        data_dir: Optional[Path] = None,
    ):
        self.data_dir = data_dir or settings.DATA_DIR
        self.retriever = retriever or HybridRetriever(data_dir=self.data_dir)
        self.qu_service = query_understanding or QueryUnderstandingService()

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

    def troubleshoot(
        self,
        query: str,
        threshold: Optional[float] = None,
        debug: bool = False,
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
                # If seen, keep the higher scoring result or combine
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
                # Boost verified grounded match
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
        # 3. Decision Gating & Response Synthesis
        # ---------------------------------------------------------
        t_syn_start = time.perf_counter()

        top_candidate = sorted_candidates[0] if sorted_candidates else None
        is_match = top_candidate is not None and top_candidate.score >= sim_thresh

        decision = "MATCH" if is_match else "NO_MATCH"
        confidence_level = "LOW_CONFIDENCE"
        if is_match:
            confidence_level = "HIGH" if top_candidate.score >= 0.70 else "MEDIUM"

        contexts: List[Context] = []
        fallback_msg: Optional[str] = None

        if is_match and top_candidate:
            raw_record = self.troubleshooting_records.get(top_candidate.problem_id)
            if raw_record:
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
                contexts.append(
                    Context(
                        goal=raw_record.get("problem", top_candidate.problem),
                        title=raw_record.get("problem", top_candidate.problem),
                        score=round(top_candidate.score, 4),
                        actions=actions,
                    )
                )
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
            contexts=contexts,
            fallback=fallback_msg,
            debug_info=debug_meta,
        )
