"""
pushup.py
──────────
Rule-based push-up form checker.

Biomechanical rules:
  1. Elbow angle <= 95 at bottom (full range of motion)
  2. Body plank - hips must stay inline with shoulders and ankles
  3. Elbow flare - elbows should not flare out beyond 55 degrees from body
  4. Head neutral - nose not too far above/below shoulder line
"""

from __future__ import annotations

import numpy as np

from src.core.angle_calculator import AngleExtractor, angle_between, midpoint
from src.core.feedback_engine import FeedbackItem
from src.core.pose_detector import LM, PoseResult
from src.core.rep_counter import RepCounter
from src.exercises.base_exercise import BaseExercise, ExerciseState


class PushUp(BaseExercise):

    ELBOW_DEPTH_THRESH = 95.0
    PLANK_DEVIATION    = 20.0
    ELBOW_FLARE_MAX    = 55.0

    def __init__(self) -> None:
        super().__init__()
        self._counter = RepCounter(
            down_threshold = 90.0,
            up_threshold   = 155.0,
        )

    @property
    def name(self) -> str:
        return "Push-Up"

    def _check_form(self, result: PoseResult) -> list[FeedbackItem]:
        ae    = AngleExtractor
        items: list[FeedbackItem] = []
        px    = result.landmarks_px

        le = ae.left_elbow(result)
        re = ae.right_elbow(result)
        avg_elbow = (le + re) / 2.0

        # Rule 1: Depth
        items.append(FeedbackItem(
            rule_id          = "pushup_depth",
            passed           = avg_elbow <= self.ELBOW_DEPTH_THRESH or avg_elbow >= 140,
            message          = "Lower your chest - go deeper",
            weight           = 2.0,
            priority         = 1,
            joint_idx        = LM.LEFT_ELBOW,
            landmark_indices = [LM.LEFT_SHOULDER, LM.LEFT_ELBOW, LM.LEFT_WRIST,
                                 LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW, LM.RIGHT_WRIST],
        ))

        # Rule 2: Plank body line
        mid_shoulder = midpoint(px[LM.LEFT_SHOULDER], px[LM.RIGHT_SHOULDER])
        mid_hip      = midpoint(px[LM.LEFT_HIP],      px[LM.RIGHT_HIP])
        mid_ankle    = midpoint(px[LM.LEFT_ANKLE],    px[LM.RIGHT_ANKLE])
        body_line_angle = angle_between(mid_shoulder, mid_hip, mid_ankle)
        plank_deviation = abs(180.0 - body_line_angle)

        items.append(FeedbackItem(
            rule_id          = "plank_alignment",
            passed           = plank_deviation <= self.PLANK_DEVIATION,
            message          = "Keep your body in a straight line - don't sag your hips",
            weight           = 2.5,
            priority         = 2,
            joint_idx        = LM.LEFT_HIP,
            landmark_indices = [LM.LEFT_SHOULDER, LM.LEFT_HIP, LM.LEFT_ANKLE,
                                 LM.RIGHT_SHOULDER, LM.RIGHT_HIP, LM.RIGHT_ANKLE],
        ))

        # Rule 3: Elbow flare
        left_flare  = angle_between(px[LM.LEFT_HIP],  px[LM.LEFT_SHOULDER],  px[LM.LEFT_ELBOW])
        right_flare = angle_between(px[LM.RIGHT_HIP], px[LM.RIGHT_SHOULDER], px[LM.RIGHT_ELBOW])
        avg_flare   = (left_flare + right_flare) / 2.0

        items.append(FeedbackItem(
            rule_id          = "elbow_flare",
            passed           = avg_flare <= self.ELBOW_FLARE_MAX,
            message          = "Tuck your elbows - keep them closer to your body",
            weight           = 1.5,
            priority         = 3,
            joint_idx        = LM.LEFT_ELBOW,
            landmark_indices = [LM.LEFT_SHOULDER, LM.LEFT_ELBOW,
                                 LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW],
        ))

        # Rule 4: Head neutral
        nose      = px[LM.NOSE]
        mid_sh_y  = mid_shoulder[1]
        head_drop = abs(nose[1] - mid_sh_y)
        frame_h   = result.landmarks_px.max()
        items.append(FeedbackItem(
            rule_id          = "head_neutral",
            passed           = head_drop / (frame_h + 1e-8) < 0.08,
            message          = "Keep your head neutral - don't drop your chin",
            weight           = 1.0,
            priority         = 4,
            joint_idx        = LM.NOSE,
            landmark_indices = [LM.NOSE, LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER],
        ))

        return items

    def update(self, pose_result: PoseResult) -> ExerciseState:
        le  = AngleExtractor.left_elbow(pose_result)
        re  = AngleExtractor.right_elbow(pose_result)
        avg = (le + re) / 2.0

        self._counter.update(avg)
        phase    = self._counter.phase.name

        feedback = self._evaluate(pose_result)
        return self._build_state(feedback, phase)
