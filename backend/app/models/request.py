"""API Request Models for SmartGuide.

Validates user input queries and enforces structural constraints for single-turn
and multi-turn troubleshooting conversations.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TroubleshootRequest(BaseModel):
    """User request model for initial troubleshooting complaints."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User complaint or troubleshooting query",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional existing session ID to resume or restart",
    )

    @field_validator("query")
    @classmethod
    def validate_query_not_whitespace(cls, value: str) -> str:
        """Reject empty or whitespace-only queries and normalize."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Query cannot be empty or contain only whitespace.")
        return stripped


class ContinueTroubleshootRequest(BaseModel):
    """Request model for continuing an interactive multi-turn troubleshooting session."""

    session_id: str = Field(..., description="UUID of the active troubleshooting session")
    clarification_id: Optional[str] = Field(
        default=None, description="ID of the clarification question answered"
    )
    answer_id: Optional[str] = Field(
        default=None, description="ID of the selected clarification option"
    )
    user_response_text: Optional[str] = Field(
        default=None, max_length=1000, description="Optional custom text follow-up response"
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("session_id cannot be empty.")
        return stripped
