"""
rep_counter.py
───────────────
Generic rep counter that works by tracking an angle signal through
a DOWN → UP → DOWN cycle (or vice-versa for pulling movements).

Uses a small circular buffer for smoothing to avoid false triggers
from noisy landmark predictions.
"""

from __future__ import annotations

from collections import deque
from enum import Enum, auto

import config


class Phase(Enum):
    IDLE = auto()
    DOWN = auto()
    UP   = auto()


class RepCounter:
    """
    Parameters
    ----------
    down_threshold : angle (deg) considered "at bottom" of movement
    up_threshold   : angle (deg) considered "at top"  of movement
    smoothing      : number of frames to average (from config if None)

    Typical squat: down_threshold=100, up_threshold=160
    Typical push-up: down_threshold=90, up_threshold=160
    """

    def __init__(
        self,
        down_threshold: float,
        up_threshold:   float,
        smoothing:      int | None = None,
    ) -> None:
        self.down_threshold = down_threshold
        self.up_threshold   = up_threshold
        self._buf: deque[float] = deque(
            maxlen=smoothing or config.REP_SMOOTHING_FRAMES
        )
        self._phase = Phase.IDLE
        self._count = 0

    # ── Public ─────────────────────────────────────────────────────────────────

    @property
    def count(self) -> int:
        return self._count

    @property
    def phase(self) -> Phase:
        return self._phase

    def update(self, angle: float) -> bool:
        """
        Feed the current frame's joint angle.
        Returns True the moment a full rep is completed.
        """
        self._buf.append(angle)
        smooth = sum(self._buf) / len(self._buf)

        rep_completed = False

        if self._phase == Phase.IDLE:
            if smooth >= self.up_threshold:
                self._phase = Phase.UP

        elif self._phase == Phase.UP:
            if smooth <= self.down_threshold:
                self._phase = Phase.DOWN

        elif self._phase == Phase.DOWN:
            if smooth >= self.up_threshold:
                self._phase = Phase.UP
                self._count += 1
                rep_completed = True

        return rep_completed

    def reset(self) -> None:
        self._count = 0
        self._phase = Phase.IDLE
        self._buf.clear()

    def progress(self) -> float:
        """
        0.0 = at top (start),  1.0 = at bottom (deepest point).
        Useful for drawing a progress arc on-screen.
        """
        if not self._buf:
            return 0.0
        smooth = sum(self._buf) / len(self._buf)
        span   = self.up_threshold - self.down_threshold
        prog   = (self.up_threshold - smooth) / (span + 1e-8)
        return max(0.0, min(1.0, prog))
