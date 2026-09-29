"""Query Understanding Service for SmartGuide.

Processes user queries, performs domain classification, extracts technical signals,
and synthesizes canonical queries for retrieval.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.services.canonicalizer import QueryCanonicalizer, CANONICAL_PROBLEMS


class QueryUnderstandingResult(BaseModel):
    """Structured representation of query understanding analysis."""

    original_query: str = Field(..., description="Original user query")
    normalized_query: str = Field(..., description="Cleaned and normalized query")
    domain: Optional[str] = Field(
        default=None, description="Identified device domain (battery, display, camera, performance)"
    )
    canonical_symptom: Optional[str] = Field(
        default=None, description="Standardized canonical technical symptom text"
    )
    target_problem_id: Optional[str] = Field(
        default=None, description="Target problem ID if high-confidence grounded mapping occurs"
    )
    extracted_signals: List[str] = Field(
        default_factory=list, description="Extracted keywords, cues, and contextual indicators"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in query understanding analysis"
    )
    reasoning_tags: List[str] = Field(
        default_factory=list, description="Descriptive reasoning tags explaining classification"
    )
    rewrite_method: str = Field(
        default="grounded_taxonomy",
        description="Method used to produce canonical symptom: grounded_taxonomy, lexical_pass_through, or out_of_scope",
    )
    fallback_used: bool = Field(
        default=False, description="Whether fallback ungrounded representation was used"
    )
    is_out_of_scope: bool = Field(
        default=False, description="Whether query was detected as completely out-of-scope / unsupported"
    )


class QueryUnderstandingService:
    """Service encapsulating query understanding, canonicalization, and signal extraction."""

    def __init__(self, canonicalizer: Optional[QueryCanonicalizer] = None):
        self.canonicalizer = canonicalizer or QueryCanonicalizer()

    def analyze(self, query: str) -> QueryUnderstandingResult:
        """Analyze user query and return structured understanding result."""
        normalized = self.canonicalizer.normalize(query)
        if not normalized:
            return QueryUnderstandingResult(
                original_query=query,
                normalized_query="",
                domain=None,
                canonical_symptom=None,
                target_problem_id=None,
                extracted_signals=[],
                confidence=0.0,
                reasoning_tags=["empty_query"],
                rewrite_method="out_of_scope",
                fallback_used=True,
                is_out_of_scope=True,
            )

        # 1. Check out of scope
        if self.canonicalizer.is_out_of_scope(query):
            return QueryUnderstandingResult(
                original_query=query,
                normalized_query=normalized,
                domain=None,
                canonical_symptom=None,
                target_problem_id=None,
                extracted_signals=["out_of_scope_topic"],
                confidence=0.0,
                reasoning_tags=["out_of_scope", "unsupported_domain"],
                rewrite_method="out_of_scope",
                fallback_used=True,
                is_out_of_scope=True,
            )

        # 2. Match grounded canonical taxonomy
        match = self.canonicalizer.canonicalize(query)
        if match:
            return QueryUnderstandingResult(
                original_query=query,
                normalized_query=normalized,
                domain=match.domain,
                canonical_symptom=match.canonical_problem,
                target_problem_id=match.problem_id,
                extracted_signals=match.matched_signals,
                confidence=match.confidence,
                reasoning_tags=["grounded_taxonomy", f"domain:{match.domain}", match.reasoning],
                rewrite_method="grounded_taxonomy",
                fallback_used=False,
                is_out_of_scope=False,
            )

        # 3. Fallback: domain heuristic inference from normalized tokens
        domain = None
        signals = []
        if any(w in normalized for w in ["battery", "charge", "power", "drain"]):
            domain = "battery"
            signals.append("domain_cue:battery")
        elif any(w in normalized for w in ["screen", "display", "touch", "bright", "gesture"]):
            domain = "display"
            signals.append("domain_cue:display")
        elif any(w in normalized for w in ["camera", "photo", "picture", "lens", "shutter"]):
            domain = "camera"
            signals.append("domain_cue:camera")
        elif any(w in normalized for w in ["slow", "lag", "freeze", "storage", "ram", "memory", "app"]):
            domain = "performance"
            signals.append("domain_cue:performance")

        return QueryUnderstandingResult(
            original_query=query,
            normalized_query=normalized,
            domain=domain,
            canonical_symptom=normalized,
            target_problem_id=None,
            extracted_signals=signals,
            confidence=0.50 if domain else 0.30,
            reasoning_tags=["lexical_pass_through"] + ([f"domain:{domain}"] if domain else ["unknown_domain"]),
            rewrite_method="lexical_pass_through",
            fallback_used=True,
            is_out_of_scope=False,
        )
