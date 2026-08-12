"""Tests for Claim primitive and factory."""
import json
from mvpc.claim import Claim, create_claim, generate_claim_id
from mvpc.provenance import Provenance, SourceType
from mvpc.trust import AttestationState, CoverageReport, Finding, Severity
from mvpc.evidence import Evidence, EvidenceType


def test_generate_claim_id_format():
    cid = generate_claim_id()
    assert cid.startswith("C-")
    parts = cid.split("-")
    assert len(parts) == 3
    assert parts[1].isdigit()
    assert len(parts[2]) == 6


def test_create_claim_defaults():
    prov = Provenance(
        source_type=SourceType.HUMAN,
        origin_description="unit test",
        timestamp="2026-08-12T00:00:00+00:00",
    )
    claim = create_claim(
        statement="1 + 1 = 2",
        origin=SourceType.HUMAN,
        scope="arithmetic",
        definitions={"1": "one"},
        provenance=prov,
    )
    assert isinstance(claim, Claim)
    assert claim.statement == "1 + 1 = 2"
    assert claim.attestation_state == AttestationState.UNVERIFIED
    assert claim.evidence == []
    assert claim.findings == []
    assert isinstance(claim.coverage, CoverageReport)
    assert claim.id.startswith("C-")


def test_claim_to_dict_serializes_enums():
    prov = Provenance(
        source_type=SourceType.AI,
        origin_description="model draft",
        timestamp="2026-08-12T00:00:00+00:00",
    )
    claim = create_claim("P", SourceType.AI, "scope", {}, prov)
    claim.findings.append(
        Finding("LEAN_SORRY", Severity.VIOLATION, "sorry", "LeanStatic", line=3)
    )
    claim.evidence.append(
        Evidence(
            EvidenceType.STATIC_ANALYSIS,
            "scan",
            "2026-08-12T00:00:00+00:00",
            artifact_path="x.lean",
            artifact_hash="abc",
        )
    )
    claim.attestation_state = AttestationState.REJECTED
    d = claim.to_dict()
    assert d["origin"] == "AI"
    assert d["attestation_state"] == "REJECTED"
    assert d["findings"][0]["severity"] == "VIOLATION"
    assert d["evidence"][0]["evidence_type"] == "STATIC_ANALYSIS"
    raw = claim.to_json()
    loaded = json.loads(raw)
    assert loaded["id"] == claim.id


def test_claim_human_signoff_optional():
    prov = Provenance(SourceType.UNKNOWN, "t", "t")
    claim = create_claim("s", SourceType.UNKNOWN, "s", {}, prov)
    assert claim.human_signoff is None
    claim.human_signoff = {
        "signer": "Dr. X",
        "timestamp": "2026-08-12T00:00:00+00:00",
        "notes": "ok",
        "accepted": True,
    }
    assert claim.to_dict()["human_signoff"]["signer"] == "Dr. X"
