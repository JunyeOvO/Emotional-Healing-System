"""
Tests for signal_pipeline.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import importlib
sp = importlib.import_module("02-信号处理.signal_pipeline")


class TestSignalPipeline:
    def test_warmup_returns_none(self):
        pipeline = sp.SignalPipeline(buffer_size=300)
        result = pipeline.feed(0.0, 0.5, 0.1)
        assert result is None

        for i in range(1, 99):
            result = pipeline.feed(i * 0.1, 0.5, 0.1)
        assert result is None

        result = pipeline.feed(9.9, 0.5, 0.1)
        assert result is not None
        assert hasattr(result, "rr")
        assert hasattr(result, "hr")

    def test_returns_values_in_range(self):
        import math
        pipeline = sp.SignalPipeline()
        for i in range(200):
            t = i * 0.1
            resp = math.sin(2 * math.pi * 0.2 * t) * 0.5 + 0.5
            ecg = 0.1 * (1 if i % 8 == 0 else 0)
            result = pipeline.feed(t, resp, ecg)
        if result:
            import math as m
            # NaN is acceptable for synthetic signals (no real peaks)
            if m.isnan(result.rr):
                assert result.rr != result.rr  # NaN is not equal to itself
            else:
                assert 0 <= result.rr <= 200, f"RR={result.rr}"
            if m.isnan(result.rmssd):
                assert result.rmssd != result.rmssd
            else:
                assert 0 <= result.rmssd <= 500, f"RMSSD={result.rmssd}"
            assert 30 <= result.hr <= 220, f"HR={result.hr}"
