"""Tests for FrameClock — 10 Hz frame assembler."""

import time
import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)
from ring_buffer import RingBuffer
from frame_clock import FrameClock, RawFrame


def test_frame_clock_output():
    """Frame clock produces RawFrames at ~10 Hz from ring buffers."""
    ecg = RingBuffer(2000)
    resp = RingBuffer(500)
    eda = RingBuffer(200)

    # Pre-fill buffers with sample data
    for i in range(20):
        ecg.push(time.time(), float(i) * 0.1)
        resp.push(time.time(), float(i) * 0.05)
        eda.push(time.time(), 5.0 + float(i) * 0.01)

    clock = FrameClock(
        ecg_buf=ecg, resp_buf=resp, eda_buf=eda, rate_hz=10.0
    )
    clock.ecg_connected = True
    clock.resp_connected = True
    clock.eda_connected = True

    clock.start()
    time.sleep(0.5)  # collect ~5 frames
    clock.stop()
    clock.join(timeout=1.0)

    frames = []
    while not clock.output_queue.empty():
        frames.append(clock.output_queue.get_nowait())

    assert len(frames) >= 3, f"Expected >=3 frames, got {len(frames)}"
    print(f"Collected {len(frames)} frames in 0.5s (~{len(frames)*2:.0f} Hz effective)")

    # Each frame should be a RawFrame with expected fields
    for f in frames:
        assert isinstance(f, RawFrame)
        assert f.timestamp > 0
        assert isinstance(f.respiration_raw, float)
        assert isinstance(f.ecg_raw, float)
        assert isinstance(f.eda_raw, float)


def test_missing_device():
    """Frame with no connected devices should produce zero-valued channels."""
    clock = FrameClock(rate_hz=10.0)
    clock.start()
    time.sleep(0.3)
    clock.stop()
    clock.join(timeout=1.0)

    frame = clock.output_queue.get_nowait()
    assert frame.ecg_raw == 0.0
    assert frame.respiration_raw == 0.0
    assert frame.eda_raw == 0.0
    assert frame.temp_skin == 34.0  # neutral default


def test_downsampling():
    """ECG downsampling: 13 samples → 1 averaged value."""
    ecg = RingBuffer(2000)
    for i in range(13):
        ecg.push(time.time(), float(i + 1))  # 1..13

    clock = FrameClock(ecg_buf=ecg, rate_hz=10.0)
    clock.ecg_connected = True
    clock.start()
    time.sleep(0.2)
    clock.stop()
    clock.join(timeout=1.0)

    frame = clock.output_queue.get_nowait()
    # mean of [1..13] = 7.0
    assert 6.5 < frame.ecg_raw < 7.5, f"Expected ~7.0, got {frame.ecg_raw}"


if __name__ == "__main__":
    test_frame_clock_output()
    test_missing_device()
    test_downsampling()
    print("All FrameClock tests passed.")
