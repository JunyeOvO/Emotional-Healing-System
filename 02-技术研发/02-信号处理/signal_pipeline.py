"""
SRP Signal Pipeline (Sprint 0 v0.3)
====================================
Processes raw multi-sensor signals through NeuroKit2 and custom estimators
to extract physiological features for independent per-signal scoring.

Pipeline flow:
  Raw frames → buffering → NeuroKit2 / custom processing → feature extraction

Signal domains:
  - Respiration: RSP → RR, amplitude, regularity, phase
  - Cardiac:     ECG → HR, RMSSD (HRV)
  - EDA:         Skin conductance → tonic level
  - ACC:         Motion → stillness index
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
from dataclasses import dataclass
from collections import deque
import warnings
import numpy as np
import neurokit2 as nk

warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")
warnings.filterwarnings("ignore", message="Too few peaks detected", module="neurokit2")


BUFFER_SIZE = 300
PROCESSING_WINDOW = 100
EDA_WINDOW = 40    # 4 seconds for tonic extraction
ACC_WINDOW = 10    # 1 second for motion RMS


@dataclass
class ProcessedFrame:
    """Extracted physiological features from a sliding window of raw signals."""
    timestamp: float

    # Respiratory features
    rr: float = 0.0                      # breaths/min
    respiration_amplitude: float = 0.0   # normalized depth (RMS)
    breath_regularity: float = 0.0       # 0=irregular, 1=periodic

    # Cardiac features
    hr: float = 0.0                      # BPM
    rmssd: float = 0.0                   # HRV index (ms)

    # EDA features
    eda_tonic: float = 0.0               # skin conductance level (μS)

    # Motion features
    motion_index: float = 0.0            # body movement (g RMS)

    # Raw snapshots (for logging)
    respiration_raw: float = 0.0
    ecg_raw: float = 0.0
    eda_raw: float = 0.0
    acc_magnitude: float = 0.0
    temp_skin: float = 0.0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "rr": round(self.rr, 2),
            "respiration_amplitude": round(self.respiration_amplitude, 4),
            "breath_regularity": round(self.breath_regularity, 4),
            "hr": round(self.hr, 1),
            "rmssd": round(self.rmssd, 1),
            "eda_tonic": round(self.eda_tonic, 2),
            "motion_index": round(self.motion_index, 4),
            "respiration_raw": round(self.respiration_raw, 4),
            "ecg_raw": round(self.ecg_raw, 4),
            "eda_raw": round(self.eda_raw, 4),
            "acc_magnitude": round(self.acc_magnitude, 4),
            "temp_skin": round(self.temp_skin, 2),
        }


class SignalPipeline:
    """Rolling-buffer processor for multi-sensor physiological signals."""

    def __init__(self, buffer_size: int = BUFFER_SIZE):
        self.resp_buffer: deque[float] = deque(maxlen=buffer_size)
        self.ecg_buffer: deque[float] = deque(maxlen=buffer_size)
        self.eda_buffer: deque[float] = deque(maxlen=buffer_size)
        self.acc_buffer: deque[float] = deque(maxlen=buffer_size)
        self.t_buffer: deque[float] = deque(maxlen=buffer_size)

        self._last_rr = 14.0
        self._last_hr = 72.0
        self._last_rmssd = 45.0
        self._last_resp_amp = 0.5
        self._last_eda_tonic = 8.0
        self._last_motion = 0.04

    def feed(self, timestamp: float, respiration: float, ecg: float,
             eda: float = 0.0, acc_mag: float = 0.0,
             temp_skin: float = 34.0) -> Optional[ProcessedFrame]:
        """Feed one multi-sensor frame into the pipeline.

        Returns ProcessedFrame after warmup, or None during warmup.
        """
        self.t_buffer.append(timestamp)
        self.resp_buffer.append(respiration)
        self.ecg_buffer.append(ecg)
        self.eda_buffer.append(eda)
        self.acc_buffer.append(acc_mag)

        if len(self.resp_buffer) < PROCESSING_WINDOW:
            return None

        # --- Respiratory processing ---
        resp_arr = np.array(self.resp_buffer, dtype=np.float64)

        try:
            resp_clean = nk.rsp_clean(resp_arr, sampling_rate=10)
            rsp_rate = nk.rsp_rate(resp_clean, sampling_rate=10, method="peak")
            valid = rsp_rate[~np.isnan(rsp_rate)]
            rr_val = float(np.mean(valid)) if len(valid) > 0 else self._last_rr
        except Exception:
            rr_val = self._simple_resp_rate(resp_arr)

        self._last_rr = rr_val
        resp_amp = float(np.std(resp_arr[-PROCESSING_WINDOW:]))
        self._last_resp_amp = resp_amp
        regularity = self._estimate_regularity(resp_arr[-PROCESSING_WINDOW:])

        # --- Cardiac processing ---
        ecg_arr = np.array(self.ecg_buffer, dtype=np.float64)

        try:
            ecg_clean = nk.ecg_clean(ecg_arr, sampling_rate=10)
            if len(ecg_clean) >= 50:
                peaks, info = nk.ecg_peaks(ecg_clean, sampling_rate=10)
                hr_val = float(info.get("ECG_Rate_Mean", self._last_hr))
                rr_intervals = np.diff(peaks) / 10.0 * 1000
                if len(rr_intervals) > 1:
                    rmssd_val = float(np.sqrt(np.mean(np.diff(rr_intervals) ** 2)))
                else:
                    rmssd_val = self._last_rmssd
                self._last_hr = hr_val
                self._last_rmssd = rmssd_val
            else:
                hr_val = self._last_hr
                rmssd_val = self._last_rmssd
        except Exception:
            hr_val = self._last_hr
            rmssd_val = self._last_rmssd

        # --- EDA processing: tonic extraction via moving average ---
        eda_arr = np.array(self.eda_buffer, dtype=np.float64)
        window_n = min(EDA_WINDOW, len(eda_arr))
        eda_tonic = float(np.mean(eda_arr[-window_n:]))
        self._last_eda_tonic = eda_tonic

        # --- Motion processing: RMS of recent ACC ---
        acc_arr = np.array(self.acc_buffer, dtype=np.float64)
        window_n = min(ACC_WINDOW, len(acc_arr))
        motion_rms = float(np.sqrt(np.mean(acc_arr[-window_n:] ** 2)))
        self._last_motion = motion_rms

        return ProcessedFrame(
            timestamp=timestamp,
            rr=rr_val,
            respiration_amplitude=resp_amp,
            breath_regularity=regularity,
            hr=hr_val,
            rmssd=rmssd_val,
            eda_tonic=eda_tonic,
            motion_index=motion_rms,
            respiration_raw=respiration,
            ecg_raw=ecg,
            eda_raw=eda,
            acc_magnitude=acc_mag,
            temp_skin=temp_skin,
        )

    # ── Fallback estimators ──────────────────────────────────────────────

    def _simple_resp_rate(self, signal: np.ndarray) -> float:
        centered = signal - np.mean(signal)
        crossings = np.sum(np.diff(np.signbit(centered)))
        secs = len(signal) / 10.0
        return (crossings / 2) * (60 / secs) if secs > 0 else self._last_rr

    def _estimate_regularity(self, signal: np.ndarray) -> float:
        centered = signal - np.mean(signal)
        autocorr = np.correlate(centered, centered, mode="full")
        autocorr = autocorr[len(autocorr) // 2:]
        autocorr = autocorr / (autocorr[0] + 1e-10)
        peaks_idx = np.where(
            (autocorr[1:-1] > autocorr[:-2]) &
            (autocorr[1:-1] > autocorr[2:])
        )[0] + 1
        if len(peaks_idx) == 0:
            return 0.5
        return float(np.clip(autocorr[peaks_idx[0]], 0, 1))


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    import importlib
    _mock = importlib.import_module("01-数据采集.mock_data")
    MockConfig = _mock.MockConfig
    generate_frame_list = _mock.generate_frame_list

    cfg = MockConfig()
    frames = generate_frame_list(duration=30.0, cfg=cfg)
    print(f"Self-test: processing {len(frames)} multi-sensor frames...")

    pipeline = SignalPipeline()
    processed_count = 0
    for f in frames:
        result = pipeline.feed(f.timestamp, f.respiration_raw, f.ecg_raw,
                               f.eda_raw, f.acc_magnitude, f.temp_skin)
        if result is not None:
            processed_count += 1

    print(f"Warmup frames dropped: {len(frames) - processed_count}")
    print(f"Processed frames: {processed_count}")
    if processed_count > 0:
        print(f"Last: RR={pipeline._last_rr:.1f}  HR={pipeline._last_hr:.1f}  "
              f"RMSSD={pipeline._last_rmssd:.1f}  EDA_tonic={pipeline._last_eda_tonic:.2f}  "
              f"Motion={pipeline._last_motion:.4f}")
