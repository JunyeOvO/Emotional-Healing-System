from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

import jsonschema


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from srp_randomization import load_plan  # noqa: E402


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _forbidden_keys(payload: object) -> set[str]:
    forbidden = {"phone", "email", "hmac", "subject_token", "contact"}
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower() in forbidden:
                found.add(key)
            found.update(_forbidden_keys(value))
    elif isinstance(payload, list):
        for value in payload:
            found.update(_forbidden_keys(value))
    return found


def verify() -> list[str]:
    errors: list[str] = []
    list_schema = _read(ROOT / "contracts/randomization-list-v1.schema.json")
    plans = {
        "stage_1": load_plan(ROOT / "fixtures/synthetic/stage_1_list_v1.json"),
        "stage_3": load_plan(ROOT / "fixtures/synthetic/stage_3_list_v1.json"),
    }
    for stage, plan in plans.items():
        try:
            jsonschema.Draft202012Validator(list_schema).validate(plan.to_dict())
        except jsonschema.ValidationError as error:
            errors.append(f"{stage}:SCHEMA:{error.json_path}")
        if plan.stage != stage or len(plan.records) != 192:
            errors.append(f"{stage}:SHAPE")
        if _forbidden_keys(plan.to_dict()):
            errors.append(f"{stage}:FORBIDDEN_KEYS")

    stage_1_counts = Counter(record.arm for record in plans["stage_1"].records)
    stage_3_counts = Counter(record.arm for record in plans["stage_3"].records)
    if stage_1_counts != {"scene_native": 96, "abstract_pacer": 96}:
        errors.append("stage_1:ARM_COUNTS")
    if stage_3_counts != {"frozen_policy": 96, "balanced_random": 96}:
        errors.append("stage_3:ARM_COUNTS")

    probability = _read(ROOT / "evidence/probability_report_v1.json")
    if probability.get("checked_sequences") != 24 or probability.get(
        "contract_validation"
    ) != "PASS":
        errors.append("PROBABILITY_REPORT")
    balance = _read(ROOT / "evidence/balance_report_v1.json")
    if balance.get("balance_basis") != "assigned" or not all(
        item.get("balanced_by_assignment") for item in balance.get("strata", [])
    ):
        errors.append("BALANCE_REPORT")
    duplicate = _read(ROOT / "fixtures/synthetic/duplicate_audit_fixture_v1.json")
    if not duplicate.get("same_allocation") or not duplicate.get("audit", {}).get("valid"):
        errors.append("DUPLICATE_AUDIT")
    summary = _read(ROOT / "evidence/x01_validation_report_v1.json")
    for stage, plan in plans.items():
        if summary.get(stage, {}).get("list_hash") != plan.list_hash:
            errors.append(f"{stage}:SUMMARY_HASH")
    return errors


def main() -> int:
    errors = verify()
    if errors:
        print("X01_VERIFY_FAIL " + ",".join(errors))
        return 1
    print("X01_VERIFY_PASS lists=2 records=384 stage1=192 stage3=192")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
