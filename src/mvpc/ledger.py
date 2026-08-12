"""Immutable evidence-chain ledger linked to witness hashes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mvpc.canonical import hash_canonical
from mvpc.failure_record import FailureRecord


@dataclass
class LedgerEntry:
    sequence: int
    entry_hash: str
    previous_hash: str | None
    payload_hash: str
    kind: str
    created_at: str
    payload: dict[str, Any] = field(default_factory=dict)


class EvidenceLedger:
    def __init__(self) -> None:
        self.entries: list[LedgerEntry] = []
        self._by_prev: dict[str | None, list[str]] = {}

    def __len__(self) -> int:
        return len(self.entries)

    def tip_hash(self) -> str | None:
        return self.entries[-1].entry_hash if self.entries else None

    def append(self, kind: str, payload: dict[str, Any]) -> LedgerEntry:
        prev = self.tip_hash()
        created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        payload_hash = hash_canonical(payload)
        body = {
            "sequence": len(self.entries),
            "previous_hash": prev,
            "payload_hash": payload_hash,
            "kind": kind,
            "created_at": created,
            "payload": payload,
        }
        entry_hash = hash_canonical(body)
        entry = LedgerEntry(
            sequence=body["sequence"],
            entry_hash=entry_hash,
            previous_hash=prev,
            payload_hash=payload_hash,
            kind=kind,
            created_at=created,
            payload=payload,
        )
        kids = self._by_prev.setdefault(prev, [])
        if kids and not payload.get("allow_branch"):
            raise ValueError(
                f"fork detected from parent {prev}: use allow_branch=True to record explicitly"
            )
        kids.append(entry_hash)
        self.entries.append(entry)
        return entry

    def append_witness(self, witness_dict: dict[str, Any]) -> LedgerEntry:
        return self.append("witness", witness_dict)

    def append_failure(self, failure: FailureRecord) -> LedgerEntry:
        return self.append("failure", failure.to_dict())

    def to_list(self) -> list[dict[str, Any]]:
        return [asdict(e) for e in self.entries]

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_list(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "EvidenceLedger":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        led = cls()
        for item in data:
            payload = dict(item.get("payload") or {})
            payload["allow_branch"] = True
            led.append(item["kind"], payload)
        return led

    def verify_chain(self) -> list[str]:
        errors: list[str] = []
        prev = None
        for i, e in enumerate(self.entries):
            if e.previous_hash != prev:
                errors.append(f"entry {i}: previous_hash mismatch")
            stripped = {k: v for k, v in e.payload.items() if k != "allow_branch"}
            if hash_canonical(e.payload) != e.payload_hash and hash_canonical(stripped) != e.payload_hash:
                errors.append(f"entry {i}: payload hash mismatch")
            prev = e.entry_hash
        return errors
