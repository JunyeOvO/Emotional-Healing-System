"""
SRP Ring Buffer — thread-safe circular buffer for sensor samples.

Each BLE device pushes samples at its native rate into a RingBuffer.
The FrameClock reads the latest value at 10 Hz for time alignment.
"""

import threading
from collections import deque


class RingBuffer:
    """Thread-safe ring buffer for sensor samples with timestamp."""

    def __init__(self, capacity: int):
        self._buf: deque[tuple[float, float]] = deque(maxlen=capacity)
        self._lock = threading.Lock()

    def push(self, timestamp: float, value: float) -> None:
        with self._lock:
            self._buf.append((timestamp, value))

    def read_latest(self) -> float:
        """Return most recent value, or 0.0 if empty."""
        with self._lock:
            if self._buf:
                return self._buf[-1][1]
            return 0.0

    def read_latest_ts(self) -> tuple[float, float]:
        """Return (timestamp, value) of most recent sample, or (0.0, 0.0)."""
        with self._lock:
            if self._buf:
                return self._buf[-1]
            return (0.0, 0.0)

    def read_window(self, n: int) -> list[float]:
        """Return last n values for downsampling."""
        with self._lock:
            return [v for _, v in list(self._buf)[-n:]]

    def clear(self) -> None:
        with self._lock:
            self._buf.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._buf)

    @property
    def is_empty(self) -> bool:
        with self._lock:
            return len(self._buf) == 0
