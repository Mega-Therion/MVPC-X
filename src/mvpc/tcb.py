"""Trusted computing base declarations for verification runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from mvpc.canonical import hash_canonical


@dataclass
class BackendTCB:
    name: str
    version: str
    binary_hash: str | None = None
    command: list[str] = field(default_factory=list)


@dataclass
class TCBDeclaration:
    mvpc_version: str
    mvpc_package_hash: str | None = None
    python_version: str | None = None
    python_binary_hash: str | None = None
    dependency_lock_hash: str | None = None
    policy_hash: str | None = None
    os_release: str | None = None
    container_or_nix_digest: str | None = None
    backends: list[BackendTCB] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def __post_init__(self) -> None:
        if not self.limitations:
            self.limitations = list(DEFAULT_LIMITATIONS)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def hash(self) -> str:
        return hash_canonical(self.to_dict())


DEFAULT_LIMITATIONS = (
    "Does not prove kernel/firmware integrity.",
    "Does not prove absence of privileged runtime memory manipulation.",
    "Does not prove that a formalization captures intended real-world meaning without human sign-off.",
    "Does not prove signing-key non-compromise.",
    "Hashes establish integrity of defined artifacts, not abstract truth.",
)


@dataclass
class TrustPolicy:
    """Accepted tools, hashes, and keys for a verification environment."""

    policy_id: str
    accepted_backend_hashes: dict[str, str] = field(default_factory=dict)
    accepted_signing_key_ids: list[str] = field(default_factory=list)
    require_container_digest: bool = False

    def allows_backend(self, name: str, binary_hash: str | None) -> bool:
        expected = self.accepted_backend_hashes.get(name)
        if expected is None:
            return True
        return binary_hash == expected
