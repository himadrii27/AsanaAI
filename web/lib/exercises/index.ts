export { createSquat }   from "./squat";
export { createPushUp }  from "./pushup";
export { createWarrior } from "./warrior";
export type { Exercise, ExerciseState, FeedbackItem } from "./types";

import { createSquat }   from "./squat";
import { createPushUp }  from "./pushup";
import { createWarrior } from "./warrior";
import type { Exercise } from "./types";

export const EXERCISE_REGISTRY: Record<string, () => Exercise> = {
  "1": createSquat,
  "2": createPushUp,
  "3": createWarrior,
};

export const EXERCISE_META = [
  { key: "1", label: "Squat",     shortcut: "1" },
  { key: "2", label: "Push-Up",   shortcut: "2" },
  { key: "3", label: "Warrior II",shortcut: "3" },
];
