from __future__ import annotations

from .errors import RandomizationError
from .models import GateEvidence


def gate_evidence_from_dedup(decision: object) -> GateEvidence:
    if not getattr(decision, "allowed", False):
        raise RandomizationError("DEDUP_RESERVATION_REJECTED")
    reservation_id = getattr(decision, "reservation_id", None)
    audit_event_id = getattr(decision, "audit_event_id", None)
    if not reservation_id or not audit_event_id:
        raise RandomizationError("DEDUP_RECEIPT_INVALID")
    return GateEvidence(
        gate="dedup_reservation",
        reservation_id=reservation_id,
        evidence_id=audit_event_id,
        passed=True,
    )
