"""
warrior_pose.py
────────────────
Yoga Warrior II (Virabhadrasana II) form checker.

Key alignment rules:
  1. Front knee directly above ankle (90 degree bend)
  2. Back leg stays straight (knee > 155)
  3. Arms extended horizontally (shoulder angle 75-110)
  4. Torso upright over hips (minimal lean)
  5. Shoulders level (no sideways tilt)
"""

from __future__ import annotations

from src.core.angle_calculator import AngleExtractor
from src.core.feedback_engine import FeedbackItem
from src.core.pose_detector import LM, PoseResult
from src.exercises.base_exercise import BaseExercise, ExerciseState


class WarriorPose(BaseExercise):

    FRONT_KNEE_TARGET   = (80.0, 105.0)
    BACK_KNEE_MIN       = 155.0
    ARM_ANGLE_TARGET    = (75.0, 110.0)
    TORSO_LEAN_LIMIT    = 20.0
    HIP_TILT_LIMIT      = 15.0

    def __init__(self) -> None:
        super().__init__()
        self._counter     = None
        self._hold_frames = 0

    @property
    def name(self) -> str:
        return "Warrior II"

    def _check_form(self, result: PoseResult) -> list[FeedbackItem]:
        ae    = AngleExtractor
        items: list[FeedbackItem] = []

        lk = ae.left_knee(result)
        rk = ae.right_knee(result)
        front_knee = lk
        back_knee  = rk

        # Rule 1: Front knee angle
        lo, hi = self.FRONT_KNEE_TARGET
        items.append(FeedbackItem(
            rule_id          = "front_knee_bend",
            passed           = lo <= front_knee <= hi,
            message          = "Bend your front knee to 90 degrees" if front_knee > hi else "Don't over-bend your front knee",
            weight           = 2.5,
            priority         = 1,
            joint_idx        = LM.LEFT_KNEE,
            landmark_indices = [LM.LEFT_HIP, LM.LEFT_KNEE, LM.LEFT_ANKLE],
        ))

        # Rule 2: Back leg straight
        items.append(FeedbackItem(
            rule_id          = "back_leg_straight",
            passed           = back_knee >= self.BACK_KNEE_MIN,
            message          = "Straighten your back leg",
            weight           = 2.0,
            priority         = 2,
            joint_idx        = LM.RIGHT_KNEE,
            landmark_indices = [LM.RIGHT_HIP, LM.RIGHT_KNEE, LM.RIGHT_ANKLE],
        ))

        # Rule 3: Arms extended
        ls_angle = ae.left_shoulder(result)
        rs_angle = ae.right_shoulder(result)
        avg_arm  = (ls_angle + rs_angle) / 2.0
        lo, hi   = self.ARM_ANGLE_TARGET
        items.append(FeedbackItem(
            rule_id          = "arms_extended",
            passed           = lo <= avg_arm <= hi,
            message          = "Extend arms fully - parallel to the floor",
            weight           = 1.5,
            priority         = 3,
            joint_idx        = LM.LEFT_SHOULDER,
            landmark_indices = [LM.LEFT_SHOULDER, LM.LEFT_ELBOW,
                                 LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW],
        ))

        # Rule 4: Torso upright
        lean = ae.torso_lean(result)
        items.append(FeedbackItem(
            rule_id          = "torso_upright",
            passed           = lean <= self.TORSO_LEAN_LIMIT,
            message          = "Keep your torso upright - don't lean forward",
            weight           = 2.0,
            priority         = 4,
            joint_idx        = LM.LEFT_HIP,
            landmark_indices = [LM.LEFT_SHOULDER, LM.LEFT_HIP,
                                 LM.RIGHT_SHOULDER, LM.RIGHT_HIP],
        ))

        # Rule 5: Shoulder level
        tilt = abs(ae.shoulder_symmetry(result))
        items.append(FeedbackItem(
            rule_id          = "shoulder_level",
            passed           = tilt <= self.HIP_TILT_LIMIT,
            message          = "Relax your shoulders - keep them level",
            weight           = 1.0,
            priority         = 5,
            joint_idx        = LM.LEFT_SHOULDER,
            landmark_indices = [LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER],
        ))

        return items

    def update(self, pose_result: PoseResult) -> ExerciseState:
        feedback = self._evaluate(pose_result)

        if feedback.all_passed:
            self._hold_frames += 1
        else:
            self._hold_frames = 0

        hold_sec    = self._hold_frames / 30.0
        phase_label = f"HOLD {hold_sec:.1f}s" if feedback.all_passed else "ADJUST"

        return self._build_state(feedback, phase_label)
