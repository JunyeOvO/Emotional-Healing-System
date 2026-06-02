#!/usr/bin/env python3
"""
SRP Data Pipeline — Main Entry Point v0.4
===========================================
4-dimension physiological pipeline:
  mock data → signal processing → 4 independent scores → weather composite → UDP + CSV.

4 dimensions (non-overlapping ANS pathways):
  breath_sync    RR tracking accuracy     呼吸→副交感    PLUX呼吸带
  breath_depth   Amplitude / RSA depth    呼吸→副交感    PLUX呼吸带
  hrv_coherence  RMSSD recovery           副交感(迷走)   Polar H10
  eda_calm       SCL decrease             交感(皮肤电)   EDA腕带

Usage:
  python main.py --weather storm --duration 60
  python main.py --weather heat --duration 0     # infinite until Ctrl+C
  python main.py --weather snow --no-udp         # offline CSV only
"""

import sys
import os
import time
import argparse
import logging
import signal
import importlib

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

# How often to print each type of status
COMPACT_INTERVAL = 50     # every 5s: compact 1-line status
DETAIL_INTERVAL = 300     # every 30s: detailed 4-dimension table


def _import(module_name: str):
    return importlib.import_module(module_name)


def run_pipeline(args: argparse.Namespace):
    dur_label = f"{args.duration:.0f}s" if args.duration > 0 else "infinite (Ctrl+C to stop)"
    mock_label = "Mock" if args.mock else "Real Device"

    # ── Startup header ────────────────────────────────────────────────────
    dim_spec = _import("02-信号处理.dimension_spec")
    presets = dim_spec.WEATHER_DIMENSION_PRESETS.get(
        args.weather, dim_spec.WEATHER_DIMENSION_PRESETS["storm"]
    )

    logger.info("=" * 60)
    logger.info(f"  SRP Data Pipeline v0.4 — 4-Dimension Mode")
    logger.info(f"  Mode: {mock_label} | Duration: {dur_label} | Weather: {args.weather}")
    logger.info("")
    logger.info(dim_spec.format_dimension_header(args.weather, presets))
    logger.info("")
    logger.info("  For live dashboard:  python visualizer.py --weather " + args.weather)
    logger.info("=" * 60)

    # ── Phase 1: Data Source ──────────────────────────────────────────────
    if args.mock:
        mock_data = _import("01-数据采集.mock_data")
        cfg = mock_data.MockConfig.for_weather(args.weather)
        frame_generator = mock_data.generate_frames(duration=args.duration, cfg=cfg)
    else:
        logger.error("Real device mode not yet implemented (stage 3)")
        sys.exit(1)

    # ── Phase 2: Signal Processing ────────────────────────────────────────
    signal_pipeline_mod = _import("02-信号处理.signal_pipeline")
    scoring_model_mod = _import("02-信号处理.scoring_model")
    pipeline = signal_pipeline_mod.SignalPipeline()
    scorer = scoring_model_mod.ScoringModel(
        cfg=scoring_model_mod.ScoringConfig.for_weather(args.weather)
    )

    # ── Phase 3: Outputs ──────────────────────────────────────────────────
    udp_sender_mod = _import("05-通信协议.udp_sender")
    csv_logger_mod = _import("05-通信协议.csv_logger")
    sender = udp_sender_mod.UDPSender() if not args.no_udp else None
    csv_log = csv_logger_mod.CSVLogger(prefix=f"sim_{args.weather}")
    csv_log.open()
    if sender:
        logger.info(f"UDP → {[f'{h}:{p}' for h, p in sender.targets]}")
    logger.info(f"CSV → {csv_log.filename}")
    logger.info("Pipeline running... (Ctrl+C to stop)")
    logger.info("")

    # ── Dimension scoring targets for display ─────────────────────────────
    dim_targets = {
        "breath_sync": presets.breath_sync.target_value,
        "breath_depth": presets.breath_depth.target_value,
        "hrv_coherence": presets.hrv_coherence.target_value,
        "eda_calm": presets.eda_calm.target_value,
    }

    # ── Phase 4: Main Loop ────────────────────────────────────────────────
    start_time = time.time()
    frame_idx = 0
    processed_count = 0
    shutdown = False

    def handle_signal(signum, frame):
        nonlocal shutdown
        logger.info("Shutdown signal received, stopping...")
        shutdown = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        for mock_frame in frame_generator:
            if shutdown:
                break

            frame_idx += 1

            processed = pipeline.feed(
                mock_frame.timestamp,
                mock_frame.respiration_raw,
                mock_frame.ecg_raw,
                mock_frame.eda_raw,
                mock_frame.acc_magnitude,
                mock_frame.temp_skin,
            )

            score = scorer.score(
                processed,
                breath_phase=mock_frame.breath_phase,
                respiration_depth=mock_frame.respiration_depth,
                guidance_prompt=mock_frame.guidance_prompt,
                weather_type=mock_frame.weather_type,
            )

            score_dict = score.to_dict()
            if sender:
                sender.send(score_dict)
            csv_log.write(score_dict)
            processed_count += 1

            # Real-time pacing: 10 Hz → 100ms per frame
            time.sleep(0.1)

            # ── Console Status ────────────────────────────────────────────
            if frame_idx % COMPACT_INTERVAL == 0:
                elapsed = time.time() - start_time
                _log_compact(elapsed, frame_idx, score, dim_targets)
            if frame_idx % DETAIL_INTERVAL == 0:
                elapsed = time.time() - start_time
                _log_detailed(elapsed, frame_idx, score, dim_targets, logger)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
    finally:
        csv_log.close()
        if sender:
            sender.close()

        elapsed = time.time() - start_time
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"  Pipeline complete in {elapsed:.1f}s")
        logger.info(f"  Frames generated: {frame_idx}")
        logger.info(f"  Frames processed: {processed_count}")
        logger.info(f"  Drop rate: {100*(frame_idx-processed_count)/max(frame_idx,1):.1f}%")
        if sender:
            logger.info(f"  UDP: {sender.stats()}")
        logger.info(f"  CSV: {csv_log.stats()}")
        logger.info("=" * 60)


# ── Console Output Formatters ─────────────────────────────────────────────

def _log_compact(elapsed: float, frame_idx: int, score, targets: dict):
    """Compact single-line status showing 4 dimensions with raw→target values."""
    sync_str = f"sync={score.breath_sync:4.0f}(RR{score.rr:.0f}→{targets['breath_sync']:.0f}bpm)"
    depth_str = f"depth={score.breath_depth:4.0f}(amp{score.respiration_amplitude:.2f})"
    hrv_str = f"hrv={score.hrv_coherence:4.0f}(RMS{score.rmssd:.0f}→{targets['hrv_coherence']:.0f}ms)"
    eda_str = f"eda={score.eda_calm:4.0f}(SCL{score.eda_tonic:.1f}μS)"

    trend_icon = {"weakening": "↓", "stable": "→", "intensifying": "↑"}.get(
        score.weather_trend, "?")
    calm_str = f"calm={score.calm_index:.0f} {score.weather_type}{trend_icon}"

    logger.info(
        f"[{elapsed:5.0f}s] f={frame_idx:>4d} | "
        f"{sync_str} {depth_str} {hrv_str} {eda_str} | {calm_str}"
    )


def _log_detailed(elapsed: float, frame_idx: int, score, targets: dict, log):
    """Detailed 4-dimension table, printed every DETAIL_INTERVAL frames."""
    dim_spec_mod = _import("02-信号处理.dimension_spec")

    raw_vals = {
        "breath_sync": score.rr,
        "breath_depth": score.respiration_amplitude,
        "hrv_coherence": score.rmssd,
        "eda_calm": score.eda_tonic,
    }
    scores = {
        "breath_sync": score.breath_sync,
        "breath_depth": score.breath_depth,
        "hrv_coherence": score.hrv_coherence,
        "eda_calm": score.eda_calm,
    }

    report = dim_spec_mod.format_dimension_report(
        scores=scores,
        raw_values=raw_vals,
        targets=targets,
        calm_index=score.calm_index,
        weather_type=score.weather_type,
        weather_intensity=score.weather_intensity,
        weather_trend=score.weather_trend,
    )
    log.info(f"[{elapsed:.0f}s] f={frame_idx} — Detailed Report:\n" + report)


def main():
    parser = argparse.ArgumentParser(
        description="SRP 4-Dimension Physiological Pipeline — mock → scores → UDP + CSV",
    )
    parser.add_argument("--mock", action="store_true", default=True,
                        help="Use simulated data (default)")
    parser.add_argument("--real", action="store_true",
                        help="Use real devices (stage 3)")
    parser.add_argument("--duration", type=float, default=60.0,
                        help="Runtime in seconds. 0 = until Ctrl+C (default: 60)")
    parser.add_argument("--weather", type=str, default="storm",
                        choices=["storm", "heat", "snow", "fade"],
                        help="Weather type (default: storm)")
    parser.add_argument("--no-udp", action="store_true",
                        help="Disable UDP sending")

    args = parser.parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
