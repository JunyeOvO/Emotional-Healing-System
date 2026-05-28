"""
SRP Scoring Model (Sprint 0)
==============================
Translates physiological features into user-facing scores.

Outputs:
  - breath_score:  0-100, how well the user matches the breathing guidance
  - calm_index:    0-100, composite calmness estimate
  - weather_intensity: 0-1, derived from calm_index (1 = severe weather)

Scoring formula:
  calm_index = breath_sync × 0.40 + hrv_score × 0.30
             + regularity × 0.20 + depth_score × 0.10

All sub-scores are 0-100 normalized.
"""

from dataclasses import dataclass, field
from typing import Optional
import math


# ── Configuration ──────────────────────────────────────────────────────────

@dataclass
class ScoringConfig:
    """Configurable scoring parameters."""
    # Target values (physiologically reasonable defaults)
    target_rr: float = 10.0           # Target respiration rate (breaths/min) — slow, calming
    target_hr: float = 70.0           # Resting HR
    target_rmssd: float = 50.0        # Good HRV (ms)
    target_amplitude: float = 0.5     # Deep breathing amplitude

    # Weights for calm_index
    w_breath: float = 0.40
    w_hrv: float = 0.30
    w_regularity: float = 0.20
    w_depth: float = 0.10

    # Smoothing
    smoothing_alpha: float = 0.3      # EMA coefficient

    # Weather mapping
    weather_threshold_clear: float = 75     # calm_index >= 75 → nearly clear
    weather_threshold_mild: float = 50      # calm_index >= 50 → mild weather
    weather_threshold_moderate: float = 25  # calm_index >= 25 → moderate

    @classmethod
    def for_weather(cls, weather_type: str) -> "ScoringConfig":
        """Factory: create ScoringConfig pre-tuned for a weather type."""
        return WEATHER_SCORING_PRESETS.get(weather_type, WEATHER_SCORING_PRESETS["storm"])


# ── Per-Weather Scoring Presets ─────────────────────────────────────────────

WEATHER_SCORING_PRESETS: dict[str, ScoringConfig] = {
    "storm": ScoringConfig(  # 焦虑 → 盒式呼吸, target 5 bpm
        target_rr=5.0,
        target_hr=85.0,
        target_rmssd=40.0,
        target_amplitude=0.5,
        w_breath=0.40,
        w_hrv=0.30,
        w_regularity=0.20,
        w_depth=0.10,
    ),
    "heat": ScoringConfig(  # 烦躁 → 长呼气, target 6.67 bpm
        target_rr=6.67,
        target_hr=80.0,
        target_rmssd=45.0,
        target_amplitude=0.6,
        w_breath=0.45,
        w_hrv=0.25,
        w_regularity=0.15,
        w_depth=0.15,
    ),
    "snow": ScoringConfig(  # 低落 → 稳定呼吸, target 6 bpm
        target_rr=6.0,
        target_hr=65.0,
        target_rmssd=55.0,
        target_amplitude=0.4,
        w_breath=0.35,
        w_hrv=0.30,
        w_regularity=0.25,
        w_depth=0.10,
    ),
    "fade": ScoringConfig(  # 孤独 → 自主呼吸, target 7.5 bpm
        target_rr=7.5,
        target_hr=62.0,
        target_rmssd=60.0,
        target_amplitude=0.35,
        w_breath=0.25,
        w_hrv=0.40,
        w_regularity=0.15,
        w_depth=0.20,
    ),
}


# ── Sub-score Calculators ──────────────────────────────────────────────────

def _breath_sync_score(rr: float, target_rr: float = 10.0) -> float:
    """How close is the user's breathing rate to the guidance target?

    Uses a Gaussian decay: score = 100 * exp(-(rr - target)² / (2*σ²))
    σ = 3 breaths/min tolerance.
    """
    sigma = 3.0
    diff = rr - target_rr
    return 100.0 * math.exp(-(diff ** 2) / (2 * sigma ** 2))


def _hrv_score(rmssd: float, target_rmssd: float = 50.0) -> float:
    """Score based on HRV (RMSSD). Higher HRV → calmer state.

    Linear mapping: 0 at RMSSD=0, 100 at RMSSD≥target*1.5.
    Clips to [0, 100].
    """
    max_val = target_rmssd * 1.5
    score = (rmssd / max_val) * 100.0
    return max(0.0, min(100.0, score))


def _regularity_score(regularity: float) -> float:
    """Map breath regularity [0, 1] to score [0, 100]."""
    return regularity * 100.0


def _depth_score(amplitude: float, target_amplitude: float = 0.5) -> float:
    """Score based on breathing depth relative to target.

    Damped: too shallow or too deep are both sub-optimal.
    Uses Gaussian with center at target_amplitude.
    """
    sigma = target_amplitude * 0.5
    diff = amplitude - target_amplitude
    return 100.0 * math.exp(-(diff ** 2) / (2 * sigma ** 2))


# ── Weather Mapping ────────────────────────────────────────────────────────

def _weather_intensity(calm_index: float, cfg: ScoringConfig) -> float:
    """Convert calm_index to weather intensity [0, 1].

    calm_index = 100 → intensity = 0 (clear sky)
    calm_index = 0   → intensity = 1 (severe weather)
    """
    return 1.0 - (calm_index / 100.0)


def _weather_trend(current: float, previous: float) -> str:
    """Determine if weather is improving or worsening."""
    diff = current - previous
    if diff > 2:
        return "weakening"
    elif diff < -2:
        return "intensifying"
    else:
        return "stable"


# ── Scoring Output ─────────────────────────────────────────────────────────

@dataclass
class ScoreFrame:
    """A single frame of scored outputs ready for UDP / CSV."""
    timestamp: float

    # Primary outputs
    breath_score: float
    calm_index: float

    # Sub-scores (for debugging / CSV)
    breath_sync: float
    hrv_score: float
    regularity_score: float
    depth_score: float

    # Derived
    weather_intensity: float
    weather_trend: str

    # Raw inputs (for CSV completeness)
    rr: float
    hr: float
    rmssd: float
    respiration_raw: float
    ecg_raw: float

    # Mock fields (carried through from generator)
    breath_phase: str = "exhale"
    guidance_prompt: str = ""
    weather_type: str = "storm"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "breath_score": round(self.breath_score, 1),
            "calm_index": round(self.calm_index, 1),
            "breath_sync": round(self.breath_sync, 1),
            "hrv_score": round(self.hrv_score, 1),
            "regularity_score": round(self.regularity_score, 1),
            "depth_score": round(self.depth_score, 1),
            "weather_intensity": round(self.weather_intensity, 4),
            "weather_trend": self.weather_trend,
            "rr": round(self.rr, 2),
            "hr": round(self.hr, 1),
            "rmssd": round(self.rmssd, 1),
            "respiration_raw": round(self.respiration_raw, 4),
            "ecg_raw": round(self.ecg_raw, 4),
            "breath_phase": self.breath_phase,
            "guidance_prompt": self.guidance_prompt,
            "weather_type": self.weather_type,
        }


# ── Scoring Model ──────────────────────────────────────────────────────────

class ScoringModel:
    """Translates ProcessedFrame features into ScoreFrame with smoothing."""

    def __init__(self, cfg: ScoringConfig | None = None):
        self.cfg = cfg or ScoringConfig()
        self._prev_calm: float = 50.0    # start at neutral
        self._prev_intensity: float = 0.5

    def score(self, processed, breath_phase: str = "exhale",
              guidance_prompt: str = "", weather_type: str = "storm") -> ScoreFrame:
        """Compute scores from a ProcessedFrame (from SignalPipeline)."""
        if processed is None:
            # Return neutral frame during warmup
            return ScoreFrame(
                timestamp=0, breath_score=50, calm_index=50,
                breath_sync=50, hrv_score=50, regularity_score=50, depth_score=50,
                weather_intensity=0.5, weather_trend="stable",
                rr=0, hr=0, rmssd=0,
                respiration_raw=0, ecg_raw=0,
                breath_phase=breath_phase, guidance_prompt=guidance_prompt,
                weather_type=weather_type,
            )

        # Sub-scores
        breath_sync = _breath_sync_score(processed.rr, self.cfg.target_rr)
        hrv_sc = _hrv_score(processed.rmssd, self.cfg.target_rmssd)
        reg_sc = _regularity_score(processed.breath_regularity)
        depth_sc = _depth_score(processed.respiration_amplitude, self.cfg.target_amplitude)

        # Weighted calm_index
        raw_calm = (
            breath_sync * self.cfg.w_breath +
            hrv_sc * self.cfg.w_hrv +
            reg_sc * self.cfg.w_regularity +
            depth_sc * self.cfg.w_depth
        )

        # EMA smoothing
        alpha = self.cfg.smoothing_alpha
        calm_index = alpha * raw_calm + (1 - alpha) * self._prev_calm
        self._prev_calm = calm_index

        # Weather
        weather_intensity = alpha * _weather_intensity(calm_index, self.cfg) + \
                            (1 - alpha) * self._prev_intensity
        self._prev_intensity = weather_intensity

        trend = _weather_trend(calm_index, self._prev_calm)

        return ScoreFrame(
            timestamp=processed.timestamp,
            breath_score=breath_sync,     # breath_score = breath_sync score (simplified)
            calm_index=calm_index,
            breath_sync=breath_sync,
            hrv_score=hrv_sc,
            regularity_score=reg_sc,
            depth_score=depth_sc,
            weather_intensity=weather_intensity,
            weather_trend=trend,
            rr=processed.rr,
            hr=processed.hr,
            rmssd=processed.rmssd,
            respiration_raw=processed.respiration_raw,
            ecg_raw=processed.ecg_raw,
            breath_phase=breath_phase,
            guidance_prompt=guidance_prompt,
            weather_type=weather_type,
        )


# ── Self-test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Inline ProcessedFrame for self-test (avoids Chinese dirname import issues)
    from dataclasses import dataclass as _dc
    @_dc
    class _PF:
        timestamp: float = 0; rr: float = 0; respiration_amplitude: float = 0
        breath_regularity: float = 0; hr: float = 0; rmssd: float = 0
        respiration_raw: float = 0; ecg_raw: float = 0

    model = ScoringModel()

    # Simulate three processed frames with improving values
    frames = [
        _PF(0, rr=18.0, respiration_amplitude=0.3,
                       breath_regularity=0.4, hr=90, rmssd=25,
                       respiration_raw=0.1, ecg_raw=0.2),
        _PF(1, rr=14.0, respiration_amplitude=0.5,
                       breath_regularity=0.6, hr=78, rmssd=35,
                       respiration_raw=0.3, ecg_raw=0.5),
        _PF(2, rr=10.5, respiration_amplitude=0.55,
                       breath_regularity=0.8, hr=72, rmssd=48,
                       respiration_raw=0.5, ecg_raw=0.8),
    ]

    for pf in frames:
        sf = model.score(pf, breath_phase="inhale")
        print(f"t={sf.timestamp:.0f}s  breath={sf.breath_score:.0f}  "
              f"calm={sf.calm_index:.0f}  weather={sf.weather_intensity:.2f}  "
              f"trend={sf.weather_trend}")
