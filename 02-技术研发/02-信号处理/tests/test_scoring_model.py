"""
Tests for scoring_model.py
"""
import sys, os
from dataclasses import dataclass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import importlib
sm = importlib.import_module("02-信号处理.scoring_model")


@dataclass
class PF:
    timestamp: float = 0
    rr: float = 10.0
    respiration_amplitude: float = 0.5
    breath_regularity: float = 1.0
    hr: float = 70.0
    rmssd: float = 50.0
    respiration_raw: float = 0.5
    ecg_raw: float = 0.1


class TestScoringModel:
    def test_default_returns_neutral(self):
        model = sm.ScoringModel()
        result = model.score(None)
        assert result.breath_score == 50
        assert result.calm_index == 50
        assert result.weather_intensity == 0.5

    def test_perfect_scoring(self):
        model = sm.ScoringModel()
        pf = PF(rr=10.0, respiration_amplitude=0.5, breath_regularity=1.0,
                hr=70.0, rmssd=50.0)
        result = model.score(pf)
        assert result.breath_score > 80, f"Expected >80 got {result.breath_score}"
        assert result.calm_index > 50
        assert 0 <= result.weather_intensity <= 1

    def test_poor_scoring(self):
        model = sm.ScoringModel()
        pf = PF(rr=25.0, respiration_amplitude=0.1, breath_regularity=0.2,
                hr=110.0, rmssd=10.0)
        result = model.score(pf)
        assert result.breath_score < 40, f"Expected <40 got {result.breath_score}"

    def test_value_ranges(self):
        model = sm.ScoringModel()
        pf = PF(rr=12.0, respiration_amplitude=0.4, breath_regularity=0.6,
                hr=78.0, rmssd=35.0)
        result = model.score(pf)
        assert 0 <= result.breath_score <= 100
        assert 0 <= result.calm_index <= 100
        assert 0 <= result.weather_intensity <= 1


class TestPerWeatherScoring:
    def test_all_weathers_have_scoring_presets(self):
        for w in ["storm", "heat", "snow", "fade"]:
            assert w in sm.WEATHER_SCORING_PRESETS, f"Missing preset for {w}"

    def test_scoring_config_for_weather(self):
        cfg = sm.ScoringConfig.for_weather("heat")
        assert cfg.target_amplitude == 0.6
        assert cfg.w_breath == 0.45
        assert round(cfg.target_rr, 2) == 6.67

    def test_different_weathers_produce_different_scores(self):
        pf = PF(rr=6.0, respiration_amplitude=0.5, breath_regularity=0.8,
                hr=75.0, rmssd=45.0)
        storm_model = sm.ScoringModel(cfg=sm.ScoringConfig.for_weather("storm"))
        heat_model = sm.ScoringModel(cfg=sm.ScoringConfig.for_weather("heat"))
        storm_result = storm_model.score(pf)
        heat_result = heat_model.score(pf)
        assert storm_result.breath_score != heat_result.breath_score

    def test_scoring_model_with_weather_type(self):
        model = sm.ScoringModel(cfg=sm.ScoringConfig.for_weather("snow"))
        pf = PF(rr=6.0, respiration_amplitude=0.4, breath_regularity=0.7,
                hr=65.0, rmssd=50.0)
        result = model.score(pf)
        assert 0 <= result.breath_score <= 100
