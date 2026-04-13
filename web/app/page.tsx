"use client";

import { useState, useCallback, useRef } from "react";
import dynamic from "next/dynamic";
import HUD from "@/components/HUD";
import type { ExerciseState, Exercise } from "@/lib/exercises/types";
import { EXERCISE_REGISTRY } from "@/lib/exercises";

// PoseCamera uses webcam + canvas — must be client-only, no SSR
const PoseCamera = dynamic(() => import("@/components/PoseCamera"), { ssr: false });

export default function Home() {
  const [exerciseKey, setExerciseKey] = useState("1");
  const [state, setState]             = useState<ExerciseState | null>(null);
  const [loaded, setLoaded]           = useState(false);
  const [started, setStarted]         = useState(false);

  // Keep a stable Exercise instance per key
  const exerciseRef  = useRef<Exercise>(EXERCISE_REGISTRY["1"]());
  const currentKey   = useRef("1");

  const getExercise = useCallback((key: string): Exercise => {
    if (key !== currentKey.current) {
      exerciseRef.current = EXERCISE_REGISTRY[key]();
      currentKey.current  = key;
    }
    return exerciseRef.current;
  }, []);

  const handleSwitch = useCallback((key: string) => {
    setState(null);
    setExerciseKey(key);
    getExercise(key); // creates new instance
  }, [getExercise]);

  const handleReset = useCallback(() => {
    exerciseRef.current.reset();
    setState(null);
  }, []);

  if (!started) {
    return (
      <main className="flex h-screen items-center justify-center bg-[#0a0a0a]">
        <div className="text-center max-w-md px-6">
          <div className="text-5xl mb-4">🏋️</div>
          <h1 className="text-3xl font-bold text-white mb-2">FormFix AI</h1>
          <p className="text-gray-400 mb-8 text-sm leading-relaxed">
            Real-time posture correction for squats, push-ups, and yoga poses.
            Your webcam stays private — all processing happens in your browser.
          </p>
          <div className="flex flex-col gap-3 text-left text-sm text-gray-400 mb-8 bg-white/5 rounded-xl p-4">
            <div>🟢 <strong className="text-white">Green joints</strong> = correct position</div>
            <div>🔴 <strong className="text-white">Red joints</strong> = needs correction</div>
            <div>🔊 <strong className="text-white">Voice cues</strong> guide you in real time</div>
            <div>📊 <strong className="text-white">Accuracy score</strong> updates every frame</div>
          </div>
          <button
            onClick={() => setStarted(true)}
            className="w-full py-3 rounded-xl bg-orange-500 hover:bg-orange-400 text-black font-bold text-lg transition-all"
          >
            Start Session
          </button>
          <p className="text-xs text-gray-600 mt-3">
            Allow camera access when prompted
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="relative w-screen h-screen overflow-hidden bg-black">
      {/* Loading overlay */}
      {!loaded && (
        <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-black">
          <div className="w-10 h-10 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-gray-400 text-sm">Loading pose model...</p>
        </div>
      )}

      {/* Camera + pose overlay */}
      <PoseCamera
        exercise={getExercise(exerciseKey)}
        onStateUpdate={setState}
        onLoaded={() => setLoaded(true)}
      />

      {/* HUD (arcs, rep counter, exercise selector) */}
      <HUD
        state={state}
        exerciseKey={exerciseKey}
        onSwitch={handleSwitch}
        onReset={handleReset}
      />
    </main>
  );
}
