"""
main.py – FormFix AI entry point
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

import config
from src.core.pose_detector import PoseDetector
from src.exercises.squat        import Squat
from src.exercises.pushup       import PushUp
from src.exercises.warrior_pose import WarriorPose
from src.ui.overlay              import Overlay
from src.utils.voice_feedback    import VoiceFeedback
from src.utils.performance_tracker import PerformanceTracker


# ── Exercise registry ──────────────────────────────────────────────────────────
EXERCISES = {
    "1": Squat,
    "2": PushUp,
    "3": WarriorPose,
}

KEY_MAP = {ord("1"): "1", ord("2"): "2", ord("3"): "3"}


def main() -> None:
    print("\n╔════════════════════════════════════╗")
    print("║       FormFix AI  –  PosePerfect   ║")
    print("╠════════════════════════════════════╣")
    print("║  [1] Squat  [2] Push-Up  [3] Warrior ║")
    print("║  [r] Reset reps   [q] Quit          ║")
    print("╚════════════════════════════════════╝\n")

    # ── Init subsystems ────────────────────────────────────────────────────────
    cap      = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,          config.TARGET_FPS)

    if not cap.isOpened():
        print("[ERROR] Could not open camera. Check CAMERA_INDEX in config.py")
        sys.exit(1)

    detector  = PoseDetector()
    overlay   = Overlay()
    voice     = VoiceFeedback()
    tracker   = PerformanceTracker()

    # ── Initial exercise ───────────────────────────────────────────────────────
    current_key = "1"
    exercise    = EXERCISES[current_key]()
    tracker.start_session(exercise.name)
    history     = tracker.recent_accuracies(exercise.name)

    print(f"[INFO] Starting with: {exercise.name}")

    # ── Main loop ──────────────────────────────────────────────────────────────
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Frame grab failed – retrying…")
            continue

        frame = cv2.flip(frame, 1)   # mirror for natural feel

        # Pose detection
        pose_result = detector.process(frame)

        if pose_result.detected:
            # Run exercise logic
            state = exercise.update(pose_result)

            # Track accuracy
            tracker.record_frame(state.feedback.accuracy)

            # Voice cue (non-blocking)
            if state.voice_cue:
                voice.speak(state.voice_cue)

            # Identify failing joints for red highlights
            failing = [
                item.joint_idx
                for item in state.feedback.items
                if not item.passed and item.joint_idx is not None
            ]

            # Render
            rendered = overlay.render(
                frame          = pose_result.annotated_frame,
                pose_result    = pose_result,
                ex_state       = state,
                exercise_name  = exercise.name,
                history        = history,
                failing_joints = failing,
            )
        else:
            rendered = frame.copy()
            cv2.putText(
                rendered, "No person detected",
                (frame.shape[1] // 2 - 120, frame.shape[0] // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.COLOR_INCORRECT, 2,
            )

        cv2.imshow("FormFix AI – PosePerfect", rendered)

        # ── Key handling ───────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        elif key == ord("r"):
            if hasattr(exercise, "_counter") and exercise._counter:
                exercise._counter.reset()
            print("[INFO] Rep counter reset")

        elif key in KEY_MAP and KEY_MAP[key] != current_key:
            # Save current session
            record = tracker.end_session(
                reps=exercise._counter.count if exercise._counter else 0
            )
            if record:
                print(f"[SESSION] {record.exercise} | "
                      f"reps={record.reps} | avg_acc={record.avg_accuracy}%")

            # Switch exercise
            current_key = KEY_MAP[key]
            exercise    = EXERCISES[current_key]()
            tracker.start_session(exercise.name)
            history     = tracker.recent_accuracies(exercise.name)
            print(f"[INFO] Switched to: {exercise.name}")

    # ── Cleanup ────────────────────────────────────────────────────────────────
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
    detector.release()
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] FormFix AI exited cleanly.")


if __name__ == "__main__":
    main()
