"""
performance_tracker.py
───────────────────────
Persists per-session stats to JSON files in data/sessions/.
Provides a lightweight history API for the overlay and future dashboard.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import config


@dataclass
class SessionRecord:
    exercise:   str
    start_ts:   float
    end_ts:     float
    reps:       int
    avg_accuracy: float
    peak_accuracy: float
    min_accuracy:  float
    frame_count:   int
    accuracy_log:  list[float] = field(default_factory=list)  # per-frame samples


class PerformanceTracker:
    """
    Usage
    -----
    tracker = PerformanceTracker()
    tracker.start_session("Squat")
    tracker.record_frame(accuracy=87.5)
    record = tracker.end_session(reps=12)
    history = tracker.load_history(exercise="Squat", limit=10)
    """

    def __init__(self) -> None:
        self._sessions_dir = Path(config.SESSIONS_DIR)
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

        self._active: Optional[dict] = None

    # ── Session lifecycle ──────────────────────────────────────────────────────

    def start_session(self, exercise: str) -> None:
        self._active = {
            "exercise":     exercise,
            "start_ts":     time.time(),
            "accuracy_log": [],
        }

    def record_frame(self, accuracy: float) -> None:
        if self._active:
            self._active["accuracy_log"].append(round(accuracy, 2))

    def end_session(self, reps: int) -> Optional[SessionRecord]:
        if not self._active:
            return None

        log  = self._active["accuracy_log"]
        avg  = sum(log) / len(log) if log else 0.0
        peak = max(log) if log else 0.0
        mn   = min(log) if log else 0.0

        record = SessionRecord(
            exercise      = self._active["exercise"],
            start_ts      = self._active["start_ts"],
            end_ts        = time.time(),
            reps          = reps,
            avg_accuracy  = round(avg, 2),
            peak_accuracy = round(peak, 2),
            min_accuracy  = round(mn, 2),
            frame_count   = len(log),
            accuracy_log  = log,
        )

        self._save(record)
        self._active = None
        return record

    # ── Querying ───────────────────────────────────────────────────────────────

    def load_history(
        self,
        exercise: Optional[str] = None,
        limit:    int           = 20,
    ) -> list[SessionRecord]:
        files = sorted(self._sessions_dir.glob("*.json"), reverse=True)
        records: list[SessionRecord] = []
        for f in files:
            try:
                data = json.loads(f.read_text())
                r    = SessionRecord(**data)
                if exercise is None or r.exercise == exercise:
                    records.append(r)
                if len(records) >= limit:
                    break
            except Exception:
                continue
        return records

    def recent_accuracies(self, exercise: Optional[str] = None, n: int = 5) -> list[float]:
        return [r.avg_accuracy for r in self.load_history(exercise, limit=n)]

    # ── Internal ───────────────────────────────────────────────────────────────

    def _save(self, record: SessionRecord) -> None:
        ts   = int(record.start_ts)
        name = f"{record.exercise.replace(' ', '_')}_{ts}.json"
        path = self._sessions_dir / name
        path.write_text(json.dumps(asdict(record), indent=2))

        # Prune oldest files if over cap
        all_files = sorted(self._sessions_dir.glob("*.json"))
        while len(all_files) > config.MAX_SESSIONS:
            all_files.pop(0).unlink()
