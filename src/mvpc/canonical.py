"""Canonical serialization and hashing for MVPC-X artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any, Iterable


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _normalize(value[k]) for k in sorted(value, key=lambda x: str(x))}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, set):
        return sorted((_normalize(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True))
    if isinstance(value, datetime):
        dt = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    return value


def canonical_json(data: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators, UTF-8 text."""
    return json.dumps(_normalize(data), ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def hash_canonical(data: Any) -> str:
    return sha256_hex(canonical_json(data))


def hash_file_bytes(content: bytes) -> str:
    return sha256_hex(content)


class HashBuilder:
    """Accumulate ordered component digests into a composite SHA-256."""

    def __init__(self) -> None:
        self._parts: list[tuple[str, str]] = []

    def add(self, name: str, digest: str) -> "HashBuilder":
        self._parts.append((name, digest))
        return self

    def add_data(self, name: str, data: Any) -> "HashBuilder":
        return self.add(name, hash_canonical(data))

    def digest(self) -> str:
        payload = [{"name": n, "sha256": d} for n, d in sorted(self._parts, key=lambda x: x[0])]
        return hash_canonical(payload)

    def items(self) -> Iterable[tuple[str, str]]:
        return list(self._parts)
