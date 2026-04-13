"""
squat.py
─────────
Rule-based squat form checker.

Biomechanical rules:
  1. Knee angle <= 110 at bottom phase  (deep enough)
  2. Knees stay over toes  (not caving inward)
  3. Back stays relatively upright  (torso lean < 50)
  4. Shoulders stay level  (no sideways lean)
"""

from __future__ import annotations

from src.core.angle_calculator import AngleExtractor
from src.core.feedback_engine import FeedbackItem
from src.core.pose_detector import LM, PoseResult
from src.core.rep_counter import RepCounter
from src.exercises.base_exercise import BaseExercise, ExerciseState


class Squat(BaseExercise):

    KNEE_DEPTH_THRESH   = 110.0
    TORSO_LEAN_LIMIT    = 50.0
    KNEE_CAVE_RATIO     = 0.80
    SHOULDER_TILT_LIMIT = 10.0

    def __init__(self) -> None:
        super().__init__()
        self._counter = RepCounter(
            down_threshold = 100.0,
            up_threshold   = 165.0,
        )

    @property
    def name(self) -> str:
        return "Squat"

    def _check_form(self, result: PoseResult) -> list[FeedbackItem]:
        ae   = AngleExtractor
        items: list[FeedbackItem] = []

        lk = ae.left_knee(result)
        rk = ae.right_knee(result)
        avg_knee = (lk + rk) / 2.0

        # Rule 1: Squat depth
        items.append(FeedbackItem(
            rule_id          = "squat_depth",
            passed           = avg_knee <= self.KNEE_DEPTH_THRESH or avg_knee >= 150,
            message          = "Lower your hips - squat deeper",
            weight           = 2.0,
            priority         = 1,
            joint_idx        = LM.LEFT_KNEE,
            landmark_indices = [LM.LEFT_HIP, LM.LEFT_KNEE, LM.LEFT_ANKLE,
                                 LM.RIGHT_HIP, LM.RIGHT_KNEE, LM.RIGHT_ANKLE],
        ))

        # Rule 2: Torso upright
        lean = ae.torso_lean(result)
        items.append(FeedbackItem(
            rule_id          = "torso_upright",
            passed           = lean <= self.TORSO_LEAN_LIMIT,
            message          = "Straighten your back - chest up",
            weight           = 2.0,
            priority         = 2,
            joint_idx        = LM.LEFT_SHOULDER,
            landmark_indices = [LM.LEFT_SHOULDER, LM.LEFT_HIP,
                                 LM.RIGHT_SHOULDER, LM.RIGHT_HIP],
        ))

        # Rule 3: Knee cave (valgus)
        lk_px = result.landmarks_px[LM.LEFT_KNEE]
        la_px = result.landmarks_px[LM.LEFT_ANKLE]
        rk_px = result.landmarks_px[LM.RIGHT_KNEE]
        ra_px = result.landmarks_px[LM.RIGHT_ANKLE]
        left_cave  = lk_px[0] > la_px[0] * (2 - self.KNEE_CAVE_RATIO)
        right_cave = rk_px[0] < ra_px[0] * self.KNEE_CAVE_RATIO

        items.append(FeedbackItem(
            rule_id          = "knee_alignment",
            passed           = not (left_cave or right_cave),
            message          = "Push knees out - keep them over toes",
            weight           = 1.5,
            priority         = 3,
            joint_idx        = LM.LEFT_KNEE,
            landmark_indices = [LM.LEFT_KNEE, LM.LEFT_ANKLE,
                                 LM.RIGHT_KNEE, LM.RIGHT_ANKLE],
        ))

        # Rule 4: Shoulder level
        tilt = abs(ae.shoulder_symmetry(result))
        items.append(FeedbackItem(
            rule_id          = "shoulder_level",
            passed           = tilt <= self.SHOULDER_TILT_LIMIT,
            message          = "Keep shoulders level - avoid leaning sideways",
            weight           = 1.0,
            priority         = 4,
            joint_idx        = LM.LEFT_SHOULDER,
            landmark_indices = [LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER],
        ))

        return items

    def update(self, pose_result: PoseResult) -> ExerciseState:
        lk  = AngleExtractor.left_knee(pose_result)
        rk  = AngleExtractor.right_knee(pose_result)
        avg = (lk + rk) / 2.0

        self._counter.update(avg)
        phase    = self._counter.phase.name

        feedback = self._evaluate(pose_result)
        return self._build_state(feedback, phase)
