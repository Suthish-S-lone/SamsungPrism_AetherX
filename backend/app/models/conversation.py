"""Conversation State and Clarification Data Models for Phase 6.

Enables multi-turn interactive guided troubleshooting, ambiguity resolution,
session tracking, and grounded diagnostic refinement.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ClarificationOption(BaseModel):
    """An individual selectable clarification option."""

    id: str = Field(..., description="Unique option identifier (e.g. opt_charging_heat)")
    label: str = Field(..., description="Short user-facing option label")
    description: Optional[str] = Field(
        default=None, description="Detailed explanatory context for the option"
    )
    signal: str = Field(..., description="Diagnostic signal added when selected")
    target_problem_id: Optional[str] = Field(
        default=None, description="Grounded target problem ID if this option resolves directly"
    )


class ClarificationQuestion(BaseModel):
    """A grounded clarification question presented when ambiguity exists."""

    id: str = Field(..., description="Unique question identifier")
    domain: str = Field(..., description="Troubleshooting domain (battery, display, camera, performance)")
    question: str = Field(..., description="Clarifying question text")
    prompt: str = Field(
        default="To narrow down the root cause, please select the option that best matches your situation:",
        description="User-facing prompt instruction",
    )
    options: List[ClarificationOption] = Field(
        ..., min_length=2, description="List of structured options"
    )
    reason: str = Field(..., description="Explanation of why clarification is needed")


class TimelineEvent(BaseModel):
    """An event in the multi-turn diagnostic timeline."""

    step: str = Field(..., description="Event step name (e.g. query, clarification, diagnosis)")
    label: str = Field(..., description="Human-readable label")
    status: Literal["completed", "active", "pending"] = Field(
        default="completed", description="Status of the timeline step"
    )
    detail: Optional[str] = Field(default=None, description="Optional detail or value")
    timestamp: Optional[float] = Field(default=None, description="Event timestamp")


class ConversationSession(BaseModel):
    """Complete multi-turn conversation session state."""

    session_id: str = Field(..., description="Unique UUID for this troubleshooting session")
    original_query: str = Field(..., description="Original user complaint text")
    current_query: str = Field(..., description="Active query text with clarification refinements")
    domain: Optional[str] = Field(default=None, description="Detected or refined domain")
    canonical_symptom: Optional[str] = Field(default=None, description="Current canonical symptom")
    extracted_signals: List[str] = Field(
        default_factory=list, description="Extracted keywords, cues, and clarification signals"
    )
    clarification_question: Optional[ClarificationQuestion] = Field(
        default=None, description="Active clarification question if ambiguity exists"
    )
    clarification_answer_id: Optional[str] = Field(
        default=None, description="Option ID selected by the user"
    )
    clarification_answer_label: Optional[str] = Field(
        default=None, description="Label of the option selected by the user"
    )
    eliminated_candidates: List[str] = Field(
        default_factory=list, description="Problem IDs eliminated through clarification"
    )
    selected_problem_id: Optional[str] = Field(
        default=None, description="Final matched problem ID from the knowledge base"
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Current confidence score")
    workflow_step: int = Field(default=0, description="Current action index in the troubleshooting plan")
    completed_steps: List[int] = Field(
        default_factory=list, description="Indices of completed actions"
    )
    resolution_status: Optional[Literal["in_progress", "resolved", "escalated"]] = Field(
        default="in_progress", description="Final resolution outcome"
    )
    status: Literal["clarification_required", "diagnosis_ready", "out_of_scope", "no_match", "error"] = Field(
        default="diagnosis_ready", description="Current session state machine status"
    )
    created_at: float = Field(..., description="Session creation timestamp")
    updated_at: float = Field(..., description="Session last updated timestamp")
