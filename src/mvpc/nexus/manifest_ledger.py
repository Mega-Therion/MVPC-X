"""Permanent paired JSON/Markdown Nexus manifests with sequential hash linkage."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mvpc.canonical import hash_canonical

GENESIS_HASH = "MVPC-X-NEXUS-GENESIS-v1"
INDEX_FILE = "ledger-index.json"


@dataclass(frozen=True)
class PermanentManifest:
    schema_version: str
    sequence: int
    created_at: str
    previous_manifest_hash: str
    manifest_hash: str
    status: str
    source_hash: str
    payload: dict[str, Any]

    def unsigned_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("manifest_hash", None)
        return data

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ManifestPair:
    manifest: PermanentManifest
    json_path: str
    markdown_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest.to_dict(),
            "json_path": self.json_path,
            "markdown_path": self.markdown_path,
        }


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_index(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": "mvpc.nexus.ledger.v1", "entries": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise TypeError("Nexus ledger index is malformed")
    return data


def _render_markdown(manifest: PermanentManifest) -> str:
    payload = manifest.payload
    lines = [
        "# MVPC-X Sovereign Nexus Permanent Manifest",
        "",
        f"- **Sequence:** `{manifest.sequence}`",
        f"- **Created:** `{manifest.created_at}`",
        f"- **Status:** `{manifest.status}`",
        f"- **Source SHA-256:** `{manifest.source_hash}`",
        f"- **Previous manifest hash:** `{manifest.previous_manifest_hash}`",
        f"- **Manifest hash:** `{manifest.manifest_hash}`",
        "",
        "## Evidence Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key in (
        "language",
        "policy_verdict",
        "final_verdict",
        "native_completed",
        "integrity_intact",
        "dependency_parity",
    ):
        if key in payload:
            lines.append(f"| `{key}` | `{json.dumps(payload[key], sort_keys=True)}` |")
    lines.extend(
        [
            "",
            "## Canonical Machine Payload",
            "",
            "```json",
            json.dumps(manifest.to_dict(), indent=2, sort_keys=True),
            "```",
            "",
            "> This Markdown companion is an explanation of the JSON manifest. Integrity is established only by recomputing the canonical JSON manifest hash and verifying the previous-manifest link.",
            "",
        ]
    )
    return "\n".join(lines)


class PermanentManifestLedger:
    """Persist a linear, tamper-evident manifest chain in an owner-selected directory."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.index_path = self.directory / INDEX_FILE

    def append(
        self, *, status: str, source_hash: str, payload: dict[str, Any]
    ) -> ManifestPair:
        index = _read_index(self.index_path)
        entries = index["entries"]
        sequence = len(entries)
        previous = entries[-1]["manifest_hash"] if entries else GENESIS_HASH
        unsigned = {
            "schema_version": "mvpc.nexus.manifest.v1",
            "sequence": sequence,
            "created_at": _utc(),
            "previous_manifest_hash": previous,
            "status": status,
            "source_hash": source_hash,
            "payload": payload,
        }
        manifest_hash = hash_canonical(unsigned)
        manifest = PermanentManifest(manifest_hash=manifest_hash, **unsigned)
        stem = f"{sequence:06d}-{manifest_hash[:16]}"
        json_path = self.directory / f"{stem}.json"
        markdown_path = self.directory / f"{stem}.md"
        if json_path.exists() or markdown_path.exists():
            raise FileExistsError(f"Refusing to overwrite permanent manifest {stem}")
        json_path.write_text(
            json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        markdown_path.write_text(_render_markdown(manifest), encoding="utf-8")
        entries.append(
            {
                "sequence": sequence,
                "manifest_hash": manifest_hash,
                "previous_manifest_hash": previous,
                "json_file": json_path.name,
                "markdown_file": markdown_path.name,
            }
        )
        self.index_path.write_text(
            json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return ManifestPair(
            manifest=manifest,
            json_path=str(json_path),
            markdown_path=str(markdown_path),
        )

    def verify(self) -> list[str]:
        """Return integrity errors; an empty list means the stored chain verifies."""
        errors: list[str] = []
        try:
            index = _read_index(self.index_path)
        except (OSError, TypeError, json.JSONDecodeError) as exc:
            return [f"ledger index unreadable: {exc}"]
        previous = GENESIS_HASH
        for expected_sequence, item in enumerate(index["entries"]):
            if item.get("sequence") != expected_sequence:
                errors.append(f"index entry {expected_sequence}: sequence mismatch")
            json_path = self.directory / str(item.get("json_file", ""))
            markdown_path = self.directory / str(item.get("markdown_file", ""))
            if not json_path.is_file() or not markdown_path.is_file():
                errors.append(f"index entry {expected_sequence}: manifest pair missing")
                continue
            try:
                raw = json.loads(json_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(
                    f"index entry {expected_sequence}: JSON unreadable: {exc}"
                )
                continue
            stored = raw.get("manifest_hash")
            unsigned = dict(raw)
            unsigned.pop("manifest_hash", None)
            if raw.get("previous_manifest_hash") != previous:
                errors.append(
                    f"index entry {expected_sequence}: previous hash mismatch"
                )
            if stored != hash_canonical(unsigned):
                errors.append(
                    f"index entry {expected_sequence}: manifest hash mismatch"
                )
            if item.get("manifest_hash") != stored:
                errors.append(f"index entry {expected_sequence}: index hash mismatch")
            markdown = markdown_path.read_text(encoding="utf-8", errors="replace")
            if stored and f"**Manifest hash:** `{stored}`" not in markdown:
                errors.append(
                    f"index entry {expected_sequence}: Markdown companion hash mismatch"
                )
            previous = str(stored or previous)
        return errors
