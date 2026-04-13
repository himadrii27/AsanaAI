import type { FeedbackItem, ExerciseState } from "./types";
import type { Landmark } from "../landmarks";

const VIS_THRESHOLD = 0.6;

export function evaluate(
  items: FeedbackItem[],
  landmarks: Landmark[],
): Omit<ExerciseState, "repCount" | "repProgress" | "phaseLabel"> {
  // Visibility gate: exclude rules whose joints are below confidence threshold
  const active = items.filter((item) => {
    if (!item.landmarkIndices.length) return true;
    return item.landmarkIndices.every(
      (i) => (landmarks[i]?.visibility ?? 1) >= VIS_THRESHOLD,
    );
  });

  if (!active.length) {
    return { items: [], accuracy: 100, topCue: null, topRuleId: null, allPassed: true };
  }

  const totalWeight  = active.reduce((s, i) => s + i.weight, 0);
  const passedWeight = active.filter((i) => i.passed).reduce((s, i) => s + i.weight, 0);
  const accuracy     = Math.round((100 * passedWeight) / (totalWeight + 1e-8) * 10) / 10;
  const allPassed    = active.every((i) => i.passed);

  const failing = active
    .filter((i) => !i.passed)
    .sort((a, b) => a.priority - b.priority);

  return {
    items:     active,
    accuracy,
    allPassed,
    topCue:    failing[0]?.message  ?? null,
    topRuleId: failing[0]?.ruleId   ?? null,
  };
}
