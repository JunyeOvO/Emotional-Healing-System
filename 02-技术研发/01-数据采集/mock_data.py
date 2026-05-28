"""
SRP Mock Data Generator (Sprint 0 v0.3)
========================================
Generates simulated physiological signals for pipeline development
before real Polar H10 + respiratory belt + auxiliary sensors are available.

Produces per frame (10 Hz):
  - Respiration waveform (sine wave, weather-specific pattern)
  - ECG-like signal (QRS bursts @ configured HR)
  - EDA (skin conductance: tonic + phasic SCR)
  - ACC magnitude (body motion, settling-down pattern)
  - Skin temperature (slow drift, peripheral vasodilation)
  - Breath phase classification (inhale / hold / exhale)
  - Guidance prompt text

Output rate: 10 Hz
"""

import time
import math
from typing import Generator
from dataclasses import dataclass, field
import numpy as np


# ── Weather-specific Breathing Configs ──────────────────────────────────────

WEATHER_BREATHING_CONFIG: dict[str, dict] = {
    "storm": {
        "breath_rate_hz": 1.0 / 12.0,
        "inhale_duration": 4.0,
        "hold_duration": 2.0,
        "exhale_duration": 6.0,
        "hr_bpm": 85.0,
        "breath_amplitude": 0.5,
        "eda_tonic_base": 8.0,
        "acc_rest_level": 0.06,
    },
    "heat": {
        "breath_rate_hz": 1.0 / 9.0,
        "inhale_duration": 3.0,
        "hold_duration": 0.0,
        "exhale_duration": 6.0,
        "hr_bpm": 80.0,
        "breath_amplitude": 0.6,
        "eda_tonic_base": 12.0,
        "acc_rest_level": 0.08,
    },
    "snow": {
        "breath_rate_hz": 1.0 / 10.0,
        "inhale_duration": 5.0,
        "hold_duration": 0.0,
        "exhale_duration": 5.0,
        "hr_bpm": 65.0,
        "breath_amplitude": 0.4,
        "eda_tonic_base": 5.0,
        "acc_rest_level": 0.02,
    },
    "fade": {
        "breath_rate_hz": 1.0 / 8.0,
        "inhale_duration": 3.5,
        "hold_duration": 0.0,
        "exhale_duration": 4.5,
        "hr_bpm": 62.0,
        "breath_amplitude": 0.35,
        "eda_tonic_base": 6.0,
        "acc_rest_level": 0.03,
    },
}


# ── Configuration ───────────────────────────────────────────────────────────

@dataclass
class MockConfig:
    """Configurable parameters for mock signal generation."""
    # Breathing
    breath_rate_hz: float = 0.2
    breath_amplitude: float = 0.5
    breath_noise_std: float = 0.02

    # ECG / Heart
    hr_bpm: float = 72.0
    ecg_noise_std: float = 0.01

    # EDA (skin conductance, μS)
    eda_tonic_base: float = 8.0        # baseline μS
    eda_phasic_rate: float = 2.0       # SCR peaks per minute
    eda_noise_std: float = 0.05

    # ACC (motion, g)
    acc_rest_level: float = 0.04       # baseline motion at rest
    acc_motion_rate: float = 1.5       # movement bursts per minute
    acc_noise_std: float = 0.005

    # TEMP (skin temperature, °C)
    temp_base: float = 34.0
    temp_drift_rate: float = 0.002     # °C/sec warming
    temp_noise_std: float = 0.02

    # Output
    frame_rate: float = 10.0

    # Breath pattern (seconds per phase)
    inhale_duration: float = 4.0
    hold_duration: float = 2.0
    exhale_duration: float = 6.0

    # Weather simulation
    weather_type: str = "storm"
    weather_intensity_base: float = 0.5

    @classmethod
    def for_weather(cls, weather_type: str, intensity: float = 0.5) -> "MockConfig":
        params = WEATHER_BREATHING_CONFIG.get(weather_type, WEATHER_BREATHING_CONFIG["storm"])
        return cls(
            breath_rate_hz=params["breath_rate_hz"],
            inhale_duration=params["inhale_duration"],
            hold_duration=params["hold_duration"],
            exhale_duration=params["exhale_duration"],
            hr_bpm=params["hr_bpm"],
            breath_amplitude=params["breath_amplitude"],
            eda_tonic_base=params["eda_tonic_base"],
            acc_rest_level=params["acc_rest_level"],
            weather_type=weather_type,
            weather_intensity_base=intensity,
        )


# ── Signal Generators ───────────────────────────────────────────────────────

def _respiration(t: float, cfg: MockConfig) -> float:
    signal = math.sin(2 * math.pi * cfg.breath_rate_hz * t) * cfg.breath_amplitude
    signal += np.random.normal(0, cfg.breath_noise_std)
    return signal


def _ecg_signal(t: float, cfg: MockConfig) -> float:
    hr_hz = cfg.hr_bpm / 60.0
    period = 1.0 / hr_hz
    phase_in_cycle = (t % period) / period

    qrs_center = 0.3
    qrs_width = 0.05
    qrs = math.exp(-((phase_in_cycle - qrs_center) / qrs_width) ** 2) * 0.8

    t_center = 0.7
    t_wave = math.exp(-((phase_in_cycle - t_center) / 0.08) ** 2) * 0.15

    return qrs + t_wave + np.random.normal(0, cfg.ecg_noise_std)


def _eda_signal(t: float, cfg: MockConfig) -> float:
    """Simulate skin conductance: slow tonic drift + phasic SCR peaks.

    Tonic component drifts downward over time (calming effect).
    Phasic component fires occasional SCR peaks (1-3/min).
    """
    # Tonic: slowly decreasing baseline (calming down over 3-5 min)
    tonic_drift = -0.3 * math.tanh(t / 120.0)
    tonic = cfg.eda_tonic_base + tonic_drift

    # Phasic: occasional SCR peaks
    scr_interval = 60.0 / cfg.eda_phasic_rate  # seconds between peaks
    scr_phase = (t % scr_interval) / scr_interval
    # Sharp SCR at phase ~0 (rise 1s, decay 3s)
    if scr_phase < 0.3:
        scr = 1.5 * math.exp(-((t % scr_interval) / 1.5) ** 0.7)
    elif (t - 0.3) % scr_interval < scr_interval and scr_phase >= 0.3:
        scr = 0.3 * math.exp(-((t % scr_interval - 0.3 * scr_interval) / 3.0))
    else:
        scr = 0

    return tonic + scr + np.random.normal(0, cfg.eda_noise_std)


def _acc_magnitude(t: float, cfg: MockConfig) -> float:
    """Simulate body motion: low baseline + occasional movement bursts.

    Motion decreases over time as user settles into the breathing exercise.
    """
    # Settling-down envelope: motion halves over 2 minutes
    envelope = 0.5 + 0.5 * math.exp(-t / 60.0)

    # Baseline rest motion
    baseline = cfg.acc_rest_level * envelope

    # Occasional movement burst
    burst_interval = 60.0 / cfg.acc_motion_rate
    burst_phase = (t % burst_interval) / burst_interval
    if burst_phase < 0.08:
        burst = 0.4 * envelope * math.exp(-((burst_phase * burst_interval) / 0.5) ** 2)
    else:
        burst = 0

    return baseline + burst + np.random.normal(0, cfg.acc_noise_std)


def _temp_skin(t: float, cfg: MockConfig) -> float:
    """Simulate skin temperature: slow warming trend + noise.

    Peripheral vasodilation during relaxation causes ~0.5°C rise over 5 min.
    """
    warming = 0.5 * math.tanh(t / 180.0)
    # Very subtle respiratory-synchronous oscillation (±0.02°C)
    resp_osc = 0.02 * math.sin(2 * math.pi * cfg.breath_rate_hz * t)
    return cfg.temp_base + warming + resp_osc + np.random.normal(0, cfg.temp_noise_std)


# ── Breath Phase Classifier ──────────────────────────────────────────────────

def _breath_phase(t: float, cfg: MockConfig) -> str:
    cycle_duration = cfg.inhale_duration + cfg.hold_duration + cfg.exhale_duration
    cycle_pos = t % cycle_duration

    if cycle_pos < cfg.inhale_duration:
        return "inhale"
    elif cycle_pos < cfg.inhale_duration + cfg.hold_duration:
        return "hold"
    else:
        return "exhale"


# ── Guidance Text ────────────────────────────────────────────────────────────

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
    weather_prompts = _WEATHER_PROMPTS.get(cfg.weather_type, _WEATHER_PROMPTS["storm"])
    return weather_prompts.get(phase, "")


# ── Frame Definition ────────────────────────────────────────────────────────

@dataclass
class MockFrame:
    """A single 10 Hz frame of simulated multi-sensor physiological data."""
    timestamp: float

    # Primary biosignals
    respiration_raw: float       # RSP waveform, normalized
    ecg_raw: float               # ECG-like QRS signal

    # Auxiliary biosignals (optional sensors)
    eda_raw: float               # Skin conductance, μS
    acc_magnitude: float         # Body motion, g (rms of 3-axis)
    temp_skin: float             # Skin temperature, °C

    # Derived / metadata
    breath_phase: str            # inhale / hold / exhale
    guidance_prompt: str         # Per-weather+phase guidance text
    weather_type: str            # storm / heat / snow / fade
    weather_intensity_base: float  # 0=clear, 1=severe (injected for simulation)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "respiration_raw": round(self.respiration_raw, 4),
            "ecg_raw": round(self.ecg_raw, 4),
            "eda_raw": round(self.eda_raw, 4),
            "acc_magnitude": round(self.acc_magnitude, 4),
            "temp_skin": round(self.temp_skin, 2),
            "breath_phase": self.breath_phase,
            "guidance_prompt": self.guidance_prompt,
            "weather_type": self.weather_type,
            "weather_intensity_base": round(self.weather_intensity_base, 4),
        }


# ── Frame Generator ─────────────────────────────────────────────────────────

def generate_frames(
    duration: float = 60.0,
    cfg: MockConfig | None = None,
) -> Generator[MockFrame, None, None]:
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
            eda_raw=_eda_signal(t, cfg),
            acc_magnitude=_acc_magnitude(t, cfg),
            temp_skin=_temp_skin(t, cfg),
            breath_phase=_breath_phase(t, cfg),
            guidance_prompt=_guidance_prompt(_breath_phase(t, cfg), cfg),
            weather_type=cfg.weather_type,
            weather_intensity_base=cfg.weather_intensity_base,
        )


# ── Convenience ──────────────────────────────────────────────────────────────

def generate_frame_list(duration: float = 60.0, cfg: MockConfig | None = None) -> list[MockFrame]:
    return list(generate_frames(duration, cfg))


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("MockDataGenerator self-test (v0.3 — multi-sensor)")
    frames = generate_frame_list(duration=5.0)
    print(f"Generated {len(frames)} frames in 5 seconds")
    print(f"Frame rate: {len(frames) / 5.0:.1f} Hz")
    print(f"\nFirst 3 frames:")
    for f in frames[:3]:
        print(f"  t={f.timestamp:.2f}s  resp={f.respiration_raw:+.4f}  "
              f"ecg={f.ecg_raw:.4f}  eda={f.eda_raw:.2f}  "
              f"acc={f.acc_magnitude:.4f}  temp={f.temp_skin:.2f}  "
              f"phase={f.breath_phase}")
    print(f"\nSignal ranges across {len(frames)} frames:")
    print(f"  EDA: {min(f.eda_raw for f in frames):.2f} — "
          f"{max(f.eda_raw for f in frames):.2f} μS")
    print(f"  ACC: {min(f.acc_magnitude for f in frames):.4f} — "
          f"{max(f.acc_magnitude for f in frames):.4f} g")
    print(f"  TEMP: {min(f.temp_skin for f in frames):.2f} — "
          f"{max(f.temp_skin for f in frames):.2f} °C")
