"""Ordered Gate 2 decision semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class GateResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EVALUABLE = "NOT_EVALUABLE"


@dataclass(frozen=True)
class GateEvidence:
    applicability: GateResult
    scci_direction: GateResult
    comprehension_total: GateResult
    comprehension_critical_layers: GateResult
    effort: GateResult
    stage_error: GateResult


ORDERED_COMPONENTS = (
    "applicability",
    "scci_direction",
    "comprehension_total",
    "comprehension_critical_layers",
    "effort",
    "stage_error",
)

REQUIRED_FREEZE_KEYS = {
    "noninferiority_margins",
    "critical_layers",
    "missing_data_rule",
    "sample_size",
}


def evaluate_ordered_gate(
    evidence: GateEvidence, *, freeze_reasons: Mapping[str, str]
) -> dict[str, object]:
    """Evaluate without allowing a later component to compensate an earlier one."""
    if not REQUIRED_FREEZE_KEYS.issubset(freeze_reasons) or any(
        not freeze_reasons[key] for key in REQUIRED_FREEZE_KEYS & set(freeze_reasons)
    ):
        return {
            "result": GateResult.NOT_EVALUABLE.value,
            "stopped_at": "formal_parameters",
            "reason_code": "FORMAL_PARAMETERS_NOT_FROZEN",
        }
    for component in ORDERED_COMPONENTS:
        result = getattr(evidence, component)
        if result != GateResult.PASS:
            return {
                "result": result.value,
                "stopped_at": component,
                "reason_code": (
                    f"{component.upper()}_FAILED"
                    if result == GateResult.FAIL
                    else f"{component.upper()}_NOT_EVALUABLE"
                ),
            }
    return {"result": GateResult.PASS.value, "stopped_at": None, "reason_code": "ALL_ORDERED_COMPONENTS_PASS"}
