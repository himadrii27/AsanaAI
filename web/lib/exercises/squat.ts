import { AngleExtractor, midpoint } from "../angles";
import { LM, type Landmark } from "../landmarks";
import { RepCounter } from "../repCounter";
import type { Exercise, ExerciseState, FeedbackItem } from "./types";
import { evaluate } from "./utils";

export function createSquat(): Exercise {
  const counter = new RepCounter(100, 165);

  function checkForm(lms: Landmark[], w: number, h: number): FeedbackItem[] {
    const ae = new AngleExtractor(lms, w, h);
    const lk = ae.leftKnee();
    const rk = ae.rightKnee();
    const avg = (lk + rk) / 2;

    const items: FeedbackItem[] = [];

    // Rule 1: Depth
    items.push({
      ruleId:          "squat_depth",
      passed:          avg <= 110 || avg >= 150,
      message:         "Lower your hips - squat deeper",
      weight:          2,
      priority:        1,
      jointIdx:        LM.LEFT_KNEE,
      landmarkIndices: [LM.LEFT_HIP, LM.LEFT_KNEE, LM.LEFT_ANKLE,
                        LM.RIGHT_HIP, LM.RIGHT_KNEE, LM.RIGHT_ANKLE],
    });

    // Rule 2: Torso upright
    const lean = ae.torsoLean();
    items.push({
      ruleId:          "torso_upright",
      passed:          lean <= 50,
      message:         "Straighten your back - chest up",
      weight:          2,
      priority:        2,
      jointIdx:        LM.LEFT_SHOULDER,
      landmarkIndices: [LM.LEFT_SHOULDER, LM.LEFT_HIP, LM.RIGHT_SHOULDER, LM.RIGHT_HIP],
    });

    // Rule 3: Shoulder level
    const tilt = Math.abs(ae.shoulderSymmetry());
    items.push({
      ruleId:          "shoulder_level",
      passed:          tilt <= 10,
      message:         "Keep shoulders level - avoid leaning sideways",
      weight:          1,
      priority:        3,
      jointIdx:        LM.LEFT_SHOULDER,
      landmarkIndices: [LM.LEFT_SHOULDER, LM.RIGHT_SHOULDER],
    });

    return items;
  }

  return {
    name: "Squat",
    key:  "1",
    update(lms, w, h) {
      const lk  = new AngleExtractor(lms, w, h).leftKnee();
      const rk  = new AngleExtractor(lms, w, h).rightKnee();
      counter.update((lk + rk) / 2);

      const items = checkForm(lms, w, h);
      return {
        ...evaluate(items, lms),
        repCount:    counter.reps,
        repProgress: counter.progress(),
        phaseLabel:  counter.currentPhase,
      };
    },
    reset: () => counter.reset(),
  };
}
