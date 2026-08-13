from mvpc.hardening.cas_doublecheck import cas_verify_with_fallback
from mvpc.hardening.consensus import EngineBallot, multi_engine_vote
from mvpc.hardening.crypto_integrity import (
    MerkleTree,
    generate_ed25519_keypair,
    sign_manifest,
    verify_manifest_signature,
)
from mvpc.hardening.repair_loop import RepairLoop
from mvpc.hardening.transitive_scan import transitive_axiom_scan
from mvpc.phys.interval_guards import audit_cps_interval_and_rates, audit_rate_of_change
from mvpc.trust_verdicts import TrustVerdict


def test_merkle_proof_roundtrip():
    leaves = ["n1", "n2", "n3", "n4"]
    tree = MerkleTree(leaves)
    proof = tree.proof(2)
    assert MerkleTree.verify_proof("n3", proof, tree.root)
    assert not MerkleTree.verify_proof("tampered", proof, tree.root)


def test_manifest_hmac_sign_verify():
    kp = generate_ed25519_keypair()
    m = sign_manifest({"claim_id": "c1", "verdict": "EVIDENCE_SUPPORTED"}, kp)
    key = kp.private_key_hex if kp.algorithm == "hmac-sha256" else kp.public_key_hex
    assert verify_manifest_signature(m, key)


def test_consensus_majority():
    engines = {
        "lean": lambda p: EngineBallot("lean", TrustVerdict.EVIDENCE_SUPPORTED.value, True),
        "isa": lambda p: EngineBallot("isa", TrustVerdict.EVIDENCE_SUPPORTED.value, True),
        "dafny": lambda p: EngineBallot("dafny", TrustVerdict.REJECTED.value, False, "nope"),
    }
    r = multi_engine_vote({}, engines)
    assert r.agreed
    assert r.pass_count == 2
    assert r.consensus_verdict != TrustVerdict.FORMALLY_CHECKED.value


def test_cas_api():
    r = cas_verify_with_fallback("x**2 - y**2", ["x - y"], "x y")
    assert r.engine
    assert isinstance(r.symbolic_ok, bool)


def test_interval_and_rate_guards():
    times = [0.0, 1.0, 2.0]
    v = [0.0, 10.0, 12.0]
    T = [300.0, 301.0, 302.0]
    ok = audit_cps_interval_and_rates(
        times, v, T, max_velocity=100, max_temperature=350, max_accel=20, max_thermal_rate=5
    )
    assert ok.ok
    bad = audit_rate_of_change([0.0, 1.0], [0.0, 100.0], max_abs_rate=10.0)
    assert not bad.ok


def test_repair_loop_zones():
    src = (
        "theorem t : True := by\n"
        "EVOLVE-BLOCK-BEGIN helpers\n"
        "sorry\n"
        "EVOLVE-BLOCK-END\n"
        "trivial\n"
    )
    out = RepairLoop(max_depth=2).run(src, error_trace="sorry")
    assert out.attempts
    assert out.stop_reason in {"repaired", "max_depth", "clean", "no evolve zones"}


def test_transitive_scan_entry_sorry():
    r = transitive_axiom_scan("theorem t : True := by sorry")
    assert not r.clean
    assert r.findings
