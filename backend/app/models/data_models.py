"""Data models for the SmartGuide Development Dataset.

NOTE: These models represent the DEVELOPMENT/PROTOTYPE assets created for building
the prototype. They are NOT official Samsung data structures.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class DevelopmentAction(BaseModel):
    """An action within a development troubleshooting record."""

    id: str = Field(..., description="Unique action identifier", min_length=1)
    name: str = Field(..., description="Action name", min_length=1)
    description: str = Field(..., description="Action description", min_length=1)
    category: Literal["manual", "auto", "critical"] = Field(
        ..., description="Action execution category"
    )
    priority: int = Field(..., description="Action execution priority", ge=1)
    steps: List[str] = Field(
        ..., description="Step-by-step guidance instructions", min_length=1
    )
    target_screen: str = Field(
        ..., description="Target UI or settings screen path", min_length=1
    )


class TroubleshootingRecord(BaseModel):
    """A development troubleshooting issue record."""

    id: str = Field(..., description="Unique troubleshooting problem ID", min_length=1)
    domain: Literal["battery", "display", "camera", "performance"] = Field(
        ..., description="Problem domain category"
    )
    problem: str = Field(..., description="Canonical problem statement", min_length=1)
    description: str = Field(..., description="Problem details", min_length=1)
    keywords: List[str] = Field(..., description="Associated keywords", min_length=1)
    actions: List[DevelopmentAction] = Field(
        ..., description="Resolution actions", min_length=1
    )
    source: str = Field(
        default="development_prototype", description="Data provenance label"
    )


class DeeplinkRecord(BaseModel):
    """A prototype deeplink entry for navigation simulation."""

    id: str = Field(..., description="Unique deeplink identifier", min_length=1)
    name: str = Field(..., description="Deeplink label", min_length=1)
    description: str = Field(..., description="Deeplink context description", min_length=1)
    message: str = Field(..., description="User prompt or notification message", min_length=1)
    qna_description: str = Field(
        ..., description="Question and answer description", min_length=1
    )
    target_screen: str = Field(
        ..., description="Target screen path in settings/UI", min_length=1
    )
    uri: str = Field(..., description="Prototype navigation URI scheme")
    source: str = Field(
        default="development_prototype", description="Data provenance label"
    )

    @field_validator("uri")
    @classmethod
    def validate_prototype_uri(cls, value: str) -> str:
        """Ensure URIs strictly use prototype:// and do not impersonate official schemes."""
        if not value.startswith("prototype://"):
            raise ValueError(
                f"Deeplink URI must start with 'prototype://', found: {value}"
            )
        if any(
            fake in value
            for fake in ["bixby://", "samsungapps://", "samsung://", "sec://"]
        ):
            raise ValueError(
                f"Development data must not use official or fabricated vendor URI schemes: {value}"
            )
        return value


class TestQueryRecord(BaseModel):
    """A test query for evaluation of retrieval and resolution."""

    __test__ = False

    id: str = Field(..., description="Query identifier", min_length=1)
    query: str = Field(..., description="Raw user query text", min_length=1)
    expected_domain: Optional[
        Literal["battery", "display", "camera", "performance"]
    ] = Field(
        default=None,
        description="Expected domain if supported, or None if out-of-scope/unsupported",
    )
    expected_problem_id: Optional[str] = Field(
        default=None,
        description="Expected target problem ID if supported, or None if out-of-scope",
    )
    source: str = Field(
        default="development_prototype", description="Data provenance label"
    )


class HoldoutQueryRecord(BaseModel):
    """Holdout benchmark query for generalization evaluation."""

    __test__ = False

    id: str = Field(..., description="Holdout query identifier", min_length=1)
    query: str = Field(..., description="Holdout natural language query text", min_length=1)
    expected_problem_id: Optional[str] = Field(
        default=None, description="Expected target problem ID or None if unsupported"
    )
    expected_domain: Optional[
        Literal["battery", "display", "camera", "performance"]
    ] = Field(
        default=None, description="Expected domain or None if unsupported"
    )
    supported: bool = Field(..., description="Whether query is in-scope")
    source: str = Field(
        default="holdout_manual", description="Data provenance label"
    )


class QueryVariationRecord(BaseModel):
    """Semantic query variations for a troubleshooting problem."""

    problem_id: str = Field(..., description="Reference problem ID", min_length=1)
    canonical_query: str = Field(
        ..., description="Standard reference query", min_length=1
    )
    query_variations: List[str] = Field(
        ..., description="Synonym and phrasing variations", min_length=1
    )
    source: str = Field(
        default="development_prototype", description="Data provenance label"
    )
