"use client";

import { useEffect, useRef, useCallback } from "react";
import { PoseLandmarker, FilesetResolver, DrawingUtils } from "@mediapipe/tasks-vision";
import type { ExerciseState, Exercise } from "@/lib/exercises/types";
import { VoiceFeedback } from "@/lib/voiceFeedback";
import { LM } from "@/lib/landmarks";

const WASM_URL  = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";
const MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";

const COLOR_CORRECT   = "#00dc3c";
const COLOR_INCORRECT = "#ff3c3c";
const COLOR_ACCENT    = "#ffa500";
const COLOR_TEXT_BG   = "rgba(15,15,15,0.75)";

interface Props {
  exercise:       Exercise;
  onStateUpdate:  (s: ExerciseState) => void;
  onLoaded:       () => void;
}

export default function PoseCamera({ exercise, onStateUpdate, onLoaded }: Props) {
  const videoRef     = useRef<HTMLVideoElement>(null);
  const canvasRef    = useRef<HTMLCanvasElement>(null);
  const landmarkerRef= useRef<PoseLandmarker | null>(null);
  const rafRef       = useRef<number>(0);
  const exerciseRef  = useRef<Exercise>(exercise);
  const voiceRef     = useRef(new VoiceFeedback());
  const runningRef   = useRef(false);

  // Keep exerciseRef in sync without restarting the loop
  useEffect(() => { exerciseRef.current = exercise; }, [exercise]);

  const processFrame = useCallback(() => {
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    const lmk    = landmarkerRef.current;

    if (!video || !canvas || !lmk || video.readyState < 2) {
      rafRef.current = requestAnimationFrame(processFrame);
      return;
    }

    // Match canvas to video
    if (canvas.width !== video.videoWidth) {
      canvas.width  = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw mirrored video frame
    ctx.save();
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);
    ctx.restore();

    // Detect pose
    const results = lmk.detectForVideo(video, performance.now());
    const lms     = results.landmarks[0];

    if (lms) {
      // Mirror landmark x-coords for display
      const mirrored = lms.map((l) => ({ ...l, x: 1 - l.x }));

      // Draw skeleton with DrawingUtils on mirrored coords
      const du = new DrawingUtils(ctx);
      du.drawConnectors(mirrored, PoseLandmarker.POSE_CONNECTIONS, {
        color: "rgba(255,255,255,0.35)",
        lineWidth: 2,
      });

      // Run exercise rules (use original landmarks for angle math)
      const ex    = exerciseRef.current;
      const state = ex.update(lms, canvas.width, canvas.height);
      onStateUpdate(state);

      // Draw joint circles — red for failing, green for passing
      const failingSet = new Set(
        state.items.filter((i) => !i.passed && i.jointIdx !== null).map((i) => i.jointIdx!)
      );
      mirrored.forEach((lm, idx) => {
        const x = lm.x * canvas.width;
        const y = lm.y * canvas.height;
        const isFailing = failingSet.has(idx);
        ctx.beginPath();
        ctx.arc(x, y, isFailing ? 9 : 5, 0, Math.PI * 2);
        ctx.fillStyle = isFailing ? COLOR_INCORRECT : COLOR_CORRECT;
        ctx.fill();
        if (isFailing) {
          ctx.beginPath();
          ctx.arc(x, y, 14, 0, Math.PI * 2);
          ctx.strokeStyle = COLOR_INCORRECT;
          ctx.lineWidth   = 2;
          ctx.stroke();
        }
      });

      // Voice feedback
      if (state.topCue && state.topRuleId) {
        state.items.forEach((i) => voiceRef.current.updateRuleState(i.ruleId, !i.passed));
        voiceRef.current.speak(state.topCue, state.topRuleId, state.accuracy);
      }

      // Draw feedback text (bottom-left)
      const sorted = [...state.items].sort((a, b) => a.priority - b.priority).slice(0, 4);
      sorted.forEach((item, i) => {
        const label  = item.passed ? "[OK]" : "[!!]";
        const color  = item.passed ? COLOR_CORRECT : COLOR_INCORRECT;
        const text   = `${label} ${item.message}`;
        const x      = 12;
        const y      = canvas.height - 160 + i * 36;
        ctx.font     = "bold 15px monospace";
        const tw     = ctx.measureText(text).width;
        ctx.fillStyle = COLOR_TEXT_BG;
        ctx.fillRect(x - 4, y - 16, tw + 12, 22);
        ctx.fillStyle = color;
        ctx.fillText(text, x, y);
      });

      // Phase label (top centre)
      drawCentreLabel(ctx, state.phaseLabel, canvas.width / 2, 32, COLOR_ACCENT);
    }

    rafRef.current = requestAnimationFrame(processFrame);
  }, [onStateUpdate]);

  useEffect(() => {
    let stream: MediaStream;

    async function init() {
      // Init MediaPipe
      const filesetResolver = await FilesetResolver.forVisionTasks(WASM_URL);
      landmarkerRef.current = await PoseLandmarker.createFromOptions(filesetResolver, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
        runningMode: "VIDEO",
        numPoses:    1,
      });

      // Init webcam
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, facingMode: "user" },
      });
      const video = videoRef.current!;
      video.srcObject = stream;
      await video.play();

      onLoaded();
      runningRef.current = true;
      rafRef.current = requestAnimationFrame(processFrame);
    }

    init().catch(console.error);

    return () => {
      cancelAnimationFrame(rafRef.current);
      runningRef.current = false;
      stream?.getTracks().forEach((t) => t.stop());
      landmarkerRef.current?.close();
    };
  }, [processFrame, onLoaded]);

  return (
    <div className="relative w-full h-full">
      {/* Hidden video source */}
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover opacity-0 pointer-events-none"
        muted
        playsInline
      />
      {/* Canvas renders both the mirrored video and the overlay */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full object-cover"
      />
    </div>
  );
}

function drawCentreLabel(
  ctx: CanvasRenderingContext2D,
  text: string,
  cx: number,
  y:   number,
  color: string,
) {
  ctx.font      = "bold 22px monospace";
  const tw      = ctx.measureText(text).width;
  ctx.fillStyle = COLOR_TEXT_BG;
  ctx.fillRect(cx - tw / 2 - 10, y - 20, tw + 20, 30);
  ctx.fillStyle = color;
  ctx.fillText(text, cx - tw / 2, y);
}
