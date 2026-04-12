"""
pose_detector.py
────────────────
Thin wrapper around MediaPipe Pose.
Exposes a clean `PoseDetector` class that:
  • Accepts a BGR OpenCV frame
  • Returns normalised & pixel landmarks
  • Draws the built-in skeleton
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

import config


# ── Landmark index constants (MediaPipe's 33-point model) ─────────────────────
class LM:
    NOSE           = 0
    LEFT_EYE       = 2;  RIGHT_EYE      = 5
    LEFT_EAR       = 7;  RIGHT_EAR      = 8
    LEFT_SHOULDER  = 11; RIGHT_SHOULDER = 12
    LEFT_ELBOW     = 13; RIGHT_ELBOW    = 14
    LEFT_WRIST     = 15; RIGHT_WRIST    = 16
    LEFT_HIP       = 23; RIGHT_HIP      = 24
    LEFT_KNEE      = 25; RIGHT_KNEE     = 26
    LEFT_ANKLE     = 27; RIGHT_ANKLE    = 28
    LEFT_HEEL      = 29; RIGHT_HEEL     = 30
    LEFT_FOOT_INDEX= 31; RIGHT_FOOT_INDEX= 32


@dataclass
class PoseResult:
    """Returned from PoseDetector.process()"""
    detected:         bool
    landmarks_norm:   list        # raw mediapipe NormalizedLandmark list
    landmarks_px:     np.ndarray  # shape (33, 2) – pixel (x, y)
    visibility:       np.ndarray  # shape (33,)   – per-landmark confidence
    annotated_frame:  np.ndarray  # frame with skeleton drawn


class PoseDetector:
    """
    Usage
    -----
    detector = PoseDetector()
    result   = detector.process(bgr_frame)
    if result.detected:
        angle = ...
    """

    def __init__(self) -> None:
        self._mp_pose    = mp.solutions.pose
        self._mp_drawing = mp.solutions.drawing_utils
        self._mp_styles  = mp.solutions.drawing_styles

        self._pose = self._mp_pose.Pose(
            model_complexity     = config.MP_MODEL_COMPLEXITY,
            smooth_landmarks     = config.MP_SMOOTH_LANDMARKS,
            min_detection_confidence = config.MP_MIN_DETECTION_CONF,
            min_tracking_confidence  = config.MP_MIN_TRACKING_CONF,
        )

    # ── Public ─────────────────────────────────────────────────────────────────

    def process(self, bgr_frame: np.ndarray) -> PoseResult:
        h, w = bgr_frame.shape[:2]
        rgb   = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        mp_result = self._pose.process(rgb)
        rgb.flags.writeable = True

        annotated = bgr_frame.copy()

        if not mp_result.pose_landmarks:
            return PoseResult(
                detected        = False,
                landmarks_norm  = [],
                landmarks_px    = np.zeros((33, 2), dtype=np.float32),
                visibility      = np.zeros(33, dtype=np.float32),
                annotated_frame = annotated,
            )

        # Draw default skeleton (we'll override colours per-joint in overlay.py)
        self._mp_drawing.draw_landmarks(
            annotated,
            mp_result.pose_landmarks,
            self._mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec = self._mp_styles.get_default_pose_landmarks_style(),
        )

        lms   = mp_result.pose_landmarks.landmark
        px    = np.array([[lm.x * w, lm.y * h]  for lm in lms], dtype=np.float32)
        vis   = np.array([lm.visibility           for lm in lms], dtype=np.float32)

        return PoseResult(
            detected        = True,
            landmarks_norm  = lms,
            landmarks_px    = px,
            visibility      = vis,
            annotated_frame = annotated,
        )

    def get_landmark_px(self, result: PoseResult, idx: int) -> tuple[float, float]:
        """Return (x, y) pixel coords for landmark index idx."""
        return tuple(result.landmarks_px[idx])

    def release(self) -> None:
        self._pose.close()
