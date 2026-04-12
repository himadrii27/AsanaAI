"""
voice_feedback.py
──────────────────
Non-blocking TTS via a background thread.
Queues cues; speaks them sequentially without stalling the video loop.
"""

from __future__ import annotations

import queue
import threading

import config


class VoiceFeedback:
    """
    Usage
    -----
    vf = VoiceFeedback()
    vf.speak("Straighten your back")
    vf.stop()   # call on app exit
    """

    def __init__(self) -> None:
        self._enabled = config.VOICE_ENABLED
        self._q: queue.Queue[str | None] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def speak(self, text: str) -> None:
        if self._enabled and text:
            self._q.put(text)

    def stop(self) -> None:
        self._q.put(None)   # sentinel to end worker thread

    def _worker(self) -> None:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", config.VOICE_RATE)
            engine.setProperty("volume", 0.9)
        except Exception:
            # If pyttsx3 unavailable, silently degrade
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
