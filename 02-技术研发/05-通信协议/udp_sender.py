"""
SRP UDP JSON Sender (Sprint 0)
================================
Sends scored physiological data as JSON over UDP to TD and Unity.

Spec (from UDP协议定义.md):
  - Transport: UDP
  - Encoding: JSON (UTF-8)
  - Rate: 10 Hz (100ms interval)
  - Ports: TD:5005, Unity:5006

Message format: see build_message() below.
"""

import json
import socket
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── Port Configuration ─────────────────────────────────────────────────────

UDP_TD_PORT = 5005      # TouchDesigner
UDP_UNITY_PORT = 5006   # Unity 2D

DEFAULT_TARGETS = [
    ("127.0.0.1", UDP_TD_PORT),
    ("127.0.0.1", UDP_UNITY_PORT),
]


# ── Message Builder ────────────────────────────────────────────────────────

def build_message(score_dict: dict) -> dict:
    """Build the full UDP JSON message per the protocol specification.

    Args:
        score_dict: Output from ScoreFrame.to_dict()

    Returns:
        Complete message dict matching UDP协议定义.md format.
    """
    ts = score_dict.get("timestamp", time.time())

    return {
        "version": "1.0",
        "timestamp": ts,
        "breath": {
            "score": score_dict.get("breath_score", 0),
            "rate": score_dict.get("rr", 0),
            "depth": score_dict.get("respiration_raw", 0),
            "phase": score_dict.get("breath_phase", "exhale"),
            "guidance_phase": score_dict.get("breath_phase", "exhale"),
        },
        "calm": {
            "index": score_dict.get("calm_index", 0),
            "trend": score_dict.get("weather_trend", "stable"),
            "weather_intensity": score_dict.get("weather_intensity", 0),
        },
        "hrv": {
            "hr": score_dict.get("hr", 0),
            "rmssd": score_dict.get("rmssd", 0),
            "coherence": 0.5,  # placeholder until real HRV coherence implemented
        },
        "weather": {
            "type": score_dict.get("weather_type", "storm"),
            "intensity": score_dict.get("weather_intensity", 0),
            "transition": score_dict.get("weather_trend", "stable"),
        },
        "guidance": {
            "prompt": score_dict.get("guidance_prompt", ""),
            "circle_radius": 0.8,  # placeholder, driven by breath phase
            "target_breath_rate": 10,
        },
    }


# ── UDP Sender ─────────────────────────────────────────────────────────────

class UDPSender:
    """Sends UDP JSON messages to multiple targets (TD + Unity)."""

    def __init__(self, targets: list[tuple[str, int]] | None = None):
        """Initialize UDP socket.

        Args:
            targets: List of (host, port) tuples. Defaults to localhost:5005,5006.
        """
        self.targets = targets or DEFAULT_TARGETS
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.frame_count = 0
        self.error_count = 0

    def send(self, score_dict: dict) -> bool:
        """Send one scored frame to all targets.

        Args:
            score_dict: ScoreFrame.to_dict() output.

        Returns:
            True if sent to all targets successfully.
        """
        message = build_message(score_dict)
        payload = json.dumps(message, ensure_ascii=False).encode("utf-8")

        all_ok = True
        for host, port in self.targets:
            try:
                self.sock.sendto(payload, (host, port))
            except OSError as e:
                logger.warning(f"UDP send to {host}:{port} failed: {e}")
                self.error_count += 1
                all_ok = False

        self.frame_count += 1
        return all_ok

    def close(self):
        """Close the UDP socket."""
        try:
            self.sock.close()
        except Exception:
            pass

    def stats(self) -> dict:
        """Return sender statistics."""
        return {
            "frames_sent": self.frame_count,
            "errors": self.error_count,
            "targets": [f"{h}:{p}" for h, p in self.targets],
        }


# ── Self-test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, os
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)

    # Quick test: send 5 frames (no receiver needed for error count)
    sender = UDPSender()
    print(f"UDP Sender self-test: {len(sender.targets)} targets")
    for i in range(5):
        test_frame = {
            "timestamp": time.time(),
            "breath_score": 72.5,
            "calm_index": 68.3,
            "rr": 14.2,
            "hr": 72.0,
            "rmssd": 45.2,
            "weather_intensity": 0.32,
            "weather_trend": "weakening",
            "weather_type": "storm",
            "breath_phase": "inhale",
            "guidance_prompt": "慢慢吸气...4秒",
            "respiration_raw": 0.65,
            "ecg_raw": 0.12,
            "breath_sync": 70.0,
            "hrv_score": 65.0,
            "regularity_score": 60.0,
            "depth_score": 55.0,
        }
        ok = sender.send(test_frame)
        print(f"  Frame {i + 1}: {'OK' if ok else 'FAIL'}")
        time.sleep(0.1)

    print(f"\nStats: {sender.stats()}")
    sender.close()
