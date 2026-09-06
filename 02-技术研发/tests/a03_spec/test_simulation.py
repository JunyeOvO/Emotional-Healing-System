from __future__ import annotations

from a03_gate2_spec.simulation import run_simulation


def test_simulation_is_deterministic_and_bounded():
    first = run_simulation(seed=17, replications=120)
    second = run_simulation(seed=17, replications=120)
    assert first == second
    for scenario in first["scenarios"].values():
        for analysis in scenario.values():
            assert all(0 <= value <= 1 for value in analysis["pass_probability"].values())


def test_simulation_covers_required_scenarios_and_analysis_sets():
    report = run_simulation(seed=21, replications=120)
    assert set(report["scenarios"]) == {
        "target", "null_manipulation", "ceiling", "differential_missing", "item_shift"
    }
    for scenario in report["scenarios"].values():
        assert set(scenario) == {"PRIMARY_CONSERVATIVE", "OBSERVED_CASE"}


def test_output_cannot_be_mistaken_for_formal_calibration():
    report = run_simulation(seed=22, replications=120)
    assert report["evidence_class"] == "SYNTHETIC_ONLY"
    assert report["formal_margins"] is None
    assert report["formal_sample_size"] is None
    assert report["decision"].startswith("SYNTHETIC_SENSITIVITY_POINT_")
