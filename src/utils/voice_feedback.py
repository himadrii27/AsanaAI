"""
voice_feedback.py
──────────────────
Platform-aware, non-blocking TTS.

macOS  : uses the built-in `say` command via subprocess.Popen — zero latency,
         natural voice, no library buffering. Any in-progress utterance is
         killed before starting a new one so cues never stack.

Other  : pyttsx3 daemon thread with a size-1 queue (stale cues are dropped).

Both paths enforce a GLOBAL_VOICE_COOLDOWN_S gate to prevent rapid-fire cues
even when multiple per-rule cooldowns expire simultaneously.
"""

from __future__ import annotations

import atexit
import queue
import subprocess
import sys
import threading
import time
from typing import Optional

import config


class VoiceFeedback:
    """
    Usage
    -----
    vf = VoiceFeedback()
    vf.speak("Straighten your back")
    vf.stop()          # call on app exit (also registered with atexit)
    """

    def __init__(self) -> None:
        self._enabled         = config.VOICE_ENABLED
        self._last_voice_time = 0.0          # global cooldown tracker
        self._current_proc: Optional[subprocess.Popen] = None

        if sys.platform == "darwin":
            self._backend = "say"
            atexit.register(self._cleanup_say)
        else:
            self._backend = "pyttsx3"
            self._q: queue.Queue[str | None] = queue.Queue(maxsize=1)
            self._thread = threading.Thread(target=self._pyttsx3_worker, daemon=True)
            self._thread.start()

    # ── Public API ─────────────────────────────────────────────────────────────

    def speak(self, text: str) -> None:
        if not self._enabled or not text:
            return

        # Global cooldown — prevents cue stacking regardless of backend
        now = time.time()
        if now - self._last_voice_time < config.GLOBAL_VOICE_COOLDOWN_S:
            return
        self._last_voice_time = now

        if self._backend == "say":
            self._speak_say(text)
        else:
            self._speak_pyttsx3(text)

    def stop(self) -> None:
        if self._backend == "say":
            self._cleanup_say()
        else:
            try:
                self._q.put_nowait(None)   # sentinel to end worker
            except queue.Full:
                pass

    # ── macOS say backend ──────────────────────────────────────────────────────

    def _speak_say(self, text: str) -> None:
        # Kill any utterance still in progress
        if self._current_proc and self._current_proc.poll() is None:
            self._current_proc.terminate()

        self._current_proc = subprocess.Popen(
            ["say", "-r", str(config.VOICE_RATE), "-v", config.VOICE_NAME_SAY, text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _cleanup_say(self) -> None:
        if self._current_proc and self._current_proc.poll() is None:
            self._current_proc.terminate()

    # ── pyttsx3 backend (non-macOS) ────────────────────────────────────────────

    def _speak_pyttsx3(self, text: str) -> None:
        try:
            self._q.put_nowait(text)
        except queue.Full:
            pass   # drop stale cue; next frame will produce a fresher one

    def _pyttsx3_worker(self) -> None:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate",   config.VOICE_RATE)
            engine.setProperty("volume", 0.9)
        except Exception:
            # pyttsx3 unavailable: drain queue silently
            while True:
                item = self._q.get()
                if item is None:
                    break
            return

        while True:
            text = self._q.get()
            if text is None:
                break
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass
