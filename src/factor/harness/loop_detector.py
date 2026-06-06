"""Repetitive reasoning loop detection."""

from __future__ import annotations

import threading
from collections import deque


class LoopDetector:
    """Detects when an agent is stuck repeating the same reasoning pattern.

    Maintains a sliding window of recent actions and flags a loop when the
    same action signature appears `threshold` times within the window.
    """

    def __init__(self, window_size: int = 10, threshold: int = 5):
        self.window_size = window_size
        self.threshold = threshold
        self._lock = threading.Lock()
        self._window: deque[str] = deque(maxlen=window_size)
        self._loop_detected = False
        self._loop_signature: str | None = None

    def record(self, action_signature: str) -> None:
        """Record an action and check for loops.

        Args:
            action_signature: A string identifying the action (e.g.
                tool name, or tool_name + hashed args).
        """
        with self._lock:
            self._window.append(action_signature)
            self._check_unlocked()

    def _check_unlocked(self) -> None:
        if len(self._window) < self.threshold:
            return

        counts: dict[str, int] = {}
        for sig in self._window:
            counts[sig] = counts.get(sig, 0) + 1

        for sig, count in counts.items():
            if count >= self.threshold:
                self._loop_detected = True
                self._loop_signature = sig
                return

        tail = list(self._window)[-self.threshold:]
        if len(set(tail)) == 1:
            self._loop_detected = True
            self._loop_signature = tail[0]

    @property
    def is_looping(self) -> bool:
        with self._lock:
            return self._loop_detected

    def status(self) -> dict:
        with self._lock:
            return {
                "is_looping": self._loop_detected,
                "loop_signature": self._loop_signature,
                "window": list(self._window),
                "window_size": self.window_size,
                "threshold": self.threshold,
            }

    def reset(self) -> None:
        with self._lock:
            self._window.clear()
            self._loop_detected = False
            self._loop_signature = None
