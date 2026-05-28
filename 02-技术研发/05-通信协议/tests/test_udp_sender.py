"""
Tests for udp_sender.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import importlib
udp = importlib.import_module("05-通信协议.udp_sender")


class TestBuildMessage:
    def test_all_fields_present(self):
        score_dict = {
            "timestamp": 1000.0, "breath_score": 72.5, "calm_index": 68.3,
            "rr": 14.2, "hr": 72.0, "rmssd": 45.2,
            "weather_intensity": 0.32, "weather_trend": "weakening",
            "weather_type": "storm", "breath_phase": "inhale",
            "guidance_prompt": "test", "respiration_raw": 0.5,
            "ecg_raw": 0.1,
        }
        msg = udp.build_message(score_dict)
        assert msg["version"] == "1.0"
        assert "breath" in msg
        assert "calm" in msg
        assert "hrv" in msg
        assert "weather" in msg
        assert "guidance" in msg
        assert msg["breath"]["score"] == 72.5
        assert msg["calm"]["weather_intensity"] == 0.32
        assert msg["hrv"]["hr"] == 72.0
        assert msg["weather"]["type"] == "storm"


class TestUDPSender:
    def test_send_to_localhost(self):
        sender = udp.UDPSender(targets=[("127.0.0.1", 50999)])
        score_dict = {
            "timestamp": 1000.0, "breath_score": 72.5,
            "calm_index": 68.3, "rr": 14.2, "hr": 72.0,
            "rmssd": 45.2, "weather_intensity": 0.32,
            "weather_trend": "weakening", "weather_type": "storm",
            "breath_phase": "inhale", "guidance_prompt": "test",
            "respiration_raw": 0.5, "ecg_raw": 0.1,
            "breath_sync": 70.0, "hrv_score": 65.0,
            "regularity_score": 60.0, "depth_score": 55.0,
        }
        ok = sender.send(score_dict)
        assert ok, "Send failed"
        assert sender.stats()["frames_sent"] == 1
        sender.close()
