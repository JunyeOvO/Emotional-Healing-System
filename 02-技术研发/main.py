#!/usr/bin/env python3
"""
SRP Data Pipeline — Main Entry Point (Sprint 0)
=================================================
Orchestrates the full pipeline: mock data → signal processing → scoring → UDP + CSV.

Usage:
  python main.py --mock --duration 60
  python main.py --mock --weather storm --duration 30
  python main.py --real          # (stage 3, when Polar H10 connected)
"""

import sys
import os
import time
import argparse
import logging
import signal
import importlib

# Ensure we can import subpackages from 02-技术研发/
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


# ── Module imports (via importlib for Chinese dirnames) ─────────────────────

def _import(module_name: str):
    """Import module by name (handles Chinese dirnames)."""
    return importlib.import_module(module_name)


# ── Main Pipeline ──────────────────────────────────────────────────────────

def run_pipeline(args: argparse.Namespace):
    """Execute the full data pipeline.

    Args:
        args: Parsed command-line arguments.
    """
    logger.info("=" * 60)
    logger.info("SRP Data Pipeline — Starting")
    dur_label = f"{args.duration:.0f}s" if args.duration > 0 else "infinite (Ctrl+C to stop)"
    logger.info(f"Mode: {'Mock' if args.mock else 'Real Device'} | "
                f"Duration: {dur_label} | Weather: {args.weather}")
    logger.info("=" * 60)

    # --- Phase 1: Data Source ---
    if args.mock:
        mock_data = _import("01-数据采集.mock_data")
        cfg = mock_data.MockConfig(
            weather_type=args.weather,
            frame_rate=10.0,
        )
        frame_generator = mock_data.generate_frames(duration=args.duration, cfg=cfg)
        logger.info(f"Mock data generator: {args.weather} weather, 10Hz")
    else:
        logger.error("Real device mode not yet implemented (stage 3)")
        sys.exit(1)

    # --- Phase 2: Signal Processing ---
    signal_pipeline_mod = _import("02-信号处理.signal_pipeline")
    scoring_model_mod = _import("02-信号处理.scoring_model")
    pipeline = signal_pipeline_mod.SignalPipeline()
    scorer = scoring_model_mod.ScoringModel(
        cfg=scoring_model_mod.ScoringConfig.for_weather(args.weather)
    )
    logger.info("Signal pipeline + scoring model initialized")

    # --- Phase 3: Outputs ---
    udp_sender_mod = _import("05-通信协议.udp_sender")
    csv_logger_mod = _import("05-通信协议.csv_logger")
    sender = udp_sender_mod.UDPSender()
    csv_log = csv_logger_mod.CSVLogger(prefix=f"sim_{args.weather}")
    csv_log.open()
    logger.info(f"UDP targets: {[f'{h}:{p}' for h, p in sender.targets]}")
    logger.info(f"CSV log: {csv_log.filename}")

    # --- Phase 4: Main Loop ---
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

            # Feed into signal pipeline
            processed = pipeline.feed(
                mock_frame.timestamp,
                mock_frame.respiration_raw,
                mock_frame.ecg_raw,
            )

            # Score (use neutral frame during warmup)
            score = scorer.score(
                processed,
                breath_phase=mock_frame.breath_phase,
                guidance_prompt=mock_frame.guidance_prompt,
                weather_type=mock_frame.weather_type,
            )

            # Output
            score_dict = score.to_dict()
            sender.send(score_dict)
            csv_log.write(score_dict)
            processed_count += 1

            # Progress every 5 seconds
            if frame_idx % 50 == 0:
                elapsed = time.time() - start_time
                logger.info(
                    f"  [{elapsed:.0f}s] frames={frame_idx} "
                    f"breath_score={score.breath_score:.1f} "
                    f"calm_index={score.calm_index:.1f} "
                    f"weather={score.weather_intensity:.2f}"
                )

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
    finally:
        # --- Cleanup ---
        csv_log.close()
        sender.close()

        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"Pipeline complete in {elapsed:.1f}s")
        logger.info(f"Frames generated: {frame_idx}")
        logger.info(f"Frames processed: {processed_count}")
        logger.info(f"UDP: {sender.stats()}")
        logger.info(f"CSV: {csv_log.stats()}")
        logger.info("=" * 60)


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SRP Data Pipeline — Mock data → Scoring → UDP + CSV",
    )
    parser.add_argument(
        "--mock", action="store_true", default=True,
        help="Use simulated data (default)",
    )
    parser.add_argument(
        "--real", action="store_true",
        help="Use real Polar H10 device (stage 3 only)",
    )
    parser.add_argument(
        "--duration", type=float, default=60.0,
        help="Pipeline runtime in seconds. 0 = run until Ctrl+C (default: 60)",
    )
    parser.add_argument(
        "--weather", type=str, default="storm",
        choices=["storm", "heat", "snow", "fade"],
        help="Weather type for demo (default: storm)",
    )
    parser.add_argument(
        "--no-udp", action="store_true",
        help="Disable UDP sending (for offline testing)",
    )

    args = parser.parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
