"""API Response Models for SmartGuide.

IMPORTANT NOTICE:
=================
Prototype schema — not official Samsung schema.
This schema was constructed for prototype development and testing.
It does NOT claim to represent official Samsung API contracts.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


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

    Prototype schema — not official Samsung schema.
    """

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
