"""Deterministic bounded Monte Carlo for A-03-SPEC sensitivity checks."""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, variance


@dataclass(frozen=True)
class Scenario:
    name: str
    scci_shift: float
    comprehension_native: float
    comprehension_abstract: float
    effort_native: float
    effort_abstract: float
    stage_error_native: float
    stage_error_abstract: float
    skipped_rate: float = 0.02
    technical_rate: float = 0.01


SCENARIOS = (
    Scenario("target", 0.75, 0.82, 0.84, 4.2, 4.0, 0.08, 0.07),
    Scenario("null_manipulation", 0.00, 0.82, 0.84, 4.2, 4.0, 0.08, 0.07),
    Scenario("ceiling", 0.65, 0.94, 0.95, 3.0, 2.9, 0.03, 0.03),
    Scenario("differential_missing", 0.75, 0.80, 0.84, 4.5, 4.0, 0.10, 0.07, 0.12, 0.05),
    Scenario("item_shift", 0.40, 0.82, 0.84, 4.2, 4.0, 0.08, 0.07),
)

SYNTHETIC_THRESHOLDS = {
    "scci_min_difference": 0.35,
    "comprehension_min_difference": -0.75,
    "critical_layer_min_difference": -1.25,
    "effort_max_difference": 1.00,
    "stage_error_max_difference": 0.08,
}


def _bounded_round(value: float, low: int, high: int) -> int:
    return min(high, max(low, int(round(value))))


def _bounded_beta(
    rng: random.Random, center: float, low: int, high: int, concentration: float
) -> int:
    proportion = min(0.99, max(0.01, (center - low) / (high - low)))
    value = low + (high - low) * rng.betavariate(
        proportion * concentration, (1 - proportion) * concentration
    )
    return _bounded_round(value, low, high)


def _participant(rng: random.Random, scenario: Scenario, native: bool) -> dict[str, object]:
    base_scci = 3.0 + (scenario.scci_shift if native else 0.0)
    scci = [_bounded_beta(rng, base_scci, 1, 5, 8.0) for _ in range(4)]
    if scenario.name == "item_shift" and native:
        scci[-1] = _bounded_round(scci[-1] - 1.0, 1, 5)

    probability = scenario.comprehension_native if native else scenario.comprehension_abstract
    comprehension: list[int | None] = []
    statuses: list[str] = []
    for _ in range(8):
        draw = rng.random()
        if draw < scenario.technical_rate:
            comprehension.append(None)
            statuses.append("TECH_UNPRESENTED")
        elif draw < scenario.technical_rate + scenario.skipped_rate:
            comprehension.append(None)
            statuses.append("SKIPPED")
        else:
            comprehension.append(int(rng.random() < probability))
            statuses.append("RESPONDED")
    effort_center = scenario.effort_native if native else scenario.effort_abstract
    effort = _bounded_beta(rng, effort_center, 1, 9, 10.0)
    stage_probability = scenario.stage_error_native if native else scenario.stage_error_abstract
    stage_errors = sum(rng.random() < stage_probability for _ in range(16)) / 16
    return {
        "scci": mean(scci),
        "comprehension": comprehension,
        "statuses": statuses,
        "effort": effort,
        "stage_errors": stage_errors,
    }


def _comprehension_score(row: dict[str, object], analysis_set: str) -> float:
    values = row["comprehension"]
    statuses = row["statuses"]
    assert isinstance(values, list) and isinstance(statuses, list)
    kept: list[int] = []
    for value, status in zip(values, statuses, strict=True):
        if status == "TECH_UNPRESENTED":
            continue
        if value is None:
            if analysis_set == "PRIMARY_CONSERVATIVE":
                kept.append(0)
        else:
            kept.append(int(value))
    return 8 * mean(kept) if kept else math.nan


def _layer_scores(row: dict[str, object], analysis_set: str) -> list[float]:
    values = row["comprehension"]
    statuses = row["statuses"]
    assert isinstance(values, list) and isinstance(statuses, list)
    scores = []
    for start in range(0, 8, 2):
        layer_row = {"comprehension": values[start:start + 2], "statuses": statuses[start:start + 2]}
        full_scale_score = _comprehension_score(layer_row, analysis_set)
        scores.append(full_scale_score / 4 if not math.isnan(full_scale_score) else math.nan)
    return scores


def _contrast(rows: list[dict[str, object]], field: str) -> tuple[float, float]:
    native = [float(row[field]) for row in rows if row["condition"] == "scene_native"]
    abstract = [float(row[field]) for row in rows if row["condition"] == "abstract_pacer"]
    if len(native) < 2 or len(abstract) < 2:
        return math.nan, math.nan
    difference = mean(native) - mean(abstract)
    standard_error = math.sqrt(variance(native) / len(native) + variance(abstract) / len(abstract))
    return difference, standard_error


def _one_experiment(
    rng: random.Random, scenario: Scenario, per_condition: int, analysis_set: str
) -> dict[str, bool]:
    rows: list[dict[str, object]] = []
    for native in (False, True):
        for _ in range(per_condition):
            row = _participant(rng, scenario, native)
            row["condition"] = "scene_native" if native else "abstract_pacer"
            row["comprehension_score"] = _comprehension_score(row, analysis_set)
            for layer_index, layer_score in enumerate(_layer_scores(row, analysis_set)):
                row[f"layer_{layer_index}"] = layer_score
            rows.append(row)
    rows = [row for row in rows if not math.isnan(float(row["comprehension_score"]))]
    z95 = 1.96
    scci_difference, scci_se = _contrast(rows, "scci")
    comprehension_difference, comprehension_se = _contrast(rows, "comprehension_score")
    effort_difference, effort_se = _contrast(rows, "effort")
    stage_difference, stage_se = _contrast(rows, "stage_errors")
    layer_contrasts = [
        _contrast(
            [row for row in rows if not math.isnan(float(row[f"layer_{index}"]))],
            f"layer_{index}",
        )
        for index in range(4)
    ]
    checks = {
        "scci": scci_difference - z95 * scci_se >= SYNTHETIC_THRESHOLDS["scci_min_difference"],
        "comprehension": comprehension_difference - z95 * comprehension_se >= SYNTHETIC_THRESHOLDS["comprehension_min_difference"],
        "critical_layers": all(
            difference - z95 * standard_error >= SYNTHETIC_THRESHOLDS["critical_layer_min_difference"]
            for difference, standard_error in layer_contrasts
        ),
        "effort": effort_difference + z95 * effort_se <= SYNTHETIC_THRESHOLDS["effort_max_difference"],
        "stage_error": stage_difference + z95 * stage_se <= SYNTHETIC_THRESHOLDS["stage_error_max_difference"],
    }
    checks["joint"] = all(checks.values())
    return checks


def run_simulation(
    *,
    seed: int = 20260906,
    replications: int = 1000,
    per_condition: int = 24,
    decision_scope: str = "sensitivity_point",
) -> dict[str, object]:
    if replications < 100 or per_condition < 2:
        raise ValueError("SIMULATION_BUDGET_TOO_SMALL")
    if decision_scope not in {"sensitivity_point", "upper_cap"}:
        raise ValueError("INVALID_DECISION_SCOPE")
    rng = random.Random(seed)
    results: dict[str, object] = {}
    for scenario in SCENARIOS:
        scenario_result = {}
        for analysis_set in ("PRIMARY_CONSERVATIVE", "OBSERVED_CASE"):
            counts = {
                name: 0
                for name in (
                    "scci", "comprehension", "critical_layers", "effort", "stage_error", "joint"
                )
            }
            for _ in range(replications):
                checks = _one_experiment(rng, scenario, per_condition, analysis_set)
                for name, passed in checks.items():
                    counts[name] += int(passed)
            probabilities = {name: count / replications for name, count in counts.items()}
            scenario_result[analysis_set] = {
                "pass_probability": probabilities,
                "joint_mc_standard_error": math.sqrt(
                    probabilities["joint"] * (1 - probabilities["joint"]) / replications
                ),
            }
        results[scenario.name] = scenario_result

    target_joint = [
        results["target"][analysis_set]["pass_probability"]["joint"]
        for analysis_set in ("PRIMARY_CONSERVATIVE", "OBSERVED_CASE")
    ]
    null_joint = [
        results["null_manipulation"][analysis_set]["pass_probability"]["joint"]
        for analysis_set in ("PRIMARY_CONSERVATIVE", "OBSERVED_CASE")
    ]
    decision_prefix = (
        "SYNTHETIC_UPPER_CAP"
        if decision_scope == "upper_cap"
        else "SYNTHETIC_SENSITIVITY_POINT"
    )
    decision = f"{decision_prefix}_{'FEASIBLE' if min(target_joint) >= 0.80 and max(null_joint) <= 0.20 else 'NO_GO'}"
    return {
        "schema_version": "1.0",
        "evidence_class": "SYNTHETIC_ONLY",
        "seed": seed,
        "replications": replications,
        "decision_scope": decision_scope,
        "participants_per_condition": per_condition,
        "total_participants_per_replication": 2 * per_condition,
        "planning_anchor_source": (
            "CONTROL_BASELINE_GATE1_85_COMPLETE_FOUR_MODULE_RESULTS_PER_GROUP"
            if per_condition == 85
            else "CALLER_SUPPLIED_SYNTHETIC_SENSITIVITY_VALUE"
        ),
        "formal_margins": None,
        "formal_sample_size": None,
        "synthetic_sensitivity_thresholds": SYNTHETIC_THRESHOLDS,
        "scenarios": results,
        "decision": decision,
        "limitations": [
            "SYNTHETIC_PARAMETERS_ARE_NOT_REAL_CALIBRATION",
            "LEVEL_A_B_AND_C_EVIDENCE_NOT_PRESENT",
            "FORMAL_MARGINS_AND_SAMPLE_SIZE_NOT_FROZEN",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260906)
    parser.add_argument("--replications", type=int, default=1000)
    parser.add_argument("--per-condition", type=int, default=24)
    parser.add_argument(
        "--decision-scope",
        choices=("sensitivity_point", "upper_cap"),
        default="sensitivity_point",
    )
    args = parser.parse_args()
    report = run_simulation(
        seed=args.seed,
        replications=args.replications,
        per_condition=args.per_condition,
        decision_scope=args.decision_scope,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['decision']}: {args.output}")


if __name__ == "__main__":
    main()
