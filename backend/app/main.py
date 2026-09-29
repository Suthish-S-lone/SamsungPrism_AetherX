"""SmartGuide FastAPI Application - Phase 3.

Provides the foundational API interface, configuration, health check,
and the /troubleshoot endpoint integrating Query Understanding,
Pretrained Neural Hybrid Retrieval, Deeplink Resolution, and Diagnostic Transparency.
"""

from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.models.request import ContinueTroubleshootRequest, TroubleshootRequest
from backend.app.models.response import HealthResponse
from backend.app.services.troubleshooting_service import (
    StructuredTroubleshootResponse,
    TroubleshootingService,
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Samsung PRISM Theme 2: Smart Guided Troubleshooting Engine",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance (lazy loaded on demand or startup)
_troubleshooting_service: Optional[TroubleshootingService] = None


def get_troubleshooting_service() -> TroubleshootingService:
    """Retrieve or lazily initialize the singleton TroubleshootingService."""
    global _troubleshooting_service
    if _troubleshooting_service is None:
        _troubleshooting_service = TroubleshootingService()
    return _troubleshooting_service


@app.get(
    "/health",
    response_model=HealthResponse,
    response_model_by_alias=True,
    summary="Subsystem health status for SmartGuide prototype",
)
def get_health() -> dict:
    """Return health status of subsystems for prototype foundation."""
    return {
        "status": "ok",
        "data": "ready",
        "schema": "ready",
        "retrieval": "not_initialized",
        "cache": "not_initialized",
        "llm": "not_initialized",
    }


@app.post(
    "/troubleshoot",
    response_model=StructuredTroubleshootResponse,
    summary="Execute end-to-end smart guided troubleshooting on user query",
)
def troubleshoot(
    request: TroubleshootRequest,
    debug: bool = Query(default=False, description="Include diagnostic transparency debug payload"),
) -> StructuredTroubleshootResponse:
    """Handle natural-language troubleshooting complaint and return actionable context with deeplinks."""
    service = get_troubleshooting_service()
    return service.troubleshoot(query=request.query, debug=debug)


@app.post(
    "/troubleshoot/continue",
    response_model=StructuredTroubleshootResponse,
    summary="Continue multi-turn troubleshooting session with user clarification answer",
)
def continue_troubleshoot(
    request: ContinueTroubleshootRequest,
    debug: bool = Query(default=False, description="Include diagnostic transparency debug payload"),
) -> StructuredTroubleshootResponse:
    """Process clarification choice or follow-up response to refine diagnosis and generate steps."""
    service = get_troubleshooting_service()
    return service.continue_troubleshoot(request=request, debug=debug)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
