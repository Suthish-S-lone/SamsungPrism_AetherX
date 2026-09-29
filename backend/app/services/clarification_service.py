"""Clarification Engine for SmartGuide Multi-Turn Troubleshooting.

Provides deterministic, grounded ambiguity detection, clarification question formulation,
and diagnostic signal refinement for Phase 6.
"""

import re
import uuid
import time
from typing import Dict, List, Optional, Tuple

from backend.app.models.conversation import (
    ClarificationOption,
    ClarificationQuestion,
    ConversationSession,
    TimelineEvent,
)
from backend.app.models.response import Context
from backend.app.retrieval.types import RetrievalResult
from backend.app.services.query_understanding import QueryUnderstandingResult


# Grounded Clarification Questions Catalog based on the 32 KB records
CLARIFICATION_CATALOG: Dict[str, ClarificationQuestion] = {
    "clarify_battery_heat": ClarificationQuestion(
        id="clarify_battery_heat",
        domain="battery",
        question="When does your phone become warm or hot?",
        prompt="To pinpoint the thermal source, please select when the temperature rise happens:",
        options=[
            ClarificationOption(
                id="opt_heat_normal",
                label="During normal use / reading",
                description="Phone gets warm in hand while doing everyday tasks like reading or browsing",
                signal="normal_use_heat",
                target_problem_id="battery_002",
            ),
            ClarificationOption(
                id="opt_heat_charging",
                label="While plugged into charger",
                description="Device heats up specifically when connected to cable or wireless charger",
                signal="charging_heat",
                target_problem_id="battery_003",
            ),
            ClarificationOption(
                id="opt_heat_app",
                label="When running a specific app or game",
                description="Excessive heat and battery drain triggered by a heavy application",
                signal="app_excessive_battery",
                target_problem_id="battery_005",
            ),
            ClarificationOption(
                id="opt_heat_idle",
                label="Even when locked / idle",
                description="Phone stays warm and loses charge even when resting on a desk",
                signal="idle_battery_drain",
                target_problem_id="battery_004",
            ),
        ],
        reason="Query expresses device heating without specifying whether it occurs during normal use, charging, or idle state.",
    ),
    "clarify_battery_drain": ClarificationQuestion(
        id="clarify_battery_drain",
        domain="battery",
        question="When does the battery drain most noticeably?",
        prompt="To identify what is consuming power, select the pattern that best matches:",
        options=[
            ClarificationOption(
                id="opt_drain_idle",
                label="Overnight or while phone is idle",
                description="Battery percentage drops substantially while you are asleep or screen is locked",
                signal="idle_battery_drain",
                target_problem_id="battery_004",
            ),
            ClarificationOption(
                id="opt_drain_update",
                label="After a recent software update",
                description="Battery life dropped abruptly following a system firmware or OS update",
                signal="software_update_drain",
                target_problem_id="battery_008",
            ),
            ClarificationOption(
                id="opt_drain_app",
                label="When using certain background apps",
                description="A particular app or social media service is chewing up power",
                signal="app_excessive_battery",
                target_problem_id="battery_005",
            ),
            ClarificationOption(
                id="opt_drain_general",
                label="Continuously throughout the day",
                description="General battery life is short and requires charging multiple times daily",
                signal="general_battery_drain",
                target_problem_id="battery_001",
            ),
        ],
        reason="Query mentions rapid drain without distinguishing idle loss, app drain, or update-related depletion.",
    ),
    "clarify_display_issue": ClarificationQuestion(
        id="clarify_display_issue",
        domain="display",
        question="What specific symptom is occurring with your screen?",
        prompt="To find the right display setting, please specify what happens:",
        options=[
            ClarificationOption(
                id="opt_disp_brightness",
                label="Brightness fluctuates on its own",
                description="Screen dims or brightens unexpectedly without you touching the slider",
                signal="brightness_fluctuation",
                target_problem_id="display_009",
            ),
            ClarificationOption(
                id="opt_disp_timeout",
                label="Screen turns off too quickly",
                description="Display goes dark before you finish reading or interacting",
                signal="screen_timeout_short",
                target_problem_id="display_010",
            ),
            ClarificationOption(
                id="opt_disp_touch",
                label="Touch response or gestures feel delayed",
                description="Swipes, navigation gestures, or taps feel unresponsive or laggy",
                signal="touch_delay",
                target_problem_id="display_014",
            ),
            ClarificationOption(
                id="opt_disp_pocket",
                label="Accidental touches inside pocket/bag",
                description="Phone wakes up or dials phantom numbers while in clothing pocket",
                signal="accidental_touch_pocket",
                target_problem_id="display_016",
            ),
        ],
        reason="Display complaint is ambiguous across brightness, timeout, touch response, and accidental touches.",
    ),
    "clarify_camera_issue": ClarificationQuestion(
        id="clarify_camera_issue",
        domain="camera",
        question="What happens when you use or open the camera?",
        prompt="To resolve the camera problem, please select the exact behavior:",
        options=[
            ClarificationOption(
                id="opt_cam_freeze",
                label="Camera app freezes or crashes",
                description="Viewfinder locks up or camera application closes abruptly when recording or taking photos",
                signal="camera_freeze",
                target_problem_id="camera_018",
            ),
            ClarificationOption(
                id="opt_cam_slow",
                label="Camera takes a long time to open",
                description="Noticeable delay or black screen when launching the camera from lock screen or app icon",
                signal="camera_startup_delay",
                target_problem_id="camera_022",
            ),
            ClarificationOption(
                id="opt_cam_blurry",
                label="Photos or videos look blurry / unfocused",
                description="Lens fails to focus sharply or images lack detail",
                signal="blurry_photos",
                target_problem_id="camera_019",
            ),
            ClarificationOption(
                id="opt_cam_storage",
                label="Camera cannot save pictures or videos",
                description="Error saving photos or camera closes due to storage restrictions",
                signal="camera_save_failure",
                target_problem_id="camera_021",
            ),
        ],
        reason="General camera complaint requires disambiguation between freeze, slow startup, focus blur, and storage save errors.",
    ),
    "clarify_performance_issue": ClarificationQuestion(
        id="clarify_performance_issue",
        domain="performance",
        question="When do you notice the performance slowdown most?",
        prompt="To find the right optimization setting, please select when sluggishness happens:",
        options=[
            ClarificationOption(
                id="opt_perf_multitask",
                label="When opening or switching multiple apps",
                description="Lag occurs due to memory/RAM pressure when multitasking",
                signal="memory_pressure",
                target_problem_id="performance_028",
            ),
            ClarificationOption(
                id="opt_perf_appfreeze",
                label="When apps freeze and become unresponsive",
                description="Applications stop responding, show 'Not Responding' dialog, or crash",
                signal="apps_freeze",
                target_problem_id="performance_026",
            ),
            ClarificationOption(
                id="opt_perf_storage",
                label="When internal storage is nearly full",
                description="System slows down because free disk storage space is running low",
                signal="storage_full",
                target_problem_id="performance_027",
            ),
            ClarificationOption(
                id="opt_perf_newapp",
                label="Slowdown began after installing a new app",
                description="Device was fast until a specific new application was installed",
                signal="app_caused_slowdown",
                target_problem_id="performance_032",
            ),
        ],
        reason="Performance slowdown could be caused by RAM memory pressure, app freeze, storage fullness, or newly installed app.",
    ),
}


class ClarificationService:
    """Service detecting domain ambiguity and formulating grounded clarification questions."""

    def __init__(self):
        # In-memory session store (thread-safe session dictionary)
        self._sessions: Dict[str, ConversationSession] = {}

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve an active session by UUID."""
        return self._sessions.get(session_id)

    def reset_session(self, session_id: str) -> Optional[ConversationSession]:
        """Reset an existing session to its initial baseline state."""
        session = self._sessions.get(session_id)
        if session:
            session.turn_count = 1
            session.current_query = session.original_query
            session.clarification_answer_id = None
            session.clarification_answer_label = None
            session.clarification_history = []
            session.selected_problem_id = None
            session.status = "clarification_required" if session.clarification_question else "diagnosis_ready"
            session.updated_at = time.time()
        return session

    def create_session(
        self,
        query: str,
        qu_result: QueryUnderstandingResult,
        status: str = "diagnosis_ready",
        clarification_question: Optional[ClarificationQuestion] = None,
        selected_problem_id: Optional[str] = None,
        confidence: float = 0.0,
        max_turns: int = 3,
    ) -> ConversationSession:
        """Create and store a new multi-turn conversation session."""
        session_id = str(uuid.uuid4())
        now = time.time()
        session = ConversationSession(
            session_id=session_id,
            original_query=query,
            current_query=query,
            domain=qu_result.domain,
            canonical_symptom=qu_result.canonical_symptom,
            extracted_signals=qu_result.extracted_signals,
            turn_count=1,
            max_turns=max_turns,
            clarification_question=clarification_question,
            selected_problem_id=selected_problem_id,
            clarification_history=[],
            confidence=confidence,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self._sessions[session_id] = session
        return session

    def detect_ambiguity(
        self,
        query: str,
        qu_result: QueryUnderstandingResult,
        top_candidates: List[RetrievalResult],
    ) -> Optional[ClarificationQuestion]:
        """Evaluate whether a query has diagnostic ambiguity warranting a clarifying question.

        Rules:
        - If query is out-of-scope or empty: NO clarification.
        - If query matched a specific high-confidence rule (>= 0.90) with explicit condition: NO clarification.
        - If query is vague / ambiguous across known dimensions (heat, general drain, screen acting weird, camera not working, phone slow): Return grounded ClarificationQuestion.
        """
        if qu_result.is_out_of_scope:
            return None

        q_lower = query.lower().strip()

        # 1. Thermal / Heat Ambiguity
        if re.search(r"\b(hot|hott|overheating|overheat|gets\s+hot|heats\s+up|warm|burning|heating|temperature\s+high|temp\s+high)\b", q_lower):
            has_charging = bool(re.search(r"\b(charging|charger|plugged|cable)\b", q_lower))
            has_normal = bool(re.search(r"\b(reading|browsing|normal\s+use|scrolling)\b", q_lower))
            has_idle = bool(re.search(r"\b(idle|standby|overnight|pocket|desk|locked|sitting|resting)\b", q_lower))
            has_app = bool(re.search(r"\b(gaming|game|specific\s+app|youtube|tiktok)\b", q_lower))

            specific_count = sum([has_charging, has_normal, has_idle, has_app])
            if specific_count == 0:
                return CLARIFICATION_CATALOG["clarify_battery_heat"]

        # 2. General Battery Drain Ambiguity
        if re.search(r"\b(battery|batry|charge|power)\b", q_lower) and re.search(r"\b(draining|drain|dies|running\s+out|bad|issue|issues|problem|problems|trouble|troubles|short)\b", q_lower):
            has_fast = bool(re.search(r"\b(fast|rapid|rapidly|quickly|quick)\b", q_lower))
            has_idle = bool(re.search(r"\b(idle|overnight|sleep|standby|morning|sitting|resting)\b", q_lower))
            has_update = bool(re.search(r"\b(update|upgrade|patch|firmware)\b", q_lower))
            has_app = bool(re.search(r"\b(app|application|game|tiktok|instagram)\b", q_lower))
            has_power_save = bool(re.search(r"\b(power\s+saving|battery\s+saver|save\s+power)\b", q_lower))
            has_charge_slow = bool(re.search(r"\b(slow|takes\s+long|hours|cable)\b", q_lower))

            if not any([has_fast, has_idle, has_update, has_app, has_power_save, has_charge_slow]) and len(q_lower.split()) <= 5:
                return CLARIFICATION_CATALOG["clarify_battery_drain"]

        # 3. Display Ambiguity
        if re.search(r"\b(screen|scrn|display)\b", q_lower) and re.search(r"\b(acting\s+weird|problem|problems|issue|issues|trouble|troubles|glitching|wrong|not\s+working)\b", q_lower):
            has_brightness = bool(re.search(r"\b(bright|brightness|dim|dark|sunlight|flicker|flickring)\b", q_lower))
            has_timeout = bool(re.search(r"\b(timeout|turns\s+off|goes\s+dark|sleeps)\b", q_lower))
            has_touch = bool(re.search(r"\b(touch|gesture|swipe|tap|unresponsive)\b", q_lower))
            has_pocket = bool(re.search(r"\b(pocket|bag|phantom|accidental)\b", q_lower))

            if not any([has_brightness, has_timeout, has_touch, has_pocket]):
                return CLARIFICATION_CATALOG["clarify_display_issue"]

        # 4. Camera Ambiguity
        if re.search(r"\b(camera|cam|camra)\b", q_lower) and re.search(r"\b(not\s+working|problem|problems|issue|issues|trouble|troubles|acting\s+up|broken|bad)\b", q_lower):
            has_freeze = bool(re.search(r"\b(freeze|freezes|freezing|crash|crashes|locks\s+up)\b", q_lower))
            has_slow = bool(re.search(r"\b(slow|delay|takes\s+time|startup|lag)\b", q_lower))
            has_blurry = bool(re.search(r"\b(blurry|blur|focus|fuzzy|out\s+of\s+focus)\b", q_lower))
            has_save = bool(re.search(r"\b(save|storage|memory|saving|pictures)\b", q_lower))

            if not any([has_freeze, has_slow, has_blurry, has_save]):
                return CLARIFICATION_CATALOG["clarify_camera_issue"]

        # 5. Performance Ambiguity
        if re.search(r"\b(slow|lag|laggy|sluggish|slowness|speed|slowdown|performance)\b", q_lower) and not re.search(r"\b(camera|charging|download|internet|wifi)\b", q_lower):
            has_freeze = bool(re.search(r"\b(freeze|freezes|freezing|frozen|crash|crashes|locks\s+up)\b", q_lower))
            has_multitask = bool(re.search(r"\b(multiple\s+apps|many\s+apps|switching|multitask|ram|memory)\b", q_lower))
            has_storage = bool(re.search(r"\b(storage|space|disk|full|gb)\b", q_lower))
            has_newapp = bool(re.search(r"\b(after\s+installing|new\s+app|recently\s+downloaded)\b", q_lower))
            has_restart = bool(re.search(r"\b(restarts|reboot)\b", q_lower))
            has_update = bool(re.search(r"\b(update|upgrade|firmware|patch)\b", q_lower))

            if not any([has_freeze, has_multitask, has_storage, has_newapp, has_restart, has_update]) and len(q_lower.split()) <= 5:
                return CLARIFICATION_CATALOG["clarify_performance_issue"]

        return None

    def refine_with_answer(
        self,
        session: ConversationSession,
        answer_id: Optional[str],
        user_response_text: Optional[str] = None,
    ) -> Tuple[str, List[str], Optional[str], bool]:
        """Process user's selected clarification answer and return refined query, signals, target problem ID, and is_irrelevant flag."""
        session.turn_count += 1
        now_ts = time.time()
        question = session.clarification_question

        selected_option: Optional[ClarificationOption] = None
        if answer_id and question:
            for opt in question.options:
                if opt.id == answer_id:
                    selected_option = opt
                    break

        if selected_option:
            session.clarification_answer_id = selected_option.id
            session.clarification_answer_label = selected_option.label
            new_signals = list(set(session.extracted_signals + [selected_option.signal]))
            session.extracted_signals = new_signals

            # Refined query combines original query with explicit option context
            refined_query = f"{session.original_query} {selected_option.label} {selected_option.signal.replace('_', ' ')}"
            session.current_query = refined_query
            session.selected_problem_id = selected_option.target_problem_id
            session.clarification_history.append({
                "turn": session.turn_count,
                "question_id": question.id if question else None,
                "answer_id": selected_option.id,
                "label": selected_option.label,
                "timestamp": now_ts,
            })
            session.updated_at = now_ts
            return refined_query, new_signals, selected_option.target_problem_id, False

        if user_response_text:
            text_clean = user_response_text.strip()
            if not text_clean:
                # Empty or whitespace only follow-up
                session.clarification_history.append({
                    "turn": session.turn_count,
                    "question_id": question.id if question else None,
                    "user_text": "",
                    "timestamp": now_ts,
                })
                session.updated_at = now_ts
                return session.current_query, session.extracted_signals, None, True

            text_lower = text_clean.lower()

            # Check if answer is completely irrelevant / noise
            troubleshooting_keywords = [
                "battery", "charge", "charging", "drain", "power", "hot", "warm", "heat", "overheating",
                "screen", "display", "brightness", "dim", "dark", "flicker", "touch", "pocket", "timeout",
                "camera", "photo", "photos", "picture", "pictures", "video", "record", "lens", "focus", "blur", "blurry",
                "slow", "lag", "laggy", "sluggish", "freeze", "freezes", "freezing", "ram", "memory", "storage", "full", "update"
            ]
            has_domain_keywords = any(kw in text_lower for kw in troubleshooting_keywords)

            # Check for contradictory answer (user corrects the domain/symptom)
            contradicts = False
            contradictory_cues = ["actually", "not", "instead", "fine", "rather", "different", "does not", "doesn't"]
            if any(cue in text_lower for cue in contradictory_cues) and has_domain_keywords:
                contradicts = True

            if not has_domain_keywords and len(text_lower.split()) <= 10:
                # Irrelevant response (e.g. "I like ice cream", "hello who is this")
                session.clarification_history.append({
                    "turn": session.turn_count,
                    "question_id": question.id if question else None,
                    "user_text": text_clean,
                    "is_irrelevant": True,
                    "timestamp": now_ts,
                })
                session.updated_at = now_ts
                return session.original_query, session.extracted_signals, None, True

            session.clarification_answer_label = text_clean
            session.clarification_history.append({
                "turn": session.turn_count,
                "question_id": question.id if question else None,
                "user_text": text_clean,
                "is_contradictory": contradicts,
                "timestamp": now_ts,
            })

            # If user explicitly contradicts, substitute query with new description
            if contradicts:
                refined_query = text_clean
            else:
                refined_query = f"{session.original_query} {text_clean}"

            session.current_query = refined_query
            session.updated_at = now_ts
            return refined_query, session.extracted_signals, None, False

        # No answer provided
        return session.current_query, session.extracted_signals, None, True
