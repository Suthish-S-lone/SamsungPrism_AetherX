"""API Request Models for SmartGuide.

Validates user input queries and enforces structural constraints.
"""

from pydantic import BaseModel, Field, field_validator


class TroubleshootRequest(BaseModel):
    """User request model for troubleshooting complaints."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User complaint or troubleshooting query",
    )

    @field_validator("query")
    @classmethod
    def validate_query_not_whitespace(cls, value: str) -> str:
        """Reject empty or whitespace-only queries and normalize."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Query cannot be empty or contain only whitespace.")
        return stripped
