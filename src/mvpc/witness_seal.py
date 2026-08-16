"""Strict Ed25519 sealing for MVPC-X proof records.

Unlike the development fallback in the older integrity helper, this module never
silently downgrades asymmetric signing to a shared secret. Production witness
seals therefore have an unambiguous trust meaning.
"""
from __future__ import annotations

from typing import Any

from .canonical import canonical_json, hash_canonical

try:
    from nacl.signing import SigningKey, VerifyKey
except ImportError:  # pragma: no cover
    SigningKey = VerifyKey = None  # type: ignore


def _require_nacl() -> None:
    if SigningKey is None or VerifyKey is None:
        raise RuntimeError("PyNaCl is required for strict MVPC-X witness sealing")


def generate_signing_keypair() -> tuple[str, str]:
    _require_nacl()
    signing_key = SigningKey.generate()
    return signing_key.encode().hex(), signing_key.verify_key.encode().hex()


def seal_payload(payload: dict[str, Any], private_key_hex: str) -> dict[str, Any]:
    _require_nacl()
    key = SigningKey(bytes.fromhex(private_key_hex))
    body = canonical_json(payload).encode("utf-8")
    signature = key.sign(body).signature.hex()
    return {
        "schema": "mvpcx.witness-seal/v1",
        "payload": payload,
        "payload_hash": hash_canonical(payload),
        "signature": signature,
        "signature_alg": "ed25519",
        "signing_key_id": key.verify_key.encode().hex(),
    }


def verify_sealed_payload(bundle: dict[str, Any]) -> bool:
    _require_nacl()
    if bundle.get("signature_alg") != "ed25519":
        return False
    payload = bundle.get("payload")
    signature = bundle.get("signature")
    public_key = bundle.get("signing_key_id")
    if not isinstance(payload, dict) or not signature or not public_key:
        return False
    if bundle.get("payload_hash") != hash_canonical(payload):
        return False
    try:
        VerifyKey(bytes.fromhex(public_key)).verify(
            canonical_json(payload).encode("utf-8"), bytes.fromhex(signature)
        )
        return True
    except Exception:
        return False
