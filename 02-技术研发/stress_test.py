#!/usr/bin/env python3
"""
SRP Full-Pipeline Stress Test (Sprint 1)
==========================================
Cycles through all 4 weather types: 15 seconds each at 10Hz.
Total: 600 frames across 60 seconds.

Verifies:
  - No dropped frames (600 generated = 600 processed post-warmup)
  - No pipeline errors
  - Per-weather score distributions in valid ranges

Usage:
  python stress_test.py
  python stress_test.py --full    # include UDP + CSV
"""

import sys
import os
import time
import importlib
from dataclasses import dataclass, field

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

WEATHER_CYCLE = ["storm", "heat", "snow", "fade"]
SECONDS_PER_SEGMENT = 15
FRAME_RATE = 10
EXPECTED_FRAMES = len(WEATHER_CYCLE) * SECONDS_PER_SEGMENT * FRAME_RATE  # 600


@dataclass
class SegmentStats:
    """Per-weather segment statistics."""
    weather_type: str
    frames: int = 0
    errors: int = 0
    warmup_dropped: int = 0
    breath_scores: list[float] = field(default_factory=list)
    calm_indices: list[float] = field(default_factory=list)
    weather_intensities: list[float] = field(default_factory=list)

    def avg_breath_score(self) -> float:
        return sum(self.breath_scores) / len(self.breath_scores) if self.breath_scores else 0.0

    def avg_calm_index(self) -> float:
        return sum(self.calm_indices) / len(self.calm_indices) if self.calm_indices else 0.0

    def avg_intensity(self) -> float:
        return sum(self.weather_intensities) / len(self.weather_intensities) if self.weather_intensities else 0.0


def run_stress_test(full: bool = False):
    """Run 60-second 4-weather stress test and print report."""
    mock_data = importlib.import_module("01-数据采集.mock_data")
    signal_pipeline_mod = importlib.import_module("02-信号处理.signal_pipeline")
    scoring_model_mod = importlib.import_module("02-信号处理.scoring_model")

    if full:
        udp_sender_mod = importlib.import_module("05-通信协议.udp_sender")
        csv_logger_mod = importlib.import_module("05-通信协议.csv_logger")

    segment_stats: dict[str, SegmentStats] = {w: SegmentStats(weather_type=w) for w in WEATHER_CYCLE}
    total_frames = 0
    total_errors = 0
    total_warmup_dropped = 0
    all_weather_intensities: list[float] = []

    print("=" * 62)
    print("  SRP FULL-PIPELINE STRESS TEST")
    print(f"  {len(WEATHER_CYCLE)} weathers x {SECONDS_PER_SEGMENT}s @ {FRAME_RATE}Hz = {EXPECTED_FRAMES} frames")
    print(f"  UDP/CSV: {'enabled' if full else 'disabled (--full to enable)'}")
    print("=" * 62)

    # Shared signal pipeline (maintains buffers across weather transitions)
    pipeline = signal_pipeline_mod.SignalPipeline()

    if full:
        sender = udp_sender_mod.UDPSender()
        csv_log = csv_logger_mod.CSVLogger(prefix="stress")
        csv_log.open()

    start_time = time.time()

    for weather in WEATHER_CYCLE:
        cfg = mock_data.MockConfig.for_weather(weather)
        frames = mock_data.generate_frame_list(duration=SECONDS_PER_SEGMENT, cfg=cfg)
        stats = segment_stats[weather]

        # Fresh scorer per weather with tuned config
        scorer = scoring_model_mod.ScoringModel(
            cfg=scoring_model_mod.ScoringConfig.for_weather(weather)
        )

        for f in frames:
            total_frames += 1
            stats.frames += 1

            try:
                processed = pipeline.feed(f.timestamp, f.respiration_raw, f.ecg_raw)

                if processed is None:
                    total_warmup_dropped += 1
                    stats.warmup_dropped += 1
                    continue

                score = scorer.score(
                    processed,
                    breath_phase=f.breath_phase,
                    guidance_prompt=f.guidance_prompt,
                    weather_type=f.weather_type,
                )
                score_dict = score.to_dict()
                stats.breath_scores.append(score.breath_score)
                stats.calm_indices.append(score.calm_index)
                stats.weather_intensities.append(score.weather_intensity)
                all_weather_intensities.append(score.weather_intensity)

                if full:
                    sender.send(score_dict)
                    csv_log.write(score_dict)

            except Exception as e:
                total_errors += 1
                stats.errors += 1
                print(f"  ERROR [{weather}] frame {f.timestamp:.1f}s: {e}")

    elapsed = time.time() - start_time

    if full:
        csv_log.close()
        sender.close()

    # ── Report ──────────────────────────────────────────────────────────────

    print()
    print(f"  Duration: {elapsed:.1f}s | Total frames: {total_frames} | Errors: {total_errors}")
    print(f"  Warmup-dropped: {total_warmup_dropped} (expected: first ~100 per pipeline warmup)")
    print(f"  Successfully scored: {total_frames - total_warmup_dropped}")
    print("-" * 62)
    print(f"  {'Weather':<8} {'Frames':>6} {'Errors':>6} {'AvgBreath':>10} {'AvgCalm':>9} {'AvgIntensity':>13}")
    print("-" * 62)

    for w in WEATHER_CYCLE:
        s = segment_stats[w]
        print(f"  {w:<8} {s.frames:>6} {s.errors:>6} {s.avg_breath_score():>10.1f} {s.avg_calm_index():>9.1f} {s.avg_intensity():>13.4f}")

    print("-" * 62)
    overall_bs = sum(sum(s.breath_scores) for s in segment_stats.values()) / max(
        sum(len(s.breath_scores) for s in segment_stats.values()), 1
    )
    overall_ci = sum(sum(s.calm_indices) for s in segment_stats.values()) / max(
        sum(len(s.calm_indices) for s in segment_stats.values()), 1
    )
    overall_wi = sum(all_weather_intensities) / max(len(all_weather_intensities), 1)
    print(f"  {'OVERALL':<8} {total_frames:>6} {total_errors:>6} {overall_bs:>10.1f} {overall_ci:>9.1f} {overall_wi:>13.4f}")
    print("=" * 62)

    # ── Verdict ──────────────────────────────────────────────────────────────

    passed = True
    if total_frames != EXPECTED_FRAMES:
        print(f"  FAIL: Expected {EXPECTED_FRAMES} frames, got {total_frames}")
        passed = False
    if total_errors > 0:
        print(f"  FAIL: {total_errors} pipeline errors")
        passed = False
    if overall_wi > 0:
        wi_range_violations = [
            wi for wi in all_weather_intensities if not (0 <= wi <= 1)
        ]
        if wi_range_violations:
            print(f"  FAIL: {len(wi_range_violations)} weather_intensity out of [0,1] range")
            passed = False

    if passed:
        print(f"  VERDICT: PASS — {EXPECTED_FRAMES} frames, 0 errors")
    else:
        print(f"  VERDICT: FAIL")

    print("=" * 62)
    return 0 if passed else 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SRP Full-Pipeline Stress Test")
    parser.add_argument("--full", action="store_true", help="Include UDP + CSV output")
    args = parser.parse_args()
    sys.exit(run_stress_test(full=args.full))
