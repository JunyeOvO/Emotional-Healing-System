from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json
import sqlite3
from types import SimpleNamespace

import pytest

from srp_randomization import (
    AllocationRequest,
    GateEvidence,
    RandomizationError,
    RandomizationStore,
    gate_evidence_from_dedup,
    generate_list,
    load_plan,
    verify_plan,
    write_plan,
)


def _evidence(reservation_id: str) -> tuple[GateEvidence, ...]:
    return tuple(
        GateEvidence(gate, reservation_id, f"{gate}:PASS", True)
        for gate in ("eligibility", "device_readiness", "dedup_reservation")
    )


def test_sealed_file_round_trip_and_tamper_detection(tmp_path) -> None:
    plan = generate_list("stage_1", ("all",), 1, b"sealed-plan-seed-01")
    path = tmp_path / "list.json"
    write_plan(plan, path)
    assert load_plan(path) == plan
    with pytest.raises(RandomizationError, match="LIST_FILE_ALREADY_EXISTS"):
        write_plan(plan, path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["records"][0]["arm"] = "tampered"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RandomizationError, match="LIST_HASH_MISMATCH"):
        load_plan(path)


def test_recomputed_hash_cannot_hide_invalid_arm_probability() -> None:
    plan = generate_list("stage_1", ("all",), 1, b"invalid-plan-seed")
    invalid = replace(
        plan,
        records=(replace(plan.records[0], arm_behavior_probability=0.75), *plan.records[1:]),
    )
    encoded = json.dumps(
        invalid.unsigned_dict(), ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    invalid = replace(invalid, list_hash=f"sha256:{hashlib.sha256(encoded).hexdigest()}")
    with pytest.raises(RandomizationError, match="ARM_PROBABILITY_INVALID"):
        verify_plan(invalid)


def test_two_concurrent_requests_receive_distinct_rows(tmp_path) -> None:
    store = RandomizationStore(tmp_path / "concurrent.sqlite")
    store.import_list(
        generate_list("stage_1", ("all",), 1, b"concurrent-seed-01"),
        actor_role="custodian",
    )

    def allocate(index: int):
        reservation_id = f"RES-{index}"
        return store.allocate_and_reveal(
            AllocationRequest(f"REQ-{index}", "stage_1", "all", reservation_id, "1.0"),
            _evidence(reservation_id),
            actor_role="allocator",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        receipts = list(executor.map(allocate, (1, 2)))
    assert len({receipt.allocation_index for receipt in receipts}) == 2


def test_audit_tail_deletion_is_detected(tmp_path) -> None:
    database = tmp_path / "audit.sqlite"
    store = RandomizationStore(database)
    store.import_list(
        generate_list("stage_1", ("all",), 1, b"audit-chain-seed-01"),
        actor_role="custodian",
    )
    with sqlite3.connect(database) as connection:
        connection.execute("DELETE FROM audit_events")
    report = store.verify_audit_chain(actor_role="auditor")
    assert report.valid is False
    assert report.reason_code == "AUDIT_ANCHOR_MISMATCH"


def test_stored_list_tamper_blocks_reveal(tmp_path) -> None:
    database = tmp_path / "tampered.sqlite"
    store = RandomizationStore(database)
    plan = generate_list("stage_1", ("all",), 1, b"stored-tamper-seed-01")
    store.import_list(plan, actor_role="custodian")
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE allocation_records SET arm = 'tampered' WHERE allocation_index = 1"
        )
    with pytest.raises(RandomizationError, match="LIST_HASH_MISMATCH"):
        store.allocate_and_reveal(
            AllocationRequest("REQ-T", "stage_1", "all", "RES-T", "1.0"),
            _evidence("RES-T"),
            actor_role="allocator",
        )


def test_g02_adapter_exports_only_opaque_receipt_fields() -> None:
    evidence = gate_evidence_from_dedup(
        SimpleNamespace(
            allowed=True,
            reservation_id="RES-G02-1",
            audit_event_id="AUD-G02-1",
            token_version=1,
        )
    )
    assert evidence == GateEvidence(
        "dedup_reservation", "RES-G02-1", "AUD-G02-1", True
    )
    assert set(evidence.__dict__) == {"gate", "reservation_id", "evidence_id", "passed"}
