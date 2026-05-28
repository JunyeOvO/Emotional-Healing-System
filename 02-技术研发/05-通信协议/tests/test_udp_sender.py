"""
Tests for udp_sender.py (v0.3 — 8 independent scores)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import importlib
udp = importlib.import_module("05-通信协议.udp_sender")


class TestBuildMessage:
    def test_all_fields_present(self):
        score_dict = {
            "timestamp": 1000.0,
            "breath_sync": 72.5, "hr_stability": 68.0, "hrv_recovery": 55.3,
            "rate_match": 60.2, "depth_quality": 58.1, "regularity": 65.7,
            "eda_calm": 70.8, "motion_stillness": 82.4,
            "weather_composite": 65.0, "weather_intensity": 0.32,
            "weather_trend": "weakening", "dominant_domain": "eda_calm",
            "weather_type": "storm", "breath_phase": "inhale",
            "rr": 14.2, "hr": 72.0, "rmssd": 45.2,
            "respiration_raw": 0.5, "respiration_amplitude": 0.4,
            "breath_regularity_raw": 0.6,
            "ecg_raw": 0.1, "eda_raw": 7.2, "eda_tonic": 7.0,
            "acc_magnitude": 0.03, "motion_index": 0.025,
            "temp_skin": 34.1, "guidance_prompt": "test",
        }
        msg = udp.build_message(score_dict)
        assert msg["version"] == "1.0"
        assert "scores" in msg
        assert "breath" in msg
        assert "cardiac" in msg
        assert "aux" in msg
        assert "weather" in msg
        assert "guidance" in msg
        assert len(msg["scores"]) == 8
        assert msg["scores"]["breath_sync"] == 72.5
        assert msg["weather"]["composite"] == 65.0
        assert msg["weather"]["intensity"] == 0.32
        assert msg["weather"]["type"] == "storm"
        assert msg["cardiac"]["hr"] == 72.0
        assert msg["aux"]["eda_tonic"] == 7.0


class TestUDPSender:
    def test_send_to_localhost(self):
        sender = udp.UDPSender(targets=[("127.0.0.1", 50999)])
        score_dict = {
            "timestamp": 1000.0,
            "breath_sync": 72.5, "hr_stability": 68.0, "hrv_recovery": 55.3,
            "rate_match": 60.2, "depth_quality": 58.1, "regularity": 65.7,
            "eda_calm": 70.8, "motion_stillness": 82.4,
            "weather_composite": 65.0, "weather_intensity": 0.32,
            "weather_trend": "weakening", "dominant_domain": "breath_sync",
            "weather_type": "storm", "breath_phase": "inhale",
            "rr": 14.2, "hr": 72.0, "rmssd": 45.2,
            "respiration_raw": 0.5, "respiration_amplitude": 0.4,
            "breath_regularity_raw": 0.6,
            "ecg_raw": 0.1, "eda_raw": 7.2, "eda_tonic": 7.0,
            "acc_magnitude": 0.03, "motion_index": 0.025,
            "temp_skin": 34.1, "guidance_prompt": "test",
        }
        ok = sender.send(score_dict)
        assert ok, "Send failed"
        assert sender.stats()["frames_sent"] == 1
        sender.close()
