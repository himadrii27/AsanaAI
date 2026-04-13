"use client";

import type { ExerciseState } from "@/lib/exercises/types";
import { EXERCISE_META } from "@/lib/exercises";

interface Props {
  state:       ExerciseState | null;
  exerciseKey: string;
  onSwitch:    (key: string) => void;
  onReset:     () => void;
}

const COLOR_CORRECT   = "#00dc3c";
const COLOR_INCORRECT = "#ff3c3c";
const COLOR_ACCENT    = "#ffa500";

function accuracyColor(acc: number) {
  if (acc >= 80) return COLOR_CORRECT;
  if (acc >= 50) return COLOR_ACCENT;
  return COLOR_INCORRECT;
}

function ArcGauge({ value, label }: { value: number; label: string }) {
  const r  = 38;
  const cx = 52;
  const cy = 52;
  const circumference = 2 * Math.PI * r;
  const dash = (value / 100) * circumference;
  const color = accuracyColor(value);

  return (
    <div className="flex flex-col items-center">
      <svg width={104} height={104} className="-rotate-90">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#333" strokeWidth={7} />
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={color}
          strokeWidth={7}
          strokeDasharray={`${dash} ${circumference}`}
          strokeLinecap="round"
        />
      </svg>
      <span className="text-2xl font-bold -mt-16" style={{ color }}>
        {Math.round(value)}%
      </span>
      <span className="text-xs text-gray-400 mt-8">{label}</span>
    </div>
  );
}

function RepBadge({ count, progress }: { count: number; progress: number }) {
  const r   = 38;
  const cx  = 52;
  const cy  = 52;
  const circ = 2 * Math.PI * r;
  const dash = progress * circ;

  return (
    <div className="flex flex-col items-center">
      <svg width={104} height={104} className="-rotate-90">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#333" strokeWidth={7} />
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={COLOR_ACCENT}
          strokeWidth={7}
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
        />
      </svg>
      <span className="text-2xl font-bold -mt-16" style={{ color: COLOR_ACCENT }}>
        {count}
      </span>
      <span className="text-xs text-gray-400 mt-8">REPS</span>
    </div>
  );
}

export default function HUD({ state, exerciseKey, onSwitch, onReset }: Props) {
  return (
    <>
      {/* Top-left: FORM arc */}
      <div className="absolute top-4 left-4 z-20">
        <ArcGauge value={state?.accuracy ?? 0} label="FORM" />
      </div>

      {/* Top-right: REP badge */}
      <div className="absolute top-4 right-4 z-20">
        <RepBadge count={state?.repCount ?? 0} progress={state?.repProgress ?? 0} />
      </div>

      {/* Bottom bar: exercise selector + reset */}
      <div className="absolute bottom-0 left-0 right-0 z-20 flex items-center justify-center gap-3 p-4 bg-black/60 backdrop-blur-sm">
        {EXERCISE_META.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => onSwitch(key)}
            className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
              exerciseKey === key
                ? "bg-orange-500 text-black"
                : "bg-white/10 text-white hover:bg-white/20"
            }`}
          >
            [{key}] {label}
          </button>
        ))}
        <button
          onClick={onReset}
          className="px-4 py-2 rounded-lg text-sm font-bold bg-white/10 text-white hover:bg-white/20"
        >
          [R] Reset
        </button>
      </div>
    </>
  );
}
