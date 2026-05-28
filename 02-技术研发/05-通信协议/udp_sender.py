"""
SRP UDP JSON Sender (Sprint 0 v0.3)
====================================
Sends multi-signal scored data as JSON over UDP to TD and Unity.

Spec:
  Transport: UDP
  Encoding: JSON (UTF-8)
  Rate: 10 Hz
  Ports: TD:5005, Unity:5006

Message structure includes all 8 independent scores, raw signals,
derived features, and weather composite.
"""

import json
import socket
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

UDP_TD_PORT = 5005
UDP_UNITY_PORT = 5006

DEFAULT_TARGETS = [
    ("127.0.0.1", UDP_TD_PORT),
    ("127.0.0.1", UDP_UNITY_PORT),
]


def build_message(score_dict: dict) -> dict:
    """Build full UDP JSON message with all 8 independent scores."""
    ts = score_dict.get("timestamp", time.time())

    return {
        "version": "1.0",
        "timestamp": ts,

        # All 8 independent scores
        "scores": {
            "breath_sync": score_dict.get("breath_sync", 50),
            "hr_stability": score_dict.get("hr_stability", 50),
            "hrv_recovery": score_dict.get("hrv_recovery", 50),
            "rate_match": score_dict.get("rate_match", 50),
            "depth_quality": score_dict.get("depth_quality", 50),
            "regularity": score_dict.get("regularity", 50),
            "eda_calm": score_dict.get("eda_calm", 50),
            "motion_stillness": score_dict.get("motion_stillness", 50),
        },

        # Weather composite
        "weather": {
            "type": score_dict.get("weather_type", "storm"),
            "composite": score_dict.get("weather_composite", 50),
            "intensity": score_dict.get("weather_intensity", 0.5),
            "trend": score_dict.get("weather_trend", "stable"),
            "dominant": score_dict.get("dominant_domain", "—"),
        },

        # Breath domain
        "breath": {
            "phase": score_dict.get("breath_phase", "exhale"),
            "rate": score_dict.get("rr", 0),
            "depth": score_dict.get("respiration_raw", 0),
            "amplitude": score_dict.get("respiration_amplitude", 0),
            "regularity_raw": score_dict.get("breath_regularity_raw", 0),
        },

        # Cardiac domain
        "cardiac": {
            "hr": score_dict.get("hr", 0),
            "rmssd": score_dict.get("rmssd", 0),
            "ecg_raw": score_dict.get("ecg_raw", 0),
        },

        # Auxiliary domain
        "aux": {
            "eda_raw": score_dict.get("eda_raw", 0),
            "eda_tonic": score_dict.get("eda_tonic", 0),
            "acc_magnitude": score_dict.get("acc_magnitude", 0),
            "motion_index": score_dict.get("motion_index", 0),
            "temp_skin": score_dict.get("temp_skin", 0),
        },

        # Guidance
        "guidance": {
            "prompt": score_dict.get("guidance_prompt", ""),
            "circle_radius": 0.8,
            "target_breath_rate": 10,
        },
    }


class UDPSender:
    """Sends UDP JSON messages to multiple targets (TD + Unity)."""

    def __init__(self, targets: list[tuple[str, int]] | None = None):
        self.targets = targets or DEFAULT_TARGETS
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.frame_count = 0
        self.error_count = 0

    def send(self, score_dict: dict) -> bool:
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
        try:
            self.sock.close()
        except Exception:
            pass

    def stats(self) -> dict:
        return {
            "frames_sent": self.frame_count,
            "errors": self.error_count,
            "targets": [f"{h}:{p}" for h, p in self.targets],
        }


if __name__ == "__main__":
    import sys, os
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)

    sender = UDPSender()
    print(f"UDP Sender self-test: {len(sender.targets)} targets")
    for i in range(5):
        test_frame = {
            "timestamp": time.time(),
            "breath_sync": 72.5, "hr_stability": 68.0, "hrv_recovery": 55.3,
            "rate_match": 60.2, "depth_quality": 58.1, "regularity": 65.7,
            "eda_calm": 70.8, "motion_stillness": 82.4,
            "weather_composite": 65.0, "weather_intensity": 0.35,
            "weather_trend": "weakening", "dominant_domain": "eda_calm",
            "weather_type": "storm", "breath_phase": "inhale",
            "rr": 8.5, "hr": 78.0, "rmssd": 40.2,
            "respiration_raw": 0.45, "respiration_amplitude": 0.4,
            "breath_regularity_raw": 0.6,
            "ecg_raw": 0.15, "eda_raw": 7.2, "eda_tonic": 7.0,
            "acc_magnitude": 0.03, "motion_index": 0.025,
            "temp_skin": 34.1,
            "guidance_prompt": "慢慢吸气...4秒",
        }
        ok = sender.send(test_frame)
        print(f"  Frame {i + 1}: {'OK' if ok else 'FAIL'}")
        time.sleep(0.1)

    print(f"\nStats: {sender.stats()}")
    sender.close()
