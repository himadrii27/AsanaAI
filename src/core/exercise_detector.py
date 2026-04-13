"""
exercise_detector.py
─────────────────────
Heuristic exercise detector.

Runs every frame alongside the active exercise module.
Does NOT auto-switch exercises — only surfaces a suggestion banner
when it confidently detects a mismatch for >= DETECTION_CONFIRMATION_FRAMES
consecutive frames.

Classification uses three angle features derived from pose landmarks:
  • torso_lean  : inclination of spine from vertical (0 = upright, 90 = horizontal)
  • avg_knee    : mean of left + right knee flexion angles
  • avg_shoulder: mean shoulder abduction (arms raised sideways)

These three features are sufficient to distinguish the three exercises
without any ML training.
"""

from __future__ import annotations

import numpy as np

import config
from src.core.angle_calculator import angle_between, deviation_from_vertical, midpoint
from src.core.pose_detector import LM


# ── Key mapping: exercise key → human label and press-key hint ─────────────────
EXERCISE_LABELS = {
    "1": ("Squat",     "1"),
    "2": ("Push-Up",   "2"),
    "3": ("Warrior II","3"),
}


class ExerciseDetector:
    """
    Usage
    -----
    det = ExerciseDetector()
    suggestion = det.update(landmarks_px, visibility, current_key)
    # suggestion is "" or "Looks like Push-Up? Press [2] to switch"
    """

    def __init__(self) -> None:
        self._candidate_counts: dict[str, int] = {"1": 0, "2": 0, "3": 0}
        self._suggestion = ""

    # ── Public ─────────────────────────────────────────────────────────────────

    def update(
        self,
        landmarks_px: np.ndarray,   # shape (33, 2)
        visibility:   np.ndarray,   # shape (33,)
        current_key:  str,          # "1" | "2" | "3"
    ) -> str:
        """Returns a suggestion string or empty string."""
        features = self._extract_features(landmarks_px, visibility)
        if features is None:
            # Not enough visible landmarks to classify
            return self._suggestion

        classified_key = self._classify(features)

        # Update counters
        for k in self._candidate_counts:
            if k == classified_key:
                self._candidate_counts[k] = min(
                    self._candidate_counts[k] + 1,
                    config.DETECTION_CONFIRMATION_FRAMES * 2,  # cap to avoid overflow
                )
            else:
                # Decay other candidates quickly
                self._candidate_counts[k] = max(0, self._candidate_counts[k] - 2)

        if classified_key is None:
            self._suggestion = ""
            return self._suggestion

        # Only suggest if classified != selected AND confirmed for enough frames
        if (classified_key != current_key and
                self._candidate_counts[classified_key] >= config.DETECTION_CONFIRMATION_FRAMES):
            name, key_hint = EXERCISE_LABELS[classified_key]
            self._suggestion = f"Looks like {name}? Press [{key_hint}] to switch"
        else:
            self._suggestion = ""

        return self._suggestion

    def reset(self) -> None:
        for k in self._candidate_counts:
            self._candidate_counts[k] = 0
        self._suggestion = ""

    # ── Feature extraction ─────────────────────────────────────────────────────

    def _extract_features(
        self,
        px:  np.ndarray,
        vis: np.ndarray,
    ) -> dict[str, float] | None:
        """
        Returns dict with keys: torso_lean, avg_knee, avg_shoulder
        Returns None if required landmarks are not visible enough.
        """
        required = [
            LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER,
            LM.LEFT_HIP,      LM.RIGHT_HIP,
            LM.LEFT_KNEE,     LM.RIGHT_KNEE,
            LM.LEFT_ANKLE,    LM.RIGHT_ANKLE,
        ]
        if any(float(vis[i]) < config.LANDMARK_VISIBILITY_THRESHOLD for i in required):
            return None

        # Torso lean: angle of mid-shoulder -> mid-hip from vertical
        mid_sh  = midpoint(px[LM.LEFT_SHOULDER], px[LM.RIGHT_SHOULDER])
        mid_hip = midpoint(px[LM.LEFT_HIP],      px[LM.RIGHT_HIP])
        torso_lean = deviation_from_vertical(mid_sh, mid_hip)

        # Average knee flexion
        lk = angle_between(px[LM.LEFT_HIP],   px[LM.LEFT_KNEE],  px[LM.LEFT_ANKLE])
        rk = angle_between(px[LM.RIGHT_HIP],  px[LM.RIGHT_KNEE], px[LM.RIGHT_ANKLE])
        avg_knee = (lk + rk) / 2.0

        # Average shoulder abduction (arms raised laterally)
        ls = angle_between(px[LM.LEFT_ELBOW],  px[LM.LEFT_SHOULDER],  px[LM.LEFT_HIP])
        rs = angle_between(px[LM.RIGHT_ELBOW], px[LM.RIGHT_SHOULDER], px[LM.RIGHT_HIP])
        # Check elbow visibility for shoulder feature
        elbow_vis = min(float(vis[LM.LEFT_ELBOW]), float(vis[LM.RIGHT_ELBOW]))
        avg_shoulder = (ls + rs) / 2.0 if elbow_vis >= config.LANDMARK_VISIBILITY_THRESHOLD else 0.0

        return {
            "torso_lean":   torso_lean,
            "avg_knee":     avg_knee,
            "avg_shoulder": avg_shoulder,
        }

    # ── Classifier ─────────────────────────────────────────────────────────────

    def _classify(self, f: dict[str, float]) -> str | None:
        torso = f["torso_lean"]
        knee  = f["avg_knee"]
        sh    = f["avg_shoulder"]

        # Push-Up: body nearly horizontal, legs straight
        if torso > 55 and knee > 155:
            return "2"

        # Squat: upright torso, knees significantly bent
        if torso < 50 and knee < 130:
            return "1"

        # Warrior II: upright, one leg bent + arms extended out
        if torso < 30 and knee < 145 and sh > 70:
            return "3"

        return None
