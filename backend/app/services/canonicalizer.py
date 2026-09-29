"""Canonicalizer and Intent Understanding Service for SmartGuide.

Translates colloquial, idiomatic, or vague natural-language complaints into
standardized technical symptom descriptions grounded in the development knowledge base.
Detects out-of-scope queries and extracts structured signals for downstream retrieval.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CanonicalMatch:
    """Represents a matched canonical symptom mapping."""

    problem_id: str
    domain: str
    canonical_problem: str
    confidence: float
    matched_signals: List[str]
    reasoning: str


# Knowledge Base Grounded Problems (32 Records)
CANONICAL_PROBLEMS: Dict[str, Dict[str, str]] = {
    "battery_001": {
        "domain": "battery",
        "problem": "Battery drains quickly",
        "target_screen": "Battery > Battery usage",
    },
    "battery_002": {
        "domain": "battery",
        "problem": "Device gets hot during normal use",
        "target_screen": "Battery > Battery usage",
    },
    "battery_003": {
        "domain": "battery",
        "problem": "Charging is slower than expected",
        "target_screen": "Battery > Charging",
    },
    "battery_004": {
        "domain": "battery",
        "problem": "Battery drains while the device is idle",
        "target_screen": "Battery > Battery usage",
    },
    "battery_005": {
        "domain": "battery",
        "problem": "An app is consuming excessive battery",
        "target_screen": "Battery > Battery usage",
    },
    "battery_006": {
        "domain": "battery",
        "problem": "Battery percentage drops unusually quickly",
        "target_screen": "Battery > Battery usage",
    },
    "battery_007": {
        "domain": "battery",
        "problem": "Power saving needs to be enabled",
        "target_screen": "Battery > Power saving",
    },
    "battery_008": {
        "domain": "battery",
        "problem": "Battery behavior changed after a software update",
        "target_screen": "Battery > Battery usage",
    },
    "display_009": {
        "domain": "display",
        "problem": "Screen brightness changes unexpectedly",
        "target_screen": "Display > Brightness",
    },
    "display_010": {
        "domain": "display",
        "problem": "Screen turns off too quickly",
        "target_screen": "Display > Screen timeout",
    },
    "display_011": {
        "domain": "display",
        "problem": "Screen stays on longer than expected",
        "target_screen": "Display > Screen timeout",
    },
    "display_012": {
        "domain": "display",
        "problem": "Navigation gestures behave unexpectedly",
        "target_screen": "Display > Navigation",
    },
    "display_013": {
        "domain": "display",
        "problem": "Navigation controls need to be changed",
        "target_screen": "Display > Navigation",
    },
    "display_014": {
        "domain": "display",
        "problem": "Touch interaction feels delayed",
        "target_screen": "Display > Touch settings",
    },
    "display_015": {
        "domain": "display",
        "problem": "Screen appearance needs adjustment",
        "target_screen": "Display > Screen mode",
    },
    "display_016": {
        "domain": "display",
        "problem": "Accidental touches occur when the screen is in a pocket",
        "target_screen": "Display > Accidental touch protection",
    },
    "camera_017": {
        "domain": "camera",
        "problem": "Camera does not open correctly",
        "target_screen": "Camera > Camera settings",
    },
    "camera_018": {
        "domain": "camera",
        "problem": "Camera application freezes",
        "target_screen": "Camera > Camera settings",
    },
    "camera_019": {
        "domain": "camera",
        "problem": "Camera photos look blurry",
        "target_screen": "Camera > Camera settings",
    },
    "camera_020": {
        "domain": "camera",
        "problem": "Camera behavior changed after an update",
        "target_screen": "Camera > Camera settings",
    },
    "camera_021": {
        "domain": "camera",
        "problem": "Camera settings need to be reset",
        "target_screen": "Camera > Camera settings",
    },
    "camera_022": {
        "domain": "camera",
        "problem": "Camera takes too long to start",
        "target_screen": "Camera > Camera settings",
    },
    "camera_023": {
        "domain": "camera",
        "problem": "Camera storage behavior needs checking",
        "target_screen": "Camera > Storage",
    },
    "camera_024": {
        "domain": "camera",
        "problem": "Camera permissions need to be checked",
        "target_screen": "Settings > App permissions > Camera",
    },
    "performance_025": {
        "domain": "performance",
        "problem": "Device becomes slow after a software update",
        "target_screen": "Device care > Performance",
    },
    "performance_026": {
        "domain": "performance",
        "problem": "Apps freeze or become unresponsive",
        "target_screen": "Device care > Memory",
    },
    "performance_027": {
        "domain": "performance",
        "problem": "Device storage is nearly full",
        "target_screen": "Device care > Storage",
    },
    "performance_028": {
        "domain": "performance",
        "problem": "Device has insufficient free memory",
        "target_screen": "Device care > Memory",
    },
    "performance_029": {
        "domain": "performance",
        "problem": "An application causes performance problems",
        "target_screen": "Settings > Apps",
    },
    "performance_030": {
        "domain": "performance",
        "problem": "Device performance is generally sluggish",
        "target_screen": "Device care > Performance",
    },
    "performance_031": {
        "domain": "performance",
        "problem": "Background activity affects performance",
        "target_screen": "Settings > Apps",
    },
    "performance_032": {
        "domain": "performance",
        "problem": "Performance changed after installing an application",
        "target_screen": "Settings > Apps",
    },
}

# Out of scope topic patterns (non-troubleshooting / general knowledge / unsupported domains)
OUT_OF_SCOPE_PATTERNS = [
    r"\bringtone\b",
    r"\bwallpaper\b",
    r"\blanguage\b.*\b(spanish|french|german|chinese|english)\b",
    r"\bprotective case\b|\bcase\b.*\bprotector\b|\bcover\b",
    r"\brain\b|\bweather\b|\bforecast\b|\btemperature in\b",
    r"\brecipe\b|\bcookies\b|\bchocolate chip\b|\bcook\b|\bbake\b",
    r"\bdistance\b.*\b(earth|moon|sun|mars|planet)\b",
    r"\border\b.*\b(pizza|food|burger|delivery)\b|\bpizza\b",
    r"\bbook\b.*\b(flight|tickets|hotel|tokyo|paris)\b|\bflight\b",
    r"\bcoffee stains\b|\bclean\b.*\b(stains|leather|wallet)\b",
    r"\bpoem\b|\bpoetry\b|\bstory\b|\bjoke\b",
    r"\bserial number\b.*\b(box|packaging|retail)\b",
    r"\bcompound interest\b|\bmortgage\b|\bloan\b|\bcalculate\b",
    r"\bmovie\b|\bfilm\b|\bwatch\b|\bhorror\b|\bnetflix\b",
    r"\bpodcast\b|\brss\b|\bfeed url\b",
    r"\bwarranty\b|\binsurance\b|\bpurchase\b.*\b(store|warranty)\b",
    r"\bbluetooth\b.*\b(car|stereo|speaker|spotify)\b|\bpair\b.*\b(car|stereo)\b",
    r"\bexchange rate\b|\bdollars\b|\beuros\b|\bcurrency\b|\bforex\b",
    r"\borigami\b|\bpaper crane\b|\bfold\b",
    r"\bdiet\b|\bvegetarian\b|\bprotein\b|\bmeal plan\b|\bcalories\b",
]


def has_word(pattern: str, text: str) -> bool:
    """Test if regex pattern matches text with word boundary semantics."""
    return bool(re.search(pattern, text, re.IGNORECASE))


class QueryCanonicalizer:
    """Local rule-assisted and pattern-grounded query canonicalizer."""

    def __init__(self):
        self.compiled_oos = [re.compile(p, re.IGNORECASE) for p in OUT_OF_SCOPE_PATTERNS]

    def is_out_of_scope(self, query: str) -> bool:
        """Check if query is outside the scope of device troubleshooting."""
        for pattern in self.compiled_oos:
            if pattern.search(query):
                return True
        return False

    def normalize(self, query: str) -> str:
        """Normalize query by stripping whitespace, lowercasing, and normalizing punctuation."""
        q = query.strip().lower()
        q = re.sub(r"[^\w\s\-\.]", " ", q)
        q = re.sub(r"\s+", " ", q).strip()
        return q

    def canonicalize(self, query: str) -> Optional[CanonicalMatch]:
        """Analyze query and return the best grounded canonical symptom match if identified."""
        if self.is_out_of_scope(query):
            return None

        q = query.lower()

        # ---------------------------------------------------------
        # DOMAIN: BATTERY
        # ---------------------------------------------------------

        # battery_008: Battery behavior changed after a software update
        if (
            has_word(r"\b(after|since|following)\b", q)
            and has_word(r"\b(update|upgrade|patch|firmware|os)\b", q)
            and has_word(r"\b(battery|power|charge|efficiency|drain)\b", q)
        ):
            return CanonicalMatch(
                problem_id="battery_008",
                domain="battery",
                canonical_problem="Battery behavior changed after a software update",
                confidence=0.95,
                matched_signals=["software_update", "battery_degradation"],
                reasoning="Query links battery/power degradation explicitly to a software/firmware update.",
            )

        # battery_004: Battery drains while the device is idle
        if (
            has_word(r"\b(idle|overnight|nightstand|sleep|sleeping|standby|morning|sitting)\b", q)
            and has_word(r"\b(battery|power|charge|drain|fallen|lost|drops|percent)\b", q)
        ):
            return CanonicalMatch(
                problem_id="battery_004",
                domain="battery",
                canonical_problem="Battery drains while the device is idle",
                confidence=0.95,
                matched_signals=["idle_condition", "battery_drain"],
                reasoning="Query describes battery or power level dropping during standby, overnight, or idle state.",
            )

        # battery_007: Power saving needs to be enabled
        if (
            has_word(r"\b(power\s+saving|energy\s+saving|energy\s+conservation|battery\s+saver|save\s+power|conserve\s+power|conserve\s+battery)\b", q)
            or (has_word(r"\b(turn\s+on|enable|activate|how\s+do\s+i)\b", q) and has_word(r"\b(power\s+saving|energy|save\s+charge|lasts\s+until)\b", q))
        ):
            return CanonicalMatch(
                problem_id="battery_007",
                domain="battery",
                canonical_problem="Power saving needs to be enabled",
                confidence=0.95,
                matched_signals=["power_saving_mode", "user_intent"],
                reasoning="Query asks how to enable or configure power saving / energy conservation mode.",
            )

        # battery_003: Charging is slower than expected
        if (
            has_word(r"\b(charging|charge|charger|adapter|cable)\b", q)
            and has_word(r"\b(slow|slower|takes\s+forever|barely\s+gained|fast\s+charging|hours\s+and\s+barely|hours\s+to\s+charge)\b", q)
        ):
            return CanonicalMatch(
                problem_id="battery_003",
                domain="battery",
                canonical_problem="Charging is slower than expected",
                confidence=0.95,
                matched_signals=["slow_charging", "power_adapter"],
                reasoning="Query complains of charging being slow, fast charging failing, or minimal gain over hours.",
            )

        # battery_002: Device gets hot during normal use (exclude screen tint / color warmth)
        if (
            not has_word(r"\b(tint|color|yellowish|warm\s+tint|screen\s+mode)\b", q)
            and has_word(r"\b(hot|overheat|overheating|heats\s+up|burning|thermal|uncomfortably\s+warm|warm\s+back|back\s+panel)\b", q)
            and has_word(r"\b(device|phone|panel|hand|reading|normal\s+use|back)\b", q)
        ):
            return CanonicalMatch(
                problem_id="battery_002",
                domain="battery",
                canonical_problem="Device gets hot during normal use",
                confidence=0.95,
                matched_signals=["device_temperature", "thermal_issue"],
                reasoning="Query indicates physical device warmth, heating, or back panel temperature elevation.",
            )

        # battery_005: An app is consuming excessive battery
        if (
            has_word(r"\b(app|application|program|social\s+media|game)\b", q)
            and has_word(r"\b(chewing|eating|consuming|draining|hogging|using\s+all|uses\s+so\s+much)\b", q)
            and has_word(r"\b(battery|power|charge|juice)\b", q)
        ):
            return CanonicalMatch(
                problem_id="battery_005",
                domain="battery",
                canonical_problem="An app is consuming excessive battery",
                confidence=0.95,
                matched_signals=["app_specific", "excessive_battery_drain"],
                reasoning="Query targets a specific app or background program consuming excessive battery power.",
            )

        # battery_006: Battery percentage drops unusually quickly
        if (
            has_word(r"\b(percentage|percent|indicator|charge\s+indicator)\b", q)
            and has_word(r"\b(tumbled|plummets|suddenly|unusually\s+quickly|in\s+minutes|jumps\s+from|drops\s+from|falls\s+rapidly|sudden\s+drop)\b", q)
        ):
            return CanonicalMatch(
                problem_id="battery_006",
                domain="battery",
                canonical_problem="Battery percentage drops unusually quickly",
                confidence=0.95,
                matched_signals=["percentage_jump", "rapid_depletion"],
                reasoning="Query reports sudden, rapid drop or cliff in battery percentage indicator.",
            )

        # battery_001: Battery drains quickly (general / frequent charging)
        if (
            (has_word(r"\bplug\b", q) and has_word(r"\bwall\b", q) and has_word(r"\bmultiple\s+times\b", q))
            or (has_word(r"\b(runs\s+out|dies|dead|drains|empty)\s+before\b", q) and has_word(r"\b(commute|evening|day|noon|lunch|afternoon|night)\b", q))
            or (
                has_word(r"\b(battery|power|charge|phone)\b", q)
                and has_word(r"\b(drains\s+quickly|draining\s+fast|dies\s+fast|doesn't\s+last|short\s+battery|battery\s+life|runs\s+out\s+fast|depleting\s+quickly|dies\s+before|dies\s+too\s+fast)\b", q)
            )
        ):
            return CanonicalMatch(
                problem_id="battery_001",
                domain="battery",
                canonical_problem="Battery drains quickly",
                confidence=0.92,
                matched_signals=["general_battery_drain", "frequent_charging"],
                reasoning="Query expresses general rapid battery depletion or needing to charge multiple times a day.",
            )

        # ---------------------------------------------------------
        # DOMAIN: DISPLAY
        # ---------------------------------------------------------

        # display_016: Accidental touches occur when the screen is in a pocket
        if (
            has_word(r"\b(pocket|trouser|bag|purse)\b", q)
            and has_word(r"\b(touch|dial|phantom|accidental|emergency|taps)\b", q)
        ) or has_word(r"\baccidental\s+touch\b", q):
            return CanonicalMatch(
                problem_id="display_016",
                domain="display",
                canonical_problem="Accidental touches occur when the screen is in a pocket",
                confidence=0.95,
                matched_signals=["pocket_environment", "accidental_touch"],
                reasoning="Query describes phantom touches, pocket dialing, or accidental screen inputs in pocket.",
            )

        # display_009: Screen brightness changes unexpectedly
        if (
            has_word(r"\b(brightness|dim|dims|flare|flares|illumination|screen\s+light|adaptive\s+brightness)\b", q)
            and has_word(r"\b(randomly|unexpectedly|on\s+its\s+own|changes|fluctuates|unreadable\s+outdoors|too\s+bright|too\s+dark|sensor)\b", q)
        ):
            return CanonicalMatch(
                problem_id="display_009",
                domain="display",
                canonical_problem="Screen brightness changes unexpectedly",
                confidence=0.95,
                matched_signals=["adaptive_brightness", "illumination_changes"],
                reasoning="Query indicates erratic or automatic brightness shifts, outdoor readability, or dimming.",
            )

        # display_010: Screen turns off too quickly
        if (
            has_word(r"\b(screen|display|panel|glass)\b", q)
            and has_word(r"\b(turns\s+off\s+too\s+quickly|goes\s+black\s+almost\s+immediately|locks\s+too\s+fast|sleeps\s+too\s+fast|timeout\s+too\s+short|turns\s+off\s+fast|stop\s+tapping|stops\s+tapping)\b", q)
        ):
            return CanonicalMatch(
                problem_id="display_010",
                domain="display",
                canonical_problem="Screen turns off too quickly",
                confidence=0.95,
                matched_signals=["screen_timeout", "premature_sleep"],
                reasoning="Query complains about screen sleeping, dimming, or turning off too quickly after inactivity.",
            )

        # display_011: Screen stays on longer than expected
        if (
            has_word(r"\b(screen|display|panel|glass)\b", q)
            and has_word(r"\b(stays\s+on|remains\s+fully\s+lit|won't\s+turn\s+off|stays\s+awake|indefinitely|longer\s+than\s+expected|doesn't\s+sleep|staying\s+lit)\b", q)
        ):
            return CanonicalMatch(
                problem_id="display_011",
                domain="display",
                canonical_problem="Screen stays on longer than expected",
                confidence=0.95,
                matched_signals=["screen_timeout", "persistent_awake"],
                reasoning="Query describes display remaining illuminated indefinitely without turning off.",
            )

        # display_012: Navigation gestures behave unexpectedly
        if (
            has_word(r"\b(gesture|gestures|swiping\s+up|swipe\s+navigation|swipe\s+from\s+bottom)\b", q)
            and has_word(r"\b(unresponsive|wrong\s+window|unexpected|behave|not\s+working|glitch)\b", q)
        ):
            return CanonicalMatch(
                problem_id="display_012",
                domain="display",
                canonical_problem="Navigation gestures behave unexpectedly",
                confidence=0.95,
                matched_signals=["navigation_gestures", "gesture_malfunction"],
                reasoning="Query reports gesture navigation glitches, wrong triggers, or swipe unresponsiveness.",
            )

        # display_013: Navigation controls need to be changed
        if (
            has_word(r"\b(navigation|navbar|button\s+layout|navigation\s+bar|three\s+button)\b", q)
            and has_word(r"\b(switch|change|buttons|controls|layout|classic)\b", q)
        ):
            return CanonicalMatch(
                problem_id="display_013",
                domain="display",
                canonical_problem="Navigation controls need to be changed",
                confidence=0.95,
                matched_signals=["navigation_settings", "button_vs_gesture"],
                reasoning="Query asks to switch between button navigation and gesture navigation controls.",
            )

        # display_014: Touch interaction feels delayed
        if (
            has_word(r"\b(touch|tapping|keyboard|typing|finger\s+drag|finger\s+drags|input\s+latency)\b", q)
            and has_word(r"\b(delayed|latency|sluggish|lagging\s+behind|lag|slow\s+response|unresponsive\s+touch)\b", q)
        ):
            return CanonicalMatch(
                problem_id="display_014",
                domain="display",
                canonical_problem="Touch interaction feels delayed",
                confidence=0.95,
                matched_signals=["touch_response", "input_latency"],
                reasoning="Query reports touch screen delay, typing latency, or drag responsiveness lag.",
            )

        # display_015: Screen appearance needs adjustment
        if (
            has_word(r"\b(tint|yellowish|color|colors|vivid|natural|screen\s+mode|eye\s+comfort|display\s+appearance|screen\s+appearance|warm\s+tint|warm\s+under)\b", q)
            and has_word(r"\b(adjustment|adjust|looks|too\s+warm|too\s+yellow|needs|change|lighting|display\s+tint)\b", q)
        ):
            return CanonicalMatch(
                problem_id="display_015",
                domain="display",
                canonical_problem="Screen appearance needs adjustment",
                confidence=0.95,
                matched_signals=["screen_appearance", "color_calibration"],
                reasoning="Query reports screen color tint, warmth, or visual appearance adjustment requirements.",
            )

        # ---------------------------------------------------------
        # DOMAIN: CAMERA
        # ---------------------------------------------------------

        # camera_020: Camera behavior changed after an update
        if (
            has_word(r"\b(after|since|following)\b", q)
            and has_word(r"\b(update|upgrade|patch|firmware|system\s+patch)\b", q)
            and has_word(r"\b(camera|photo|capture|shutter|photography)\b", q)
        ):
            return CanonicalMatch(
                problem_id="camera_020",
                domain="camera",
                canonical_problem="Camera behavior changed after an update",
                confidence=0.95,
                matched_signals=["system_update", "camera_issue"],
                reasoning="Query attributes camera glitches or failure to a recent system patch or software update.",
            )

        # camera_021: Camera settings need to be reset
        if (
            has_word(r"\b(camera|photography\s+app|photo\s+app)\b", q)
            and has_word(r"\b(reset|factory\s+defaults|restore|default\s+settings)\b", q)
        ):
            return CanonicalMatch(
                problem_id="camera_021",
                domain="camera",
                canonical_problem="Camera settings need to be reset",
                confidence=0.95,
                matched_signals=["camera_reset", "factory_defaults"],
                reasoning="Query asks how to reset or restore camera settings to factory defaults.",
            )

        # camera_022: Camera takes too long to start
        if (
            has_word(r"\b(camera|shutter|viewfinder|photography)\b", q)
            and has_word(r"\b(takes\s+too\s+long|five\s+to\s+ten\s+seconds|seconds\s+to\s+appear|slow\s+to\s+open|slow\s+to\s+start|delayed\s+opening|launch\s+takes)\b", q)
        ):
            return CanonicalMatch(
                problem_id="camera_022",
                domain="camera",
                canonical_problem="Camera takes too long to start",
                confidence=0.95,
                matched_signals=["slow_camera_launch", "startup_delay"],
                reasoning="Query highlights excessive latency or delay when opening/launching the camera app.",
            )

        # camera_023: Camera storage behavior needs checking
        if (
            has_word(r"\b(camera|pictures|photos|recordings|video|snapshots)\b", q)
            and has_word(r"\b(storage|filling\s+up|internal\s+drive|sd\s+card|save\s+location|space)\b", q)
        ):
            return CanonicalMatch(
                problem_id="camera_023",
                domain="camera",
                canonical_problem="Camera storage behavior needs checking",
                confidence=0.95,
                matched_signals=["camera_storage", "internal_capacity"],
                reasoning="Query describes camera media storage location or photos consuming excessive storage.",
            )

        # camera_024: Camera permissions need to be checked
        if (
            has_word(r"\b(camera|photo\s+application|lens)\b", q)
            and has_word(r"\b(permission|permissions|access|cannot\s+access|denied|blocked|hardware\s+lens)\b", q)
        ):
            return CanonicalMatch(
                problem_id="camera_024",
                domain="camera",
                canonical_problem="Camera permissions need to be checked",
                confidence=0.95,
                matched_signals=["camera_permissions", "hardware_access"],
                reasoning="Query relates to camera or microphone permissions and access restrictions.",
            )

        # camera_019: Camera photos look blurry
        if (
            has_word(r"\b(photo|photos|pictures|images|snapshot|snapshots|camera)\b", q)
            and has_word(r"\b(blurry|out\s+of\s+focus|soft|fuzzy|muddy|lack\s+sharpness|not\s+sharp|focus\s+issue)\b", q)
        ):
            return CanonicalMatch(
                problem_id="camera_019",
                domain="camera",
                canonical_problem="Camera photos look blurry",
                confidence=0.95,
                matched_signals=["blurry_photos", "focus_quality"],
                reasoning="Query reports blurry, muddy, soft, or out-of-focus camera capture quality.",
            )

        # camera_018: Camera application freezes
        if (
            has_word(r"\b(camera|viewfinder|photography)\b", q)
            and has_word(r"\b(freeze|freezes|locks\s+up|hanging|frozen|unresponsive|lock\s+up)\b", q)
        ):
            return CanonicalMatch(
                problem_id="camera_018",
                domain="camera",
                canonical_problem="Camera application freezes",
                confidence=0.95,
                matched_signals=["camera_freeze", "viewfinder_lockup"],
                reasoning="Query reports camera viewfinder or camera app freezing during use or recording.",
            )

        # camera_017: Camera does not open correctly
        if (
            has_word(r"\b(camera|photography\s+icon|photo\s+app)\b", q)
            and has_word(r"\b(does\s+not\s+open|won't\s+open|cannot\s+open|crashing\s+back|black\s+window|camera\s+failed|fails\s+to\s+open|crashes\s+on\s+launch|closes\s+immediately)\b", q)
        ):
            return CanonicalMatch(
                problem_id="camera_017",
                domain="camera",
                canonical_problem="Camera does not open correctly",
                confidence=0.95,
                matched_signals=["camera_crash", "launch_failure"],
                reasoning="Query describes camera failing to launch, crashing to home, or throwing 'Camera failed' popups.",
            )

        # ---------------------------------------------------------
        # DOMAIN: PERFORMANCE
        # ---------------------------------------------------------

        # performance_025: Device becomes slow after a software update
        if (
            has_word(r"\b(after|since|following)\b", q)
            and has_word(r"\b(update|upgrade|patch|os\s+upgrade|system\s+update)\b", q)
            and has_word(r"\b(slow|sluggish|bogged\s+down|stuttery|lag|performance)\b", q)
        ):
            return CanonicalMatch(
                problem_id="performance_025",
                domain="performance",
                canonical_problem="Device becomes slow after a software update",
                confidence=0.95,
                matched_signals=["os_update", "device_sluggishness"],
                reasoning="Query links broad phone sluggishness or stuttering directly to a recent OS / system update.",
            )

        # performance_032: Performance changed after installing an application
        if (
            has_word(r"\b(after|since|ever\s+since)\b", q)
            and has_word(r"\b(download|install|installing|new\s+app|utility)\b", q)
            and has_word(r"\b(performance|responsiveness|tanked|slow|lag)\b", q)
        ):
            return CanonicalMatch(
                problem_id="performance_032",
                domain="performance",
                canonical_problem="Performance changed after installing an application",
                confidence=0.95,
                matched_signals=["app_installation", "performance_drop"],
                reasoning="Query connects system slowdown or responsiveness drop to installing a specific new application.",
            )

        # performance_027: Device storage is nearly full
        if (
            has_word(r"\b(storage|disk\s+space|internal\s+capacity|drive\s+space|storage\s+capacity)\b", q)
            and has_word(r"\b(full|nearly\s+full|critically\s+low|exhausted|cannot\s+complete|no\s+space|low\s+storage|running\s+out\s+of\s+space)\b", q)
        ):
            return CanonicalMatch(
                problem_id="performance_027",
                domain="performance",
                canonical_problem="Device storage is nearly full",
                confidence=0.95,
                matched_signals=["low_storage", "disk_capacity"],
                reasoning="Query indicates phone internal storage or disk capacity is exhausted or critically low.",
            )

        # performance_028: Device has insufficient free memory
        if (
            has_word(r"\b(ram|memory|multitasking|switching\s+between)\b", q)
            and has_word(r"\b(insufficient|low\s+memory|depleted|forces\s+a\s+reload|killed|free\s+memory|not\s+enough\s+ram|apps\s+reload)\b", q)
        ):
            return CanonicalMatch(
                problem_id="performance_028",
                domain="performance",
                canonical_problem="Device has insufficient free memory",
                confidence=0.95,
                matched_signals=["low_ram", "multitasking_reloads"],
                reasoning="Query identifies RAM depletion, multitasking app reloads, or low memory conditions.",
            )

        # performance_031: Background activity affects performance
        if (
            has_word(r"\b(background|syncing|sync|background\s+process|background\s+tasks)\b", q)
            and has_word(r"\b(activity|hogging|resources|affects\s+performance|slowing|draining\s+performance)\b", q)
        ):
            return CanonicalMatch(
                problem_id="performance_031",
                domain="performance",
                canonical_problem="Background activity affects performance",
                confidence=0.95,
                matched_signals=["background_activity", "resource_consumption"],
                reasoning="Query reports background syncing or background processes consuming system resources.",
            )

        # performance_029: An application causes performance problems
        if (
            has_word(r"\b(game|app|application|program)\b", q)
            and has_word(r"\b(slows\s+to\s+a\s+crawl|causes\s+lag|performance\s+problem|makes\s+system\s+slow|heavy\s+app|causes\s+performance\s+problems)\b", q)
        ):
            return CanonicalMatch(
                problem_id="performance_029",
                domain="performance",
                canonical_problem="An application causes performance problems",
                confidence=0.95,
                matched_signals=["problematic_app", "system_slowdown"],
                reasoning="Query identifies a specific heavy app or game that brings device performance down.",
            )

        # performance_026: Apps freeze or become unresponsive
        if (
            has_word(r"\b(apps|application|programs)\b", q)
            and has_word(r"\b(freeze|freezing|unresponsive|anr|application\s+not\s+responding|lock\s+up|crash\s+frequently)\b", q)
        ):
            return CanonicalMatch(
                problem_id="performance_026",
                domain="performance",
                canonical_problem="Apps freeze or become unresponsive",
                confidence=0.95,
                matched_signals=["app_freeze", "anr_popup"],
                reasoning="Query reports apps throwing Application Not Responding (ANR) popups or freezing.",
            )

        # performance_030: Device performance is generally sluggish
        if (
            has_word(r"\b(sluggish|lag|jank|frame\s+drops|stutter|slow|choppy)\b", q)
            and has_word(r"\b(device|phone|scrolling|menus|system|ui|generally|overall)\b", q)
        ):
            return CanonicalMatch(
                problem_id="performance_030",
                domain="performance",
                canonical_problem="Device performance is generally sluggish",
                confidence=0.92,
                matched_signals=["general_lag", "ui_jank"],
                reasoning="Query describes general interface stutter, frame drops, or system-wide lag.",
            )

        return None
