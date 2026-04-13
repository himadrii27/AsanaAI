import type { Landmark } from "../landmarks";

export interface FeedbackItem {
  ruleId:   string;
  passed:   boolean;
  message:  string;
  weight:   number;
  priority: number;
  jointIdx: number | null;
  landmarkIndices: number[];
}

export interface ExerciseState {
  items:       FeedbackItem[];
  accuracy:    number;          // 0–100
  topCue:      string | null;
  topRuleId:   string | null;
  allPassed:   boolean;
  repCount:    number;
  repProgress: number;          // 0–1
  phaseLabel:  string;
}

export interface Exercise {
  name:    string;
  key:     string;
  update:  (landmarks: Landmark[], width: number, height: number) => ExerciseState;
  reset:   () => void;
}
