"""Tests for Evidence primitive."""
from dataclasses import asdict
from mvpc.evidence import Evidence, EvidenceType


def test_evidence_types_exist():
    assert EvidenceType.FORMAL_PROOF
    assert EvidenceType.STATIC_ANALYSIS
    assert EvidenceType.NATIVE_VERIFICATION
    assert EvidenceType.COMPUTATION


def test_evidence_dataclass_fields():
    ev = Evidence(
        evidence_type=EvidenceType.STATIC_ANALYSIS,
        description="test scan",
        timestamp="2026-08-12T00:00:00+00:00",
        artifact_path="/tmp/a.lean",
        artifact_hash="deadbeef",
        content_summary="ok",
        metadata={"engine": "lean"},
    )
    assert ev.artifact_hash == "deadbeef"
    d = asdict(ev)
    assert d["description"] == "test scan"
    assert d["metadata"]["engine"] == "lean"


def test_evidence_optional_fields_default_none():
    ev = Evidence(
        evidence_type=EvidenceType.DATA_INTEGRITY,
        description="hash only",
        timestamp="t",
    )
    assert ev.artifact_path is None
    assert ev.artifact_hash is None
    assert ev.metadata is None
