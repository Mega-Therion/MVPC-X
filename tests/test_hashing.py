"""Tests for SHA-256 hashing and witness integrity."""
import hashlib
from pathlib import Path

from mvpc.hashing import hash_content, hash_dict, hash_file, verify_witness_hash


def test_hash_content_deterministic():
    a = hash_content("sovereign")
    b = hash_content("sovereign")
    c = hash_content("Sovereign")
    assert a == b
    assert a != c
    assert len(a) == 64


def test_hash_dict_key_order_independent():
    h1 = hash_dict({"b": 2, "a": 1})
    h2 = hash_dict({"a": 1, "b": 2})
    assert h1 == h2


def test_hash_file(tmp_path: Path):
    p = tmp_path / "x.bin"
    p.write_bytes(b"abc123")
    h = hash_file(str(p))
    assert h == hashlib.sha256(b"abc123").hexdigest()


def test_verify_witness_hash_valid():
    payload = {"claim_id": "C-1", "attestation_state": "VERIFIED", "x": 1}
    wh = hash_dict(payload)
    witness = dict(payload)
    witness["witness_hash"] = wh
    assert verify_witness_hash(witness) is True


def test_verify_witness_hash_tamper_detected():
    payload = {"claim_id": "C-1", "attestation_state": "VERIFIED"}
    wh = hash_dict(payload)
    witness = dict(payload)
    witness["witness_hash"] = wh
    witness["attestation_state"] = "REJECTED"
    assert verify_witness_hash(witness) is False


def test_verify_witness_hash_missing_field():
    assert verify_witness_hash({"claim_id": "C-1"}) is False
