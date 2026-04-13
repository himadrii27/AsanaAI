import { AngleExtractor } from "../angles";
import { LM, type Landmark } from "../landmarks";
import type { Exercise, FeedbackItem } from "./types";
import { evaluate } from "./utils";

export function createWarrior(): Exercise {
  let holdFrames = 0;

  function checkForm(lms: Landmark[], w: number, h: number): FeedbackItem[] {
    const ae = new AngleExtractor(lms, w, h);
    const lk = ae.leftKnee();
    const rk = ae.rightKnee();
    const items: FeedbackItem[] = [];

    // Rule 1: Front knee (90 deg)
    const lo = 80, hi = 105;
    items.push({
      ruleId:          "front_knee_bend",
      passed:          lo <= lk && lk <= hi,
      message:         lk > hi ? "Bend your front knee to 90 degrees" : "Don't over-bend your front knee",
      weight:          2.5,
      priority:        1,
      jointIdx:        LM.LEFT_KNEE,
      landmarkIndices: [LM.LEFT_HIP, LM.LEFT_KNEE, LM.LEFT_ANKLE],
    });

    // Rule 2: Back leg straight
    items.push({
      ruleId:          "back_leg_straight",
      passed:          rk >= 155,
      message:         "Straighten your back leg",
      weight:          2,
      priority:        2,
      jointIdx:        LM.RIGHT_KNEE,
      landmarkIndices: [LM.RIGHT_HIP, LM.RIGHT_KNEE, LM.RIGHT_ANKLE],
    });

    // Rule 3: Arms extended
    const ls = ae.leftShoulder();
    const rs = ae.rightShoulder();
    const avgArm = (ls + rs) / 2;
    items.push({
      ruleId:          "arms_extended",
      passed:          75 <= avgArm && avgArm <= 110,
      message:         "Extend arms fully - parallel to the floor",
      weight:          1.5,
      priority:        3,
      jointIdx:        LM.LEFT_SHOULDER,
      landmarkIndices: [LM.LEFT_SHOULDER, LM.LEFT_ELBOW, LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW],
    });

    // Rule 4: Torso upright
    const lean = ae.torsoLean();
    items.push({
      ruleId:          "torso_upright",
      passed:          lean <= 20,
      message:         "Keep your torso upright - don't lean forward",
      weight:          2,
      priority:        4,
      jointIdx:        LM.LEFT_HIP,
      landmarkIndices: [LM.LEFT_SHOULDER, LM.LEFT_HIP, LM.RIGHT_SHOULDER, LM.RIGHT_HIP],
    });

    return items;
  }

  return {
    name: "Warrior II",
    key:  "3",
    update(lms, w, h) {
      const items   = checkForm(lms, w, h);
      const result  = evaluate(items, lms);

      if (result.allPassed) holdFrames++;
      else holdFrames = 0;

      const holdSec   = holdFrames / 30;
      const phase     = result.allPassed ? `HOLD ${holdSec.toFixed(1)}s` : "ADJUST";

      return { ...result, repCount: 0, repProgress: 0, phaseLabel: phase };
    },
    reset: () => { holdFrames = 0; },
  };
}
