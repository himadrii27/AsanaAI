"""
angle_calculator.py
────────────────────
Pure maths for extracting biomechanically meaningful angles
from a set of 2D pose landmarks.

All public functions take numpy (x, y) arrays and return degrees.
"""

from __future__ import annotations
import numpy as np
from src.core.pose_detector import LM, PoseResult


# ── Primitives ─────────────────────────────────────────────────────────────────

def angle_between(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """
    Interior angle (degrees) at vertex *b* formed by segments b→a and b→c.
    Returns a value in [0, 180].
    """
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def deviation_from_vertical(a: np.ndarray, b: np.ndarray) -> float:
    """Angle (degrees) that segment a→b makes with the vertical axis."""
    vec  = b - a
    vert = np.array([0.0, 1.0])
    cos  = np.dot(vec, vert) / (np.linalg.norm(vec) + 1e-8)
    return float(np.degrees(np.arccos(np.clip(abs(cos), 0.0, 1.0))))


def midpoint(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (a + b) / 2.0


# ── High-level extractors (use PoseResult directly) ────────────────────────────

def _p(result: PoseResult, idx: int) -> np.ndarray:
    """Shorthand: landmark pixel coords as numpy array."""
    return result.landmarks_px[idx]


class AngleExtractor:
    """
    Stateless helper that pulls named angles from a PoseResult.
    All returned values are in degrees (floats).
    """

    # ── Lower body ─────────────────────────────────────────────────────────────

    @staticmethod
    def left_knee(r: PoseResult) -> float:
        return angle_between(_p(r, LM.LEFT_HIP), _p(r, LM.LEFT_KNEE), _p(r, LM.LEFT_ANKLE))

    @staticmethod
    def right_knee(r: PoseResult) -> float:
        return angle_between(_p(r, LM.RIGHT_HIP), _p(r, LM.RIGHT_KNEE), _p(r, LM.RIGHT_ANKLE))

    @staticmethod
    def left_hip(r: PoseResult) -> float:
        return angle_between(_p(r, LM.LEFT_SHOULDER), _p(r, LM.LEFT_HIP), _p(r, LM.LEFT_KNEE))

    @staticmethod
    def right_hip(r: PoseResult) -> float:
        return angle_between(_p(r, LM.RIGHT_SHOULDER), _p(r, LM.RIGHT_HIP), _p(r, LM.RIGHT_KNEE))

    # ── Upper body ─────────────────────────────────────────────────────────────

    @staticmethod
    def left_elbow(r: PoseResult) -> float:
        return angle_between(_p(r, LM.LEFT_SHOULDER), _p(r, LM.LEFT_ELBOW), _p(r, LM.LEFT_WRIST))

    @staticmethod
    def right_elbow(r: PoseResult) -> float:
        return angle_between(_p(r, LM.RIGHT_SHOULDER), _p(r, LM.RIGHT_ELBOW), _p(r, LM.RIGHT_WRIST))

    @staticmethod
    def left_shoulder(r: PoseResult) -> float:
        return angle_between(_p(r, LM.LEFT_ELBOW), _p(r, LM.LEFT_SHOULDER), _p(r, LM.LEFT_HIP))

    @staticmethod
    def right_shoulder(r: PoseResult) -> float:
        return angle_between(_p(r, LM.RIGHT_ELBOW), _p(r, LM.RIGHT_SHOULDER), _p(r, LM.RIGHT_HIP))

    # ── Spine / trunk ──────────────────────────────────────────────────────────

    @staticmethod
    def torso_lean(r: PoseResult) -> float:
        """Deviation of the spine (mid-shoulder → mid-hip) from vertical."""
        mid_shoulder = midpoint(_p(r, LM.LEFT_SHOULDER), _p(r, LM.RIGHT_SHOULDER))
        mid_hip      = midpoint(_p(r, LM.LEFT_HIP),      _p(r, LM.RIGHT_HIP))
        return deviation_from_vertical(mid_shoulder, mid_hip)

    @staticmethod
    def shoulder_symmetry(r: PoseResult) -> float:
        """
        Tilt of the shoulder line from horizontal (0° = level).
        Positive means left shoulder is higher.
        """
        ls = _p(r, LM.LEFT_SHOULDER)
        rs = _p(r, LM.RIGHT_SHOULDER)
        delta_y = rs[1] - ls[1]
        delta_x = rs[0] - ls[0] + 1e-8
        return float(np.degrees(np.arctan2(delta_y, delta_x)))

    # ── Convenience bundle ─────────────────────────────────────────────────────

    @staticmethod
    def all_angles(r: PoseResult) -> dict[str, float]:
        ae = AngleExtractor
        return {
            "left_knee":          ae.left_knee(r),
            "right_knee":         ae.right_knee(r),
            "left_hip":           ae.left_hip(r),
            "right_hip":          ae.right_hip(r),
            "left_elbow":         ae.left_elbow(r),
            "right_elbow":        ae.right_elbow(r),
            "left_shoulder":      ae.left_shoulder(r),
            "right_shoulder":     ae.right_shoulder(r),
            "torso_lean":         ae.torso_lean(r),
            "shoulder_symmetry":  ae.shoulder_symmetry(r),
        }
