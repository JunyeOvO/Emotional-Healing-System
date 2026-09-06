from __future__ import annotations

import json
from pathlib import Path

from a03_gate2_spec import GateEvidence, GateResult, evaluate_ordered_gate


ALL_PASS = GateEvidence(*([GateResult.PASS] * 6))
FROZEN_FIXTURE = {
    "noninferiority_margins": "fixture",
    "critical_layers": "fixture",
    "missing_data_rule": "fixture",
    "sample_size": "fixture",
}


def test_gate_requires_formal_freeze_before_evaluation():
    result = evaluate_ordered_gate(ALL_PASS, freeze_reasons={})
    assert result["result"] == "NOT_EVALUABLE"
    assert result["reason_code"] == "FORMAL_PARAMETERS_NOT_FROZEN"


def test_gate_stops_at_first_failure_without_compensation():
    evidence = GateEvidence(
        GateResult.PASS,
        GateResult.FAIL,
        GateResult.PASS,
        GateResult.PASS,
        GateResult.PASS,
        GateResult.PASS,
    )
    result = evaluate_ordered_gate(evidence, freeze_reasons=FROZEN_FIXTURE)
    assert result["result"] == "FAIL"
    assert result["stopped_at"] == "scci_direction"


def test_gate_passes_only_when_every_component_passes():
    result = evaluate_ordered_gate(ALL_PASS, freeze_reasons=FROZEN_FIXTURE)
    assert result["result"] == "PASS"


def test_freeze_reason_fixture_covers_missing_and_candidate_cases():
    fixture = Path(__file__).resolve().parents[2] / "02-信号处理" / "a03_gate2_spec" / "fixtures" / "scoring_edge_cases_v1.0.json"
    cases = json.loads(fixture.read_text(encoding="utf-8"))["freeze_cases"]
    observed = [
        evaluate_ordered_gate(ALL_PASS, freeze_reasons=case["freeze_reasons"])["reason_code"]
        for case in cases
    ]
    assert observed == [case["expected"] for case in cases]
