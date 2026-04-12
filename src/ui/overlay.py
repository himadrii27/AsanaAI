"""
overlay.py
───────────
All OpenCV drawing logic lives here.
Keeps main.py clean and separates rendering from business logic.

Draws:
  • Accuracy score arc
  • Rep counter badge
  • Joint highlight circles (green/red)
  • Feedback cue banner
  • Phase label
  • Mini scoreboard (last 5 session accuracies)
"""

from __future__ import annotations

import math
import cv2
import numpy as np

import config
from src.exercises.base_exercise import ExerciseState
from src.core.feedback_engine import FeedbackResult
from src.core.pose_detector import PoseResult


# ── Helpers ────────────────────────────────────────────────────────────────────

def _put_text_with_bg(
    frame: np.ndarray,
    text:  str,
    org:   tuple[int, int],
    scale: float     = 0.7,
    thick: int       = 2,
    fg:    tuple     = (255, 255, 255),
    bg:    tuple     = config.COLOR_TEXT_BG,
    pad:   int       = 6,
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thick)
    x, y = org
    cv2.rectangle(frame, (x - pad, y - th - pad), (x + tw + pad, y + baseline + pad), bg, -1)
    cv2.putText(frame, text, (x, y), font, scale, fg, thick, cv2.LINE_AA)


def _accuracy_color(acc: float) -> tuple[int, int, int]:
    """Interpolate red → yellow → green based on accuracy."""
    if acc >= 80:
        return config.COLOR_CORRECT
    if acc >= 50:
        return config.COLOR_ACCENT
    return config.COLOR_INCORRECT


# ── Main renderer ──────────────────────────────────────────────────────────────

class Overlay:

    def __init__(self) -> None:
        self._font = cv2.FONT_HERSHEY_SIMPLEX

    def render(
        self,
        frame:          np.ndarray,
        pose_result:    PoseResult,
        ex_state:       ExerciseState,
        exercise_name:  str,
        history:        list[float],   # last N session accuracies
        failing_joints: list[int],
    ) -> np.ndarray:
        out = frame.copy()

        self._draw_joint_highlights(out, pose_result, failing_joints)
        self._draw_accuracy_arc(out, ex_state.feedback.accuracy)
        self._draw_rep_badge(out, ex_state.rep_count, ex_state.rep_progress)
        self._draw_feedback_banner(out, ex_state.feedback)
        self._draw_phase_label(out, ex_state.phase_label)
        self._draw_exercise_name(out, exercise_name)
        self._draw_history(out, history)

        return out

    # ── Private drawing methods ────────────────────────────────────────────────

    def _draw_joint_highlights(
        self,
        frame: np.ndarray,
        pose:  PoseResult,
        failing: list[int],
    ) -> None:
        for idx in range(33):
            px = pose.landmarks_px[idx]
            x, y = int(px[0]), int(px[1])
            color  = config.COLOR_INCORRECT if idx in failing else config.COLOR_CORRECT
            radius = 10 if idx in failing else 5
            cv2.circle(frame, (x, y), radius, color, -1)
            if idx in failing:
                cv2.circle(frame, (x, y), radius + 4, config.COLOR_INCORRECT, 2)

    def _draw_accuracy_arc(self, frame: np.ndarray, accuracy: float) -> None:
        h, w    = frame.shape[:2]
        cx, cy  = w - 80, 80
        radius  = 55
        color   = _accuracy_color(accuracy)

        # Background circle
        cv2.circle(frame, (cx, cy), radius, (50, 50, 50), 6)

        # Accuracy arc
        angle = int(360 * accuracy / 100.0)
        cv2.ellipse(frame, (cx, cy), (radius, radius), -90, 0, angle, color, 6)

        # Text inside arc
        label = f"{int(accuracy)}%"
        (tw, th), _ = cv2.getTextSize(label, self._font, 0.65, 2)
        cv2.putText(
            frame, label,
            (cx - tw // 2, cy + th // 2),
            self._font, 0.65, color, 2, cv2.LINE_AA,
        )
        _put_text_with_bg(frame, "FORM", (cx - 20, cy + radius + 20), scale=0.45)

    def _draw_rep_badge(
        self, frame: np.ndarray, count: int, progress: float
    ) -> None:
        h, w   = frame.shape[:2]
        cx, cy = 80, 80
        radius = 55
        color  = config.COLOR_ACCENT

        cv2.circle(frame, (cx, cy), radius, (50, 50, 50), 6)

        arc_angle = int(360 * progress)
        cv2.ellipse(frame, (cx, cy), (radius, radius), -90, 0, arc_angle, color, 6)

        label = str(count)
        (tw, th), _ = cv2.getTextSize(label, self._font, 1.0, 2)
        cv2.putText(
            frame, label,
            (cx - tw // 2, cy + th // 2),
            self._font, 1.0, config.COLOR_ACCENT, 2, cv2.LINE_AA,
        )
        _put_text_with_bg(frame, "REPS", (cx - 20, cy + radius + 20), scale=0.45)

    def _draw_feedback_banner(
        self, frame: np.ndarray, feedback: FeedbackResult
    ) -> None:
        h, w = frame.shape[:2]

        # Show top-3 rules along the left side
        y_start = h - 160
        for i, item in enumerate(
            sorted(feedback.items, key=lambda x: x.priority)[:4]
        ):
            icon  = "✓" if item.passed else "✗"
            color = config.COLOR_CORRECT if item.passed else config.COLOR_INCORRECT
            text  = f"{icon} {item.message}"
            _put_text_with_bg(frame, text, (10, y_start + i * 35),
                              scale=0.55, thick=1, fg=color)

    def _draw_phase_label(self, frame: np.ndarray, phase: str) -> None:
        h, w = frame.shape[:2]
        _put_text_with_bg(
            frame, phase,
            (w // 2 - 50, 30),
            scale=0.9, thick=2,
            fg=config.COLOR_ACCENT,
        )

    def _draw_exercise_name(self, frame: np.ndarray, name: str) -> None:
        h, w = frame.shape[:2]
        _put_text_with_bg(
            frame, name.upper(),
            (w // 2 - 70, h - 20),
            scale=0.7, thick=2,
            fg=config.COLOR_NEUTRAL,
        )

    def _draw_history(self, frame: np.ndarray, history: list[float]) -> None:
        if not history:
            return
        h, w  = frame.shape[:2]
        bw    = 30
        gap   = 8
        x0    = w - 180
        y_bot = h - 20

        _put_text_with_bg(frame, "HISTORY", (x0, y_bot - 100), scale=0.4, thick=1)
        for i, acc in enumerate(history[-5:]):
            bar_h = int(80 * acc / 100.0)
            x     = x0 + i * (bw + gap)
            color = _accuracy_color(acc)
            cv2.rectangle(frame, (x, y_bot - bar_h), (x + bw, y_bot), color, -1)
            cv2.putText(frame, f"{int(acc)}", (x, y_bot - bar_h - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)
