"""Unit and integration tests for Phase 3 Services and Endpoints.

Tests:
1. Knowledge-base grounded QueryCanonicalizer across all 4 domains.
2. Out-of-scope intent detection for unsupported topics.
3. QueryUnderstandingService analysis and signal extraction.
4. TroubleshootingService end-to-end matching, fallback, and deeplink resolution.
5. POST /troubleshoot FastAPI endpoint and diagnostic transparency payload.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.canonicalizer import QueryCanonicalizer
from backend.app.services.query_understanding import QueryUnderstandingService
from backend.app.services.troubleshooting_service import TroubleshootingService


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def canonicalizer() -> QueryCanonicalizer:
    """Query canonicalizer fixture."""
    return QueryCanonicalizer()


@pytest.fixture
def qu_service() -> QueryUnderstandingService:
    """Query understanding service fixture."""
    return QueryUnderstandingService()


@pytest.fixture
def tb_service() -> TroubleshootingService:
    """Troubleshooting service fixture."""
    return TroubleshootingService()


# ---------------------------------------------------------
# 1. Canonicalizer Domain Tests
# ---------------------------------------------------------

def test_canonicalize_battery_cases(canonicalizer: QueryCanonicalizer):
    """Test canonicalization of varied colloquial battery complaints."""
    # Rapid drain
    m1 = canonicalizer.canonicalize("I have to plug my phone into the wall multiple times throughout the day.")
    assert m1 is not None
    assert m1.problem_id == "battery_001"
    assert m1.domain == "battery"

    # Device gets hot
    m2 = canonicalizer.canonicalize("The back panel becomes uncomfortably warm even when I am just reading emails.")
    assert m2 is not None
    assert m2.problem_id == "battery_002"

    # Slow charging
    m3 = canonicalizer.canonicalize("My phone has been connected to the power adapter for two hours and barely gained twenty percent.")
    assert m3 is not None
    assert m3.problem_id == "battery_003"

    # Overnight / idle drain
    m4 = canonicalizer.canonicalize("When I wake up in the morning, the power level has fallen by thirty percent overnight on my nightstand.")
    assert m4 is not None
    assert m4.problem_id == "battery_004"

    # Specific app battery drain
    m5 = canonicalizer.canonicalize("A specific social media program seems to be chewing through all my power in the background.")
    assert m5 is not None
    assert m5.problem_id == "battery_005"

    # Percentage drop
    m6 = canonicalizer.canonicalize("The remaining charge indicator suddenly tumbled from fifty percent down to fifteen percent in minutes.")
    assert m6 is not None
    assert m6.problem_id == "battery_006"

    # Power saving
    m7 = canonicalizer.canonicalize("How do I turn on energy conservation mode so my charge lasts until tonight?")
    assert m7 is not None
    assert m7.problem_id == "battery_007"

    # Battery after update
    m8 = canonicalizer.canonicalize("Ever since installing yesterday firmware upgrade, my power efficiency has gotten noticeably worse.")
    assert m8 is not None
    assert m8.problem_id == "battery_008"


def test_canonicalize_display_cases(canonicalizer: QueryCanonicalizer):
    """Test canonicalization of varied display complaints."""
    # Brightness changes
    m1 = canonicalizer.canonicalize("The panel randomly dims and then flares up to maximum illumination on its own.")
    assert m1 is not None
    assert m1.problem_id == "display_009"

    # Screen turns off too fast
    m2 = canonicalizer.canonicalize("The panel goes black almost immediately after I stop tapping on it.")
    assert m2 is not None
    assert m2.problem_id == "display_010"

    # Screen stays on
    m3 = canonicalizer.canonicalize("The glass remains fully lit indefinitely even after I set the device down on the table.")
    assert m3 is not None
    assert m3.problem_id == "display_011"

    # Gestures
    m4 = canonicalizer.canonicalize("Swiping up from the bottom of the glass to go home is completely unresponsive or triggers the wrong window.")
    assert m4 is not None
    assert m4.problem_id == "display_012"

    # Navbar buttons
    m5 = canonicalizer.canonicalize("I want to switch from swipe navigation back to classic three button layout at the bottom.")
    assert m5 is not None
    assert m5.problem_id == "display_013"

    # Touch delay
    m6 = canonicalizer.canonicalize("Typing on the on screen keyboard feels sluggish with noticeable input latency.")
    assert m6 is not None
    assert m6.problem_id == "display_014"

    # Screen appearance
    m7 = canonicalizer.canonicalize("The display tint looks way too yellowish and warm under indoor lighting.")
    assert m7 is not None
    assert m7.problem_id == "display_015"

    # Pocket touch
    m8 = canonicalizer.canonicalize("The phone keeps dialing emergency numbers and registering phantom taps while inside my trouser pocket.")
    assert m8 is not None
    assert m8.problem_id == "display_016"


def test_canonicalize_camera_cases(canonicalizer: QueryCanonicalizer):
    """Test canonicalization of varied camera complaints."""
    # Camera won't open / crash
    m1 = canonicalizer.canonicalize("Tapping the photography icon shows a black window before crashing back to the home screen.")
    assert m1 is not None
    assert m1.problem_id == "camera_017"

    # Camera freeze
    m2 = canonicalizer.canonicalize("The viewfinder completely locks up whenever I attempt to record a video clip.")
    assert m2 is not None
    assert m2.problem_id == "camera_018"

    # Blurry photos
    m3 = canonicalizer.canonicalize("All my portrait snapshots turn out soft and out of focus even in bright daylight.")
    assert m3 is not None
    assert m3.problem_id == "camera_019"

    # Camera after update
    m4 = canonicalizer.canonicalize("Ever since the latest system patch, the photo capture software has developed strange glitches.")
    assert m4 is not None
    assert m4.problem_id == "camera_020"

    # Reset camera
    m5 = canonicalizer.canonicalize("How can I restore the photography app configurations back to factory defaults?")
    assert m5 is not None
    assert m5.problem_id == "camera_021"

    # Slow camera start
    m6 = canonicalizer.canonicalize("It takes nearly five to ten seconds for the shutter interface to appear when I double press the power key.")
    assert m6 is not None
    assert m6.problem_id == "camera_022"

    # Camera storage
    m7 = canonicalizer.canonicalize("High resolution pictures and recordings are filling up the internal drive too quickly.")
    assert m7 is not None
    assert m7.problem_id == "camera_023"

    # Camera permissions
    m8 = canonicalizer.canonicalize("The photo application claims it cannot access the hardware lens or microphone.")
    assert m8 is not None
    assert m8.problem_id == "camera_024"


def test_canonicalize_performance_cases(canonicalizer: QueryCanonicalizer):
    """Test canonicalization of varied performance complaints."""
    # Slow after update
    m1 = canonicalizer.canonicalize("The entire phone feels bogged down and stuttery following the OS upgrade.")
    assert m1 is not None
    assert m1.problem_id == "performance_025"

    # Apps freeze
    m2 = canonicalizer.canonicalize("My daily apps keep throwing Application Not Responding popups.")
    assert m2 is not None
    assert m2.problem_id == "performance_026"

    # Storage full
    m3 = canonicalizer.canonicalize("A system notification warns that disk space is critically low and downloads cannot complete.")
    assert m3 is not None
    assert m3.problem_id == "performance_027"

    # RAM low
    m4 = canonicalizer.canonicalize("Background programs keep getting killed because available RAM is constantly depleted.")
    assert m4 is not None
    assert m4.problem_id == "performance_028"

    # Heavy game/app
    m5 = canonicalizer.canonicalize("Whenever a particular 3D game is active, the entire operating system slows to a crawl.")
    assert m5 is not None
    assert m5.problem_id == "performance_029"

    # General sluggishness
    m6 = canonicalizer.canonicalize("Opening menus and scrolling through social feeds has severe frame drops and jank.")
    assert m6 is not None
    assert m6.problem_id == "performance_030"

    # Background activity
    m7 = canonicalizer.canonicalize("Too many background syncing processes are hogging system resources.")
    assert m7 is not None
    assert m7.problem_id == "performance_031"

    # After installing app
    m8 = canonicalizer.canonicalize("Ever since downloading that new file manager utility, phone responsiveness has tanked.")
    assert m8 is not None
    assert m8.problem_id == "performance_032"


# ---------------------------------------------------------
# 2. Out of Scope Tests
# ---------------------------------------------------------

@pytest.mark.parametrize(
    "oos_query",
    [
        "Will it rain tomorrow in Seattle?",
        "Can you give me a recipe for chocolate chip cookies?",
        "How do I order pizza using a delivery app?",
        "I want to book flight tickets to Tokyo next month.",
        "How do I clean coffee stains off my phone leather wallet cover?",
        "Can you write a poem about artificial intelligence?",
        "How do I calculate compound interest for a mortgage loan?",
        "Recommend me a good horror movie to watch this weekend.",
        "How do I set a custom MP3 song as my incoming ringtone?",
        "I want to download a live aesthetic wallpaper for my lockscreen.",
        "How do I fold an origami paper crane?",
        "Can you recommend a high protein vegetarian diet plan?",
    ],
)
def test_out_of_scope_queries(canonicalizer: QueryCanonicalizer, oos_query: str):
    """Ensure non-troubleshooting queries are correctly flagged as out-of-scope."""
    assert canonicalizer.is_out_of_scope(oos_query) is True
    match = canonicalizer.canonicalize(oos_query)
    assert match is None


# ---------------------------------------------------------
# 3. Query Understanding Service Tests
# ---------------------------------------------------------

def test_query_understanding_analysis(qu_service: QueryUnderstandingService):
    """Test full analysis result structure for supported and unsupported queries."""
    res = qu_service.analyze("My battery is dying so quickly after the latest update")
    assert res.domain == "battery"
    assert res.canonical_symptom == "Battery behavior changed after a software update"
    assert res.confidence >= 0.90
    assert res.is_out_of_scope is False
    assert len(res.extracted_signals) > 0

    # Out of scope query analysis
    oos_res = qu_service.analyze("What is the recipe for baking chocolate cookies?")
    assert oos_res.is_out_of_scope is True
    assert oos_res.domain is None
    assert oos_res.confidence == 0.0


# ---------------------------------------------------------
# 4. Troubleshooting Service End-to-End Tests
# ---------------------------------------------------------

def test_troubleshooting_service_match(tb_service: TroubleshootingService):
    """Test end-to-end troubleshooting for a matched query."""
    response = tb_service.troubleshoot(
        "I have to plug my phone into the wall multiple times throughout the day.",
        debug=True,
    )
    assert len(response.contexts) == 1
    assert response.fallback is None
    ctx = response.contexts[0]
    assert "battery" in ctx.goal.lower() or "drains" in ctx.goal.lower()
    assert ctx.score >= 0.70
    assert len(ctx.actions) > 0

    # Verify action and prototype deeplink
    action = ctx.actions[0]
    assert action.target_screen == "Battery > Battery usage"
    assert action.deeplink == "prototype://settings/battery/battery_usage"
    assert len(action.steps) > 0

    # Verify debug metadata
    assert response.debug_info is not None
    assert response.debug_info.retrieval.decision == "MATCH"
    assert response.debug_info.latency.total_pipeline_ms > 0.0


def test_troubleshooting_service_out_of_scope(tb_service: TroubleshootingService):
    """Test end-to-end troubleshooting for an out-of-scope query."""
    response = tb_service.troubleshoot("Where can I book flight tickets to Tokyo?", debug=True)
    assert len(response.contexts) == 0
    assert response.fallback is not None
    assert "outside this domain" in response.fallback
    assert response.debug_info is not None
    assert response.debug_info.retrieval.decision == "OUT_OF_SCOPE"


# ---------------------------------------------------------
# 5. FastAPI /troubleshoot Endpoint Tests
# ---------------------------------------------------------

def test_endpoint_troubleshoot_success(client: TestClient):
    """Test POST /troubleshoot returns matched troubleshooting context."""
    payload = {"query": "My phone screen is staying lit indefinitely"}
    response = client.post("/troubleshoot", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["contexts"]) == 1
    assert data["fallback"] is None
    context = data["contexts"][0]
    assert "screen stays on" in context["goal"].lower()
    assert len(context["actions"]) > 0
    assert context["actions"][0]["deeplink"].startswith("prototype://")


def test_endpoint_troubleshoot_with_debug(client: TestClient):
    """Test POST /troubleshoot with ?debug=true includes diagnostic metadata."""
    payload = {"query": "My camera photos look blurry"}
    response = client.post("/troubleshoot?debug=true", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["contexts"]) == 1
    assert data["debug_info"] is not None
    assert data["debug_info"]["query_understanding"]["domain"] == "camera"
    assert data["debug_info"]["retrieval"]["decision"] == "MATCH"
    assert "total_pipeline_ms" in data["debug_info"]["latency"]


def test_endpoint_troubleshoot_unsupported_rejection(client: TestClient):
    """Test POST /troubleshoot on unsupported query gracefully returns fallback."""
    payload = {"query": "How do I order pizza using an app?"}
    response = client.post("/troubleshoot", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["contexts"]) == 0
    assert data["fallback"] is not None
    assert "outside this domain" in data["fallback"]
