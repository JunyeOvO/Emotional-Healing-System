from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2] / "08-随机化"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verify_x01 import verify


def test_checked_in_x01_evidence_is_self_consistent() -> None:
    assert verify() == []
