"""Layer 1: HMAC/Ed25519 witness signatures + Merkle AST digests."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

try:
    from nacl.exceptions import BadSignatureError
    from nacl.signing import SigningKey, VerifyKey

    _HAS_NACL = True
except ImportError:  # pragma: no cover
    SigningKey = VerifyKey = BadSignatureError = None  # type: ignore
    _HAS_NACL = False

from mvpc.canonical import canonical_json, sha256_hex


@dataclass
class KeyPair:
    private_key_hex: str
    public_key_hex: str
    algorithm: str  # ed25519 | hmac-sha256


def generate_ed25519_keypair() -> KeyPair:
    if not _HAS_NACL:
        seed = hashlib.sha256(b"mvpc-dev-only-seed").digest()
        return KeyPair(
            private_key_hex=seed.hex(),
            public_key_hex=hashlib.sha256(seed + b"pub").hexdigest(),
            algorithm="hmac-sha256",
        )
    sk = SigningKey.generate()
    return KeyPair(
        private_key_hex=sk.encode().hex(),
        public_key_hex=sk.verify_key.encode().hex(),
        algorithm="ed25519",
    )


def hmac_sign(message: bytes | str, secret_hex: str) -> str:
    if isinstance(message, str):
        message = message.encode("utf-8")
    key = bytes.fromhex(secret_hex)
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def hmac_verify(message: bytes | str, secret_hex: str, signature_hex: str) -> bool:
    expected = hmac_sign(message, secret_hex)
    return hmac.compare_digest(expected, signature_hex)


def sign_manifest(manifest: dict[str, Any], keypair: KeyPair) -> dict[str, Any]:
    payload = {k: v for k, v in manifest.items() if k not in {"signature", "signing_key_id"}}
    msg = canonical_json(payload).encode("utf-8")
    out = dict(manifest)
    if keypair.algorithm == "ed25519" and _HAS_NACL:
        sk = SigningKey(bytes.fromhex(keypair.private_key_hex))
        sig = sk.sign(msg).signature.hex()
        out["signature"] = sig
        out["signing_key_id"] = keypair.public_key_hex[:16]
        out["signature_alg"] = "ed25519"
    else:
        out["signature"] = hmac_sign(msg, keypair.private_key_hex)
        out["signing_key_id"] = keypair.public_key_hex[:16]
        out["signature_alg"] = "hmac-sha256"
    out["payload_hash"] = sha256_hex(msg)
    return out


def verify_manifest_signature(manifest: dict[str, Any], public_or_secret_hex: str) -> bool:
    alg = manifest.get("signature_alg", "hmac-sha256")
    sig = manifest.get("signature")
    if not sig:
        return False
    payload = {
        k: v
        for k, v in manifest.items()
        if k not in {"signature", "signing_key_id", "signature_alg", "payload_hash"}
    }
    msg = canonical_json(payload).encode("utf-8")
    if alg == "ed25519" and _HAS_NACL:
        try:
            vk = VerifyKey(bytes.fromhex(public_or_secret_hex))
            vk.verify(msg, bytes.fromhex(sig))
            return True
        except Exception:
            return False
    return hmac_verify(msg, public_or_secret_hex, sig)


class MerkleTree:
    def __init__(self, leaves: Sequence[str | bytes]) -> None:
        self.leaves = [self._leaf(x) for x in leaves]
        self.layers: list[list[str]] = []
        self.root = self._build()

    @staticmethod
    def _leaf(x: str | bytes) -> str:
        if isinstance(x, str):
            x = x.encode("utf-8")
        return sha256_hex(b"leaf:" + x)

    def _build(self) -> str:
        if not self.leaves:
            empty = sha256_hex(b"empty")
            self.layers = [[empty]]
            return empty
        layer = list(self.leaves)
        self.layers = [layer]
        while len(layer) > 1:
            nxt: list[str] = []
            for i in range(0, len(layer), 2):
                left = layer[i]
                right = layer[i + 1] if i + 1 < len(layer) else left
                nxt.append(sha256_hex(f"node:{left}:{right}".encode()))
            layer = nxt
            self.layers.append(layer)
        return layer[0]

    def proof(self, index: int) -> list[tuple[str, str]]:
        if index < 0 or index >= len(self.leaves):
            raise IndexError(index)
        path: list[tuple[str, str]] = []
        idx = index
        for layer in self.layers[:-1]:
            if idx % 2 == 0:
                sib = layer[idx + 1] if idx + 1 < len(layer) else layer[idx]
                path.append(("R", sib))
            else:
                path.append(("L", layer[idx - 1]))
            idx //= 2
        return path

    @staticmethod
    def verify_proof(leaf: str | bytes, proof: list[tuple[str, str]], root: str) -> bool:
        h = MerkleTree._leaf(leaf)
        for side, sib in proof:
            if side == "R":
                h = sha256_hex(f"node:{h}:{sib}".encode())
            else:
                h = sha256_hex(f"node:{sib}:{h}".encode())
        return h == root

    @staticmethod
    def from_ast_nodes(nodes: Iterable[str]) -> "MerkleTree":
        return MerkleTree(list(nodes))
