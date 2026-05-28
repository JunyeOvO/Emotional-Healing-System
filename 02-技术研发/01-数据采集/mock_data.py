"""
SRP Mock Data Generator (Sprint 0)
====================================
Generates simulated physiological signals for pipeline development
before real Polar H10 + respiratory belt are available.

Produces:
  - Respiratory waveform (sine wave @ 0.2 Hz = 12 breaths/min)
  - ECG-like signal (QRS bursts @ 1.2 Hz = 72 BPM)
  - Breath phase classification (inhale / hold / exhale)

Output rate: 10 Hz configurable (default matches UDP spec)
"""

import time
import math
from typing import Generator
from dataclasses import dataclass, field
import numpy as np


# ── Weather-specific Breathing Configs ──────────────────────────────────────

WEATHER_BREATHING_CONFIG: dict[str, dict] = {
    "storm": {  # 焦虑 → 4-2-6 盒式呼吸 (12s cycle)
        "breath_rate_hz": 1.0 / 12.0,
        "inhale_duration": 4.0,
        "hold_duration": 2.0,
        "exhale_duration": 6.0,
        "hr_bpm": 85.0,
        "breath_amplitude": 0.5,
    },
    "heat": {   # 烦躁 → 长呼气降温 1:2 (9s cycle)
        "breath_rate_hz": 1.0 / 9.0,
        "inhale_duration": 3.0,
        "hold_duration": 0.0,
        "exhale_duration": 6.0,
        "hr_bpm": 80.0,
        "breath_amplitude": 0.6,
    },
    "snow": {   # 低落 → 稳定呼吸 5-5 (10s cycle)
        "breath_rate_hz": 1.0 / 10.0,
        "inhale_duration": 5.0,
        "hold_duration": 0.0,
        "exhale_duration": 5.0,
        "hr_bpm": 65.0,
        "breath_amplitude": 0.4,
    },
    "fade": {   # 孤独 → 自主呼吸 (8s variable cycle)
        "breath_rate_hz": 1.0 / 8.0,
        "inhale_duration": 3.5,
        "hold_duration": 0.0,
        "exhale_duration": 4.5,
        "hr_bpm": 62.0,
        "breath_amplitude": 0.35,
    },
}


# ── Configuration ──────────────────────────────────────────────────────────

@dataclass
class MockConfig:
    """Configurable parameters for mock signal generation."""
    # Breathing
    breath_rate_hz: float = 0.2       # 12 breaths/min
    breath_amplitude: float = 0.5      # normalized amplitude
    breath_noise_std: float = 0.02     # small Gaussian noise

    # ECG / Heart
    hr_bpm: float = 72.0              # resting heart rate
    ecg_noise_std: float = 0.01

    # Output
    frame_rate: float = 10.0           # Hz (matches UDP spec)

    # Breath pattern (seconds per phase)
    # 4-2-6 pattern: inhale 4s, hold 2s, exhale 6s
    inhale_duration: float = 4.0
    hold_duration: float = 2.0
    exhale_duration: float = 6.0

    # Weather simulation (for demo variation)
    weather_type: str = "storm"       # storm / heat / snow / fade
    weather_intensity_base: float = 0.5  # 0=calm, 1=severe

    @classmethod
    def for_weather(cls, weather_type: str, intensity: float = 0.5) -> "MockConfig":
        """Factory: create MockConfig pre-configured for a weather type."""
        params = WEATHER_BREATHING_CONFIG.get(weather_type, WEATHER_BREATHING_CONFIG["storm"])
        return cls(
            breath_rate_hz=params["breath_rate_hz"],
            inhale_duration=params["inhale_duration"],
            hold_duration=params["hold_duration"],
            exhale_duration=params["exhale_duration"],
            hr_bpm=params["hr_bpm"],
            breath_amplitude=params["breath_amplitude"],
            weather_type=weather_type,
            weather_intensity_base=intensity,
        )


# ── Signal Generators ──────────────────────────────────────────────────────

def _respiration(t: float, cfg: MockConfig) -> float:
    """Simulate a respiratory waveform (sine + noise)."""
    signal = math.sin(2 * math.pi * cfg.breath_rate_hz * t) * cfg.breath_amplitude
    signal += np.random.normal(0, cfg.breath_noise_std)
    return signal


def _ecg_signal(t: float, cfg: MockConfig) -> float:
    """Simulate a simplified QRS-like ECG signal.

    Produces periodic sharp positive peaks (representing R-waves)
    at the configured HR, with slight timing jitter for realism.
    """
    hr_hz = cfg.hr_bpm / 60.0              # 1.2 Hz
    period = 1.0 / hr_hz                   # seconds between R-waves
    phase_in_cycle = (t % period) / period  # [0, 1)

    # QRS burst centered at 30% of the cardiac cycle
    qrs_center = 0.3
    qrs_width = 0.05
    qrs = math.exp(-((phase_in_cycle - qrs_center) / qrs_width) ** 2) * 0.8

    # Tiny T-wave (repolarization) at ~70%
    t_center = 0.7
    t_wave = math.exp(-((phase_in_cycle - t_center) / 0.08) ** 2) * 0.15

    signal = qrs + t_wave + np.random.normal(0, cfg.ecg_noise_std)
    return signal


# ── Breath Phase Classifier ────────────────────────────────────────────────

def _breath_phase(t: float, cfg: MockConfig) -> str:
    """Classify current breath phase based on 4-2-6 breathing pattern.

    Uses a repeating 12-second cycle: inhale→hold→exhale.
    """
    cycle_duration = cfg.inhale_duration + cfg.hold_duration + cfg.exhale_duration
    cycle_pos = t % cycle_duration

    if cycle_pos < cfg.inhale_duration:
        return "inhale"
    elif cycle_pos < cfg.inhale_duration + cfg.hold_duration:
        return "hold"
    else:
        return "exhale"


# ── Guidance Text ──────────────────────────────────────────────────────────

_WEATHER_PROMPTS: dict[str, dict[str, str]] = {
    "storm": {
        "inhale": "慢慢吸气...4秒",
        "hold": "屏住呼吸...2秒",
        "exhale": "缓缓呼出...6秒",
    },
    "heat": {
        "inhale": "深吸气...3秒",
        "hold": "",
        "exhale": "长长呼出...6秒",
    },
    "snow": {
        "inhale": "平稳吸气...5秒",
        "hold": "",
        "exhale": "缓缓呼气...5秒",
    },
    "fade": {
        "inhale": "自然吸气...",
        "hold": "",
        "exhale": "轻轻呼出...",
    },
}


def _guidance_prompt(phase: str, cfg: MockConfig) -> str:
    """Return per-weather guidance prompt for the current breath phase."""
    weather_prompts = _WEATHER_PROMPTS.get(cfg.weather_type, _WEATHER_PROMPTS["storm"])
    return weather_prompts.get(phase, "")


# ── Frame Generator (main public API) ──────────────────────────────────────

@dataclass
class MockFrame:
    """A single 10Hz frame of simulated physiological data."""
    timestamp: float
    # Raw signals
    respiration_raw: float
    ecg_raw: float
    # Derived
    breath_phase: str
    guidance_prompt: str
    # Injected weather parameters (for demo variety)
    weather_type: str
    weather_intensity_base: float

    def to_dict(self) -> dict:
        """Serialize to dict for downstream consumers."""
        return {
            "timestamp": self.timestamp,
            "respiration_raw": round(self.respiration_raw, 4),
            "ecg_raw": round(self.ecg_raw, 4),
            "breath_phase": self.breath_phase,
            "guidance_prompt": self.guidance_prompt,
            "weather_type": self.weather_type,
            "weather_intensity_base": round(self.weather_intensity_base, 4),
        }


def generate_frames(
    duration: float = 60.0,
    cfg: MockConfig | None = None,
) -> Generator[MockFrame, None, None]:
    """Generate mock physiological data frames at 10 Hz.

    Args:
        duration: Total simulation duration in seconds.
        cfg: Configuration object; uses defaults if None.

    Yields:
        MockFrame objects at cfg.frame_rate Hz.
    """
    if cfg is None:
        cfg = MockConfig()

    import itertools
    dt = 1.0 / cfg.frame_rate

    if duration <= 0:
        iterator = itertools.count()
    else:
        iterator = range(int(duration * cfg.frame_rate))

    for i in iterator:
        t = i * dt
        yield MockFrame(
            timestamp=t,
            respiration_raw=_respiration(t, cfg),
            ecg_raw=_ecg_signal(t, cfg),
            breath_phase=_breath_phase(t, cfg),
            guidance_prompt=_guidance_prompt(_breath_phase(t, cfg), cfg),
            weather_type=cfg.weather_type,
            weather_intensity_base=cfg.weather_intensity_base,
        )


# ── Convenience Function ───────────────────────────────────────────────────

def generate_frame_list(duration: float = 60.0, cfg: MockConfig | None = None) -> list[MockFrame]:
    """Return all frames as a list (for testing / batch processing)."""
    return list(generate_frames(duration, cfg))


# ── Self-test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("MockDataGenerator self-test")
    frames = generate_frame_list(duration=5.0)
    print(f"Generated {len(frames)} frames in 5 seconds")
    print(f"Frame rate: {len(frames) / 5.0:.1f} Hz")
    print(f"\nFirst 3 frames:")
    for f in frames[:3]:
        print(f"  t={f.timestamp:.2f}s  resp={f.respiration_raw:+.4f}  "
              f"ecg={f.ecg_raw:.4f}  phase={f.breath_phase}")
    print(f"Phase distribution: ", end="")
    from collections import Counter
    counts = Counter(f.breath_phase for f in frames)
    for phase, n in counts.items():
        print(f"{phase}={n} ", end="")
    print()
