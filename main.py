"""
main.py - FormFix AI entry point
──────────────────────────────────
Runs the real-time posture correction loop.

Controls
--------
  [1]  Switch to Squat
  [2]  Switch to Push-Up
  [3]  Switch to Warrior II
  [r]  Reset rep counter
  [q]  Quit and save session
"""

from __future__ import annotations

import sys
import cv2
import numpy as np

import config
from src.core.pose_detector import PoseDetector
from src.core.exercise_detector import ExerciseDetector
from src.exercises.squat        import Squat
from src.exercises.pushup       import PushUp
from src.exercises.warrior_pose import WarriorPose
from src.ui.overlay              import Overlay
from src.utils.voice_feedback    import VoiceFeedback
from src.utils.performance_tracker import PerformanceTracker


EXERCISES = {
    "1": Squat,
    "2": PushUp,
    "3": WarriorPose,
}

KEY_MAP = {ord("1"): "1", ord("2"): "2", ord("3"): "3"}


def _draw_suggestion(frame: np.ndarray, text: str) -> None:
    """Semi-transparent banner at the bottom of the frame."""
    if not text:
        return
    h, w   = frame.shape[:2]
    font   = cv2.FONT_HERSHEY_SIMPLEX
    scale  = 0.65
    thick  = 2
    (tw, th), _ = cv2.getTextSize(text, font, scale, thick)
    pad    = 10
    x      = (w - tw) // 2
    y      = h - 60

    # Translucent background
    overlay_layer = frame.copy()
    cv2.rectangle(overlay_layer,
                  (x - pad, y - th - pad),
                  (x + tw + pad, y + pad),
                  (20, 20, 20), -1)
    cv2.addWeighted(overlay_layer, 0.7, frame, 0.3, 0, frame)

    cv2.putText(frame, text, (x, y), font, scale,
                config.COLOR_ACCENT, thick, cv2.LINE_AA)


def main() -> None:
    print("\n+====================================+")
    print("|       FormFix AI  -  PosePerfect   |")
    print("+====================================+")
    print("|  [1] Squat  [2] Push-Up  [3] Warrior |")
    print("|  [r] Reset reps   [q] Quit          |")
    print("+====================================+\n")

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,          config.TARGET_FPS)

    if not cap.isOpened():
        print("[ERROR] Could not open camera. Check CAMERA_INDEX in config.py")
        sys.exit(1)

    pose_detector    = PoseDetector()
    ex_detector      = ExerciseDetector()
    overlay          = Overlay()
    voice            = VoiceFeedback()
    tracker          = PerformanceTracker()

    current_key = "1"
    exercise    = EXERCISES[current_key]()
    tracker.start_session(exercise.name)
    history     = tracker.recent_accuracies(exercise.name)

    print(f"[INFO] Starting with: {exercise.name}")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame       = cv2.flip(frame, 1)
        pose_result = pose_detector.process(frame)

        if pose_result.detected:
            # Run exercise logic (visibility gating handled inside)
            state = exercise.update(pose_result)

            tracker.record_frame(state.feedback.accuracy)

            # Voice - non-blocking (VoiceFeedback enforces global cooldown)
            if state.voice_cue:
                voice.speak(state.voice_cue)

            # Exercise mismatch detection
            suggestion = ex_detector.update(
                pose_result.landmarks_px,
                pose_result.visibility,
                current_key,
            )

            failing = [
                item.joint_idx
                for item in state.feedback.items
                if not item.passed and item.joint_idx is not None
            ]

            rendered = overlay.render(
                frame          = pose_result.annotated_frame,
                pose_result    = pose_result,
                ex_state       = state,
                exercise_name  = exercise.name,
                history        = history,
                failing_joints = failing,
            )

            _draw_suggestion(rendered, suggestion)

        else:
            rendered = frame.copy()
            cv2.putText(
                rendered, "No person detected - step into frame",
                (50, frame.shape[0] // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, config.COLOR_INCORRECT, 2,
            )

        cv2.imshow("FormFix AI - PosePerfect", rendered)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        elif key == ord("r"):
            if exercise._counter:
                exercise._counter.reset()
            ex_detector.reset()
            print("[INFO] Rep counter reset")

        elif key in KEY_MAP and KEY_MAP[key] != current_key:
            record = tracker.end_session(
                reps=exercise._counter.count if exercise._counter else 0
            )
            if record:
                print(f"[SESSION] {record.exercise} | "
                      f"reps={record.reps} | avg_acc={record.avg_accuracy}%")

            current_key = KEY_MAP[key]
            exercise    = EXERCISES[current_key]()
            ex_detector.reset()
            tracker.start_session(exercise.name)
            history     = tracker.recent_accuracies(exercise.name)
            print(f"[INFO] Switched to: {exercise.name}")

    # Cleanup
    record = tracker.end_session(
        reps=exercise._counter.count if exercise._counter else 0
    )
    if record:
        print(f"\n[SESSION SAVED]")
        print(f"  Exercise     : {record.exercise}")
        print(f"  Reps         : {record.reps}")
        print(f"  Avg Accuracy : {record.avg_accuracy}%")
        print(f"  Peak Accuracy: {record.peak_accuracy}%")

    voice.stop()
    pose_detector.release()
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] FormFix AI exited cleanly.")


if __name__ == "__main__":
    main()
