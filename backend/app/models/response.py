"""API Response Models for SmartGuide.

IMPORTANT NOTICE:
=================
Prototype schema — not official Samsung schema.
This schema was constructed for prototype development and testing.
It does NOT claim to represent official Samsung API contracts.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from backend.app.models.conversation import ClarificationQuestion, TimelineEvent


class Step(BaseModel):
    """A single step in a troubleshooting action plan."""

    text: str = Field(..., description="Actionable instruction text", min_length=1)


class Action(BaseModel):
    """An action with target screen and optional prototype deeplink."""

    action_name: str = Field(..., description="Name of the action", min_length=1)
    description: str = Field(..., description="Detailed description", min_length=1)
    category: Literal["auto", "manual", "critical"] = Field(
        ..., description="Execution mode"
    )
    steps: List[Step] = Field(..., description="List of instructional steps")
    target_screen: str = Field(..., description="Target UI/Settings location", min_length=1)
    deeplink: Optional[str] = Field(
        default=None,
        description="Prototype deeplink URI (must use prototype:// if present)",
    )


class Context(BaseModel):
    """Troubleshooting context representing a matched resolution pathway."""

    goal: str = Field(..., description="User goal or underlying issue solved", min_length=1)
    title: str = Field(..., description="Context title", min_length=1)
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance or confidence score between 0.0 and 1.0",
    )
    actions: List[Action] = Field(
        default_factory=list, description="Ordered resolution actions"
    )


class TroubleshootResponse(BaseModel):
    """Top-level prototype troubleshooting response model.

    Supports single-turn, multi-turn clarification flows, and explicit diagnostic states.
    """

    status: Literal[
        "diagnosis_ready",
        "clarification_required",
        "insufficient_information",
        "unsupported",
        "out_of_scope",
        "no_match",
        "error",
    ] = Field(
        default="diagnosis_ready", description="Current status of the troubleshooting request"
    )
    session_id: Optional[str] = Field(
        default=None, description="Active session ID for continuing the troubleshooting conversation"
    )
    turn_count: Optional[int] = Field(
        default=None, description="Current turn number in multi-turn conversation"
    )
    max_turns: Optional[int] = Field(
        default=None, description="Maximum permitted diagnostic turns"
    )
    clarification: Optional[ClarificationQuestion] = Field(
        default=None, description="Clarification question when ambiguity exists and confidence is low"
    )
    clarification_history: Optional[List[dict]] = Field(
        default=None, description="Historical list of past clarification questions and answers"
    )
    final_problem_id: Optional[str] = Field(
        default=None, description="Matched grounded knowledge base problem ID"
    )
    domain: Optional[str] = Field(
        default=None, description="Identified device domain (battery, display, camera, performance)"
    )
    canonical_symptom: Optional[str] = Field(
        default=None, description="Canonical normalized technical symptom text"
    )
    extracted_signals: Optional[List[str]] = Field(
        default=None, description="Extracted reasoning signals and keywords"
    )
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Confidence score of the diagnosis"
    )
    timeline: Optional[List[TimelineEvent]] = Field(
        default=None, description="Diagnostic progression timeline events"
    )
    contexts: List[Context] = Field(
        default_factory=list,
        description="Ranked troubleshooting contexts addressing the user query",
    )
    fallback: Optional[str] = Field(
        default=None,
        description="Fallback message or guidance when no confident match exists",
    )


class HealthResponse(BaseModel):
    """Health check response reporting subsystem readiness for Phase 1."""

    status: str = "ok"
    data: str = "ready"
    schema_status: str = Field(default="ready", alias="schema")
    retrieval: str = "not_initialized"
    cache: str = "not_initialized"
    llm: str = "not_initialized"

    model_config = {
        "populate_by_name": True,
    }
