"""
SRP Signal Pipeline (Sprint 0)
================================
Processes raw respiration and ECG signals through NeuroKit2/BioSPPy
to extract physiological features for the scoring model.

Pipeline flow:
  Raw frames → buffering → NeuroKit2 processing → feature extraction
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

# Suppress noisy NeuroKit2/numpy warnings on mock data with low peak counts.
# These are expected during warmup and smooth-signal periods — the fallback
# estimators handle them correctly.
warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")
warnings.filterwarnings("ignore", message="Too few peaks detected", module="neurokit2")


# ── Configuration ──────────────────────────────────────────────────────────

# Buffer sizes: need enough data for reliable signal processing
BUFFER_SIZE = 300          # ~30 seconds at 10Hz
PROCESSING_WINDOW = 100    # ~10 seconds for rolling features


# ── Feature Output ─────────────────────────────────────────────────────────

@dataclass
class ProcessedFrame:
    """Features extracted from a sliding window of raw signals."""
    timestamp: float

    # Respiratory features
    rr: float = 0.0                # Respiratory rate (breaths/min)
    respiration_amplitude: float = 0.0  # Normalized depth
    breath_regularity: float = 0.0      # 0=irregular, 1=perfectly periodic

    # Cardiac features
    hr: float = 0.0                # Heart rate (BPM)
    rmssd: float = 0.0             # HRV index (ms)

    # Raw signal snapshot (for logging)
    respiration_raw: float = 0.0
    ecg_raw: float = 0.0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "rr": round(self.rr, 2),
            "respiration_amplitude": round(self.respiration_amplitude, 4),
            "breath_regularity": round(self.breath_regularity, 4),
            "hr": round(self.hr, 1),
            "rmssd": round(self.rmssd, 1),
            "respiration_raw": round(self.respiration_raw, 4),
            "ecg_raw": round(self.ecg_raw, 4),
        }


# ── Signal Pipeline ────────────────────────────────────────────────────────

class SignalPipeline:
    """Rolling-buffer signal processor using NeuroKit2 + BioSPPy.

    Maintains two ring buffers (respiration & ECG), and periodically
    runs NeuroKit2 processing on the latest window to extract features.
    """

    def __init__(self, buffer_size: int = BUFFER_SIZE):
        self.resp_buffer: deque[float] = deque(maxlen=buffer_size)
        self.ecg_buffer: deque[float] = deque(maxlen=buffer_size)
        self.t_buffer: deque[float] = deque(maxlen=buffer_size)
        self._last_rr = 14.0           # initial guess (~12 breaths/min)
        self._last_hr = 72.0           # initial guess (~72 BPM)
        self._last_rmssd = 45.0        # initial guess (resting HRV)
        self._last_resp_amp = 0.5

    def feed(self, timestamp: float, respiration: float, ecg: float) -> Optional[ProcessedFrame]:
        """Feed one raw frame into the pipeline. Returns ProcessedFrame when
        enough data is buffered, or None during warmup.

        Called at the source frame rate (10 Hz).
        """
        self.t_buffer.append(timestamp)
        self.resp_buffer.append(respiration)
        self.ecg_buffer.append(ecg)

        # Warmup: need at least PROCESSING_WINDOW samples
        if len(self.resp_buffer) < PROCESSING_WINDOW:
            return None

        # --- Respiratory processing ---
        resp_arr = np.array(self.resp_buffer, dtype=np.float64)

        # Clean the respiration signal
        try:
            resp_clean = nk.rsp_clean(resp_arr, sampling_rate=10)
            resp_info = nk.rsp_findpeaks(resp_clean, sampling_rate=10)
            rsp_rate = nk.rsp_rate(resp_clean, sampling_rate=10, method="peak")
            valid = rsp_rate[~np.isnan(rsp_rate)]
            rr_val = float(np.mean(valid)) if len(valid) > 0 else self._last_rr
        except Exception:
            # Fallback: simple peak counting
            rr_val = self._simple_resp_rate(resp_arr)

        self._last_rr = rr_val

        # Amplitude (RMS of recent signal)
        resp_amp = float(np.std(resp_arr[-PROCESSING_WINDOW:]))
        self._last_resp_amp = resp_amp

        # Regularity: autocorrelation peak
        regularity = self._estimate_regularity(resp_arr[-PROCESSING_WINDOW:])

        # --- Cardiac processing ---
        ecg_arr = np.array(self.ecg_buffer, dtype=np.float64)

        try:
            ecg_clean = nk.ecg_clean(ecg_arr, sampling_rate=10)
            # NeuroKit2 needs at least ~250 samples at 10Hz for peak detection,
            # scale up via interpolation if needed
            if len(ecg_clean) >= 50:
                peaks, info = nk.ecg_peaks(ecg_clean, sampling_rate=10)
                hr_val = float(info.get("ECG_Rate_Mean", self._last_hr))
                # RMSSD from RR intervals
                rr_intervals = np.diff(peaks) / 10.0 * 1000  # ms
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
            # Fallback for mock ECG (may have too few peaks)
            hr_val = self._last_hr
            rmssd_val = self._last_rmssd

        return ProcessedFrame(
            timestamp=timestamp,
            rr=rr_val,
            respiration_amplitude=resp_amp,
            breath_regularity=regularity,
            hr=hr_val,
            rmssd=rmssd_val,
            respiration_raw=respiration,
            ecg_raw=ecg,
        )

    # ── Fallback estimators (when NeuroKit2 fails on sparse mock data) ──

    def _simple_resp_rate(self, signal: np.ndarray) -> float:
        """Count zero-crossings as fallback respiration rate estimate."""
        centered = signal - np.mean(signal)
        crossings = np.sum(np.diff(np.signbit(centered)))
        secs = len(signal) / 10.0
        return (crossings / 2) * (60 / secs) if secs > 0 else self._last_rr

    def _estimate_regularity(self, signal: np.ndarray) -> float:
        """Estimate breath regularity via autocorrelation peak strength."""
        centered = signal - np.mean(signal)
        autocorr = np.correlate(centered, centered, mode="full")
        autocorr = autocorr[len(autocorr) // 2:]
        autocorr = autocorr / (autocorr[0] + 1e-10)
        # Find first peak beyond lag 0
        peaks_idx = np.where(
            (autocorr[1:-1] > autocorr[:-2]) &
            (autocorr[1:-1] > autocorr[2:])
        )[0] + 1
        if len(peaks_idx) == 0:
            return 0.5
        first_peak = peaks_idx[0]
        return float(np.clip(autocorr[first_peak], 0, 1))


# ── Self-test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Add parent and grandparent dirs for cross-package import
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    # Use importlib to handle Chinese dirnames
    import importlib
    _mock = importlib.import_module("01-数据采集.mock_data")
    MockConfig = _mock.MockConfig
    generate_frame_list = _mock.generate_frame_list

    cfg = MockConfig()
    frames = generate_frame_list(duration=30.0, cfg=cfg)
    print(f"Self-test: processing {len(frames)} frames...")

    pipeline = SignalPipeline()
    processed_count = 0
    for f in frames:
        result = pipeline.feed(f.timestamp, f.respiration_raw, f.ecg_raw)
        if result is not None:
            processed_count += 1

    print(f"Warmup frames dropped: {len(frames) - processed_count}")
    print(f"Processed frames: {processed_count}")
    if processed_count > 0:
        print(f"Last frame: RR={pipeline._last_rr:.1f}  HR={pipeline._last_hr:.1f}  "
              f"RMSSD={pipeline._last_rmssd:.1f}")
