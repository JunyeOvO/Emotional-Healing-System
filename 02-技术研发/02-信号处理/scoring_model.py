"""
SRP Scoring Model (Sprint 0 v0.3)
==================================
Independent per-signal scoring (8 dimensions) → weather composite.

Each physiological signal domain has its own 0-100 score.
Weather intensity is the weighted composite of all 8 scores.

Architecture:
  8 raw/derived signals → 8 independent scores → 1 weather composite
"""

from dataclasses import dataclass, field
from typing import Optional
import math


# ── Configuration ──────────────────────────────────────────────────────────

@dataclass
class ScoringConfig:
    """Per-weather scoring targets and weights."""

    # Targets
    target_rr: float = 10.0
    target_hr: float = 70.0
    target_rmssd: float = 50.0
    target_amplitude: float = 0.5

    # 8 independent score weights → weather composite
    w_breath_sync: float = 0.18
    w_hr_stability: float = 0.12
    w_hrv_recovery: float = 0.20
    w_rate_match: float = 0.10
    w_depth_quality: float = 0.08
    w_regularity: float = 0.10
    w_eda_calm: float = 0.12
    w_motion_stillness: float = 0.10

    # Smoothing
    smoothing_alpha: float = 0.3

    @classmethod
    def for_weather(cls, weather_type: str) -> "ScoringConfig":
        return WEATHER_SCORING_PRESETS.get(weather_type, WEATHER_SCORING_PRESETS["storm"])


# ── Per-weather presets ─────────────────────────────────────────────────────

WEATHER_SCORING_PRESETS: dict[str, ScoringConfig] = {
    "storm": ScoringConfig(  # 焦虑 — 强调呼吸同步 + 规律
        target_rr=5.0, target_hr=85.0, target_rmssd=40.0, target_amplitude=0.5,
        w_breath_sync=0.20, w_hr_stability=0.10, w_hrv_recovery=0.18,
        w_rate_match=0.12, w_depth_quality=0.08, w_regularity=0.12,
        w_eda_calm=0.10, w_motion_stillness=0.10,
    ),
    "heat": ScoringConfig(  # 烦躁 — 强调呼吸深度 + HR稳定
        target_rr=6.67, target_hr=80.0, target_rmssd=45.0, target_amplitude=0.6,
        w_breath_sync=0.15, w_hr_stability=0.15, w_hrv_recovery=0.15,
        w_rate_match=0.08, w_depth_quality=0.15, w_regularity=0.07,
        w_eda_calm=0.12, w_motion_stillness=0.13,
    ),
    "snow": ScoringConfig(  # 低落 — 强调 HRV + EDA calm
        target_rr=6.0, target_hr=65.0, target_rmssd=55.0, target_amplitude=0.4,
        w_breath_sync=0.12, w_hr_stability=0.10, w_hrv_recovery=0.22,
        w_rate_match=0.10, w_depth_quality=0.08, w_regularity=0.10,
        w_eda_calm=0.15, w_motion_stillness=0.13,
    ),
    "fade": ScoringConfig(  # 孤独 — 强调 HRV + EDA
        target_rr=7.5, target_hr=62.0, target_rmssd=60.0, target_amplitude=0.35,
        w_breath_sync=0.08, w_hr_stability=0.08, w_hrv_recovery=0.25,
        w_rate_match=0.05, w_depth_quality=0.10, w_regularity=0.06,
        w_eda_calm=0.20, w_motion_stillness=0.18,
    ),
}


# ── Independent Score Calculators (8 functions, one per signal) ────────────

def score_breath_sync(rr: float, target_rr: float) -> float:
    """How close is breathing rate to the guidance target?  Gaussian decay."""
    sigma = 3.0
    diff = rr - target_rr
    return 100.0 * math.exp(-(diff ** 2) / (2 * sigma ** 2))


def score_hr_stability(hr: float, prev_hr: float, target_hr: float) -> float:
    """Heart rate stability: low beat-to-beat variation = stable."""
    variation = abs(hr - prev_hr)
    # 0 BPM variation → 100, 10 BPM variation → 0
    return max(0.0, 100.0 - variation * 10.0)


def score_hrv_recovery(rmssd: float, target_rmssd: float) -> float:
    """HRV (RMSSD) recovery toward target. Linear, clip at 100."""
    max_val = target_rmssd * 1.5
    return max(0.0, min(100.0, (rmssd / max_val) * 100.0))


def score_rate_match(rr: float, prev_rr: float, target_rr: float) -> float:
    """RR trend: is it moving toward the target?"""
    if prev_rr == 0:
        return 50.0
    prev_diff = abs(prev_rr - target_rr)
    curr_diff = abs(rr - target_rr)
    improvement = prev_diff - curr_diff
    # Positive improvement → higher score
    base = 50.0 + improvement * 10.0
    return max(0.0, min(100.0, base))


def score_depth_quality(amplitude: float, target_amplitude: float) -> float:
    """Breathing depth quality relative to target. Gaussian centered at target."""
    sigma = target_amplitude * 0.5
    diff = amplitude - target_amplitude
    return 100.0 * math.exp(-(diff ** 2) / (2 * sigma ** 2))


def score_regularity(regularity: float) -> float:
    """Breath pattern regularity: autocorrelation strength → 0-100."""
    return regularity * 100.0


def score_eda_calm(eda_tonic: float, init_eda: float) -> float:
    """EDA calm: decreasing skin conductance = calming down.

    Score increases as EDA drops below initial baseline.
    """
    if init_eda == 0:
        return 50.0
    drop = init_eda - eda_tonic
    # Each 0.5 μS drop = 10 points
    base = 50.0 + drop * 20.0
    return max(0.0, min(100.0, base))


def score_motion_stillness(motion: float) -> float:
    """Motion stillness: lower acceleration = more still/relaxed."""
    # 0g → 100, 0.5g → 0
    return max(0.0, min(100.0, 100.0 - motion * 200.0))


# ── Weather Mapping ─────────────────────────────────────────────────────────

def _weather_intensity(composite: float) -> float:
    """Composite calm → weather intensity. 100=clear, 0=severe."""
    return 1.0 - (composite / 100.0)


def _weather_trend(current: float, previous: float) -> str:
    diff = current - previous
    if diff > 2:
        return "weakening"
    elif diff < -2:
        return "intensifying"
    else:
        return "stable"


def _dominant_domain(scores: dict) -> str:
    """Which score domain is currently contributing most to improvement."""
    if not scores:
        return "—"
    return max(scores, key=scores.get)


# ── Scoring Output ─────────────────────────────────────────────────────────

@dataclass
class ScoreFrame:
    """One scored frame with all 8 independent scores + weather composite."""
    timestamp: float

    # 8 independent per-signal scores (0-100)
    breath_sync: float
    hr_stability: float
    hrv_recovery: float
    rate_match: float
    depth_quality: float
    regularity: float
    eda_calm: float
    motion_stillness: float

    # Weather composite
    weather_composite: float         # 0-100, weighted average of all scores
    weather_intensity: float         # 0-1, derived from composite
    weather_trend: str               # weakening / stable / intensifying
    dominant_domain: str             # which score leads improvement

    # Raw inputs (for CSV completeness)
    rr: float
    hr: float
    rmssd: float
    respiration_raw: float
    ecg_raw: float
    eda_raw: float
    eda_tonic: float
    acc_magnitude: float
    motion_index: float
    temp_skin: float
    respiration_amplitude: float
    breath_regularity_raw: float

    # Metadata
    breath_phase: str = "exhale"
    guidance_prompt: str = ""
    weather_type: str = "storm"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            # 8 independent scores
            "breath_sync": round(self.breath_sync, 1),
            "hr_stability": round(self.hr_stability, 1),
            "hrv_recovery": round(self.hrv_recovery, 1),
            "rate_match": round(self.rate_match, 1),
            "depth_quality": round(self.depth_quality, 1),
            "regularity": round(self.regularity, 1),
            "eda_calm": round(self.eda_calm, 1),
            "motion_stillness": round(self.motion_stillness, 1),
            # Weather composite
            "weather_composite": round(self.weather_composite, 1),
            "weather_intensity": round(self.weather_intensity, 4),
            "weather_trend": self.weather_trend,
            "dominant_domain": self.dominant_domain,
            # Raw signals
            "rr": round(self.rr, 2),
            "hr": round(self.hr, 1),
            "rmssd": round(self.rmssd, 1),
            "respiration_raw": round(self.respiration_raw, 4),
            "ecg_raw": round(self.ecg_raw, 4),
            "eda_raw": round(self.eda_raw, 4),
            "eda_tonic": round(self.eda_tonic, 2),
            "acc_magnitude": round(self.acc_magnitude, 4),
            "motion_index": round(self.motion_index, 4),
            "temp_skin": round(self.temp_skin, 2),
            "respiration_amplitude": round(self.respiration_amplitude, 4),
            "breath_regularity_raw": round(self.breath_regularity_raw, 4),
            # Metadata
            "breath_phase": self.breath_phase,
            "guidance_prompt": self.guidance_prompt,
            "weather_type": self.weather_type,
        }

    def score_list(self) -> list[tuple[str, float]]:
        """Return all 8 scores as ordered (name, value) pairs for display."""
        return [
            ("Breath Sync", self.breath_sync),
            ("HR Stability", self.hr_stability),
            ("HRV Recovery", self.hrv_recovery),
            ("Rate Match", self.rate_match),
            ("Depth Quality", self.depth_quality),
            ("Regularity", self.regularity),
            ("EDA Calm", self.eda_calm),
            ("Motion Stillness", self.motion_stillness),
        ]


# ── Scoring Model ──────────────────────────────────────────────────────────

class ScoringModel:
    """Translates ProcessedFrame features into 8 independent scores + weather."""

    def __init__(self, cfg: ScoringConfig | None = None):
        self.cfg = cfg or ScoringConfig()
        self._prev_composite: float = 50.0
        self._prev_intensity: float = 0.5
        self._prev_hr: float = 72.0
        self._prev_rr: float = 14.0
        self._init_eda: Optional[float] = None
        self._warmup_frames: int = 0

    def score(self, processed, breath_phase: str = "exhale",
              guidance_prompt: str = "", weather_type: str = "storm") -> ScoreFrame:
        """Compute all 8 independent scores from a ProcessedFrame."""

        if processed is None:
            return self._neutral_frame(breath_phase, guidance_prompt, weather_type)

        # Capture initial EDA baseline (first 5 processed frames avg)
        if self._init_eda is None:
            self._init_eda = processed.eda_tonic if processed.eda_tonic > 0 else 8.0
        elif self._warmup_frames < 50:
            self._init_eda = self._init_eda * 0.9 + processed.eda_tonic * 0.1
        self._warmup_frames += 1

        # Compute all 8 independent scores
        s1 = score_breath_sync(processed.rr, self.cfg.target_rr)
        s2 = score_hr_stability(processed.hr, self._prev_hr, self.cfg.target_hr)
        s3 = score_hrv_recovery(processed.rmssd, self.cfg.target_rmssd)
        s4 = score_rate_match(processed.rr, self._prev_rr, self.cfg.target_rr)
        s5 = score_depth_quality(processed.respiration_amplitude, self.cfg.target_amplitude)
        s6 = score_regularity(processed.breath_regularity)
        s7 = score_eda_calm(processed.eda_tonic, self._init_eda)
        s8 = score_motion_stillness(processed.motion_index)

        # Weighted weather composite
        w = self.cfg
        raw_composite = (
            s1 * w.w_breath_sync +
            s2 * w.w_hr_stability +
            s3 * w.w_hrv_recovery +
            s4 * w.w_rate_match +
            s5 * w.w_depth_quality +
            s6 * w.w_regularity +
            s7 * w.w_eda_calm +
            s8 * w.w_motion_stillness
        )

        # EMA smoothing
        alpha = self.cfg.smoothing_alpha
        composite = alpha * raw_composite + (1 - alpha) * self._prev_composite
        self._prev_composite = composite

        intensity = alpha * _weather_intensity(composite) + (1 - alpha) * self._prev_intensity
        self._prev_intensity = intensity

        trend = _weather_trend(composite, self._prev_composite)

        scores_dict = {
            "breath_sync": s1, "hr_stability": s2, "hrv_recovery": s3,
            "rate_match": s4, "depth_quality": s5, "regularity": s6,
            "eda_calm": s7, "motion_stillness": s8,
        }
        dominant = _dominant_domain(scores_dict)

        # Update state
        self._prev_hr = processed.hr
        self._prev_rr = processed.rr

        return ScoreFrame(
            timestamp=processed.timestamp,
            breath_sync=s1, hr_stability=s2, hrv_recovery=s3,
            rate_match=s4, depth_quality=s5, regularity=s6,
            eda_calm=s7, motion_stillness=s8,
            weather_composite=composite,
            weather_intensity=intensity,
            weather_trend=trend,
            dominant_domain=dominant,
            rr=processed.rr, hr=processed.hr, rmssd=processed.rmssd,
            respiration_raw=processed.respiration_raw,
            ecg_raw=processed.ecg_raw,
            eda_raw=processed.eda_raw,
            eda_tonic=processed.eda_tonic,
            acc_magnitude=processed.acc_magnitude,
            motion_index=processed.motion_index,
            temp_skin=processed.temp_skin,
            respiration_amplitude=processed.respiration_amplitude,
            breath_regularity_raw=processed.breath_regularity,
            breath_phase=breath_phase,
            guidance_prompt=guidance_prompt,
            weather_type=weather_type,
        )

    def _neutral_frame(self, phase: str, prompt: str, weather: str) -> ScoreFrame:
        return ScoreFrame(
            timestamp=0,
            breath_sync=50, hr_stability=50, hrv_recovery=50,
            rate_match=50, depth_quality=50, regularity=50,
            eda_calm=50, motion_stillness=50,
            weather_composite=50, weather_intensity=0.5,
            weather_trend="stable", dominant_domain="—",
            rr=0, hr=0, rmssd=0,
            respiration_raw=0, ecg_raw=0, eda_raw=0, eda_tonic=0,
            acc_magnitude=0, motion_index=0, temp_skin=0,
            respiration_amplitude=0, breath_regularity_raw=0,
            breath_phase=phase, guidance_prompt=prompt, weather_type=weather,
        )


# ── Self-test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from dataclasses import dataclass as _dc

    @_dc
    class _PF:
        timestamp: float = 0; rr: float = 0; respiration_amplitude: float = 0
        breath_regularity: float = 0; hr: float = 0; rmssd: float = 0
        eda_tonic: float = 0; motion_index: float = 0
        respiration_raw: float = 0; ecg_raw: float = 0
        eda_raw: float = 0; acc_magnitude: float = 0; temp_skin: float = 0

    for weather in ["storm", "heat", "snow", "fade"]:
        cfg = ScoringConfig.for_weather(weather)
        model = ScoringModel(cfg)
        print(f"\n=== {weather} ===")
        print(f"Weights: BS={cfg.w_breath_sync:.0%} HS={cfg.w_hr_stability:.0%} "
              f"HRV={cfg.w_hrv_recovery:.0%} RM={cfg.w_rate_match:.0%} "
              f"DQ={cfg.w_depth_quality:.0%} RG={cfg.w_regularity:.0%} "
              f"EDA={cfg.w_eda_calm:.0%} MS={cfg.w_motion_stillness:.0%}")

        frames = [
            _PF(0, rr=14, respiration_amplitude=0.3, breath_regularity=0.5,
                hr=85, rmssd=30, eda_tonic=10, motion_index=0.08,
                respiration_raw=0.1, ecg_raw=0.1, eda_raw=10, acc_magnitude=0.08,
                temp_skin=34),
            _PF(1, rr=10, respiration_amplitude=0.5, breath_regularity=0.7,
                hr=78, rmssd=42, eda_tonic=8, motion_index=0.04,
                respiration_raw=0.3, ecg_raw=0.2, eda_raw=8, acc_magnitude=0.04,
                temp_skin=34.1),
            _PF(2, rr=6, respiration_amplitude=0.55, breath_regularity=0.85,
                hr=72, rmssd=50, eda_tonic=7, motion_index=0.02,
                respiration_raw=0.5, ecg_raw=0.3, eda_raw=7, acc_magnitude=0.02,
                temp_skin=34.2),
        ]
        for pf in frames:
            sf = model.score(pf)
            print(f"  t={sf.timestamp:.0f}s composite={sf.weather_composite:.0f} "
                  f"intensity={sf.weather_intensity:.2f} trend={sf.weather_trend} "
                  f"dominant={sf.dominant_domain}")
