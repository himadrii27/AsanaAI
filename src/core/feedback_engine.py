"""
feedback_engine.py
───────────────────
Rule-based feedback engine.

Each exercise module pushes a list of FeedbackItem objects here.
The engine:
  1. Skips rules whose key joints are below visibility threshold (avoids false cues)
  2. Deduplicates and prioritises cues
  3. Throttles repeated voice output via per-rule + global cooldown
  4. Computes an accuracy score (0-100) from rule pass/fail weights
  5. Silences voice when form is already good (>= VOICE_SILENCE_ABOVE_ACCURACY)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

import config


# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class FeedbackItem:
    """
    Represents a single posture rule check.

    Attributes
    ----------
    rule_id          : unique string key for deduplication / cooldown tracking
    passed           : True = rule satisfied (green), False = violated (red)
    message          : human-readable cue shown on screen and spoken aloud
    weight           : contribution to accuracy score (default 1)
    priority         : lower number = higher priority (spoken first)
    joint_idx        : optional landmark index to highlight on the skeleton
    landmark_indices : landmark indices this rule depends on; if any have
                       visibility < LANDMARK_VISIBILITY_THRESHOLD the rule
                       is skipped entirely to avoid false positives
    """
    rule_id:          str
    passed:           bool
    message:          str
    weight:           float     = 1.0
    priority:         int       = 5
    joint_idx:        Optional[int]  = None
    landmark_indices: list[int] = field(default_factory=list)


@dataclass
class FeedbackResult:
    items:      list[FeedbackItem]
    accuracy:   float              # 0.0 - 100.0
    top_cue:    Optional[str]      # most important failing message
    all_passed: bool


# ── Engine ─────────────────────────────────────────────────────────────────────

class FeedbackEngine:
    """
    Usage
    -----
    engine  = FeedbackEngine()
    result  = engine.evaluate(items, visibility)   # returns FeedbackResult
    cue     = engine.next_voice_cue(result)        # returns cue string or None
    """

    def __init__(self) -> None:
        self._last_spoken: dict[str, float] = {}   # rule_id -> timestamp

    def evaluate(
        self,
        items:      list[FeedbackItem],
        visibility: Optional[np.ndarray] = None,   # shape (33,) confidence scores
    ) -> FeedbackResult:
        """
        Parameters
        ----------
        items      : rules produced by _check_form()
        visibility : per-landmark confidence array from MediaPipe (optional).
                     Rules whose landmark_indices contain a joint below
                     LANDMARK_VISIBILITY_THRESHOLD are excluded from scoring.
        """
        if not items:
            return FeedbackResult(items=[], accuracy=100.0,
                                  top_cue=None, all_passed=True)

        # ── Visibility gating ──────────────────────────────────────────────────
        # Rules whose key joints are occluded are excluded entirely so they
        # don't artificially inflate the accuracy score (which would silence voice).
        if visibility is not None:
            items = [
                item for item in items
                if not item.landmark_indices
                or min(float(visibility[i]) for i in item.landmark_indices)
                   >= config.LANDMARK_VISIBILITY_THRESHOLD
            ]

        total_weight  = sum(i.weight for i in items)
        passed_weight = sum(i.weight for i in items if i.passed)

        accuracy   = 100.0 * passed_weight / (total_weight + 1e-8)
        all_passed = all(i.passed for i in items)

        failing = sorted(
            (i for i in items if not i.passed),
            key=lambda i: i.priority,
        )
        top_cue = failing[0].message if failing else None

        return FeedbackResult(
            items      = items,
            accuracy   = round(accuracy, 1),
            top_cue    = top_cue,
            all_passed = all_passed,
        )

    def next_voice_cue(self, result: FeedbackResult) -> Optional[str]:
        """
        Returns the top failing cue if:
          1. Form is below VOICE_SILENCE_ABOVE_ACCURACY (no cues during good form)
          2. Per-rule cooldown (FEEDBACK_COOLDOWN_SEC) has expired
        """
        # Silence when form is good
        if result.accuracy >= config.VOICE_SILENCE_ABOVE_ACCURACY:
            return None

        if result.top_cue is None:
            return None

        item = next(
            (i for i in result.items
             if i.message == result.top_cue and not i.passed),
            None,
        )
        if item is None:
            return None

        now      = time.time()
        last     = self._last_spoken.get(item.rule_id, 0.0)
        cooldown = config.FEEDBACK_COOLDOWN_SEC

        if now - last >= cooldown:
            self._last_spoken[item.rule_id] = now
            return result.top_cue

        return None

    def failing_joint_indices(self, result: FeedbackResult) -> list[int]:
        """Landmark indices for joints that have failing rules."""
        return [
            i.joint_idx for i in result.items
            if not i.passed and i.joint_idx is not None
        ]
