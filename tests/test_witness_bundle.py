from mvpc.policy_manifest import template_strict
from mvpc.tcb import TCBDeclaration
from mvpc.traceability import (
    ArtifactKind,
    ProvenanceLabel,
    TraceLink,
    TraceabilityChain,
)
from mvpc.trust_verdicts import TrustVerdict
from mvpc.witness_bundle import WitnessBundle, WitnessEntry


def _chain_ok() -> TraceabilityChain:
    chain = TraceabilityChain()
    for i, kind in enumerate(
        [
            ArtifactKind.NATURAL_LANGUAGE_CLAIM,
            ArtifactKind.STRUCTURED_CLAIM,
            ArtifactKind.FORMAL_STATEMENT,
            ArtifactKind.PROOF_OR_CHECKER_RESULT,
        ]
    ):
        chain.add(
            TraceLink(
                artifact_id=f"A-{i}",
                kind=kind,
                content_hash=f"h{i}",
                provenance=ProvenanceLabel.HUMAN,
                human_approved=True,
            )
        )
    return chain


def test_bundle_manifest_and_summary():
    policy = template_strict()
    tcb = TCBDeclaration(mvpc_version="8.0.0-dev", policy_hash=policy.hash())
    chain = _chain_ok()
    witness = WitnessEntry(
        verdict=TrustVerdict.FORMALLY_CHECKED,
        claim_hash="c" * 64,
        policy_hash=policy.hash(),
        tcb_hash=tcb.hash(),
        traceability_hash=chain.hash(),
        backend_name="lean",
        assumptions=["classical logic"],
    )
    bundle = WitnessBundle(witness=witness, tcb=tcb, policy=policy, traceability=chain)
    assert bundle.is_valid()
    assert "FORMALLY_CHECKED" in bundle.summary()
    assert bundle.manifest()["format_version"] == "1.0.0"


def test_unapproved_ai_blocks_truth_verdict():
    policy = template_strict()
    tcb = TCBDeclaration(mvpc_version="8.0.0-dev", policy_hash=policy.hash())
    chain = TraceabilityChain()
    chain.add(
        TraceLink(
            artifact_id="S-1",
            kind=ArtifactKind.FORMAL_STATEMENT,
            content_hash="h",
            provenance=ProvenanceLabel.AI_PROPOSED,
        )
    )
    witness = WitnessEntry(
        verdict=TrustVerdict.FORMALLY_CHECKED,
        claim_hash="c" * 64,
        policy_hash=policy.hash(),
        tcb_hash=tcb.hash(),
        traceability_hash=chain.hash(),
    )
    bundle = WitnessBundle(witness=witness, tcb=tcb, policy=policy, traceability=chain)
    assert any("unapproved AI" in e for e in bundle.validation_errors())
