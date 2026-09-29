"""Unit tests for API schemas, request validation, and the /health endpoint.

Verifies:
- Request validation rejection of missing, empty, whitespace, and oversized queries.
- Prototype response schema instantiation and validation.
- FastAPI /health endpoint response structure and values.
"""

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.request import TroubleshootRequest
from backend.app.models.response import (
    Action,
    Context,
    Step,
    TroubleshootResponse,
    HealthResponse,
)


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a FastAPI TestClient instance."""
    return TestClient(app)


# ---------------------------------------------------------
# Request Validation Tests (Test 8)
# ---------------------------------------------------------

def test_valid_request():
    """Valid user complaint query passes validation."""
    req = TroubleshootRequest(query="My battery is draining too fast while browsing")
    assert req.query == "My battery is draining too fast while browsing"


def test_reject_empty_query():
    """Empty string query is rejected."""
    with pytest.raises(ValidationError):
        TroubleshootRequest(query="")


def test_reject_whitespace_only_query():
    """Whitespace-only query is rejected."""
    with pytest.raises(ValidationError):
        TroubleshootRequest(query="   \n\t  ")


def test_reject_oversized_query():
    """Query exceeding max length constraint (2000 chars) is rejected."""
    oversized = "a" * 2001
    with pytest.raises(ValidationError):
        TroubleshootRequest(query=oversized)


def test_whitespace_is_trimmed():
    """Leading and trailing whitespace is cleaned."""
    req = TroubleshootRequest(query="  Device overheating when charging  ")
    assert req.query == "Device overheating when charging"


# ---------------------------------------------------------
# Response Schema Validation Tests (Test 9)
# ---------------------------------------------------------

def test_prototype_response_schema_valid():
    """Verify prototype troubleshooting response conforms to prototype schema."""
    step1 = Step(text="Open Settings")
    step2 = Step(text="Tap on Battery")
    step3 = Step(text="Enable Power Saving")

    action = Action(
        action_name="Enable Power Saving Mode",
        description="Reduces power consumption by limiting background activity.",
        category="manual",
        steps=[step1, step2, step3],
        target_screen="Battery > Power saving",
        deeplink="prototype://settings/battery/power_saving",
    )

    context = Context(
        goal="Prolong battery duration",
        title="Battery Saver Configuration",
        score=0.95,
        actions=[action],
    )

    response = TroubleshootResponse(
        contexts=[context],
        fallback=None,
    )

    assert len(response.contexts) == 1
    assert response.contexts[0].score == 0.95
    assert response.contexts[0].actions[0].category == "manual"
    assert response.contexts[0].actions[0].deeplink == "prototype://settings/battery/power_saving"
    assert response.fallback is None


def test_prototype_response_fallback():
    """Verify fallback response for unhandled/unsupported queries."""
    response = TroubleshootResponse(
        contexts=[],
        fallback="I could not find troubleshooting steps for your query in the prototype knowledge base.",
    )
    assert len(response.contexts) == 0
    assert response.fallback is not None


def test_score_range_validation():
    """Ensure score must be between 0.0 and 1.0."""
    with pytest.raises(ValidationError):
        Context(
            goal="Goal",
            title="Title",
            score=1.5,  # Invalid: > 1.0
            actions=[],
        )

    with pytest.raises(ValidationError):
        Context(
            goal="Goal",
            title="Title",
            score=-0.1,  # Invalid: < 0.0
            actions=[],
        )


# ---------------------------------------------------------
# Health Endpoint Tests (Test 10)
# ---------------------------------------------------------

def test_health_endpoint(client: TestClient):
    """GET /health returns 200 OK with expected Phase 1 subsystem status."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data == {
        "status": "ok",
        "data": "ready",
        "schema": "ready",
        "retrieval": "not_initialized",
        "cache": "not_initialized",
        "llm": "not_initialized",
    }

    # Validate against HealthResponse model
    health_obj = HealthResponse.model_validate(data)
    assert health_obj.status == "ok"
    assert health_obj.schema_status == "ready"
