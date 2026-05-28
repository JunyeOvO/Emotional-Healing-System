#!/usr/bin/env python3
"""
SRP Data Pipeline — Main Entry Point (Sprint 0 v0.3)
======================================================
Multi-sensor data pipeline: mock data → signal processing → 8 independent scores → weather composite → UDP + CSV.

Usage:
  python main.py --weather storm --duration 60
  python main.py --weather heat --duration 0    # infinite until Ctrl+C
  python main.py --weather snow --no-udp        # offline CSV only
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


def _import(module_name: str):
    return importlib.import_module(module_name)


def run_pipeline(args: argparse.Namespace):
    dur_label = f"{args.duration:.0f}s" if args.duration > 0 else "infinite (Ctrl+C to stop)"
    logger.info("=" * 60)
    logger.info("SRP Data Pipeline — Multi-Sensor Mode")
    logger.info(f"Mode: {'Mock' if args.mock else 'Real Device'} | "
                f"Duration: {dur_label} | Weather: {args.weather}")
    logger.info("")
    logger.info("  For live dashboard, run:  python visualizer.py --weather " + args.weather)
    logger.info("  This is the headless pipeline (UDP + CSV only).")
    logger.info("=" * 60)

    # --- Phase 1: Data Source ---
    if args.mock:
        mock_data = _import("01-数据采集.mock_data")
        cfg = mock_data.MockConfig.for_weather(args.weather)
        frame_generator = mock_data.generate_frames(duration=args.duration, cfg=cfg)
        logger.info(f"Mock data: {args.weather} weather, 10Hz, 8 signals")
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
    logger.info("Pipeline + 8-dim scoring model initialized")

    # --- Phase 3: Outputs ---
    udp_sender_mod = _import("05-通信协议.udp_sender")
    csv_logger_mod = _import("05-通信协议.csv_logger")
    sender = udp_sender_mod.UDPSender() if not args.no_udp else None
    csv_log = csv_logger_mod.CSVLogger(prefix=f"sim_{args.weather}")
    csv_log.open()
    if sender:
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
                guidance_prompt=mock_frame.guidance_prompt,
                weather_type=mock_frame.weather_type,
            )

            score_dict = score.to_dict()
            if sender:
                sender.send(score_dict)
            csv_log.write(score_dict)
            processed_count += 1

            # Real-time pacing: 10Hz = 0.1s per frame
            time.sleep(0.1)

            if frame_idx % 50 == 0:
                elapsed = time.time() - start_time
                logger.info(
                    f"  [{elapsed:.0f}s] f={frame_idx} | "
                    f"BS={score.breath_sync:.0f} HS={score.hr_stability:.0f} "
                    f"HRV={score.hrv_recovery:.0f} RM={score.rate_match:.0f} "
                    f"DQ={score.depth_quality:.0f} RG={score.regularity:.0f} "
                    f"EDA={score.eda_calm:.0f} MS={score.motion_stillness:.0f} | "
                    f"WX={score.weather_composite:.0f} {score.weather_trend}"
                )

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
    finally:
        csv_log.close()
        if sender:
            sender.close()

        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"Pipeline complete in {elapsed:.1f}s")
        logger.info(f"Frames generated: {frame_idx}")
        logger.info(f"Frames processed: {processed_count}")
        if sender:
            logger.info(f"UDP: {sender.stats()}")
        logger.info(f"CSV: {csv_log.stats()}")
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="SRP Multi-Sensor Data Pipeline — 8 scores → weather composite",
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
