"""Services module for SmartGuide Theme 2 prototype.

Exposes Canonicalizer, Query Understanding, and Structured Troubleshooting services.
"""

from backend.app.services.canonicalizer import (
    CANONICAL_PROBLEMS,
    CanonicalMatch,
    QueryCanonicalizer,
)
from backend.app.services.query_understanding import (
    QueryUnderstandingResult,
    QueryUnderstandingService,
)
from backend.app.services.troubleshooting_service import (
    DiagnosticDebugMetadata,
    StructuredTroubleshootResponse,
    TroubleshootingService,
)

__all__ = [
    "CANONICAL_PROBLEMS",
    "CanonicalMatch",
    "QueryCanonicalizer",
    "QueryUnderstandingResult",
    "QueryUnderstandingService",
    "DiagnosticDebugMetadata",
    "StructuredTroubleshootResponse",
    "TroubleshootingService",
]
