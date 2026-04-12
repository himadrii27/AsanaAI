"""
base_exercise.py
─────────────────
Abstract base class every exercise module must implement.
Enforces a consistent interface so main.py can swap exercises
at runtime without any special-casing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.core.pose_detector import PoseResult
from src.core.feedback_engine import FeedbackEngine, FeedbackResult
from src.core.rep_counter import RepCounter


@dataclass
class ExerciseState:
    """Snapshot returned each frame."""
    feedback:   FeedbackResult
    rep_count:  int
    rep_progress: float     # 0.0→1.0 arc for UI
    phase_label: str        # e.g. "DOWN", "UP", "HOLD"
    voice_cue:  str | None  # cue to speak this frame (or None)


class BaseExercise(ABC):
    """
    Subclass this for every exercise.

    Subclasses must implement:
      • name          → display name
      • _check_form() → return list[FeedbackItem]
      • update()      → call super().update() then add rep logic
    """

    def __init__(self) -> None:
        self._engine    = FeedbackEngine()
        self._counter: RepCounter | None = None   # set by subclass

    # ── Contract ───────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def _check_form(self, result: PoseResult) -> list:
        """Return a list of FeedbackItem objects for this frame."""
        ...

    @abstractmethod
    def update(self, pose_result: PoseResult) -> ExerciseState:
        """Process one frame and return ExerciseState."""
        ...

    # ── Helpers for subclasses ─────────────────────────────────────────────────

    def _build_state(
        self,
        feedback:     FeedbackResult,
        phase_label:  str,
    ) -> ExerciseState:
        voice = self._engine.next_voice_cue(feedback) if not feedback.all_passed else None
        if feedback.all_passed:
            # Only say "Great form!" once per session via cooldown trick
            from src.core.feedback_engine import FeedbackItem
            good_item = FeedbackItem(
                rule_id="great_form", passed=True,
                message="Great form! Keep it up.", priority=10
            )
            voice = self._engine.next_voice_cue(
                self._engine.evaluate([good_item])
            )

        return ExerciseState(
            feedback     = feedback,
            rep_count    = self._counter.count if self._counter else 0,
            rep_progress = self._counter.progress() if self._counter else 0.0,
            phase_label  = phase_label,
            voice_cue    = voice,
        )
