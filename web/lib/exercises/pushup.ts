import { AngleExtractor, angleBetween, midpoint } from "../angles";
import { LM, type Landmark } from "../landmarks";
import { RepCounter } from "../repCounter";
import type { Exercise, ExerciseState, FeedbackItem } from "./types";
import { evaluate } from "./utils";

export function createPushUp(): Exercise {
  const counter = new RepCounter(90, 155);

  function checkForm(lms: Landmark[], w: number, h: number): FeedbackItem[] {
    const ae = new AngleExtractor(lms, w, h);
    const le = ae.leftElbow();
    const re = ae.rightElbow();
    const avg = (le + re) / 2;

    const toP = (idx: number): [number, number] =>
      [lms[idx].x * w, lms[idx].y * h];

    const items: FeedbackItem[] = [];

    // Rule 1: Depth
    items.push({
      ruleId:          "pushup_depth",
      passed:          avg <= 95 || avg >= 140,
      message:         "Lower your chest - go deeper",
      weight:          2,
      priority:        1,
      jointIdx:        LM.LEFT_ELBOW,
      landmarkIndices: [LM.LEFT_SHOULDER, LM.LEFT_ELBOW, LM.LEFT_WRIST,
                        LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW, LM.RIGHT_WRIST],
    });

    // Rule 2: Plank body line
    const midSh    = midpoint(toP(LM.LEFT_SHOULDER), toP(LM.RIGHT_SHOULDER));
    const midHip   = midpoint(toP(LM.LEFT_HIP),      toP(LM.RIGHT_HIP));
    const midAnkle = midpoint(toP(LM.LEFT_ANKLE),    toP(LM.RIGHT_ANKLE));
    const bodyAngle    = angleBetween(midSh, midHip, midAnkle);
    const plankDev     = Math.abs(180 - bodyAngle);
    items.push({
      ruleId:          "plank_alignment",
      passed:          plankDev <= 20,
      message:         "Keep your body straight - don't sag your hips",
      weight:          2.5,
      priority:        2,
      jointIdx:        LM.LEFT_HIP,
      landmarkIndices: [LM.LEFT_SHOULDER, LM.LEFT_HIP, LM.LEFT_ANKLE,
                        LM.RIGHT_SHOULDER, LM.RIGHT_HIP, LM.RIGHT_ANKLE],
    });

    // Rule 3: Elbow flare
    const leftFlare  = angleBetween(toP(LM.LEFT_HIP),  toP(LM.LEFT_SHOULDER),  toP(LM.LEFT_ELBOW));
    const rightFlare = angleBetween(toP(LM.RIGHT_HIP), toP(LM.RIGHT_SHOULDER), toP(LM.RIGHT_ELBOW));
    items.push({
      ruleId:          "elbow_flare",
      passed:          (leftFlare + rightFlare) / 2 <= 55,
      message:         "Tuck your elbows - keep them closer to your body",
      weight:          1.5,
      priority:        3,
      jointIdx:        LM.LEFT_ELBOW,
      landmarkIndices: [LM.LEFT_SHOULDER, LM.LEFT_ELBOW, LM.RIGHT_SHOULDER, LM.RIGHT_ELBOW],
    });

    return items;
  }

  return {
    name: "Push-Up",
    key:  "2",
    update(lms, w, h) {
      const le = new AngleExtractor(lms, w, h).leftElbow();
      const re = new AngleExtractor(lms, w, h).rightElbow();
      counter.update((le + re) / 2);

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
