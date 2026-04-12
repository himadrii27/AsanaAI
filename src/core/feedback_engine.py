"""
feedback_engine.py
───────────────────
Rule-based feedback engine.

Each exercise module pushes a list of FeedbackItem objects here.
The engine:
  1. Deduplicates and prioritises cues
  2. Throttles repeated voice output via a cooldown timer
  3. Computes an accuracy score (0–100) from rule pass/fail weights
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import config


# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class FeedbackItem:
    """
    Represents a single posture rule check.

    Attributes
    ----------
    rule_id    : unique string key for deduplication / cooldown tracking
    passed     : True  → rule satisfied  (show in green)
                 False → rule violated   (show in red)
    message    : human-readable cue shown on screen and spoken aloud
    weight     : how much this rule contributes to the accuracy score (default 1)
    priority   : lower number = higher priority (spoken first)
    joint_idx  : optional landmark index to highlight on the skeleton
    """
    rule_id:   str
    passed:    bool
    message:   str
    weight:    float = 1.0
    priority:  int   = 5
    joint_idx: Optional[int] = None


@dataclass
class FeedbackResult:
    items:         list[FeedbackItem]
    accuracy:      float              # 0.0 – 100.0
    top_cue:       Optional[str]      # most important failing message
    all_passed:    bool


# ── Engine ─────────────────────────────────────────────────────────────────────

class FeedbackEngine:
    """
    Usage
    -----
    engine  = FeedbackEngine()
    result  = engine.evaluate(items)          # returns FeedbackResult
    cue     = engine.next_voice_cue(result)   # returns cue string or None
    """

    def __init__(self) -> None:
        self._last_spoken: dict[str, float] = {}   # rule_id → timestamp

    def evaluate(self, items: list[FeedbackItem]) -> FeedbackResult:
        if not items:
            return FeedbackResult(items=[], accuracy=100.0,
                                  top_cue=None, all_passed=True)

        total_weight  = sum(i.weight for i in items)
        passed_weight = sum(i.weight for i in items if i.passed)

        accuracy   = 100.0 * passed_weight / (total_weight + 1e-8)
        all_passed = all(i.passed for i in items)

        # highest-priority failing rule (lowest priority number)
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
        Returns the top failing cue if its cooldown has expired, else None.
        Internally records the timestamp so the same cue is not repeated
        too rapidly (configurable via FEEDBACK_COOLDOWN_SEC).
        """
        if result.top_cue is None:
            return None

        # find the matching item to get its rule_id
        item = next(
            (i for i in result.items
             if i.message == result.top_cue and not i.passed),
            None,
        )
        if item is None:
            return None

        now     = time.time()
        last    = self._last_spoken.get(item.rule_id, 0.0)
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
